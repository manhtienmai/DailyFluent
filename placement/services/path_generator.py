# placement/services/path_generator.py

from typing import List, Dict
from django.utils import timezone
from datetime import timedelta

from ..models import (
    UserLearningProfile, LearningPath, LearningMilestone,
    DifficultyLevel, SkillCategory
)


class LearningPathGenerator:
    """
    Generate personalized learning path dựa trên:
    1. Kết quả Placement Test
    2. Mục tiêu điểm số
    3. Thời gian có sẵn
    """
    
    # Điểm cần thiết cho mỗi level
    LEVEL_THRESHOLDS = {
        DifficultyLevel.BEGINNER: 295,
        DifficultyLevel.ELEMENTARY: 395,
        DifficultyLevel.INTERMEDIATE: 595,
        DifficultyLevel.UPPER_INTERMEDIATE: 795,
        DifficultyLevel.ADVANCED: 895,
        DifficultyLevel.EXPERT: 990,
    }
    
    # Weight cho từng skill khi prioritize
    SKILL_WEIGHTS = {
        'R5': 1.5,  # Grammar có weight cao vì ảnh hưởng nhiều
        'VOC': 1.4,
        'L3': 1.2,
        'R7': 1.2,
        'L4': 1.1,
        'R6': 1.0,
        'L2': 0.9,
        'L1': 0.8,
        'GRM': 1.3,
    }
    
    def __init__(self, user, target_score: int, target_date=None):
        self.user = user
        self.profile, _ = UserLearningProfile.objects.get_or_create(user=user)
        self.target_score = target_score
        self.target_date = target_date
        self.current_score = self.profile.estimated_score
    
    def generate(self) -> LearningPath:
        """Main method: Generate learning path"""
        
        # 1. Phân tích gap
        gap_analysis = self._analyze_skill_gaps()
        
        # 2. Xác định priority skills
        priority_skills = self._prioritize_skills(gap_analysis)
        
        # 3. Tính thời gian cần thiết
        estimated_days = self._estimate_duration(gap_analysis)
        
        # 4. Deactivate old paths
        LearningPath.objects.filter(
            user=self.user,
            is_active=True
        ).update(is_active=False)
        
        # 5. Tạo path
        path = LearningPath.objects.create(
            user=self.user,
            name=self._generate_path_name(),
            description=self._generate_description(gap_analysis),
            target_score=self.target_score,
            target_skills=priority_skills,
            estimated_days=estimated_days
        )
        
        # 6. Tạo milestones
        self._create_milestones(path, priority_skills, gap_analysis)
        
        # 7. Update user profile
        self.profile.target_score = self.target_score
        self.profile.target_date = self.target_date
        self.profile.weak_skills = priority_skills[:3]
        self.profile.save(update_fields=['target_score', 'target_date', 'weak_skills', 'updated_at'])
        
        return path
    
    def _analyze_skill_gaps(self) -> Dict:
        """Phân tích khoảng cách giữa hiện tại và mục tiêu"""
        skill_proficiency = self.profile.skill_proficiency
        
        # Mức proficiency cần để đạt target score
        target_proficiency = self._score_to_proficiency(self.target_score)
        
        gaps = {}
        for skill in SkillCategory:
            current = skill_proficiency.get(skill.value, {}).get('level', 0.5)
            gap = max(0, target_proficiency - current)
            gaps[skill.value] = {
                'current': current,
                'target': target_proficiency,
                'gap': gap,
                'improvement_needed': gap / target_proficiency if target_proficiency > 0 else 0
            }
        
        return gaps
    
    def _score_to_proficiency(self, score: int) -> float:
        """Convert TOEIC score to proficiency (0-1)"""
        return min(1.0, score / 990)
    
    def _prioritize_skills(self, gaps: Dict) -> List[str]:
        """Sắp xếp skills theo độ ưu tiên cần cải thiện"""
        scored_skills = []
        for skill, data in gaps.items():
            priority_score = data['gap'] * self.SKILL_WEIGHTS.get(skill, 1.0)
            scored_skills.append((skill, priority_score))
        
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        return [skill for skill, _ in scored_skills]
    
    def _estimate_duration(self, gaps: Dict) -> int:
        """Ước tính số ngày cần để đạt mục tiêu"""
        score_gap = self.target_score - self.current_score
        
        if score_gap <= 0:
            return 30  # Minimum 30 days for maintenance
        
        # Giả định: Học đều đặn 30 phút/ngày
        # Tăng trung bình 1-2 điểm/ngày cho beginner
        # Tăng 0.5-1 điểm/ngày cho advanced
        
        if self.current_score < 400:
            points_per_day = 1.5
        elif self.current_score < 600:
            points_per_day = 1.0
        elif self.current_score < 800:
            points_per_day = 0.7
        else:
            points_per_day = 0.4
        
        estimated_days = int(score_gap / points_per_day)
        return max(30, min(365, estimated_days))  # 1 tháng - 1 năm
    
    def _generate_path_name(self) -> str:
        """Tạo tên cho learning path"""
        if self.target_score >= 900:
            return "TOEIC Master Path"
        elif self.target_score >= 700:
            return "Advanced TOEIC Journey"
        elif self.target_score >= 500:
            return "Intermediate TOEIC Builder"
        else:
            return "TOEIC Foundation Course"
    
    def _generate_description(self, gaps: Dict) -> str:
        """Tạo mô tả cho path"""
        weak_skills = sorted(gaps.items(), key=lambda x: x[1]['gap'], reverse=True)[:3]
        skill_names = [SkillCategory(s[0]).label for s in weak_skills]
        
        return (
            f"Lộ trình cá nhân hóa từ {self.current_score} → {self.target_score} điểm TOEIC. "
            f"Tập trung cải thiện: {', '.join(skill_names)}."
        )
    
    def _create_milestones(
        self, 
        path: LearningPath, 
        priority_skills: List[str],
        gaps: Dict
    ):
        """Tạo các milestone cho path"""
        milestones_data = []
        
        # Milestone 1: Foundation - Vocabulary cơ bản
        milestones_data.append({
            'title': '🎯 Foundation: Core Vocabulary',
            'description': 'Xây dựng nền tảng từ vựng TOEIC cơ bản',
            'target_skill': 'VOC',
            'target_proficiency': 0.5,
        })
        
        # Milestone 2-4: Focus on weak skills
        for i, skill in enumerate(priority_skills[:3]):
            milestones_data.append({
                'title': f'📚 Skill Focus: {SkillCategory(skill).label}',
                'description': f'Tập trung cải thiện {SkillCategory(skill).label}',
                'target_skill': skill,
                'target_proficiency': min(0.8, gaps[skill]['current'] + 0.2),
            })
        
        # Milestone 5: Practice Tests
        milestones_data.append({
            'title': '📝 Practice Tests',
            'description': 'Luyện đề và làm quen format thi',
            'target_skill': None,
            'target_proficiency': 0.7,
        })
        
        # Milestone 6: Final Review
        milestones_data.append({
            'title': '🏆 Final Review & Mock Test',
            'description': 'Ôn tập tổng hợp và thi thử',
            'target_skill': None,
            'target_proficiency': 0.8,
        })
        
        # Create milestone objects
        for order, data in enumerate(milestones_data, 1):
            LearningMilestone.objects.create(
                path=path,
                order=order,
                title=data['title'],
                description=data['description'],
                target_skill=data.get('target_skill'),
                target_proficiency=data['target_proficiency'],
                is_unlocked=(order == 1)  # Chỉ unlock milestone đầu tiên
            )
    
    def _get_appropriate_level(self, current_proficiency: float) -> int:
        """Xác định level phù hợp dựa trên proficiency hiện tại"""
        if current_proficiency < 0.3:
            return DifficultyLevel.BEGINNER
        elif current_proficiency < 0.5:
            return DifficultyLevel.ELEMENTARY
        elif current_proficiency < 0.65:
            return DifficultyLevel.INTERMEDIATE
        elif current_proficiency < 0.8:
            return DifficultyLevel.UPPER_INTERMEDIATE
        else:
            return DifficultyLevel.ADVANCED
