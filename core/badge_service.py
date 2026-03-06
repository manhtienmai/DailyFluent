# core/badge_service.py
"""
Service để kiểm tra và trao badge thành tựu cho user.
Hỗ trợ 35+ loại badges cho Streak, Vocabulary, Exams, Dictation, Time-based, Special.
"""
from django.utils import timezone


# Badge definitions với điều kiện và metadata
BADGE_DEFINITIONS = {
    # ===== STREAK BADGES =====
    'first_step': {
        'name': 'Bước Đầu Tiên',
        'description': 'Hoàn thành Bộ từ vựng đầu tiên',
        'icon': '👣',
        'order': 1,
    },
    'week_warrior': {
        'name': 'Chiến Binh 7 Ngày',
        'description': 'Streak 7 ngày liên tục',
        'icon': '🔥',
        'order': 2,
    },
    'streak_14': {
        'name': 'Kiên Trì',
        'description': 'Streak 14 ngày liên tục',
        'icon': '💪',
        'order': 3,
    },
    'streak_30': {
        'name': 'Thói Quen Vàng',
        'description': 'Streak 30 ngày liên tục',
        'icon': '🏅',
        'order': 4,
    },
    'streak_60': {
        'name': 'Bất Khuất',
        'description': 'Streak 60 ngày liên tục',
        'icon': '🛡️',
        'order': 5,
    },
    'streak_100': {
        'name': 'Bậc Thầy Kỷ Luật',
        'description': 'Streak 100 ngày liên tục',
        'icon': '👑',
        'order': 6,
    },
    'streak_365': {
        'name': 'Huyền Thoại',
        'description': 'Streak 365 ngày - 1 năm học liên tục!',
        'icon': '🌟',
        'order': 7,
    },
    
    # ===== VOCABULARY BADGES =====
    'century': {
        'name': 'Trăm Từ',
        'description': 'Học được 100 từ vựng',
        'icon': '💯',
        'order': 10,
    },
    'vocab_500': {
        'name': 'Nhà Sưu Tầm',
        'description': 'Học được 500 từ vựng',
        'icon': '📖',
        'order': 11,
    },
    'vocab_1000': {
        'name': 'Kho Từ Vựng',
        'description': 'Học được 1,000 từ vựng',
        'icon': '📚',
        'order': 12,
    },
    'vocab_2000': {
        'name': 'Bách Khoa',
        'description': 'Học được 2,000 từ vựng',
        'icon': '🏛️',
        'order': 13,
    },
    'vocab_5000': {
        'name': 'Từ Điển Sống',
        'description': 'Học được 5,000 từ vựng',
        'icon': '📕',
        'order': 14,
    },
    'level_master': {
        'name': 'Chinh Phục Level',
        'description': 'Hoàn thành 1 Level TOEIC',
        'icon': '🎓',
        'order': 15,
    },
    'perfect_set': {
        'name': 'Set Hoàn Hảo',
        'description': '10/10 trong 1 Set quiz',
        'icon': '⭐',
        'order': 16,
    },
    'set_10': {
        'name': 'Học Viên Chăm Chỉ',
        'description': 'Hoàn thành 10 Sets từ vựng',
        'icon': '📝',
        'order': 17,
    },
    'set_50': {
        'name': 'Master Từ Vựng',
        'description': 'Hoàn thành 50 Sets từ vựng',
        'icon': '🎯',
        'order': 18,
    },
    'review_master': {
        'name': 'Ôn Tập Siêu Đẳng',
        'description': 'Ôn tập 500 từ vựng',
        'icon': '🔄',
        'order': 19,
    },
    
    # ===== EXAM BADGES =====
    'first_exam': {
        'name': 'Thử Thách Đầu Tiên',
        'description': 'Hoàn thành bài thi đầu tiên',
        'icon': '📋',
        'order': 20,
    },
    'exam_10': {
        'name': 'Luyện Đề Chăm Chỉ',
        'description': 'Hoàn thành 10 bài thi',
        'icon': '📝',
        'order': 21,
    },
    'exam_50': {
        'name': 'Chiến Binh Luyện Đề',
        'description': 'Hoàn thành 50 bài thi',
        'icon': '⚔️',
        'order': 22,
    },
    'exam_100': {
        'name': 'Cao Thủ Luyện Đề',
        'description': 'Hoàn thành 100 bài thi',
        'icon': '🏆',
        'order': 23,
    },
    'perfect_exam': {
        'name': 'Điểm Tuyệt Đối',
        'description': 'Đạt 100% trong 1 bài thi',
        'icon': '💎',
        'order': 24,
    },
    'high_score_80': {
        'name': 'Điểm Cao 80+',
        'description': 'Đạt ≥80% trong bài thi',
        'icon': '🌟',
        'order': 25,
    },
    'high_score_90': {
        'name': 'Điểm Xuất Sắc',
        'description': 'Đạt ≥90% trong bài thi',
        'icon': '✨',
        'order': 26,
    },
    'speed_demon': {
        'name': 'Tốc Độ Ánh Sáng',
        'description': 'Hoàn thành exam dưới 50% thời gian',
        'icon': '⚡',
        'order': 27,
    },
    'full_test': {
        'name': 'Thi Thật',
        'description': 'Hoàn thành Full Test TOEIC',
        'icon': '📊',
        'order': 28,
    },
    
    # ===== DICTATION BADGES =====
    'first_dictation': {
        'name': 'Lắng Nghe Đầu Tiên',
        'description': 'Hoàn thành bài dictation đầu tiên',
        'icon': '👂',
        'order': 30,
    },
    'dictation_10': {
        'name': 'Tai Thính',
        'description': 'Hoàn thành 10 bài dictation',
        'icon': '🎧',
        'order': 31,
    },
    'dictation_50': {
        'name': 'Bậc Thầy Nghe',
        'description': 'Hoàn thành 50 bài dictation',
        'icon': '🎵',
        'order': 32,
    },
    'perfect_dictation': {
        'name': 'Chính Tả Hoàn Hảo',
        'description': '100% chính xác trong 1 bài dictation',
        'icon': '✍️',
        'order': 33,
    },
    'listening_streak': {
        'name': 'Nghe Mỗi Ngày',
        'description': '7 ngày liên tiếp làm dictation',
        'icon': '🔊',
        'order': 34,
    },
    
    # ===== TIME-BASED BADGES =====
    'early_bird': {
        'name': 'Chim Sớm',
        'description': 'Học trước 7h sáng',
        'icon': '🌅',
        'order': 40,
    },
    'night_owl': {
        'name': 'Cú Đêm',
        'description': 'Học sau 11h đêm',
        'icon': '🦉',
        'order': 41,
    },
    'weekend_warrior': {
        'name': 'Chiến Binh Cuối Tuần',
        'description': 'Học cả 2 ngày cuối tuần',
        'icon': '📆',
        'order': 42,
    },
    'lunch_learner': {
        'name': 'Học Giờ Nghỉ',
        'description': 'Học trong giờ trưa (12h-13h)',
        'icon': '🍱',
        'order': 43,
    },
    
    # ===== SPECIAL BADGES =====
    'all_rounder': {
        'name': 'Toàn Diện',
        'description': 'Làm cả Vocab, Exam, Dictation trong 1 ngày',
        'icon': '🌈',
        'order': 50,
    },
    'comeback': {
        'name': 'Quay Lại',
        'description': 'Học lại sau 7+ ngày nghỉ',
        'icon': '🔙',
        'order': 51,
    },
    'perfectionist': {
        'name': 'Hoàn Hảo Chủ Nghĩa',
        'description': '5 Perfect Sets liên tiếp',
        'icon': '💫',
        'order': 52,
    },
    'sharpshooter': {
        'name': 'Bắn Tỉa',
        'description': '10 câu đúng liên tiếp trong quiz',
        'icon': '🎯',
        'order': 53,
    },
    'speed_learner': {
        'name': 'Học Nhanh',
        'description': 'Hoàn thành 5 sets trong 1 ngày',
        'icon': '🚀',
        'order': 54,
    },
}


def ensure_badges_exist():
    """
    Đảm bảo tất cả badges được định nghĩa trong database.
    Nên gọi khi khởi động app hoặc sau khi migrate.
    """
    from core.models import Badge
    
    for code, data in BADGE_DEFINITIONS.items():
        Badge.objects.update_or_create(
            code=code,
            defaults={
                'name': data['name'],
                'description': data['description'],
                'icon': data['icon'],
                'order': data['order'],
            }
        )


# ===== STREAK CHECK FUNCTIONS =====

def check_first_step(user):
    """Check: Hoàn thành Set đầu tiên"""
    from vocab.models import UserSetProgress
    return UserSetProgress.objects.filter(
        user=user, 
        status=UserSetProgress.ProgressStatus.COMPLETED
    ).exists()


def _get_max_streak(user):
    """Helper: Get max của current_streak và longest_streak"""
    from streak.models import StreakStat
    try:
        stat = StreakStat.objects.get(user=user)
        return max(stat.current_streak, stat.longest_streak)
    except StreakStat.DoesNotExist:
        return 0


def check_week_warrior(user):
    """Check: Streak 7 ngày"""
    return _get_max_streak(user) >= 7


def check_streak_14(user):
    """Check: Streak 14 ngày"""
    return _get_max_streak(user) >= 14


def check_streak_30(user):
    """Check: Streak 30 ngày"""
    return _get_max_streak(user) >= 30


def check_streak_60(user):
    """Check: Streak 60 ngày"""
    return _get_max_streak(user) >= 60


def check_streak_100(user):
    """Check: Streak 100 ngày"""
    return _get_max_streak(user) >= 100


def check_streak_365(user):
    """Check: Streak 365 ngày"""
    return _get_max_streak(user) >= 365


# ===== VOCABULARY CHECK FUNCTIONS =====

def _get_vocab_count(user):
    """Helper: Count learned words (state >= 2 = đã review ít nhất 1 lần)"""
    from vocab.models import FsrsCardStateEn
    return FsrsCardStateEn.objects.filter(user=user, state__gte=2).count()


def check_century(user):
    """Check: Học 100 từ"""
    return _get_vocab_count(user) >= 100


def check_vocab_500(user):
    """Check: Học 500 từ"""
    return _get_vocab_count(user) >= 500


def check_vocab_1000(user):
    """Check: Học 1,000 từ"""
    return _get_vocab_count(user) >= 1000


def check_vocab_2000(user):
    """Check: Học 2,000 từ"""
    return _get_vocab_count(user) >= 2000


def check_vocab_5000(user):
    """Check: Học 5,000 từ"""
    return _get_vocab_count(user) >= 5000


def check_level_master(user):
    """Check: Hoàn thành 1 Level TOEIC (tất cả sets của 1 level)"""
    from vocab.models import VocabularySet, UserSetProgress
    
    toeic_levels = [600, 730, 860, 990]
    
    for level in toeic_levels:
        sets_in_level = VocabularySet.objects.filter(
            toeic_level=level,
            status=VocabularySet.Status.PUBLISHED
        ).values_list('id', flat=True)
        
        if not sets_in_level:
            continue
        
        completed_count = UserSetProgress.objects.filter(
            user=user,
            vocabulary_set_id__in=sets_in_level,
            status=UserSetProgress.ProgressStatus.COMPLETED
        ).count()
        
        if completed_count == len(sets_in_level):
            return True
    
    return False


def check_perfect_set(user):
    """Check: 10/10 trong 1 Set quiz (100% score)"""
    from vocab.models import UserSetProgress
    return UserSetProgress.objects.filter(
        user=user,
        quiz_best_score=100
    ).exists()


def _get_completed_sets_count(user):
    """Helper: Count completed sets"""
    from vocab.models import UserSetProgress
    return UserSetProgress.objects.filter(
        user=user,
        status=UserSetProgress.ProgressStatus.COMPLETED
    ).count()


def check_set_10(user):
    """Check: Hoàn thành 10 Sets"""
    return _get_completed_sets_count(user) >= 10


def check_set_50(user):
    """Check: Hoàn thành 50 Sets"""
    return _get_completed_sets_count(user) >= 50


def check_review_master(user):
    """Check: Ôn tập 500 từ (total_reviews sum >= 500)"""
    from vocab.models import FsrsCardStateEn
    from django.db.models import Sum
    result = FsrsCardStateEn.objects.filter(user=user).aggregate(
        total=Sum('total_reviews')
    )
    return (result['total'] or 0) >= 500


# ===== EXAM CHECK FUNCTIONS =====

def _get_exam_count(user):
    """Helper: Count submitted exams"""
    from exam.models import ExamAttempt
    return ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED
    ).count()


def check_first_exam(user):
    """Check: Hoàn thành bài thi đầu tiên"""
    return _get_exam_count(user) >= 1


def check_exam_10(user):
    """Check: Hoàn thành 10 bài thi"""
    return _get_exam_count(user) >= 10


def check_exam_50(user):
    """Check: Hoàn thành 50 bài thi"""
    return _get_exam_count(user) >= 50


def check_exam_100(user):
    """Check: Hoàn thành 100 bài thi"""
    return _get_exam_count(user) >= 100


def check_perfect_exam(user):
    """Check: Đạt 100% trong 1 bài thi"""
    from exam.models import ExamAttempt
    return ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        correct_count__gt=0
    ).extra(
        where=['correct_count = total_questions']
    ).exists()


def check_high_score_80(user):
    """Check: Đạt ≥80% trong bài thi"""
    from exam.models import ExamAttempt
    attempts = ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        total_questions__gt=0
    )
    for attempt in attempts:
        if attempt.total_questions > 0:
            score = (attempt.correct_count / attempt.total_questions) * 100
            if score >= 80:
                return True
    return False


def check_high_score_90(user):
    """Check: Đạt ≥90% trong bài thi"""
    from exam.models import ExamAttempt
    attempts = ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        total_questions__gt=0
    )
    for attempt in attempts:
        if attempt.total_questions > 0:
            score = (attempt.correct_count / attempt.total_questions) * 100
            if score >= 90:
                return True
    return False


def check_speed_demon(user):
    """Check: Hoàn thành exam < 50% thời gian cho phép"""
    from exam.models import ExamAttempt
    attempts = ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        started_at__isnull=False,
        submitted_at__isnull=False
    ).select_related('template')
    
    for attempt in attempts:
        if attempt.template.time_limit and attempt.template.time_limit > 0:
            time_used = (attempt.submitted_at - attempt.started_at).total_seconds() / 60
            if time_used < (attempt.template.time_limit / 2):
                return True
    return False


def check_full_test(user):
    """Check: Hoàn thành Full Test TOEIC (200 questions)"""
    from exam.models import ExamAttempt
    return ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        total_questions__gte=200
    ).exists()


# ===== DICTATION CHECK FUNCTIONS =====

def _get_dictation_progress_count(user):
    """Helper: Count dictation exercises with progress"""
    from core.models import DictationProgress
    return DictationProgress.objects.filter(user=user).count()


def check_first_dictation(user):
    """Check: Hoàn thành bài dictation đầu tiên"""
    from core.models import DictationProgress
    return DictationProgress.objects.filter(
        user=user,
        current_segment__gt=0
    ).exists()


def check_dictation_10(user):
    """Check: Hoàn thành 10 bài dictation"""
    from core.models import DictationProgress
    return DictationProgress.objects.filter(
        user=user,
        current_segment__gt=0
    ).count() >= 10


def check_dictation_50(user):
    """Check: Hoàn thành 50 bài dictation"""
    from core.models import DictationProgress
    return DictationProgress.objects.filter(
        user=user,
        current_segment__gt=0
    ).count() >= 50


def check_perfect_dictation(user):
    """Check: 100% chính xác trong 1 bài dictation"""
    from core.models import DictationProgress
    # A perfect dictation is when current_segment equals total_segments
    return DictationProgress.objects.filter(
        user=user,
        total_segments__gt=0
    ).extra(
        where=['current_segment = total_segments']
    ).exists()


def check_listening_streak(user):
    """Check: 7 ngày liên tiếp làm dictation"""
    # This requires tracking daily dictation activity
    # For now, return False until we add proper tracking
    return False


# ===== TIME-BASED CHECK FUNCTIONS =====

def check_early_bird(user):
    """Check: Học trước 7h sáng"""
    # Requires time tracking in DailyActivity
    return False


def check_night_owl(user):
    """Check: Học sau 11h đêm"""
    # Requires time tracking in DailyActivity
    return False


def check_weekend_warrior(user):
    """Check: Học cả 2 ngày cuối tuần trong tuần này hoặc bất kỳ tuần nào"""
    from streak.models import DailyActivity
    from datetime import timedelta
    
    # Check recent 30 days for any weekend pair
    today = timezone.localdate()
    activities = DailyActivity.objects.filter(
        user=user,
        date__gte=today - timedelta(days=30)
    ).values_list('date', flat=True)
    
    activity_dates = set(activities)
    
    # Check each weekend
    for i in range(5):  # Check last 5 weekends
        # Find the most recent Saturday
        days_since_saturday = (today.weekday() + 2) % 7
        saturday = today - timedelta(days=days_since_saturday + (7 * i))
        sunday = saturday + timedelta(days=1)
        
        if saturday in activity_dates and sunday in activity_dates:
            return True
    
    return False


def check_lunch_learner(user):
    """Check: Học trong giờ trưa (12h-13h)"""
    # Requires time tracking in DailyActivity
    return False


# ===== SPECIAL CHECK FUNCTIONS =====

def check_all_rounder(user):
    """Check: Làm cả Vocab, Exam, Dictation trong 1 ngày"""
    # This requires tracking activities by date
    # Check if today has all 3 activities
    from streak.models import DailyActivity
    from exam.models import ExamAttempt
    from core.models import DictationProgress
    
    today = timezone.localdate()
    
    # Check vocab activity
    has_vocab = DailyActivity.objects.filter(
        user=user,
        date=today,
        lessons_completed__gt=0
    ).exists()
    
    # Check exam activity
    has_exam = ExamAttempt.objects.filter(
        user=user,
        status=ExamAttempt.Status.SUBMITTED,
        submitted_at__date=today
    ).exists()
    
    # Check dictation activity (updated today)
    has_dictation = DictationProgress.objects.filter(
        user=user,
        updated_at__date=today
    ).exists()
    
    return has_vocab and has_exam and has_dictation


def check_comeback(user):
    """Check: Học lại sau 7+ ngày nghỉ"""
    from streak.models import DailyActivity
    from datetime import timedelta
    
    activities = list(
        DailyActivity.objects.filter(user=user)
        .order_by('-date')
        .values_list('date', flat=True)[:100]
    )
    
    if len(activities) < 2:
        return False
    
    for i in range(len(activities) - 1):
        gap = (activities[i] - activities[i + 1]).days
        if gap > 7:
            return True
    
    return False


def check_perfectionist(user):
    """Check: 5 Perfect Sets liên tiếp"""
    from vocab.models import UserSetProgress
    
    perfect_count = UserSetProgress.objects.filter(
        user=user,
        quiz_best_score=100
    ).count()
    
    return perfect_count >= 5


def check_sharpshooter(user):
    """Check: 10 câu đúng liên tiếp trong quiz"""
    # This requires tracking consecutive correct answers
    # For now, check if user has any perfect quiz with 10+ questions
    from vocab.models import UserSetProgress
    return UserSetProgress.objects.filter(
        user=user,
        quiz_best_score=100,
        words_total__gte=10
    ).exists()


def check_speed_learner(user):
    """Check: Hoàn thành 5 sets trong 1 ngày"""
    from vocab.models import UserSetProgress
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    
    # Check if any date has 5+ completed sets
    result = UserSetProgress.objects.filter(
        user=user,
        status=UserSetProgress.ProgressStatus.COMPLETED,
        completed_at__isnull=False
    ).annotate(
        date=TruncDate('completed_at')
    ).values('date').annotate(
        count=Count('id')
    ).filter(count__gte=5)
    
    return result.exists()


# ===== MAPPING & MAIN FUNCTIONS =====

BADGE_CHECKERS = {
    # Streak
    'first_step': check_first_step,
    'week_warrior': check_week_warrior,
    'streak_14': check_streak_14,
    'streak_30': check_streak_30,
    'streak_60': check_streak_60,
    'streak_100': check_streak_100,
    'streak_365': check_streak_365,
    
    # Vocabulary
    'century': check_century,
    'vocab_500': check_vocab_500,
    'vocab_1000': check_vocab_1000,
    'vocab_2000': check_vocab_2000,
    'vocab_5000': check_vocab_5000,
    'level_master': check_level_master,
    'perfect_set': check_perfect_set,
    'set_10': check_set_10,
    'set_50': check_set_50,
    'review_master': check_review_master,
    
    # Exam
    'first_exam': check_first_exam,
    'exam_10': check_exam_10,
    'exam_50': check_exam_50,
    'exam_100': check_exam_100,
    'perfect_exam': check_perfect_exam,
    'high_score_80': check_high_score_80,
    'high_score_90': check_high_score_90,
    'speed_demon': check_speed_demon,
    'full_test': check_full_test,
    
    # Dictation
    'first_dictation': check_first_dictation,
    'dictation_10': check_dictation_10,
    'dictation_50': check_dictation_50,
    'perfect_dictation': check_perfect_dictation,
    'listening_streak': check_listening_streak,
    
    # Time-based
    'early_bird': check_early_bird,
    'night_owl': check_night_owl,
    'weekend_warrior': check_weekend_warrior,
    'lunch_learner': check_lunch_learner,
    
    # Special
    'all_rounder': check_all_rounder,
    'comeback': check_comeback,
    'perfectionist': check_perfectionist,
    'sharpshooter': check_sharpshooter,
    'speed_learner': check_speed_learner,
}


def check_and_award_badges(user):
    """
    Kiểm tra và trao badge cho user nếu đạt điều kiện.
    Returns list of newly awarded badges.
    """
    from core.models import Badge, UserBadge
    
    # Ensure all badges exist in DB
    ensure_badges_exist()
    
    # Get badges user already earned
    earned_codes = set(
        UserBadge.objects.filter(user=user).values_list('badge__code', flat=True)
    )
    
    newly_awarded = []
    
    for code, checker in BADGE_CHECKERS.items():
        if code in earned_codes:
            continue  # Already has this badge
        
        try:
            if checker(user):
                # Award the badge
                badge = Badge.objects.get(code=code)
                UserBadge.objects.create(user=user, badge=badge)
                newly_awarded.append(badge)
        except Exception as e:
            # Log error but continue checking other badges
            print(f"Error checking badge {code}: {e}")
            continue
    
    return newly_awarded


def get_user_badges_with_status(user):
    """
    Get all badges with earned status for display.
    Returns list of dicts with badge info and earned status.
    """
    from core.models import Badge, UserBadge
    
    # Ensure badges exist
    ensure_badges_exist()
    
    # Get all badges
    all_badges = Badge.objects.all().order_by('order')
    
    # Get earned badge IDs
    earned_badge_ids = set(
        UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    )
    
    # Get earned_at for earned badges
    earned_at_map = {}
    for ub in UserBadge.objects.filter(user=user).select_related('badge'):
        earned_at_map[ub.badge_id] = ub.earned_at
    
    result = []
    for badge in all_badges:
        result.append({
            'badge': badge,
            'earned': badge.id in earned_badge_ids,
            'earned_at': earned_at_map.get(badge.id),
        })
    
    return result
