# placement/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import (
    PlacementTest, PlacementQuestion, PlacementAnswer, 
    UserLearningProfile, LearningPath, DailyLesson
)
from .services.adaptive_test import AdaptivePlacementEngine
from .services.path_generator import LearningPathGenerator
from .services.daily_recommender import DailyRecommendationEngine


# ============== Template Views ==============

@login_required
def test_welcome(request):
    """Welcome screen for placement test"""
    # Check if user has existing profile
    profile = UserLearningProfile.objects.filter(user=request.user).first()
    has_taken_test = PlacementTest.objects.filter(
        user=request.user, 
        status=PlacementTest.TestStatus.COMPLETED
    ).exists()
    
    # Check for in-progress test
    in_progress = PlacementTest.objects.filter(
        user=request.user,
        status=PlacementTest.TestStatus.IN_PROGRESS
    ).first()
    
    return render(request, 'placement/test_welcome.html', {
        'profile': profile,
        'has_taken_test': has_taken_test,
        'in_progress_test': in_progress,
    })


@login_required
def test_take(request):
    """Main test taking interface"""
    # Get or create in-progress test
    test = PlacementTest.objects.filter(
        user=request.user,
        status=PlacementTest.TestStatus.IN_PROGRESS
    ).first()
    
    if not test:
        test = PlacementTest.objects.create(user=request.user)
    
    engine = AdaptivePlacementEngine(test)
    
    return render(request, 'placement/test_take.html', {
        'test': test,
        'min_questions': engine.MIN_QUESTIONS,
        'max_questions': engine.MAX_QUESTIONS,
    })


@login_required
def test_result(request, test_id):
    """Display test results"""
    test = get_object_or_404(
        PlacementTest, 
        id=test_id, 
        user=request.user,
        status=PlacementTest.TestStatus.COMPLETED
    )
    
    return render(request, 'placement/test_result.html', {
        'test': test,
    })


@login_required
def goal_setting(request):
    """Goal setting interface after placement test"""
    profile = get_object_or_404(UserLearningProfile, user=request.user)
    
    return render(request, 'placement/goal_setting.html', {
        'profile': profile,
        'target_score_options': [500, 600, 700, 800, 900, 990],
    })


@login_required
def daily_dashboard(request):
    """Daily learning dashboard"""
    engine = DailyRecommendationEngine(request.user)
    lesson = engine.generate_daily_lesson()
    
    # Get active learning path
    active_path = LearningPath.objects.filter(
        user=request.user,
        is_active=True
    ).prefetch_related('milestones').first()
    
    # Get profile
    profile = UserLearningProfile.objects.filter(user=request.user).first()
    
    return render(request, 'placement/daily_dashboard.html', {
        'lesson': lesson,
        'path': active_path,
        'profile': profile,
    })


@login_required
def learning_path_view(request):
    """View current learning path details"""
    path = LearningPath.objects.filter(
        user=request.user,
        is_active=True
    ).prefetch_related('milestones').first()
    
    if not path:
        return render(request, 'placement/no_path.html')
    
    return render(request, 'placement/learning_path.html', {
        'path': path,
    })


# ============== API Views ==============

class PlacementTestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Bắt đầu placement test mới"""
        # Check if có test đang dở
        existing = PlacementTest.objects.filter(
            user=request.user,
            status=PlacementTest.TestStatus.IN_PROGRESS
        ).first()
        
        if existing:
            engine = AdaptivePlacementEngine(existing)
            next_question = engine.select_next_question()
            return Response({
                'test_id': existing.id,
                'message': 'Resuming existing test',
                'questions_answered': existing.questions_answered,
                'question': self._serialize_question(next_question) if next_question else None,
                'progress': {
                    'answered': existing.questions_answered,
                    'min_required': engine.MIN_QUESTIONS,
                    'max_questions': engine.MAX_QUESTIONS
                }
            })
        
        # Tạo test mới
        test = PlacementTest.objects.create(user=request.user)
        engine = AdaptivePlacementEngine(test)
        first_question = engine.select_next_question()
        
        if not first_question:
            return Response({
                'error': 'No questions available for placement test'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response({
            'test_id': test.id,
            'question': self._serialize_question(first_question),
            'progress': {
                'answered': 0,
                'min_required': engine.MIN_QUESTIONS,
                'max_questions': engine.MAX_QUESTIONS
            }
        })
    
    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """Submit câu trả lời và lấy câu tiếp theo"""
        test = get_object_or_404(PlacementTest, pk=pk, user=request.user)
        
        if test.status != PlacementTest.TestStatus.IN_PROGRESS:
            return Response({'error': 'Test is not in progress'}, status=400)
        
        engine = AdaptivePlacementEngine(test)
        
        # Validate input
        question_id = request.data.get('question_id')
        selected = request.data.get('answer')
        time_spent = request.data.get('time_spent', 0)
        
        if not question_id or not selected:
            return Response({'error': 'question_id and answer are required'}, status=400)
        
        try:
            question = PlacementQuestion.objects.get(pk=question_id)
        except PlacementQuestion.DoesNotExist:
            return Response({'error': 'Question not found'}, status=404)
        
        is_correct = selected.upper() == question.correct_answer.upper()
        
        # Update ability
        new_ability = engine.update_ability(question, is_correct)
        
        # Save answer
        PlacementAnswer.objects.create(
            test=test,
            question=question,
            selected_answer=selected.upper(),
            is_correct=is_correct,
            time_spent=time_spent,
            ability_after=new_ability
        )
        
        # Update test state
        test.current_ability = new_ability
        test.questions_answered += 1
        test.save(update_fields=['current_ability', 'questions_answered'])
        
        # Update question stats
        question.times_shown += 1
        if is_correct:
            question.times_correct += 1
        question.save(update_fields=['times_shown', 'times_correct'])
        
        # Update answered_ids in engine
        engine.answered_ids.add(question.id)
        
        # Check if should stop
        if engine.should_stop():
            result = engine.finalize_test()
            return Response({
                'completed': True,
                'result': result
            })
        
        # Get next question
        next_question = engine.select_next_question()
        
        if not next_question:
            # No more questions available, finalize
            result = engine.finalize_test()
            return Response({
                'completed': True,
                'result': result
            })
        
        return Response({
            'completed': False,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'question': self._serialize_question(next_question),
            'progress': {
                'answered': test.questions_answered,
                'estimated_score': engine.ability_to_toeic_score(new_ability),
                'can_finish': test.questions_answered >= engine.MIN_QUESTIONS
            }
        })
    
    @action(detail=True, methods=['post'])
    def finish_early(self, request, pk=None):
        """Kết thúc test sớm (sau khi đủ MIN_QUESTIONS)"""
        test = get_object_or_404(PlacementTest, pk=pk, user=request.user)
        engine = AdaptivePlacementEngine(test)
        
        if test.questions_answered < engine.MIN_QUESTIONS:
            return Response(
                {'error': f'Cần trả lời ít nhất {engine.MIN_QUESTIONS} câu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = engine.finalize_test()
        return Response({'result': result})
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """Xem kết quả test"""
        test = get_object_or_404(PlacementTest, pk=pk, user=request.user)
        
        if test.status != PlacementTest.TestStatus.COMPLETED:
            return Response(
                {'error': 'Test chưa hoàn thành'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'total_score': test.estimated_score,
            'listening_score': test.estimated_listening,
            'reading_score': test.estimated_reading,
            'confidence_interval': test.confidence_interval,
            'skill_scores': test.skill_scores,
            'questions_answered': test.questions_answered,
            'completed_at': test.completed_at
        })
    
    def _serialize_question(self, question):
        if not question:
            return None
        options = {
            'A': question.option_a,
            'B': question.option_b,
            'C': question.option_c,
        }
        if question.option_d:
            options['D'] = question.option_d
            
        return {
            'id': question.id,
            'skill': question.skill,
            'skill_label': question.get_skill_display(),
            'question_text': question.question_text,
            'question_audio': question.question_audio,
            'question_image': question.question_image,
            'context_text': question.context_text,
            'context_audio': question.context_audio,
            'options': options
        }


class LearningPathViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate learning path mới"""
        target_score = request.data.get('target_score')
        target_date = request.data.get('target_date')
        
        if not target_score:
            return Response(
                {'error': 'target_score is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_score = int(target_score)
        except ValueError:
            return Response(
                {'error': 'target_score must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new path
        generator = LearningPathGenerator(
            request.user,
            target_score=target_score,
            target_date=target_date
        )
        path = generator.generate()
        
        return Response({
            'path_id': path.id,
            'name': path.name,
            'description': path.description,
            'estimated_days': path.estimated_days,
            'milestones': [
                {
                    'id': m.id,
                    'order': m.order,
                    'title': m.title,
                    'description': m.description,
                    'is_unlocked': m.is_unlocked,
                    'is_completed': m.is_completed,
                }
                for m in path.milestones.all()
            ]
        })
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Lấy learning path hiện tại"""
        path = LearningPath.objects.filter(
            user=request.user,
            is_active=True
        ).prefetch_related('milestones').first()
        
        if not path:
            return Response({'path': None})
        
        return Response({
            'path': {
                'id': path.id,
                'name': path.name,
                'description': path.description,
                'progress': path.progress_percentage,
                'target_score': path.target_score,
                'estimated_days': path.estimated_days,
                'milestones': [
                    {
                        'id': m.id,
                        'order': m.order,
                        'title': m.title,
                        'description': m.description,
                        'target_skill': m.target_skill,
                        'is_completed': m.is_completed,
                        'is_unlocked': m.is_unlocked
                    }
                    for m in path.milestones.all()
                ]
            }
        })


class DailyLessonViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Lấy bài học hôm nay"""
        engine = DailyRecommendationEngine(request.user)
        lesson = engine.generate_daily_lesson()
        
        return Response({
            'date': lesson.date,
            'target_minutes': lesson.target_minutes,
            'actual_minutes': lesson.actual_minutes,
            'completion_rate': lesson.completion_rate,
            'activities': lesson.recommended_activities,
            'completed': lesson.completed_activities
        })
    
    @action(detail=False, methods=['post'])
    def complete_activity(self, request):
        """Đánh dấu hoàn thành activity"""
        engine = DailyRecommendationEngine(request.user)
        
        activity_index = request.data.get('activity_index')
        actual_data = request.data.get('data', {})
        
        if activity_index is None:
            return Response(
                {'error': 'activity_index is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        engine.mark_activity_completed(int(activity_index), actual_data)
        
        return Response({'success': True})


# ============== JSON API endpoints (function-based) ==============

@login_required
@require_POST
def api_start_test(request):
    """Start a new placement test (AJAX endpoint)"""
    viewset = PlacementTestViewSet()
    viewset.request = request
    response = viewset.start(request)
    return JsonResponse(response.data, status=response.status_code)


@login_required
@require_POST
def api_submit_answer(request, test_id):
    """Submit an answer (AJAX endpoint)"""
    data = json.loads(request.body)
    
    test = get_object_or_404(PlacementTest, pk=test_id, user=request.user)
    engine = AdaptivePlacementEngine(test)
    
    question_id = data.get('question_id')
    selected = data.get('answer')
    time_spent = data.get('time_spent', 0)
    
    question = get_object_or_404(PlacementQuestion, pk=question_id)
    is_correct = selected.upper() == question.correct_answer.upper()
    
    # Update ability
    new_ability = engine.update_ability(question, is_correct)
    
    # Save answer
    PlacementAnswer.objects.create(
        test=test,
        question=question,
        selected_answer=selected.upper(),
        is_correct=is_correct,
        time_spent=time_spent,
        ability_after=new_ability
    )
    
    # Update test state
    test.current_ability = new_ability
    test.questions_answered += 1
    test.save(update_fields=['current_ability', 'questions_answered'])
    
    # Update question stats
    question.times_shown += 1
    if is_correct:
        question.times_correct += 1
    question.save(update_fields=['times_shown', 'times_correct'])
    
    # Check if should stop
    engine.answered_ids.add(question.id)
    
    if engine.should_stop():
        result = engine.finalize_test()
        return JsonResponse({
            'completed': True,
            'result': result
        })
    
    # Get next question
    next_question = engine.select_next_question()
    
    if not next_question:
        result = engine.finalize_test()
        return JsonResponse({
            'completed': True,
            'result': result
        })
    
    return JsonResponse({
        'completed': False,
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'question': {
            'id': next_question.id,
            'skill': next_question.skill,
            'skill_label': next_question.get_skill_display(),
            'question_text': next_question.question_text,
            'question_audio': next_question.question_audio,
            'question_image': next_question.question_image,
            'context_text': next_question.context_text,
            'context_audio': next_question.context_audio,
            'options': {
                'A': next_question.option_a,
                'B': next_question.option_b,
                'C': next_question.option_c,
                'D': next_question.option_d,
            } if next_question.option_d else {
                'A': next_question.option_a,
                'B': next_question.option_b,
                'C': next_question.option_c,
            }
        },
        'progress': {
            'answered': test.questions_answered,
            'estimated_score': engine.ability_to_toeic_score(new_ability),
            'can_finish': test.questions_answered >= engine.MIN_QUESTIONS
        }
    })


@login_required
@require_POST
def api_generate_path(request):
    """Generate a learning path (AJAX endpoint)"""
    data = json.loads(request.body)
    target_score = data.get('target_score')
    target_date = data.get('target_date')
    
    if not target_score:
        return JsonResponse({'error': 'target_score is required'}, status=400)
    
    generator = LearningPathGenerator(
        request.user,
        target_score=int(target_score),
        target_date=target_date
    )
    path = generator.generate()
    
    return JsonResponse({
        'path_id': path.id,
        'name': path.name,
        'description': path.description,
        'estimated_days': path.estimated_days,
    })
