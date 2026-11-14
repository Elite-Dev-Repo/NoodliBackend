import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.utils import timezone

from tracked_sessions.models import Sessions

from .models import Goal

logger = logging.getLogger(__name__)


def get_period_start(period, today=None):
    """Return the first day of the goal's current period."""
    today = today or timezone.localdate()
    if period == Goal.Period.WEEKLY:
        return today - timedelta(days=6)
    return today


def period_label(period):
    return "this week" if period == Goal.Period.WEEKLY else "today"


def format_duration(seconds):
    total = max(0, int(round(seconds or 0)))
    hours, remainder = divmod(total, 3600)
    minutes = remainder // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return f"{total}s"


def calculate_goal_seconds(goal, today=None):
    """Total tracked seconds for a goal in its current period."""
    today = today or timezone.localdate()
    start = get_period_start(goal.period, today)
    sessions = Sessions.objects.filter(
        user=goal.user,
        date__gte=start,
        date__lte=today,
    )

    if goal.metric == Goal.Metric.APP_TIME:
        raw_name = (goal.app_name or "").strip()
        base_name = raw_name[:-4] if raw_name.lower().endswith(".exe") else raw_name
        sessions = sessions.filter(
            Q(name__iexact=base_name) | Q(name__iexact=f"{base_name}.exe")
        )

    result = sessions.aggregate(total=Sum("seconds_used"))
    return result["total"] or 0


def is_goal_met(goal, progress_seconds=None, today=None):
    if progress_seconds is None:
        progress_seconds = calculate_goal_seconds(goal, today)
    return progress_seconds >= goal.target_seconds


def already_notified(goal, today=None):
    if not goal.last_notified_on:
        return False

    today = today or timezone.localdate()
    if goal.period == Goal.Period.WEEKLY:
        return goal.last_notified_on >= get_period_start(goal.period, today)
    return goal.last_notified_on == today


def build_goal_message(goal, progress_seconds):
    period = period_label(goal.period)
    scope = goal.app_name if goal.metric == Goal.Metric.APP_TIME else "all apps"
    progress = format_duration(progress_seconds)
    target = format_duration(goal.target_seconds)
    username = goal.user.username or goal.user.email

    if goal.goal_type == Goal.GoalType.LIMIT:
        subject = f"Goal reached: {goal.title}"
        message = (
            f"Hi {username},\n\n"
            f'Your Noodli goal "{goal.title}" has been reached.\n\n'
            f"You've spent {progress} in {scope} {period}, which is at or over "
            f"your limit of {target}.\n\n"
            "Consider taking a short break and coming back refreshed.\n\n"
            "Keep going,\n"
            "The Noodli team"
        )
    else:
        subject = f"Goal achieved: {goal.title}"
        message = (
            f"Hi {username},\n\n"
            f'Congratulations! You achieved your Noodli goal "{goal.title}".\n\n'
            f"You've spent {progress} in {scope} {period}, hitting your target "
            f"of {target}.\n\n"
            "Nice work - keep the momentum going.\n\n"
            "The Noodli team"
        )

    return subject, message


def send_goal_email(goal, progress_seconds):
    subject, message = build_goal_message(goal, progress_seconds)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [goal.user.email],
    )


def check_goal(goal, today=None):
    """Email the user if the goal was met and hasn't been emailed this period."""
    if not goal.is_active or not goal.email_notifications:
        return False

    today = today or timezone.localdate()
    if already_notified(goal, today):
        return False

    progress = calculate_goal_seconds(goal, today)
    if progress < goal.target_seconds:
        return False

    try:
        send_goal_email(goal, progress)
    except Exception:
        logger.exception(
            "Failed to send goal notification email for goal %s", goal.pk
        )
        return False

    goal.last_notified_on = today
    goal.save(update_fields=["last_notified_on", "updated_at"])
    return True


def evaluate_goals_for_user(user, today=None):
    """Check every active, email-enabled goal for a user."""
    today = today or timezone.localdate()
    goals = Goal.objects.filter(
        user=user,
        is_active=True,
        email_notifications=True,
    )

    notified = []
    for goal in goals:
        try:
            if check_goal(goal, today):
                notified.append(goal.pk)
        except Exception:
            logger.exception("Failed to evaluate goal %s", goal.pk)

    return notified
