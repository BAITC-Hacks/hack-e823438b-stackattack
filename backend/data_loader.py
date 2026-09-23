"""Load contractor facts without filling missing values or ranking profiles."""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Tuple

from .models import Contractor


DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "data" / "contractors.csv"
REQUIRED_COLUMNS = (
    "id", "anon_name", "categories", "city", "city_imputed", "synthetic",
    "price_from_kzt", "price_imputed", "event_formats", "languages",
    "max_hours", "busy_dates", "description",
)


class DatasetError(ValueError):
    """The CSV cannot be interpreted safely."""


def _values(value: str) -> Tuple[str, ...]:
    # Preserve source order and spelling, removing whitespace and duplicates.
    return tuple(dict.fromkeys(part.strip() for part in value.split("|") if part.strip()))


def _flag(value: str) -> Optional[bool]:
    if not value:
        return None
    normalized = value.casefold()
    if normalized in ("true", "1"):
        return True
    if normalized in ("false", "0"):
        return False
    raise ValueError("ожидалось true/false или 1/0")


def _number(value: str) -> Optional[Decimal]:
    if not value:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("ожидалось число") from exc
    if not number.is_finite() or number < 0:
        raise ValueError("ожидалось конечное неотрицательное число")
    return number


def _dates(value: str) -> Tuple[date, ...]:
    result = []
    for item in _values(value):
        parsed = date.fromisoformat(item)
        if parsed.isoformat() != item:
            raise ValueError("ожидалась дата YYYY-MM-DD")
        result.append(parsed)
    return tuple(result)


def load_contractors(path: Optional[Path] = None) -> Tuple[Contractor, ...]:
    """Read UTF-8 comma-separated CSV; fail on malformed facts and duplicate IDs.

    Empty numeric/flag cells become None, empty lists become (). No missing
    facts are inferred. An empty busy_dates list is not a confirmed booking
    guarantee. Boolean encodings accepted: true/false (any case) and 1/0.
    The number of profiles is deliberately not hardcoded.
    """
    source = Path(path) if path is not None else DEFAULT_DATASET_PATH
    if not source.is_file():
        raise FileNotFoundError(f"CSV не найден: {source}. Добавьте исходный датасет.")

    converters = {
        "categories": _values,
        "event_formats": _values,
        "languages": _values,
        "busy_dates": _dates,
        "price_from_kzt": _number,
        "max_hours": _number,
        "city_imputed": _flag,
        "price_imputed": _flag,
        "synthetic": _flag,
    }
    contractors = []
    seen_ids = set()
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        try:
            if reader.fieldnames is None:
                raise DatasetError("CSV пуст: отсутствует заголовок")
            headers = [name.strip() for name in reader.fieldnames]
            if len(set(headers)) != len(headers):
                raise DatasetError("В CSV повторяются названия колонок")
            reader.fieldnames = headers
            missing = set(REQUIRED_COLUMNS) - set(headers)
            if missing:
                raise DatasetError(f"Отсутствуют колонки: {', '.join(sorted(missing))}")
            for row in reader:
                location = f"CSV, строка {reader.line_num}"
                if None in row or any(value is None for value in row.values()):
                    raise DatasetError(f"{location}: число значений не совпадает с заголовком")
                facts = {key: row[key].strip() for key in REQUIRED_COLUMNS}
                for key in ("id", "anon_name"):
                    if not facts[key]:
                        raise DatasetError(f"{location}, {key}: обязательное значение пусто")
                if facts["id"] in seen_ids:
                    raise DatasetError(f"{location}: повторяется id {facts['id']}")
                seen_ids.add(facts["id"])
                for key, convert in converters.items():
                    try:
                        facts[key] = convert(facts[key])
                    except ValueError as exc:
                        raise DatasetError(f"{location}, {key}: {exc}") from exc
                contractors.append(Contractor(**facts))
        except csv.Error as exc:
            raise DatasetError(f"Некорректный CSV, строка {reader.line_num}: {exc}") from exc
    return tuple(contractors)
