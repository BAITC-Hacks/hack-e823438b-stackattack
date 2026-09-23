import csv
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.data_loader import REQUIRED_COLUMNS
from backend.main import create_app
from tests.helpers import query


class APITests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "catalogue.csv"
        row = dict.fromkeys(REQUIRED_COLUMNS, "")
        row.update(id="TEST-API", anon_name="Тестовый профиль", city="Алматы", categories="Фотограф", price_from_kzt="200000", event_formats="свадьба", languages="русский", max_hours="10")
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow(row)

    def test_end_to_end_api_and_static_frontend(self):
        with TestClient(create_app(self.path)) as client:
            self.assertEqual(client.get("/health").json()["contractors_loaded"], 1)
            self.assertEqual(client.get("/api/filters").json()["cities"], ["Алматы"])
            payload = query().model_dump(mode="json")
            response = client.post("/api/recommend", json=payload)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["recommendations"][0]["name"], "Тестовый профиль")
            self.assertEqual(client.post("/recommendations", json=payload).json(), response.json())
            self.assertEqual(client.post("/api/what-if", json=payload).status_code, 200)
            self.assertIn("EventDNA", client.get("/").text)
            self.assertEqual(client.get("/style.css").status_code, 200)
            self.assertEqual(client.get("/openapi.json").status_code, 200)

    def test_validation(self):
        with TestClient(create_app(self.path)) as client:
            for change in ({"budget": -1}, {"budget": True}, {"budget": "NaN"}, {"date": "bad"}, {"city": " "}, {"duration_hours": 0}, {"language": " "}, {"unknown": 1}):
                with self.subTest(change=change):
                    payload = {**query().model_dump(mode="json"), **change}
                    self.assertEqual(client.post("/api/recommend", json=payload).status_code, 422)

    def test_empty_dataset_explicitly_unavailable(self):
        self.path.write_text(",".join(REQUIRED_COLUMNS) + "\n", encoding="utf-8")
        with TestClient(create_app(self.path)) as client:
            self.assertEqual(client.get("/health").json()["status"], "dataset_empty")
            self.assertEqual(client.post("/api/recommend", json=query().model_dump(mode="json")).status_code, 503)
            self.assertEqual(client.post("/api/what-if", json=query().model_dump(mode="json")).status_code, 503)
