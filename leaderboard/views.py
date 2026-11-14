from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions
from rest_framework.response import Response

from users.models import User

from .serializers import LeaderboardUserSerializer


class LeaderboardView(generics.ListAPIView):
    """Rank every active user by the total hours they have used Noodli."""

    serializer_class = LeaderboardUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .annotate(
                total_seconds=Coalesce(
                    Sum('user_sessions__seconds_used'), Value(0)
                )
            )
            .order_by('-total_seconds', 'username')
        )

    def list(self, request, *args, **kwargs):
        users = list(self.get_queryset())

        for position, user in enumerate(users, start=1):
            user.rank = position

        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
