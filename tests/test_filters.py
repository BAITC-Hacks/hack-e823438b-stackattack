import unittest
from datetime import date
from decimal import Decimal
from backend.filters import evaluate_contractor
from tests.helpers import contractor, query


class FilterTests(unittest.TestCase):
    def test_each_constraint(self):
        cases = [
            ({"categories": ("Ведущий",)}, "wrong_category"),
            ({"city": "Астана"}, "wrong_city"),
            ({"event_formats": ("той",)}, "wrong_event_format"),
            ({"busy_dates": (date(2026, 11, 14),)}, "busy"),
            ({"price_from_kzt": Decimal(400001)}, "over_budget"),
            ({"price_from_kzt": None}, "price_unknown"),
            ({"max_hours": Decimal(7)}, "duration_exceeded"),
            ({"max_hours": None}, "duration_unknown"),
            ({"languages": ("казахский",)}, "language_mismatch"),
        ]
        for change, code in cases:
            with self.subTest(code=code):
                self.assertEqual(evaluate_contractor(contractor(**change), query())[1], code)

    def test_exact_boundaries_and_case(self):
        c = contractor(price_from_kzt=Decimal(400000), max_hours=Decimal(8))
        self.assertIsNone(evaluate_contractor(c, query(city=" алматы ", category="фотограф")))

    def test_optional_constraints_and_other_busy_date(self):
        c = contractor(max_hours=None, languages=(), busy_dates=(date(2026, 11, 15),))
        self.assertIsNone(evaluate_contractor(c, query(duration_hours=None, language=None)))

    def test_first_rejection_is_stable(self):
        self.assertEqual(evaluate_contractor(contractor(city="Астана", price_from_kzt=None), query()), ("city", "wrong_city"))
