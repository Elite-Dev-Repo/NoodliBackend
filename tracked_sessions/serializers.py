from rest_framework import serializers

from .models import Sessions


class SessionsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Sessions
        fields = ['id', 'name', 'seconds_used', 'date', 'user']
        read_only_fields = ['id', 'user']
