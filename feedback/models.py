import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import IntegrityError, models, transaction
from django.urls import reverse


def _make_public_token() -> str:
    token = secrets.token_urlsafe(9)
    return token.rstrip("=")


class Client(models.Model):
    name = models.CharField(max_length=200)
    public_token = models.CharField(max_length=64, unique=True, blank=True)
    google_review_url = models.URLField(max_length=2000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def get_public_path(self) -> str:
        return reverse("public-feedback", kwargs={"token": self.public_token})

    def get_public_url(self) -> str:
        base = getattr(settings, "PUBLIC_BASE_URL", None)
        if base:
            return f"{base}{self.get_public_path()}"
        return self.get_public_path()

    def save(self, *args, **kwargs):
        if self.public_token:
            return super().save(*args, **kwargs)

        last_err = None
        for _ in range(10):
            self.public_token = _make_public_token()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as err:
                last_err = err

        raise last_err  # pragma: no cover


class Feedback(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.client}: {self.rating} ({self.created_at:%Y-%m-%d})"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile"
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="users")

    def __str__(self) -> str:
        return f"{self.user} -> {self.client}"
