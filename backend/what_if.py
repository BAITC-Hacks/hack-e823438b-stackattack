from datetime import timedelta

from backend.filters import evaluate_contractor


def count_eligible(contractors, request):
    count = 0

    for contractor in contractors:
        passed, _ = evaluate_contractor(
            contractor,
            request,
        )

        if passed:
            count += 1

    return count


def build_what_if(contractors, request):
    current_count = count_eligible(
        contractors,
        request,
    )

    suggestions = []

    budget_steps = [
        50000,
        100000,
        200000,
    ]

    for step in budget_steps:
        changed = request.model_copy(
            update={
                "budget": request.budget + step
            }
        )

        new_count = count_eligible(
            contractors,
            changed,
        )

        gain = new_count - current_count

        if gain > 0:
            suggestions.append(
                {
                    "type": "budget",
                    "title": (
                        f"Увеличить бюджет на "
                        f"{step:,} ₸".replace(",", " ")
                    ),
                    "new_value": request.budget + step,
                    "new_candidates": gain,
                    "total_candidates": new_count,
                }
            )

    for days in range(1, 4):
        new_date = (
            request.date
            + timedelta(days=days)
        )

        changed = request.model_copy(
            update={
                "date": new_date
            }
        )

        new_count = count_eligible(
            contractors,
            changed,
        )

        gain = new_count - current_count

        if gain > 0:
            suggestions.append(
                {
                    "type": "date",
                    "title": (
                        f"Перенести дату на "
                        f"{new_date.strftime('%d.%m.%Y')}"
                    ),
                    "new_value": new_date.isoformat(),
                    "new_candidates": gain,
                    "total_candidates": new_count,
                }
            )

    if (
        request.duration_hours is not None
        and request.duration_hours > 1
    ):
        for decrease in [1, 2]:
            new_duration = (
                request.duration_hours
                - decrease
            )

            if new_duration <= 0:
                continue

            changed = request.model_copy(
                update={
                    "duration_hours": new_duration
                }
            )

            new_count = count_eligible(
                contractors,
                changed,
            )

            gain = new_count - current_count

            if gain > 0:
                suggestions.append(
                    {
                        "type": "duration",
                        "title": (
                            f"Сократить длительность "
                            f"до {new_duration:g} ч."
                        ),
                        "new_value": new_duration,
                        "new_candidates": gain,
                        "total_candidates": new_count,
                    }
                )

    suggestions.sort(
        key=lambda item: (
            -item["new_candidates"],
            item["type"],
        )
    )

    return {
        "current_candidates": current_count,
        "suggestions": suggestions[:5],
    }
