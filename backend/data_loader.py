from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).parent / "data" / "contractors.csv"


def split_pipe(value):
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


def parse_bool(value):
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "да",
    }


def load_contractors():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = {
        "id",
        "anon_name",
        "categories",
        "city",
        "price_from_kzt",
        "event_formats",
        "languages",
        "max_hours",
        "busy_dates",
        "description",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing CSV columns: {sorted(missing)}"
        )

    contractors = []

    for _, row in df.iterrows():
        contractors.append(
            {
                "id": str(row["id"]).strip(),
                "name": str(row["anon_name"]).strip(),
                "categories": split_pipe(row["categories"]),
                "city": (
                    str(row["city"]).strip()
                    if not pd.isna(row["city"])
                    else None
                ),
                "price": (
                    int(row["price_from_kzt"])
                    if not pd.isna(row["price_from_kzt"])
                    else None
                ),
                "event_formats": split_pipe(
                    row["event_formats"]
                ),
                "languages": split_pipe(
                    row["languages"]
                ),
                "max_hours": (
                    float(row["max_hours"])
                    if not pd.isna(row["max_hours"])
                    else None
                ),
                "busy_dates": split_pipe(
                    row["busy_dates"]
                ),
                "description": (
                    str(row["description"]).strip()
                    if not pd.isna(row["description"])
                    else ""
                ),
                "synthetic": parse_bool(
                    row.get("synthetic", False)
                ),
                "city_imputed": parse_bool(
                    row.get("city_imputed", False)
                ),
                "price_imputed": parse_bool(
                    row.get("price_imputed", False)
                ),
            }
        )

    return contractors
