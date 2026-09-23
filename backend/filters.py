"""Ordered hard constraints. Missing required facts fail closed."""

STAGES = ("category", "city", "event_format", "availability", "budget", "duration", "language")


def normalized(value):
    return value.strip().casefold()


def contains(values, target):
    return normalized(target) in {normalized(value) for value in values}


def evaluate_contractor(contractor, request):
    """Return the first rejection as (stage, code), or None."""
    if not contains(contractor.categories, request.category):
        return "category", "wrong_category"
    if normalized(contractor.city) != normalized(request.city):
        return "city", "wrong_city"
    if not contains(contractor.event_formats, request.event_format):
        return "event_format", "wrong_event_format"
    if request.date in contractor.busy_dates:
        return "availability", "busy"
    if contractor.price_from_kzt is None:
        return "budget", "price_unknown"
    if contractor.price_from_kzt > request.budget:
        return "budget", "over_budget"
    if request.duration_hours is not None:
        if contractor.max_hours is None:
            return "duration", "duration_unknown"
        if contractor.max_hours < request.duration_hours:
            return "duration", "duration_exceeded"
    if request.language is not None and not contains(contractor.languages, request.language):
        return "language", "language_mismatch"
    return None
