from backend.filters import contains_value


def calculate_data_confidence(contractor):
    score = 100

    if contractor["price_imputed"]:
        score -= 15

    if contractor["city_imputed"]:
        score -= 15

    if contractor["synthetic"]:
        score -= 10

    return max(score, 0)


def calculate_score(contractor, request):
    score = 50.0

    price = contractor["price"]

    if price is not None:
        ratio = price / request.budget
        score += max(0, 25 * (1 - ratio))

    if (
        request.duration_hours is not None
        and contractor["max_hours"] is not None
    ):
        reserve = (
            contractor["max_hours"]
            - request.duration_hours
        )

        score += min(
            10,
            max(0, reserve * 2),
        )

    if (
        request.language
        and contains_value(
            contractor["languages"],
            request.language,
        )
    ):
        score += 10

    confidence = calculate_data_confidence(
        contractor
    )

    score += 5 * (confidence / 100)

    return round(min(score, 100), 2)


def rank_contractors(contractors, request):
    scored = []

    for contractor in contractors:
        item = contractor.copy()
        item["score"] = calculate_score(
            contractor,
            request,
        )
        item["data_confidence"] = (
            calculate_data_confidence(contractor)
        )

        scored.append(item)

    return sorted(
        scored,
        key=lambda item: (
            -item["score"],
            item["price"]
            if item["price"] is not None
            else float("inf"),
            item["id"],
        ),
    )
