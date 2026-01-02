from django import template

register = template.Library()


@register.filter
def stars(value: int | str | None) -> str:
    try:
        rating = int(value or 0)
    except (TypeError, ValueError):
        rating = 0
    rating = max(0, min(5, rating))
    on = "★" * rating
    off = "☆" * (5 - rating)
    return f'<span class="stars-display"><span class="on">{on}</span><span class="off">{off}</span></span>'

