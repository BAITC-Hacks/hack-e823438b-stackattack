"""Real reruns of the same engine; counts include all eligible candidates."""
from datetime import date, timedelta
from decimal import Decimal
from .engine import recommend
from .models import RecommendationRequest


def build_what_if(contractors, request):
    baseline = recommend(contractors, request)
    changes = [("budget", {"budget": request.budget + step}) for step in (50000, 100000, 200000)]
    for days in range(1, 4):
        if (date.max - request.date).days >= days:
            changes.append(("date", {"date": request.date + timedelta(days=days)}))
    if request.duration_hours is not None:
        for decrease in (1, 2):
            if request.duration_hours > decrease:
                changes.append(("duration", {"duration_hours": request.duration_hours - Decimal(decrease)}))
    scenarios, suggestions = [], []
    before = set(baseline["eligible_ids"])
    for kind, change in changes:
        updated = RecommendationRequest.model_validate({**request.model_dump(), **change})
        result = recommend(contractors, updated)
        after = set(result["eligible_ids"])
        added, removed = sorted(after - before), sorted(before - after)
        scenarios.append(dict(type=kind, changes=change, added_ids=added, removed_ids=removed,
                              eligible_delta=len(after) - len(before), result=result))
        if len(after) > len(before):
            new_value = next(iter(change.values()))
            title = {
                "budget": f"Бюджет: {updated.budget} ₸",
                "date": f"Дата: {updated.date}",
                "duration": f"Длительность: {updated.duration_hours} ч",
            }[kind]
            suggestions.append(dict(type=kind, title=title, new_value=new_value,
                                    new_candidates=len(added), removed_candidates=len(removed),
                                    eligible_delta=len(after) - len(before), total_candidates=len(after)))
    suggestions.sort(key=lambda item: (-item["eligible_delta"], item["type"]))
    return dict(baseline=baseline, scenarios=scenarios, current_candidates=len(before), suggestions=suggestions[:5])
