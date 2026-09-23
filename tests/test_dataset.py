"""Small artificial fixtures test parsing; they are not catalogue profiles."""

import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from backend.data_loader import DatasetError, REQUIRED_COLUMNS, load_contractors


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "test.csv"
        self.row = dict.fromkeys(REQUIRED_COLUMNS, "")
        self.row.update(
            id="TEST-1", anon_name="Тестовый профиль", categories=" Фотограф | Видеограф |Фотограф ",
            city=" Алматы ", city_imputed="false", synthetic="1", price_imputed="TRUE",
            price_from_kzt="200000", max_hours="8.5", event_formats="свадьба|той",
            languages="русский|казахский", busy_dates="2026-11-14|2026-11-15",
            description="Описание, с запятой\nи переносом строки",
        )

    def write_rows(self, rows, columns=REQUIRED_COLUMNS):
        with self.path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def test_normalizes_facts_and_preserves_dates_and_description(self):
        self.write_rows([self.row])
        contractor, = load_contractors(self.path)
        self.assertEqual(contractor.city, "Алматы")
        self.assertEqual(contractor.categories, ("Фотограф", "Видеограф"))
        self.assertEqual(contractor.price_from_kzt, Decimal("200000"))
        self.assertEqual(contractor.max_hours, Decimal("8.5"))
        self.assertEqual(contractor.busy_dates, (date(2026, 11, 14), date(2026, 11, 15)))
        self.assertFalse(contractor.city_imputed)
        self.assertTrue(contractor.synthetic)
        self.assertTrue(contractor.price_imputed)
        self.assertEqual(contractor.description, self.row["description"])
        self.assertEqual(load_contractors(self.path), (contractor,))

    def test_missing_values_are_not_invented(self):
        row = dict.fromkeys(REQUIRED_COLUMNS, "")
        row.update(id="TEST-2", anon_name="Пустой тестовый профиль")
        self.write_rows([row])
        contractor, = load_contractors(self.path)
        self.assertIsNone(contractor.price_from_kzt)
        self.assertIsNone(contractor.max_hours)
        self.assertIsNone(contractor.synthetic)
        self.assertEqual(contractor.busy_dates, ())
        self.assertEqual(contractor.city, "")

    def test_invalid_facts_report_field(self):
        for field, value in (
            ("busy_dates", "2026-02-30"), ("price_from_kzt", "NaN"),
            ("price_from_kzt", "-1"), ("max_hours", "Infinity"),
            ("price_from_kzt", "unknown"), ("synthetic", "maybe"), ("id", ""),
        ):
            with self.subTest(field=field, value=value):
                self.write_rows([dict(self.row, **{field: value})])
                with self.assertRaisesRegex(DatasetError, field):
                    load_contractors(self.path)

    def test_duplicate_ids_are_rejected(self):
        self.write_rows([self.row, self.row])
        with self.assertRaisesRegex(DatasetError, "повторяется id"):
            load_contractors(self.path)

    def test_missing_columns_are_rejected(self):
        self.write_rows([], columns=("id", "anon_name"))
        with self.assertRaisesRegex(DatasetError, "Отсутствуют колонки"):
            load_contractors(self.path)

    def test_bad_row_length_is_rejected(self):
        self.write_rows([])
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write("TEST-1,short\n")
        with self.assertRaisesRegex(DatasetError, "число значений"):
            load_contractors(self.path)

    def test_empty_file_is_rejected(self):
        self.path.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(DatasetError, "CSV пуст"):
            load_contractors(self.path)

    def test_missing_file_has_actionable_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "Добавьте исходный датасет"):
            load_contractors(self.path)


if __name__ == "__main__":
    unittest.main()
