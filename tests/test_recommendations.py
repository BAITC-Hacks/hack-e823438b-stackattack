import unittest
from datetime import date
from decimal import Decimal
from backend.engine import recommend
from backend.what_if import build_what_if
from tests.helpers import contractor, query


class RecommendationTests(unittest.TestCase):
    def test_zero_to_many_and_all_profiles_accounted_for(self):
        for count in range(6):
            with self.subTest(count=count):
                items = [contractor(id=f"TEST-{i}") for i in range(count)]
                result = recommend(items, query())
                self.assertEqual(result["returned_count"], min(count, 3))
                self.assertEqual(len(result["recommendations"]) + len(result["rejections"]), count)
                self.assertEqual(result["funnel"]["final"], count)

    def test_order_score_and_ties_are_deterministic(self):
        items = [contractor(id="B"), contractor(id="A"), contractor(id="C", price_from_kzt=Decimal(100000))]
        a = recommend(items, query())
        b = recommend(list(reversed(items)), query())
        self.assertEqual(a["recommendations"], b["recommendations"])
        self.assertEqual(a["eligible_ids"], ["C", "A", "B"])
        self.assertEqual(a["recommendations"][0]["score"], Decimal("0.75"))

    def test_busy_never_recommended_and_funnel_conserves_counts(self):
        items = [contractor(id="busy", busy_dates=(date(2026, 11, 14),)), contractor(id="expensive", price_from_kzt=Decimal(500000)), contractor()]
        r = recommend(items, query())
        self.assertEqual(r["eligible_ids"], ["TEST-1"])
        self.assertEqual(r["funnel"]["event_format"], 3)
        self.assertEqual(r["funnel"]["availability"], 2)
        self.assertEqual(r["funnel"]["budget"], 1)
        self.assertEqual(r["why_not"]["busy"]["count"], 1)
        self.assertEqual(r["rejections"][0]["requested"], date(2026, 11, 14))

    def test_zero_budget_and_provenance_do_not_break_ranking(self):
        r = recommend([contractor(price_from_kzt=Decimal(0))], query(budget=0))
        self.assertEqual(r["recommendations"][0]["score"], 0)
        a = contractor(id="A", synthetic=True, price_imputed=True)
        b = contractor(id="B", synthetic=False, price_imputed=False)
        self.assertEqual(recommend([b, a], query())["eligible_ids"], ["A", "B"])

    def test_reasons_are_factual(self):
        reasons = recommend([contractor()], query())["recommendations"][0]["why_this"]
        self.assertEqual(next(x for x in reasons if x["code"] == "budget_headroom")["actual"], 200000)
        self.assertIn("не указана среди занятых", next(x for x in reasons if x["code"] == "availability")["text"])

    def test_what_if_reruns_budget_date_and_duration(self):
        items = [contractor(id="busy", busy_dates=(date(2026, 11, 14),)), contractor(id="price", price_from_kzt=Decimal(500000)), contractor(id="short", max_hours=Decimal(6)), contractor(id="tomorrow_busy", busy_dates=(date(2026, 11, 15),))]
        r = build_what_if(items, query())
        budget, day, duration = r["scenarios"]
        self.assertEqual(budget["added_ids"], ["price"])
        self.assertEqual(day["added_ids"], ["busy"])
        self.assertEqual(day["removed_ids"], ["tomorrow_busy"])
        self.assertEqual(day["eligible_delta"], 0)
        self.assertEqual(duration["added_ids"], ["short"])
        self.assertEqual(query().duration_hours, 8)
