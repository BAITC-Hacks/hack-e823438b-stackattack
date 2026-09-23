"""Budget headroom ranking; this score is not a quality/probability estimate."""
from decimal import Decimal


def fit_score(contractor, request):
    if request.budget == 0:
        return Decimal(0)
    return (request.budget - contractor.price_from_kzt) / request.budget


def rank_contractors(contractors, request):
    return sorted(contractors, key=lambda item: (-fit_score(item, request), item.id))
