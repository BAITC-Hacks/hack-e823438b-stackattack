"""Shared deterministic pipeline for recommendations and scenario comparison."""
from collections import Counter

from .explanations import REJECTION_LABELS, build_explanation, rejection_details
from .filters import STAGES, evaluate_contractor
from .scoring import fit_score, rank_contractors


def recommend(contractors, request):
    eligible, rejections = [], []
    funnel = dict(total=len(contractors), **{stage: 0 for stage in STAGES})
    for contractor in contractors:
        failure = evaluate_contractor(contractor, request)
        for stage in STAGES:
            if failure and stage == failure[0]:
                break
            funnel[stage] += 1
        if failure:
            rejections.append(rejection_details(contractor, request, *failure))
        else:
            eligible.append(contractor)
    ranked = rank_contractors(eligible, request)
    cards = []
    for contractor in ranked[:3]:
        cards.append(dict(
            id=contractor.id, name=contractor.anon_name, city=contractor.city,
            categories=contractor.categories, event_formats=contractor.event_formats,
            languages=contractor.languages, max_hours=contractor.max_hours,
            price=contractor.price_from_kzt, description=contractor.description,
            score=fit_score(contractor, request), why_this=build_explanation(contractor, request),
            data_confidence=dict(city_imputed=contractor.city_imputed,
                                 price_imputed=contractor.price_imputed, synthetic=contractor.synthetic),
        ))
    for position, contractor in enumerate(ranked[3:], start=4):
        rejections.append(dict(contractor_id=contractor.id, name=contractor.anon_name,
                               rejected_at="ranking", reason="below_top_3",
                               details=REJECTION_LABELS["below_top_3"], rank=position,
                               score=fit_score(contractor, request)))
    counts = Counter(item["reason"] for item in rejections)
    funnel.update(final=len(eligible), returned=len(cards))
    return dict(query=request.model_dump(mode="json"), funnel=funnel,
                total_contractors=len(contractors), eligible_count=len(eligible),
                eligible_ids=[item.id for item in ranked], returned_count=len(cards),
                recommendations=cards, rejections=rejections,
                why_not={code: dict(label=REJECTION_LABELS[code], count=count) for code, count in sorted(counts.items())},
                message=None if cards else "Нет подрядчиков, удовлетворяющих всем заданным условиям.")
