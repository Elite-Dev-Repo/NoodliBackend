import secrets
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from tracked_sessions.models import Sessions

User = get_user_model()

APP_NAME = "Instagram"

DUMMY_USERS = [
    ("neonfox", "18.0"),
    ("pixelpanda", "16.5"),
    ("lunarotter", "15.25"),
    ("cobaltwolf", "14.0"),
    ("velvetcrane", "12.75"),
    ("echojaguar", "11.5"),
    ("solarfinch", "10.0"),
    ("mysticbadger", "8.75"),
    ("toffeecomet", "7.5"),
    ("quartzraven", "6.0"),
    ("hyperlynx", "4.25"),
    ("duskmeadow", "2.5"),
    ("frostkoi", "1.0"),
]


class Command(BaseCommand):
    help = (
        "Create 13 dummy leaderboard users, each with a single app session "
        "totalling 18 hours or less."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Generate and print a new password for existing dummy users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        today = date.today()
        reset_passwords = options["reset_passwords"]
        rows = []

        for username, hours in DUMMY_USERS:
            email = f"{username}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": username, "is_active": True},
            )

            password = None
            changed = False

            if created or reset_passwords:
                password = f"Ndl!{secrets.token_urlsafe(18)}"
                user.set_password(password)
                changed = True

            if user.username != username:
                user.username = username
                changed = True

            if not user.is_active:
                user.is_active = True
                changed = True

            if changed:
                user.save()

            seconds = int(Decimal(hours) * 3600)
            session, session_created = Sessions.objects.get_or_create(
                user=user,
                name=APP_NAME,
                date=today,
                defaults={"seconds_used": seconds},
            )

            if not session_created and session.seconds_used != seconds:
                session.seconds_used = seconds
                session.save(update_fields=["seconds_used"])

            Sessions.objects.filter(user=user).exclude(pk=session.pk).delete()

            rows.append(
                {
                    "username": username,
                    "email": email,
                    "password": password,
                    "hours": hours,
                }
            )

        generated_count = sum(1 for row in rows if row["password"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(rows)} dummy users "
                f"({generated_count} password(s) generated)."
            )
        )
        self.stdout.write("")
        self.stdout.write(
            f"{'USERNAME':<14} {'HOURS':>6}  {'EMAIL':<28} PASSWORD"
        )
        self.stdout.write("-" * 90)

        for row in rows:
            self.stdout.write(
                f"{row['username']:<14} {row['hours']:>6}  "
                f"{row['email']:<28} {row['password'] or '(unchanged)'}"
            )
