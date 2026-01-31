# placement/services/daily_recommender.py

from typing import List, Dict, Optional
from django.utils import timezone
from datetime import date, timedelta

from ..models import (
    UserLearningProfile, LearningPath, LearningMilestone,
    DailyLesson, SkillProgress, SkillCategory
)


class DailyRecommendationEngine:
    """
    Generate daily learning recommendations dựa trên:
    1. FSRS due cards (từ vocab app)
    2. Learning path progress  
    3. Weak skills cần practice
    4. User preferences
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = self._get_or_create_profile()
        self.today = date.today()
    
    def _get_or_create_profile(self) -> UserLearningProfile:
        """Get or create user learning profile"""
        profile, _ = UserLearningProfile.objects.get_or_create(user=self.user)
        return profile
    
    def generate_daily_lesson(self) -> DailyLesson:
        """Main method: Generate today's recommendations"""
        
        # Check if already exists
        lesson, created = DailyLesson.objects.get_or_create(
            user=self.user,
            date=self.today,
            defaults={
                'target_minutes': self.profile.preferred_session_length
            }
        )
        
        if not created and lesson.recommended_activities:
            return lesson  # Already generated
        
        activities = []
        
        # 1. FSRS Due Reviews (highest priority)
        due_reviews = self._get_due_reviews()
        if due_reviews:
            activities.append({
                'type': 'vocab_review',
                'priority': 1,
                'count': min(30, due_reviews['count']),
                'estimated_minutes': min(30, due_reviews['count']) * 0.5,
                'reason': f"{due_reviews['count']} từ cần ôn tập hôm nay",
                'data': {'due_count': due_reviews['count']}
            })
        
        # 2. Learning Path Progress
        path_activity = self._get_path_activity()
        if path_activity:
            activities.append(path_activity)
        
        # 3. Weak Skill Practice
        weak_skill_activity = self._get_weak_skill_practice()
        if weak_skill_activity:
            activities.append(weak_skill_activity)
        
        # 4. New Vocabulary (if time allows)
        if self._has_time_for_new_content(activities):
            new_vocab = self._get_new_vocabulary()
            if new_vocab:
                activities.append(new_vocab)
        
        # 5. Listening Practice (mix it up)
        if self._should_add_listening():
            activities.append({
                'type': 'listening_practice',
                'priority': 4,
                'count': 5,
                'estimated_minutes': 10,
                'reason': 'Luyện nghe hàng ngày',
                'data': {'part': self._get_random_listening_part()}
            })
        
        # Sort by priority
        activities.sort(key=lambda x: x['priority'])
        
        lesson.recommended_activities = activities
        lesson.save(update_fields=['recommended_activities'])
        
        return lesson
    
    def _get_due_reviews(self) -> Optional[Dict]:
        """Lấy số lượng cards cần review theo FSRS"""
        try:
            from vocab.models import FsrsCardStateEn
            due_count = FsrsCardStateEn.objects.filter(
                user=self.user,
                due__lte=timezone.now()
            ).count()
            
            if due_count > 0:
                return {'count': due_count}
        except ImportError:
            pass
        return None
    
    def _get_path_activity(self) -> Optional[Dict]:
        """Lấy activity từ learning path hiện tại"""
        active_path = LearningPath.objects.filter(
            user=self.user,
            is_active=True
        ).first()
        
        if not active_path:
            return None
        
        # Tìm milestone đang active
        current_milestone = active_path.milestones.filter(
            is_unlocked=True,
            is_completed=False
        ).first()
        
        if not current_milestone:
            return None
        
        # Xác định content cần học
        if current_milestone.vocabulary_set_ids:
            return {
                'type': 'path_vocab',
                'priority': 2,
                'count': 15,
                'estimated_minutes': 10,
                'reason': f'Tiếp tục: {current_milestone.title}',
                'data': {
                    'milestone_id': current_milestone.id,
                    'vocab_set_ids': current_milestone.vocabulary_set_ids[:2],
                    'milestone_title': current_milestone.title
                }
            }
        
        if current_milestone.exam_template_ids:
            return {
                'type': 'path_exam',
                'priority': 2,
                'count': 1,
                'estimated_minutes': 20,
                'reason': f'Luyện đề: {current_milestone.title}',
                'data': {
                    'milestone_id': current_milestone.id,
                    'exam_template_ids': current_milestone.exam_template_ids[:1],
                    'milestone_title': current_milestone.title
                }
            }
        
        # Default: general skill practice
        if current_milestone.target_skill:
            return {
                'type': 'skill_practice',
                'priority': 2,
                'count': 10,
                'estimated_minutes': 8,
                'reason': f'Milestone: {current_milestone.title}',
                'data': {
                    'milestone_id': current_milestone.id,
                    'skill': current_milestone.target_skill
                }
            }
        
        return None
    
    def _get_weak_skill_practice(self) -> Optional[Dict]:
        """Tạo bài tập cho skill yếu nhất"""
        weak_skills = self.profile.weak_skills
        
        if not weak_skills:
            return None
        
        weakest = weak_skills[0]
        skill_level = self.profile.get_skill_level(weakest)
        
        return {
            'type': 'skill_practice',
            'priority': 3,
            'count': 10,
            'estimated_minutes': 8,
            'reason': f'Cải thiện điểm yếu: {SkillCategory(weakest).label}',
            'data': {
                'skill': weakest,
                'current_level': skill_level
            }
        }
    
    def _has_time_for_new_content(self, activities: List[Dict]) -> bool:
        """Kiểm tra còn thời gian cho content mới không"""
        total_minutes = sum(a.get('estimated_minutes', 0) for a in activities)
        return total_minutes < self.profile.preferred_session_length - 5
    
    def _get_new_vocabulary(self) -> Optional[Dict]:
        """Gợi ý học từ vựng mới"""
        try:
            from vocab.models import VocabularySet, UserSetProgress
            
            # Tìm set chưa hoàn thành
            completed_set_ids = UserSetProgress.objects.filter(
                user=self.user,
                status='completed'
            ).values_list('vocabulary_set_id', flat=True)
            
            incomplete_set = VocabularySet.objects.filter(
                status='published'
            ).exclude(
                id__in=completed_set_ids
            ).first()
            
            if incomplete_set:
                return {
                    'type': 'new_vocab',
                    'priority': 5,
                    'count': 10,
                    'estimated_minutes': 5,
                    'reason': 'Học từ vựng mới',
                    'data': {
                        'vocab_set_id': incomplete_set.id,
                        'vocab_set_name': incomplete_set.title
                    }
                }
        except ImportError:
            pass
        return None
    
    def _should_add_listening(self) -> bool:
        """Quyết định có thêm listening practice không"""
        # Thêm listening nếu chưa practice trong 2 ngày
        recent_listening = SkillProgress.objects.filter(
            user=self.user,
            skill__startswith='L',
            date__gte=self.today - timedelta(days=2)
        ).exists()
        
        return not recent_listening
    
    def _get_random_listening_part(self) -> str:
        """Random một part listening để practice"""
        import random
        parts = ['L1', 'L2', 'L3', 'L4']
        
        # Ưu tiên part yếu
        weak_skills = self.profile.weak_skills
        weak_listening = [s for s in weak_skills if s.startswith('L')]
        
        if weak_listening:
            return random.choice(weak_listening)
        return random.choice(parts)
    
    def mark_activity_completed(self, activity_index: int, actual_data: Dict):
        """Đánh dấu activity đã hoàn thành"""
        lesson = DailyLesson.objects.get(user=self.user, date=self.today)
        
        completed = lesson.completed_activities or []
        completed.append({
            'index': activity_index,
            'completed_at': timezone.now().isoformat(),
            **actual_data
        })
        
        lesson.completed_activities = completed
        lesson.actual_minutes += actual_data.get('time_spent', 0)
        lesson.save(update_fields=['completed_activities', 'actual_minutes'])
        
        # Update skill progress if applicable
        if 'skill' in actual_data and 'accuracy' in actual_data:
            self._update_skill_progress(
                actual_data['skill'],
                actual_data.get('accuracy', 0),
                actual_data.get('time_spent', 0)
            )
    
    def _update_skill_progress(self, skill: str, accuracy: float, time_spent: int):
        """Cập nhật tiến độ skill"""
        progress, _ = SkillProgress.objects.get_or_create(
            user=self.user,
            skill=skill,
            date=self.today,
            defaults={'proficiency': self.profile.get_skill_level(skill)}
        )
        
        progress.questions_attempted += 1
        progress.study_time += time_spent
        if accuracy > 0:
            progress.proficiency = (progress.proficiency + accuracy) / 2
        progress.save()
        
        # Update profile
        self.profile.update_skill(skill, accuracy)
