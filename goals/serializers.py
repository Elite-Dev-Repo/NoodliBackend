from rest_framework import serializers

from .models import Goal
from .utils import calculate_goal_seconds, is_goal_met


class GoalSerializer(serializers.ModelSerializer):
    progress_seconds = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    goal_met = serializers.SerializerMethodField()
    target_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id',
            'title',
            'metric',
            'app_name',
            'period',
            'goal_type',
            'target_minutes',
            'target_seconds',
            'email_notifications',
            'is_active',
            'last_notified_on',
            'progress_seconds',
            'progress_percent',
            'goal_met',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'last_notified_on',
            'created_at',
            'updated_at',
        ]

    def _progress(self, obj):
        cache = self.context.setdefault('goal_progress', {})
        if obj.pk not in cache:
            cache[obj.pk] = calculate_goal_seconds(obj)
        return cache[obj.pk]

    def get_progress_seconds(self, obj):
        return self._progress(obj)

    def get_progress_percent(self, obj):
        if not obj.target_seconds:
            return 0
        progress = self._progress(obj)
        return round(min(progress / obj.target_seconds, 1) * 100, 1)

    def get_goal_met(self, obj):
        return is_goal_met(obj, self._progress(obj))

    def validate(self, attrs):
        metric = attrs.get(
            'metric', getattr(self.instance, 'metric', Goal.Metric.TOTAL_TIME)
        )
        app_name = attrs.get(
            'app_name', getattr(self.instance, 'app_name', '')
        ).strip()
        target_minutes = attrs.get(
            'target_minutes',
            getattr(self.instance, 'target_minutes', 60),
        )

        if metric == Goal.Metric.APP_TIME and not app_name:
            raise serializers.ValidationError(
                {'app_name': 'Choose an app for app-specific goals.'}
            )

        if target_minutes < 1:
            raise serializers.ValidationError(
                {'target_minutes': 'Set a target of at least 1 minute.'}
            )

        attrs['app_name'] = app_name
        return attrs
