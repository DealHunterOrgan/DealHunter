import math

from django import template

register = template.Library()


def _stars_from_score(score):
    try:
        value = float(score)
    except (TypeError, ValueError):
        return 0

    if value <= 0:
        return 0

    stars = math.ceil(value / 20)
    return max(1, min(stars, 5))


@register.filter
def score_to_stars(score):
    stars = _stars_from_score(score)
    return "★" * stars + "☆" * (5 - stars)


@register.filter
def score_stars_class(score):
    stars = _stars_from_score(score)
    if stars >= 4:
        return "score-gold"
    if stars >= 3:
        return "score-yellow"
    return "score-red"
