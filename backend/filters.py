def normalize(value):
    if value is None:
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


def contains_value(values, target):
    target = normalize(target)

    return any(
        normalize(value) == target
        for value in values
    )


def evaluate_contractor(contractor, request):
    if not contains_value(
        contractor["categories"],
        request.category,
    ):
        return False, "wrong_category"

    if normalize(contractor["city"]) != normalize(
        request.city
    ):
        return False, "wrong_city"

    if not contains_value(
        contractor["event_formats"],
        request.event_format,
    ):
        return False, "wrong_event_format"

    selected_date = request.date.isoformat()

    if selected_date in contractor["busy_dates"]:
        return False, "busy"

    if (
        contractor["price"] is not None
        and contractor["price"] > request.budget
    ):
        return False, "over_budget"

    if (
        request.duration_hours is not None
        and contractor["max_hours"] is not None
        and contractor["max_hours"]
        < request.duration_hours
    ):
        return False, "duration_too_long"

    if (
        request.language
        and not contains_value(
            contractor["languages"],
            request.language,
        )
    ):
        return False, "wrong_language"

    return True, None
