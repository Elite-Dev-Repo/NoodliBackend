from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'metric',
        'app_name',
        'period',
        'goal_type',
        'target_minutes',
        'is_active',
        'email_notifications',
        'last_notified_on',
    )
    list_filter = (
        'metric',
        'period',
        'goal_type',
        'is_active',
        'email_notifications',
    )
    search_fields = ('title', 'app_name', 'user__email', 'user__username')
