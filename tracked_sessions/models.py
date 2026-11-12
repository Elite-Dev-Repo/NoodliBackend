from django.db import models
from users.models import User
# Create your models here.

class Sessions(models.Model):
    name = models.CharField(max_length=150)
    seconds_used = models.PositiveIntegerField(default=0)
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_sessions")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["name", "date", 'user'],
                name = "unique_user_app_record"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name} "