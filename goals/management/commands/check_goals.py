from django.core.management.base import BaseCommand
from django.utils import timezone

from goals.models import Goal
from goals.utils import check_goal


class Command(BaseCommand):
    help = 'Check active goals and email users whose goals have been met.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        goals = Goal.objects.filter(
            is_active=True,
            email_notifications=True,
        ).select_related('user')

        notified = 0
        for goal in goals:
            if check_goal(goal, today):
                notified += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Notified {goal.user.email} about "{goal.title}"'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Checked {goals.count()} goals, sent {notified} notification(s).'
            )
        )
