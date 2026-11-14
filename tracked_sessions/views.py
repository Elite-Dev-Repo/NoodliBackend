from rest_framework import generics, permissions
from .models import Sessions
from .serializers import SessionsSerializer
from django.db import transaction
from django.db.models import F

from goals.utils import evaluate_goals_for_user


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = SessionsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Sessions.objects.filter(user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        # Automatically enable 'many=True' when the incoming payload is a list
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        data = self.request.data

        with transaction.atomic():
            for d in data:
                name = d.get("name")
                count = d.get("count", 0)
                date = d.get("date")

                # Safely get or create the session entry
                obj, created = Sessions.objects.get_or_create(
                    user=self.request.user,
                    name=name,
                    date=date,
                    defaults={"seconds_used": count}
                )

                # If it already exists for today, increment the existing count atomically
                if not created:
                    Sessions.objects.filter(pk=obj.pk).update(
                        seconds_used=F('seconds_used') + count
                    )

        # Goals are evaluated after tracking data is written so emails reflect
        # the latest usage totals.
        evaluate_goals_for_user(self.request.user)


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SessionsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Sessions.objects.filter(user=self.request.user)