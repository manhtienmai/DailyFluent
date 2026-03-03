"""Placement API — test, results, dashboard, goals, learning path."""

import random
from ninja import Router, Schema
from typing import List, Optional

router = Router()


@router.get("")
def placement_home(request):
    """Placement welcome — check if user has taken a test."""
    from placement.models import PlacementTest, UserLearningProfile
    tests = PlacementTest.objects.filter(user=request.user)
    has_profile = UserLearningProfile.objects.filter(user=request.user).exists()
    latest = tests.first()
    return {
        "has_taken_test": tests.exists(),
        "has_profile": has_profile,
        "latest_test": {
            "id": latest.id,
            "status": latest.status,
            "started_at": latest.started_at.isoformat(),
            "estimated_score": latest.estimated_score,
        } if latest else None,
    }


@router.post("/test/start")
def start_test(request):
    """Start a new placement test."""
    from placement.models import PlacementTest, PlacementQuestion

    test = PlacementTest.objects.create(user=request.user)
    # Get a random question (medium difficulty)
    qs = PlacementQuestion.objects.filter(is_active=True, difficulty=3)
    ids = list(qs.values_list('id', flat=True))
    if not ids:
        ids = list(PlacementQuestion.objects.filter(is_active=True).values_list('id', flat=True))
    question = PlacementQuestion.objects.get(id=random.choice(ids)) if ids else None

    return {
        "test_id": test.id,
        "question": _question_out(question) if question else None,
    }


@router.get("/test/question")
def next_question(request, test_id: int):
    """Get next adaptive question."""
    from placement.models import PlacementTest, PlacementQuestion

    test = PlacementTest.objects.get(id=test_id, user=request.user)
    answered_ids = list(test.answers.values_list("question_id", flat=True))

    question = PlacementQuestion.objects.filter(
        is_active=True
    ).exclude(
        id__in=answered_ids
    )
    ids = list(question.values_list('id', flat=True))
    picked = PlacementQuestion.objects.get(id=random.choice(ids)) if ids else None

    if not picked:
        return {"question": None, "test_complete": True}

    return {
        "question": _question_out(picked),
        "questions_answered": test.questions_answered,
        "test_complete": False,
    }


@router.post("/test/answer")
def submit_answer(request, test_id: int, question_id: int, answer: str, time_spent: int = 0):
    """Submit a placement test answer."""
    from placement.models import PlacementTest, PlacementQuestion, PlacementAnswer

    test = PlacementTest.objects.get(id=test_id, user=request.user)
    question = PlacementQuestion.objects.get(id=question_id)
    is_correct = answer == question.correct_answer

    # Simple ability update
    if is_correct:
        test.current_ability += 0.3
    else:
        test.current_ability -= 0.3
    test.questions_answered += 1

    PlacementAnswer.objects.create(
        test=test,
        question=question,
        selected_answer=answer,
        is_correct=is_correct,
        time_spent=time_spent,
        ability_after=test.current_ability,
    )
    test.save()

    # Check if test is complete (20 questions)
    is_complete = test.questions_answered >= 20
    if is_complete:
        from django.utils import timezone
        test.status = "completed"
        test.completed_at = timezone.now()
        # Estimate TOEIC score from ability
        test.estimated_score = _ability_to_score(test.current_ability, test.questions_answered)
        test.save()
        _update_learning_profile(request.user, test)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "test_complete": is_complete,
        "questions_answered": test.questions_answered,
    }


@router.get("/result/{test_id}")
def test_result(request, test_id: int):
    """Get placement test results."""
    from placement.models import PlacementTest
    test = PlacementTest.objects.get(id=test_id, user=request.user)
    answers = test.answers.select_related("question").all()
    correct = answers.filter(is_correct=True).count()
    total = answers.count()

    return {
        "test_id": test.id,
        "estimated_score": test.estimated_score,
        "estimated_listening": test.estimated_listening,
        "estimated_reading": test.estimated_reading,
        "total": total,
        "correct": correct,
        "accuracy": round(correct / max(total, 1) * 100),
        "status": test.status,
        "completed_at": test.completed_at.isoformat() if test.completed_at else None,
    }


@router.get("/dashboard")
def dashboard(request):
    """Learning dashboard with skill breakdown."""
    from placement.models import UserLearningProfile
    try:
        profile = UserLearningProfile.objects.get(user=request.user)
        return {
            "estimated_score": profile.estimated_score,
            "current_level": profile.current_level,
            "skill_proficiency": profile.skill_proficiency,
            "weak_skills": profile.weak_skills,
            "strong_skills": profile.strong_skills,
            "target_score": profile.target_score,
            "target_date": profile.target_date.isoformat() if profile.target_date else None,
            "total_study_time": profile.total_study_time,
            "total_questions_answered": profile.total_questions_answered,
            "overall_accuracy": profile.overall_accuracy,
        }
    except UserLearningProfile.DoesNotExist:
        return {
            "estimated_score": 0,
            "current_level": 3,
            "skill_proficiency": {},
            "weak_skills": [],
            "strong_skills": [],
            "target_score": None,
            "target_date": None,
            "total_study_time": 0,
            "total_questions_answered": 0,
            "overall_accuracy": 0,
        }


@router.get("/goals")
def get_goals(request):
    """Get user learning goals (from profile)."""
    from placement.models import UserLearningProfile
    try:
        profile = UserLearningProfile.objects.get(user=request.user)
        return {
            "target_score": profile.target_score,
            "target_date": profile.target_date.isoformat() if profile.target_date else None,
            "preferred_session_length": profile.preferred_session_length,
        }
    except UserLearningProfile.DoesNotExist:
        return {
            "target_score": 600,
            "target_date": None,
            "preferred_session_length": 15,
        }


@router.put("/goals")
def update_goals(request, target_score: int = 600, preferred_session_length: int = 15):
    """Update learning goals."""
    from placement.models import UserLearningProfile
    profile, _ = UserLearningProfile.objects.get_or_create(user=request.user)
    profile.target_score = target_score
    profile.preferred_session_length = preferred_session_length
    profile.save()
    return {"success": True}


@router.get("/path")
def learning_path(request):
    """Get personalized learning path."""
    from placement.models import LearningPath, LearningMilestone
    paths = LearningPath.objects.filter(user=request.user, is_active=True)
    result = []
    for path in paths:
        milestones = path.milestones.all()
        result.append({
            "id": path.id,
            "name": path.name,
            "description": path.description,
            "target_score": path.target_score,
            "progress": path.progress_percentage,
            "milestones": [
                {
                    "id": m.id,
                    "order": m.order,
                    "title": m.title,
                    "description": m.description,
                    "target_skill": m.target_skill,
                    "is_completed": m.is_completed,
                    "is_unlocked": m.is_unlocked,
                }
                for m in milestones
            ],
        })
    return result


def _question_out(q):
    return {
        "id": q.id,
        "skill": q.skill,
        "difficulty": q.difficulty,
        "question_text": q.question_text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "audio_url": q.question_audio or "",
        "image_url": q.question_image or "",
    }


def _ability_to_score(ability, questions_answered):
    """Convert IRT ability to estimated TOEIC score."""
    # Rough mapping: ability -3 to +3 → score 10 to 990
    score = int(500 + ability * 165)
    return max(10, min(990, score))


def _update_learning_profile(user, test):
    """Create/update learning profile from test results."""
    from placement.models import UserLearningProfile
    profile, _ = UserLearningProfile.objects.get_or_create(user=user)
    if test.estimated_score:
        profile.estimated_score = test.estimated_score
    profile.total_questions_answered += test.questions_answered
    # Update overall accuracy
    answers = test.answers.all()
    correct = answers.filter(is_correct=True).count()
    total = answers.count()
    if total > 0:
        profile.overall_accuracy = correct / total
    profile.save()
    profile.recalculate_weak_strong_skills()
