# streak/services.py
from datetime import timedelta

from django.utils import timezone

from .models import DailyActivity, StreakStat


def get_today_for_user(user=None):
    """
    Lấy ngày hôm nay theo TIME_ZONE của project.
    Nếu sau này mỗi user có timezone riêng thì thay đổi logic ở đây.
    """
    # Django 3.2+ có timezone.localdate()
    return timezone.localdate()


def register_study_activity(user, lessons=0, minutes=0, points=0):
    """
    Gọi hàm này mỗi khi user hoàn thành 1 bài học / hoạt động học.
    Ví dụ: từ app learning gọi:
      register_study_activity(request.user, lessons=1, minutes=10, points=20)
    """
    today = get_today_for_user(user)

    activity, created = DailyActivity.objects.get_or_create(
        user=user,
        date=today,
        defaults={
            'lessons_completed': lessons,
            'minutes_studied': minutes,
            'points_earned': points,
        }
    )

    if not created:
        # Cộng dồn hoạt động trong ngày
        activity.lessons_completed += lessons
        activity.minutes_studied += minutes
        activity.points_earned += points
        activity.save()

    # Sau khi cập nhật activity, kiểm tra điều kiện để tính streak
    _update_streak_for_user(user, today, activity)


def _update_streak_for_user(user, today, activity: DailyActivity):
    """
    Cập nhật streak dựa trên DailyActivity của hôm nay.
    Điều kiện đơn giản: ít nhất 1 bài học trong ngày => được tính streak.
    """
    # Chưa đủ điều kiện, không làm gì
    if activity.lessons_completed <= 0:
        return

    streak, created = StreakStat.objects.get_or_create(user=user)

    # Nếu hôm nay đã được ghi nhận là ngày active rồi thì không update nữa
    if streak.last_active_date == today:
        return

    yesterday = today - timedelta(days=1)

    if streak.last_active_date == yesterday:
        # Tiếp tục streak
        streak.current_streak += 1
    else:
        # Bị đứt (hoặc bắt đầu mới)
        # Nếu muốn dùng Freeze, bạn có thể viết logic ở đây.
        streak.current_streak = 1

    streak.last_active_date = today

    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.save()


def recalculate_streak_from_history(user):
    """
    Optional: khi muốn build lại streak từ toàn bộ DailyActivity (trong trường hợp đổi rule).
    """
    activities = DailyActivity.objects.filter(user=user, lessons_completed__gt=0).order_by('date')

    streak, _ = StreakStat.objects.get_or_create(user=user)
    streak.current_streak = 0
    streak.longest_streak = 0
    streak.last_active_date = None

    previous_date = None

    for act in activities:
        if previous_date is None:
            streak.current_streak = 1
        else:
            if act.date == previous_date + timedelta(days=1):
                streak.current_streak += 1
            elif act.date == previous_date:
                # cùng ngày, bỏ qua (vì đã tính)
                pass
            else:
                # bị đứt chuỗi
                streak.current_streak = 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_active_date = act.date
        previous_date = act.date

    streak.save()
    return streak
