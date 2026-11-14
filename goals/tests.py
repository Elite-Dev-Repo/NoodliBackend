from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from tracked_sessions.models import Sessions
from users.models import User

from .models import Goal
from .utils import calculate_goal_seconds, evaluate_goals_for_user


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class GoalNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='goals@example.com',
            password='test-pass-123',
            username='goals-tester',
            is_active=True,
        )
        self.today = timezone.localdate()

    def create_goal(self, **overrides):
        data = {
            'user': self.user,
            'title': 'Instagram limit',
            'metric': Goal.Metric.APP_TIME,
            'app_name': 'Instagram',
            'period': Goal.Period.DAILY,
            'goal_type': Goal.GoalType.LIMIT,
            'target_minutes': 30,
        }
        data.update(overrides)
        return Goal.objects.create(**data)

    def add_session(self, name, seconds, date=None):
        return Sessions.objects.create(
            user=self.user,
            name=name,
            seconds_used=seconds,
            date=date or self.today,
        )

    def test_progress_matches_app_sessions_ignoring_exe_suffix(self):
        self.add_session('Instagram.exe', 600)
        self.add_session('Chrome.exe', 300)
        goal = self.create_goal()

        self.assertEqual(calculate_goal_seconds(goal, self.today), 600)

    def test_sends_email_once_when_goal_is_met(self):
        self.add_session('Instagram.exe', 1800)
        goal = self.create_goal()

        notified = evaluate_goals_for_user(self.user, self.today)
        self.assertEqual(notified, [goal.pk])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Goal reached', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        goal.refresh_from_db()
        self.assertEqual(goal.last_notified_on, self.today)

        self.assertEqual(evaluate_goals_for_user(self.user, self.today), [])
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_when_below_target(self):
        self.add_session('Instagram.exe', 600)
        self.create_goal()

        self.assertEqual(evaluate_goals_for_user(self.user, self.today), [])
        self.assertEqual(len(mail.outbox), 0)

    def test_achievement_goal_email_and_no_email_when_disabled(self):
        self.add_session('Chrome.exe', 3600)
        achieved = self.create_goal(
            title='Chrome focus',
            metric=Goal.Metric.TOTAL_TIME,
            app_name='',
            goal_type=Goal.GoalType.ACHIEVE,
            target_minutes=45,
        )
        self.create_goal(
            title='Muted goal',
            metric=Goal.Metric.TOTAL_TIME,
            app_name='',
            target_minutes=1,
            email_notifications=False,
        )

        notified = evaluate_goals_for_user(self.user, self.today)
        self.assertEqual(notified, [achieved.pk])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Goal achieved', mail.outbox[0].subject)

    def test_weekly_goal_uses_rolling_week(self):
        self.add_session('Instagram.exe', 1800, self.today)
        self.add_session(
            'Instagram.exe',
            1800,
            self.today - timedelta(days=6),
        )
        self.add_session(
            'Instagram.exe',
            1800,
            self.today - timedelta(days=7),
        )
        goal = self.create_goal(period=Goal.Period.WEEKLY, target_minutes=60)

        self.assertEqual(calculate_goal_seconds(goal, self.today), 3600)
