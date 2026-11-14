from rest_framework import serializers

from users.models import User


class LeaderboardUserSerializer(serializers.ModelSerializer):
    """Public leaderboard representation of a user.

    Deliberately exposes only the username (never the email address) along
    with their aggregated usage.
    """

    rank = serializers.IntegerField(read_only=True)
    total_seconds = serializers.IntegerField(read_only=True)
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'rank', 'total_seconds', 'total_hours']

    def get_total_hours(self, obj):
        return round((obj.total_seconds or 0) / 3600, 2)
