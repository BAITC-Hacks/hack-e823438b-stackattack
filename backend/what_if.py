"""Real reruns of the same engine; counts include all eligible candidates."""
from datetime import date, timedelta
from decimal import Decimal
from .engine import recommend
from .models import RecommendationRequest


def build_what_if(contractors, request):
    baseline = recommend(contractors, request)
    changes = [{"budget": request.budget + Decimal(100000)}]
    if request.date < date.max:
        changes.append({"date": request.date + timedelta(days=1)})
    if request.duration_hours is not None and request.duration_hours > 2:
        changes.append({"duration_hours": request.duration_hours - 2})
    scenarios = []
    before = set(baseline["eligible_ids"])
    for change in changes:
        updated = RecommendationRequest.model_validate({**request.model_dump(), **change})
        result = recommend(contractors, updated)
        after = set(result["eligible_ids"])
        scenarios.append(dict(changes=change, added_ids=sorted(after - before), removed_ids=sorted(before - after),
                              eligible_delta=len(after) - len(before), result=result))
    return dict(baseline=baseline, scenarios=scenarios)
