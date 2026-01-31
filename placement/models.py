# placement/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone


class SkillCategory(models.TextChoices):
    """Các kỹ năng TOEIC"""
    LISTENING_PHOTOS = 'L1', 'Listening - Photos'
    LISTENING_QA = 'L2', 'Listening - Question & Response'
    LISTENING_CONVERSATIONS = 'L3', 'Listening - Conversations'
    LISTENING_TALKS = 'L4', 'Listening - Talks'
    READING_INCOMPLETE = 'R5', 'Reading - Incomplete Sentences'
    READING_TEXT_COMPLETION = 'R6', 'Reading - Text Completion'
    READING_COMPREHENSION = 'R7', 'Reading - Reading Comprehension'
    VOCABULARY = 'VOC', 'Vocabulary'
    GRAMMAR = 'GRM', 'Grammar'


class DifficultyLevel(models.IntegerChoices):
    """Mức độ khó (tương ứng khoảng điểm TOEIC)"""
    BEGINNER = 1, 'Beginner (10-295)'
    ELEMENTARY = 2, 'Elementary (300-395)'
    INTERMEDIATE = 3, 'Intermediate (400-595)'
    UPPER_INTERMEDIATE = 4, 'Upper Intermediate (600-795)'
    ADVANCED = 5, 'Advanced (800-895)'
    EXPERT = 6, 'Expert (900-990)'


# ============== PLACEMENT TEST ==============

class PlacementQuestion(models.Model):
    """Ngân hàng câu hỏi placement test"""
    
    skill = models.CharField(
        max_length=3,
        choices=SkillCategory.choices,
        db_index=True
    )
    difficulty = models.IntegerField(
        choices=DifficultyLevel.choices,
        db_index=True
    )
    
    # Nội dung câu hỏi
    question_text = models.TextField()
    question_audio = models.URLField(blank=True, null=True)  # Cho listening
    question_image = models.URLField(blank=True, null=True)  # Cho Part 1
    
    # Context (đoạn văn, hội thoại)
    context_text = models.TextField(blank=True)
    context_audio = models.URLField(blank=True, null=True)
    
    # Đáp án
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500, blank=True)  # Part 2 chỉ có 3 options
    correct_answer = models.CharField(max_length=1)  # A, B, C, D
    
    # Explanation
    explanation = models.TextField(blank=True, help_text="Giải thích đáp án đúng")
    
    # IRT Parameters (Item Response Theory)
    irt_difficulty = models.FloatField(default=0.0, help_text="b parameter (-3 to +3)")
    irt_discrimination = models.FloatField(default=1.0, help_text="a parameter (0.5 to 2.5)")
    irt_guessing = models.FloatField(default=0.25, help_text="c parameter")
    
    # Metadata
    times_shown = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['skill', 'difficulty']),
            models.Index(fields=['irt_difficulty']),
        ]
        verbose_name = "Placement Question"
        verbose_name_plural = "Placement Questions"

    def __str__(self):
        return f"[{self.skill}] {self.question_text[:50]}..."

    @property
    def empirical_difficulty(self):
        """Độ khó thực tế dựa trên data"""
        if self.times_shown < 10:
            return None
        return 1 - (self.times_correct / self.times_shown)


class PlacementTest(models.Model):
    """Một lượt thi placement của user"""
    
    class TestStatus(models.TextChoices):
        IN_PROGRESS = 'progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ABANDONED = 'abandoned', 'Abandoned'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='placement_tests'
    )
    
    status = models.CharField(
        max_length=10,
        choices=TestStatus.choices,
        default=TestStatus.IN_PROGRESS
    )
    
    # Kết quả
    estimated_score = models.IntegerField(null=True, blank=True)  # 10-990
    estimated_listening = models.IntegerField(null=True, blank=True)  # 5-495
    estimated_reading = models.IntegerField(null=True, blank=True)  # 5-495
    confidence_interval = models.IntegerField(default=50)  # ±50 điểm
    
    # Skill breakdown
    skill_scores = models.JSONField(default=dict)
    # Format: {"L1": 0.7, "L2": 0.5, "R5": 0.8, ...}
    
    # Adaptive test state
    current_ability = models.FloatField(default=0.0)  # θ trong IRT (-3 to +3)
    questions_answered = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Placement Test"
        verbose_name_plural = "Placement Tests"

    def __str__(self):
        return f"{self.user.username} - {self.status} ({self.estimated_score or 'N/A'})"


class PlacementAnswer(models.Model):
    """Câu trả lời trong placement test"""
    
    test = models.ForeignKey(
        PlacementTest, 
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        PlacementQuestion,
        on_delete=models.CASCADE
    )
    
    selected_answer = models.CharField(max_length=1)  # A, B, C, D
    is_correct = models.BooleanField()
    time_spent = models.IntegerField(default=0)  # seconds
    
    # Ability estimate sau câu này
    ability_after = models.FloatField()
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
        verbose_name = "Placement Answer"
        verbose_name_plural = "Placement Answers"

    def __str__(self):
        return f"Q{self.question.id}: {self.selected_answer} ({'✓' if self.is_correct else '✗'})"


# ============== USER PROFILE & LEVEL ==============

class UserLearningProfile(models.Model):
    """Profile học tập của user - CẬP NHẬT LIÊN TỤC"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_profile'
    )
    
    # Level tổng thể
    current_level = models.IntegerField(
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.INTERMEDIATE
    )
    estimated_score = models.IntegerField(default=450)  # TOEIC score
    
    # Chi tiết từng skill (0.0 - 1.0)
    skill_proficiency = models.JSONField(default=dict)
    # Format: {
    #     "L1": {"level": 0.7, "confidence": 0.8, "last_updated": "2024-01-15"},
    #     "R5": {"level": 0.5, "confidence": 0.6, "last_updated": "2024-01-14"},
    #     ...
    # }
    
    # Điểm yếu cần focus
    weak_skills = models.JSONField(default=list)  # ["R5", "L3"]
    strong_skills = models.JSONField(default=list)  # ["L1", "R7"]
    
    # Mục tiêu
    target_score = models.IntegerField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    
    # Learning preferences (learned from behavior)
    preferred_session_length = models.IntegerField(default=15)  # minutes
    best_learning_time = models.CharField(max_length=20, default='evening')
    preferred_content_types = models.JSONField(default=list)  # ['flashcard', 'quiz']
    
    # Statistics
    total_study_time = models.IntegerField(default=0)  # minutes
    total_questions_answered = models.IntegerField(default=0)
    overall_accuracy = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Learning Profile"
        verbose_name_plural = "User Learning Profiles"

    def __str__(self):
        return f"{self.user.username} - Level {self.current_level} ({self.estimated_score})"

    def get_skill_level(self, skill: str) -> float:
        """Lấy level của một skill cụ thể"""
        return self.skill_proficiency.get(skill, {}).get('level', 0.5)
    
    def update_skill(self, skill: str, performance: float, weight: float = 0.3):
        """Cập nhật skill sau khi làm bài"""
        current = self.get_skill_level(skill)
        # Exponential moving average
        new_level = current * (1 - weight) + performance * weight
        
        if skill not in self.skill_proficiency:
            self.skill_proficiency[skill] = {}
        
        self.skill_proficiency[skill].update({
            'level': round(new_level, 3),
            'confidence': min(0.95, self.skill_proficiency.get(skill, {}).get('confidence', 0.5) + 0.05),
            'last_updated': str(timezone.now().date())
        })
        self.save(update_fields=['skill_proficiency', 'updated_at'])
    
    def recalculate_weak_strong_skills(self):
        """Recalculate weak and strong skills based on proficiency"""
        if not self.skill_proficiency:
            return
        
        skills_with_levels = [
            (skill, data.get('level', 0.5)) 
            for skill, data in self.skill_proficiency.items()
        ]
        skills_with_levels.sort(key=lambda x: x[1])
        
        # Bottom 3 are weak, top 3 are strong
        self.weak_skills = [s[0] for s in skills_with_levels[:3]]
        self.strong_skills = [s[0] for s in skills_with_levels[-3:]]
        self.save(update_fields=['weak_skills', 'strong_skills', 'updated_at'])


# ============== ADAPTIVE LEARNING PATH ==============

class LearningPath(models.Model):
    """Lộ trình học được generate cho user"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_paths'
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Mục tiêu của path này
    target_score = models.IntegerField()
    target_skills = models.JSONField(default=list)  # Skills cần improve
    
    # Trạng thái
    is_active = models.BooleanField(default=True)
    progress_percentage = models.FloatField(default=0.0)
    
    # Thời gian
    estimated_days = models.IntegerField()  # Dự kiến hoàn thành
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Learning Path"
        verbose_name_plural = "Learning Paths"

    def __str__(self):
        return f"{self.user.username}: {self.name}"
    
    def update_progress(self):
        """Update progress based on completed milestones"""
        total = self.milestones.count()
        if total == 0:
            return
        completed = self.milestones.filter(is_completed=True).count()
        self.progress_percentage = round((completed / total) * 100, 1)
        self.save(update_fields=['progress_percentage'])


class LearningMilestone(models.Model):
    """Các mốc trong learning path"""
    
    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    
    order = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Mục tiêu của milestone
    target_skill = models.CharField(
        max_length=3,
        choices=SkillCategory.choices,
        null=True, blank=True
    )
    target_proficiency = models.FloatField(default=0.7)  # 0-1
    
    # Nội dung học (references to other apps)
    vocabulary_set_ids = models.JSONField(default=list)  # List of VocabularySet IDs
    grammar_point_ids = models.JSONField(default=list)   # List of GrammarPoint IDs
    exam_template_ids = models.JSONField(default=list)   # List of ExamTemplate IDs
    
    # Tiến độ
    is_completed = models.BooleanField(default=False)
    is_unlocked = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['path', 'order']
        unique_together = ['path', 'order']
        verbose_name = "Learning Milestone"
        verbose_name_plural = "Learning Milestones"

    def __str__(self):
        return f"{self.path.name} - {self.order}. {self.title}"
    
    def mark_complete(self):
        """Mark milestone as complete and unlock next"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
        
        # Unlock next milestone
        next_milestone = LearningMilestone.objects.filter(
            path=self.path,
            order=self.order + 1
        ).first()
        if next_milestone:
            next_milestone.is_unlocked = True
            next_milestone.save(update_fields=['is_unlocked'])
        
        # Update path progress
        self.path.update_progress()


class DailyLesson(models.Model):
    """Bài học được gợi ý mỗi ngày"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='daily_lessons'
    )
    date = models.DateField()
    
    # Nội dung gợi ý
    recommended_activities = models.JSONField(default=list)
    # Format: [
    #     {"type": "vocab_review", "set_id": 1, "count": 20, "reason": "Due for review"},
    #     {"type": "practice_quiz", "skill": "R5", "count": 10, "reason": "Weak skill"},
    #     {"type": "new_vocab", "set_id": 2, "count": 10, "reason": "Path progress"},
    # ]
    
    # Đã hoàn thành
    completed_activities = models.JSONField(default=list)
    
    # Thống kê
    target_minutes = models.IntegerField(default=30)
    actual_minutes = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = "Daily Lesson"
        verbose_name_plural = "Daily Lessons"

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @property
    def completion_rate(self):
        """Return completion percentage"""
        if not self.recommended_activities:
            return 0
        return len(self.completed_activities) / len(self.recommended_activities) * 100


class SkillProgress(models.Model):
    """Track tiến độ skill theo thời gian"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='skill_progress'
    )
    skill = models.CharField(max_length=3, choices=SkillCategory.choices)
    date = models.DateField()
    
    # Metrics
    proficiency = models.FloatField()  # 0-1
    questions_attempted = models.IntegerField(default=0)
    questions_correct = models.IntegerField(default=0)
    study_time = models.IntegerField(default=0)  # minutes
    
    class Meta:
        unique_together = ['user', 'skill', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        verbose_name = "Skill Progress"
        verbose_name_plural = "Skill Progress"

    def __str__(self):
        return f"{self.user.username} - {self.skill} ({self.date}): {self.proficiency:.0%}"
    
    @property
    def accuracy(self):
        if self.questions_attempted == 0:
            return 0
        return self.questions_correct / self.questions_attempted
