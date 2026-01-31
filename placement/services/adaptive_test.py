# placement/services/adaptive_test.py

import math
import random
from typing import Optional, Dict, List
from django.utils import timezone

from ..models import (
    PlacementTest, PlacementQuestion, PlacementAnswer,
    UserLearningProfile, SkillCategory, DifficultyLevel
)


class AdaptivePlacementEngine:
    """
    Computer Adaptive Test (CAT) sử dụng Item Response Theory (IRT)
    3-Parameter Logistic Model (3PL)
    """
    
    # Cấu hình test
    MIN_QUESTIONS = 20  # Tối thiểu
    MAX_QUESTIONS = 40  # Tối đa
    STOP_SE_THRESHOLD = 0.30  # Dừng khi Standard Error đủ nhỏ
    
    # Phân bổ câu hỏi theo skill
    SKILL_DISTRIBUTION = {
        'L1': 2, 'L2': 3, 'L3': 4, 'L4': 3,  # Listening: 12
        'R5': 5, 'R6': 3, 'R7': 5,  # Reading: 13
        'VOC': 8, 'GRM': 7,  # Vocab & Grammar: 15
    }  # Total: 40
    
    def __init__(self, test: PlacementTest):
        self.test = test
        self.user = test.user
        self.answered_ids = set(
            test.answers.values_list('question_id', flat=True)
        )
    
    def probability_correct(
        self, 
        ability: float, 
        difficulty: float, 
        discrimination: float = 1.0,
        guessing: float = 0.25
    ) -> float:
        """
        3PL IRT Model: P(correct) = c + (1-c) / (1 + e^(-a(θ-b)))
        
        Args:
            ability (θ): Năng lực người thi (-3 to +3)
            difficulty (b): Độ khó câu hỏi (-3 to +3)  
            discrimination (a): Độ phân biệt (0.5 to 2.5)
            guessing (c): Xác suất đoán đúng (thường 0.25 cho 4 options)
        """
        exponent = -discrimination * (ability - difficulty)
        # Avoid overflow
        if exponent > 700:
            return guessing
        if exponent < -700:
            return 1.0
        return guessing + (1 - guessing) / (1 + math.exp(exponent))
    
    def information_function(
        self,
        ability: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.25
    ) -> float:
        """
        Fisher Information: Đo lường độ chính xác của ước lượng ability
        Câu hỏi có information cao nhất khi difficulty ≈ ability
        """
        p = self.probability_correct(ability, difficulty, discrimination, guessing)
        q = 1 - p
        
        if p <= guessing or p >= 1:
            return 0
        
        numerator = (discrimination ** 2) * ((p - guessing) ** 2) * q
        denominator = ((1 - guessing) ** 2) * p
        
        if denominator == 0:
            return 0
        return numerator / denominator
    
    def select_next_question(self) -> Optional[PlacementQuestion]:
        """
        Chọn câu hỏi tiếp theo với Maximum Information criterion
        Kết hợp với content balancing
        """
        current_ability = self.test.current_ability
        
        # Xác định skill cần hỏi tiếp (content balancing)
        skill_counts = self._get_skill_counts()
        target_skill = self._get_next_skill(skill_counts)
        
        # Lấy câu hỏi chưa trả lời của skill đó
        candidates = PlacementQuestion.objects.filter(
            skill=target_skill,
            is_active=True
        ).exclude(
            id__in=self.answered_ids
        )
        
        if not candidates.exists():
            # Fallback: lấy từ skill khác chưa đủ quota
            for skill, target_count in self.SKILL_DISTRIBUTION.items():
                current_count = skill_counts.get(skill, 0)
                if current_count < target_count:
                    candidates = PlacementQuestion.objects.filter(
                        skill=skill,
                        is_active=True
                    ).exclude(id__in=self.answered_ids)
                    if candidates.exists():
                        break
        
        if not candidates.exists():
            # Final fallback: any active question not answered
            candidates = PlacementQuestion.objects.filter(
                is_active=True
            ).exclude(id__in=self.answered_ids)
        
        if not candidates.exists():
            return None
        
        # Tính information cho từng câu
        best_question = None
        max_info = -1
        
        for q in candidates[:50]:  # Limit để tối ưu performance
            info = self.information_function(
                current_ability,
                q.irt_difficulty,
                q.irt_discrimination,
                q.irt_guessing
            )
            
            # Thêm randomness nhỏ để tránh lặp lại pattern
            info += random.uniform(0, 0.1)
            
            if info > max_info:
                max_info = info
                best_question = q
        
        return best_question
    
    def _get_skill_counts(self) -> Dict[str, int]:
        """Đếm số câu đã hỏi theo skill"""
        counts = {skill.value: 0 for skill in SkillCategory}
        for answer in self.test.answers.select_related('question'):
            counts[answer.question.skill] = counts.get(answer.question.skill, 0) + 1
        return counts
    
    def _get_next_skill(self, current_counts: Dict[str, int]) -> str:
        """Chọn skill tiếp theo dựa trên phân bổ mục tiêu"""
        # Tính tỷ lệ hoàn thành của mỗi skill
        completion_ratios = {}
        for skill, target in self.SKILL_DISTRIBUTION.items():
            current = current_counts.get(skill, 0)
            completion_ratios[skill] = current / target if target > 0 else 1
        
        # Chọn skill có tỷ lệ hoàn thành thấp nhất
        return min(completion_ratios, key=completion_ratios.get)
    
    def update_ability(self, question: PlacementQuestion, is_correct: bool) -> float:
        """
        Cập nhật ước lượng ability sau mỗi câu trả lời
        Sử dụng Newton-Raphson method (simplified)
        """
        current_ability = self.test.current_ability
        
        # Probability of correct answer at current ability
        p = self.probability_correct(
            current_ability,
            question.irt_difficulty,
            question.irt_discrimination,
            question.irt_guessing
        )
        
        # Update step based on response
        response = 1 if is_correct else 0
        step_size = 0.5 / (1 + self.test.questions_answered * 0.1)  # Decreasing step size
        
        # Gradient of log-likelihood
        if is_correct:
            gradient = question.irt_discrimination * (1 - p) * (p - question.irt_guessing) / (p * (1 - question.irt_guessing))
        else:
            gradient = -question.irt_discrimination * (p - question.irt_guessing) / ((1 - p) * (1 - question.irt_guessing))
        
        new_ability = current_ability + step_size * gradient
        
        # Bound ability to reasonable range
        new_ability = max(-3, min(3, new_ability))
        
        return new_ability
    
    def calculate_standard_error(self) -> float:
        """
        Tính Standard Error of Estimation (SEE)
        SE = 1 / sqrt(sum of information)
        """
        total_info = 0
        current_ability = self.test.current_ability
        
        for answer in self.test.answers.select_related('question'):
            q = answer.question
            total_info += self.information_function(
                current_ability,
                q.irt_difficulty,
                q.irt_discrimination,
                q.irt_guessing
            )
        
        if total_info == 0:
            return 3.0  # Maximum uncertainty
        
        return 1 / math.sqrt(total_info)
    
    def should_stop(self) -> bool:
        """Kiểm tra điều kiện dừng test"""
        num_questions = self.test.questions_answered
        
        # Dừng nếu đủ câu hỏi tối đa
        if num_questions >= self.MAX_QUESTIONS:
            return True
        
        # Chưa đủ câu hỏi tối thiểu
        if num_questions < self.MIN_QUESTIONS:
            return False
        
        # Dừng nếu SE đủ nhỏ
        se = self.calculate_standard_error()
        return se <= self.STOP_SE_THRESHOLD
    
    def ability_to_toeic_score(self, ability: float) -> int:
        """
        Convert IRT ability (-3 to +3) sang điểm TOEIC (10-990)
        """
        # Linear mapping với adjustment
        # ability -3 ≈ 10, ability 0 ≈ 500, ability +3 ≈ 990
        score = 500 + (ability * 163)
        return max(10, min(990, round(score / 5) * 5))
    
    def finalize_test(self) -> Dict:
        """Hoàn thành test và tính kết quả cuối"""
        
        # Tính skill scores
        skill_scores = self._calculate_skill_scores()
        
        # Tính điểm tổng
        listening_skills = ['L1', 'L2', 'L3', 'L4']
        reading_skills = ['R5', 'R6', 'R7', 'VOC', 'GRM']
        
        listening_abilities = [skill_scores.get(s, 0) for s in listening_skills if s in skill_scores]
        reading_abilities = [skill_scores.get(s, 0) for s in reading_skills if s in skill_scores]
        
        listening_ability = sum(listening_abilities) / len(listening_abilities) if listening_abilities else 0
        reading_ability = sum(reading_abilities) / len(reading_abilities) if reading_abilities else 0
        
        # Convert to TOEIC scores (each section max 495)
        listening_score = self.ability_to_toeic_score(listening_ability) // 2
        reading_score = self.ability_to_toeic_score(reading_ability) // 2
        total_score = listening_score + reading_score
        
        # Confidence interval based on SE
        se = self.calculate_standard_error()
        confidence_interval = int(se * 163)  # Convert SE to TOEIC scale
        
        # Update test
        self.test.estimated_score = total_score
        self.test.estimated_listening = listening_score
        self.test.estimated_reading = reading_score
        self.test.confidence_interval = confidence_interval
        self.test.skill_scores = skill_scores
        self.test.status = PlacementTest.TestStatus.COMPLETED
        self.test.completed_at = timezone.now()
        self.test.save()
        
        # Update or create UserLearningProfile
        self._update_user_profile(total_score, skill_scores)
        
        return {
            'total_score': total_score,
            'listening_score': listening_score,
            'reading_score': reading_score,
            'confidence_interval': confidence_interval,
            'skill_scores': skill_scores,
            'questions_answered': self.test.questions_answered
        }
    
    def _calculate_skill_scores(self) -> Dict[str, float]:
        """Tính điểm cho từng skill"""
        skill_results = {}
        
        for answer in self.test.answers.select_related('question'):
            skill = answer.question.skill
            if skill not in skill_results:
                skill_results[skill] = {'correct': 0, 'total': 0, 'ability_sum': 0}
            
            skill_results[skill]['total'] += 1
            skill_results[skill]['ability_sum'] += answer.ability_after
            if answer.is_correct:
                skill_results[skill]['correct'] += 1
        
        skill_scores = {}
        for skill, data in skill_results.items():
            if data['total'] > 0:
                # Use average ability after answering questions in this skill
                avg_ability = data['ability_sum'] / data['total']
                skill_scores[skill] = round(avg_ability, 2)
        
        return skill_scores
    
    def _update_user_profile(self, total_score: int, skill_scores: Dict[str, float]):
        """Update UserLearningProfile with test results"""
        profile, created = UserLearningProfile.objects.get_or_create(
            user=self.user,
            defaults={'estimated_score': total_score}
        )
        
        # Update estimated score
        profile.estimated_score = total_score
        
        # Determine current level
        if total_score < 300:
            profile.current_level = DifficultyLevel.BEGINNER
        elif total_score < 400:
            profile.current_level = DifficultyLevel.ELEMENTARY
        elif total_score < 600:
            profile.current_level = DifficultyLevel.INTERMEDIATE
        elif total_score < 800:
            profile.current_level = DifficultyLevel.UPPER_INTERMEDIATE
        elif total_score < 900:
            profile.current_level = DifficultyLevel.ADVANCED
        else:
            profile.current_level = DifficultyLevel.EXPERT
        
        # Update skill proficiency
        for skill, ability in skill_scores.items():
            # Convert ability (-3 to +3) to proficiency (0 to 1)
            proficiency = (ability + 3) / 6
            proficiency = max(0, min(1, proficiency))
            
            profile.skill_proficiency[skill] = {
                'level': round(proficiency, 3),
                'confidence': 0.8,  # High confidence from placement test
                'last_updated': str(timezone.now().date())
            }
        
        profile.save()
        
        # Recalculate weak/strong skills
        profile.recalculate_weak_strong_skills()
