from collections import Counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.data_loader import load_contractors
from backend.explanations import (
    REJECTION_LABELS,
    build_explanation,
)
from backend.filters import evaluate_contractor
from backend.models import RecommendationRequest
from backend.scoring import rank_contractors
from backend.what_if import build_what_if


app = FastAPI(
    title="EventDNA API",
    description="Explainable event contractor recommendation engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

contractors = load_contractors()


@app.get("/")
def root():
    return {
        "name": "EventDNA",
        "status": "ok",
        "contractors_loaded": len(contractors),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "contractors_loaded": len(contractors),
    }


@app.get("/filters")
def get_filters():
    cities = sorted(
        {
            contractor["city"]
            for contractor in contractors
            if contractor["city"]
        }
    )

    categories = sorted(
        {
            category
            for contractor in contractors
            for category in contractor["categories"]
        }
    )

    event_formats = sorted(
        {
            event_format
            for contractor in contractors
            for event_format
            in contractor["event_formats"]
        }
    )

    languages = sorted(
        {
            language
            for contractor in contractors
            for language in contractor["languages"]
        }
    )

    prices = [
        contractor["price"]
        for contractor in contractors
        if contractor["price"] is not None
    ]

    return {
        "cities": cities,
        "categories": categories,
        "event_formats": event_formats,
        "languages": languages,
        "price_range": {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
        },
    }


@app.post("/recommendations")
def recommendations(
    request: RecommendationRequest,
):
    eligible = []
    rejected = Counter()

    for contractor in contractors:
        passed, reason = evaluate_contractor(
            contractor,
            request,
        )

        if passed:
            eligible.append(contractor)
        else:
            rejected[reason] += 1

    ranked = rank_contractors(
        eligible,
        request,
    )

    top_three = ranked[:3]

    cards = []

    for contractor in top_three:
        cards.append(
            {
                "id": contractor["id"],
                "name": contractor["name"],
                "categories": contractor[
                    "categories"
                ],
                "city": contractor["city"],
                "price": contractor["price"],
                "event_formats": contractor[
                    "event_formats"
                ],
                "languages": contractor[
                    "languages"
                ],
                "max_hours": contractor[
                    "max_hours"
                ],
                "description": contractor[
                    "description"
                ],
                "score": contractor["score"],
                "data_confidence": contractor[
                    "data_confidence"
                ],
                "price_imputed": contractor[
                    "price_imputed"
                ],
                "city_imputed": contractor[
                    "city_imputed"
                ],
                "synthetic": contractor[
                    "synthetic"
                ],
                "why_this": build_explanation(
                    contractor,
                    request,
                ),
            }
        )

    why_not = {
        code: {
            "label": REJECTION_LABELS.get(
                code,
                code,
            ),
            "count": count,
        }
        for code, count in rejected.items()
    }

    return {
        "query": {
            "city": request.city,
            "date": request.date.isoformat(),
            "event_format": request.event_format,
            "category": request.category,
            "budget": request.budget,
            "duration_hours": request.duration_hours,
            "language": request.language,
        },
        "total_contractors": len(contractors),
        "eligible_count": len(eligible),
        "returned_count": len(cards),
        "recommendations": cards,
        "why_not": why_not,
    }


@app.post("/what-if")
def what_if(
    request: RecommendationRequest,
):
    return build_what_if(
        contractors,
        request,
    )
