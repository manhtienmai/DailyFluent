# placement/admin.py

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export import resources

from .models import (
    PlacementQuestion, PlacementTest, PlacementAnswer,
    UserLearningProfile, LearningPath, LearningMilestone,
    DailyLesson, SkillProgress
)


# ============== Resources for Import/Export ==============

class PlacementQuestionResource(resources.ModelResource):
    class Meta:
        model = PlacementQuestion
        fields = (
            'id', 'skill', 'difficulty', 'question_text', 'question_audio',
            'question_image', 'context_text', 'context_audio',
            'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer',
            'explanation', 'irt_difficulty', 'irt_discrimination', 'irt_guessing',
            'is_active'
        )
        import_id_fields = ['id']


# ============== Admin Classes ==============

@admin.register(PlacementQuestion)
class PlacementQuestionAdmin(ImportExportModelAdmin):
    resource_class = PlacementQuestionResource
    
    list_display = [
        'id', 'skill', 'difficulty', 'question_preview', 
        'correct_answer', 'irt_difficulty_display', 'accuracy_display', 'is_active'
    ]
    list_filter = ['skill', 'difficulty', 'is_active']
    search_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('skill', 'difficulty', 'is_active')
        }),
        ('Question Content', {
            'fields': ('question_text', 'question_audio', 'question_image')
        }),
        ('Context', {
            'fields': ('context_text', 'context_audio'),
            'classes': ('collapse',)
        }),
        ('Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation')
        }),
        ('IRT Parameters', {
            'fields': ('irt_difficulty', 'irt_discrimination', 'irt_guessing'),
            'description': 'Item Response Theory parameters for adaptive testing'
        }),
        ('Statistics', {
            'fields': ('times_shown', 'times_correct'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    question_preview.short_description = 'Question'
    
    def irt_difficulty_display(self, obj):
        color = 'green' if obj.irt_difficulty < 0 else 'orange' if obj.irt_difficulty < 1 else 'red'
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, obj.irt_difficulty
        )
    irt_difficulty_display.short_description = 'IRT Diff'
    
    def accuracy_display(self, obj):
        if obj.times_shown < 10:
            return '-'
        acc = obj.times_correct / obj.times_shown * 100
        return f'{acc:.0f}%'
    accuracy_display.short_description = 'Accuracy'


class PlacementAnswerInline(admin.TabularInline):
    model = PlacementAnswer
    extra = 0
    readonly_fields = ['question', 'selected_answer', 'is_correct', 'time_spent', 'ability_after', 'answered_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PlacementTest)
class PlacementTestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'status', 'estimated_score', 
        'questions_answered', 'started_at', 'completed_at'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'user', 'status', 'estimated_score', 'estimated_listening',
        'estimated_reading', 'confidence_interval', 'skill_scores',
        'current_ability', 'questions_answered', 'started_at', 'completed_at'
    ]
    inlines = [PlacementAnswerInline]
    
    def has_add_permission(self, request):
        return False


@admin.register(UserLearningProfile)
class UserLearningProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'current_level', 'estimated_score', 
        'target_score', 'weak_skills_display', 'updated_at'
    ]
    list_filter = ['current_level']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Level & Score', {
            'fields': ('current_level', 'estimated_score')
        }),
        ('Skills', {
            'fields': ('skill_proficiency', 'weak_skills', 'strong_skills')
        }),
        ('Goals', {
            'fields': ('target_score', 'target_date')
        }),
        ('Preferences', {
            'fields': ('preferred_session_length', 'best_learning_time', 'preferred_content_types'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_study_time', 'total_questions_answered', 'overall_accuracy'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def weak_skills_display(self, obj):
        return ', '.join(obj.weak_skills) if obj.weak_skills else '-'
    weak_skills_display.short_description = 'Weak Skills'


class LearningMilestoneInline(admin.TabularInline):
    model = LearningMilestone
    extra = 0
    fields = ['order', 'title', 'target_skill', 'is_unlocked', 'is_completed']


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'name', 'target_score', 
        'progress_percentage', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'name']
    inlines = [LearningMilestoneInline]
    
    def has_add_permission(self, request):
        return False  # Paths should be generated, not manually created


@admin.register(LearningMilestone)
class LearningMilestoneAdmin(admin.ModelAdmin):
    list_display = [
        'path', 'order', 'title', 'target_skill', 
        'is_unlocked', 'is_completed'
    ]
    list_filter = ['is_unlocked', 'is_completed', 'target_skill']
    search_fields = ['title', 'path__name']


@admin.register(DailyLesson)
class DailyLessonAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'target_minutes', 'actual_minutes', 
        'activities_count', 'completed_count'
    ]
    list_filter = ['date']
    search_fields = ['user__username']
    readonly_fields = ['recommended_activities', 'completed_activities']
    
    def activities_count(self, obj):
        return len(obj.recommended_activities) if obj.recommended_activities else 0
    activities_count.short_description = 'Activities'
    
    def completed_count(self, obj):
        return len(obj.completed_activities) if obj.completed_activities else 0
    completed_count.short_description = 'Completed'


@admin.register(SkillProgress)
class SkillProgressAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'skill', 'date', 'proficiency', 
        'questions_attempted', 'accuracy_display', 'study_time'
    ]
    list_filter = ['skill', 'date']
    search_fields = ['user__username']
    
    def accuracy_display(self, obj):
        if obj.questions_attempted == 0:
            return '-'
        return f'{obj.accuracy * 100:.0f}%'
    accuracy_display.short_description = 'Accuracy'
