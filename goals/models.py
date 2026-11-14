from django.conf import settings
from django.db import models


class Goal(models.Model):
    class Metric(models.TextChoices):
        TOTAL_TIME = "total_time", "Total screen time"
        APP_TIME = "app_time", "App screen time"

    class Period(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"

    class GoalType(models.TextChoices):
        LIMIT = "limit", "Limit (notify when exceeded)"
        ACHIEVE = "achieve", "Achievement (notify when reached)"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="goals",
    )
    title = models.CharField(max_length=150)
    metric = models.CharField(
        max_length=20,
        choices=Metric.choices,
        default=Metric.TOTAL_TIME,
    )
    app_name = models.CharField(max_length=150, blank=True, default="")
    period = models.CharField(
        max_length=20,
        choices=Period.choices,
        default=Period.DAILY,
    )
    goal_type = models.CharField(
        max_length=20,
        choices=GoalType.choices,
        default=GoalType.LIMIT,
    )
    target_minutes = models.PositiveIntegerField(default=60)
    email_notifications = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_notified_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"

    @property
    def target_seconds(self):
        return self.target_minutes * 60
