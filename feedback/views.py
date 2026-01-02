from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect, render

from .forms import PublicFeedbackForm
from .models import Client, Feedback


PUBLIC_LANGUAGES: list[tuple[str, str]] = [
    ("fi", "Suomi"),
    ("sv", "Svenska"),
    ("en", "English"),
]

PUBLIC_TEXT: dict[str, dict[str, str]] = {
    "fi": {
        "public_title": "Palaute",
        "public_intro": "Anna arvosana ja halutessasi kommentti.",
        "rating_label": "Arvosana",
        "comment_label": "Kommentti (valinnainen)",
        "submit": "Lähetä palaute",
        "thanks_title": "Kiitos palautteesta!",
        "google_cta": "Jaa palautteesi Googlessa",
    },
    "sv": {
        "public_title": "Feedback",
        "public_intro": "Ge ett betyg och en kommentar om du vill.",
        "rating_label": "Betyg",
        "comment_label": "Kommentar (valfri)",
        "submit": "Skicka feedback",
        "thanks_title": "Tack för din feedback!",
        "google_cta": "Dela din feedback på Google",
    },
    "en": {
        "public_title": "Feedback",
        "public_intro": "Give a rating and an optional comment.",
        "rating_label": "Rating",
        "comment_label": "Comment (optional)",
        "submit": "Submit feedback",
        "thanks_title": "Thanks for your feedback!",
        "google_cta": "Share your feedback on Google",
    },
}


def _normalize_lang(raw: str | None) -> str:
    code = (raw or "").strip().lower()
    if code in PUBLIC_TEXT:
        return code
    return "fi"


def _get_client_for_user(request: HttpRequest) -> Client | None:
    profile = getattr(request.user, "customer_profile", None)
    return profile.client if profile else None


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "feedback/home.html")


def public_feedback(request: HttpRequest, token: str) -> HttpResponse:
    token = (token or "").strip()
    if not token:
        raise Http404

    lang = _normalize_lang(request.POST.get("lang") if request.method == "POST" else request.GET.get("lang"))
    try:
        client = Client.objects.get(public_token=token)
    except Client.DoesNotExist as exc:
        raise Http404 from exc

    if request.method == "POST":
        form = PublicFeedbackForm(request.POST, lang=lang)
        if form.is_valid():
            if form.cleaned_data.get("website"):
                url = reverse("public-thanks", kwargs={"token": client.public_token})
                return redirect(f"{url}?lang={lang}")

            rating = form.cleaned_data["rating"]
            comment = (form.cleaned_data.get("comment") or "").strip() or None
            ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
                "REMOTE_ADDR"
            )
            ua = request.META.get("HTTP_USER_AGENT")

            Feedback.objects.create(
                client=client,
                rating=rating,
                comment=comment,
                metadata={"ip": ip, "ua": ua},
            )

            url = reverse("public-thanks", kwargs={"token": client.public_token})
            return redirect(f"{url}?r={rating}&lang={lang}")
    else:
        form = PublicFeedbackForm(lang=lang)

    return render(
        request,
        "feedback/public_feedback.html",
        {
            "client": client,
            "form": form,
            "lang": lang,
            "languages": PUBLIC_LANGUAGES,
            "t": PUBLIC_TEXT[lang],
        },
    )


def public_thanks(request: HttpRequest, token: str) -> HttpResponse:
    token = (token or "").strip()
    try:
        client = Client.objects.get(public_token=token)
    except Client.DoesNotExist as exc:
        raise Http404 from exc

    lang = _normalize_lang(request.GET.get("lang"))
    rating_raw = (request.GET.get("r") or "").strip()
    rating = int(rating_raw) if rating_raw.isdigit() else None
    show_google = bool(client.google_review_url) and rating in (4, 5)

    return render(
        request,
        "feedback/public_thanks.html",
        {
            "client": client,
            "lang": lang,
            "languages": PUBLIC_LANGUAGES,
            "t": PUBLIC_TEXT[lang],
            "show_google": show_google,
        },
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        messages.info(request, "Olet superuser: hallinta löytyy /admin/ -polusta.")
        qs = Feedback.objects.select_related("client").all()
    else:
        client = _get_client_for_user(request)
        if not client:
            messages.error(request, "Käyttäjällä ei ole liitettyä asiakasta (CustomerProfile).")
            return render(request, "feedback/dashboard.html", {"client": None, "page": None, "stats": None})
        qs = Feedback.objects.filter(client=client).select_related("client")

    stats = qs.aggregate(count=Count("id"), avg_rating=Avg("rating"))
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page") or 1)

    client = None if request.user.is_superuser else _get_client_for_user(request)
    return render(
        request,
        "feedback/dashboard.html",
        {"client": client, "page": page, "stats": stats},
    )
