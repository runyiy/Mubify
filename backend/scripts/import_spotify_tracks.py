import csv
import sys
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.track import Track


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = BASE_DIR / "data" / "dataset.csv"

BATCH_SIZE = 1000


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_row(row: dict) -> dict | None:
    track_id = row.get("track_id")
    artists = row.get("artists")
    album_name = row.get("album_name")
    track_name = row.get("track_name")
    track_genre = row.get("track_genre")

    if not track_id or not artists or not album_name or not track_name or not track_genre:
        return None

    return {
        "track_id": track_id.strip(),
        "artists": artists.strip(),
        "album_name": album_name.strip(),
        "track_name": track_name.strip(),
        "popularity": parse_int(row.get("popularity")),
        "duration_ms": parse_int(row.get("duration_ms")),
        "explicit": parse_bool(row.get("explicit")),
        "danceability": parse_float(row.get("danceability")),
        "energy": parse_float(row.get("energy")),
        "key": parse_int(row.get("key")),
        "loudness": parse_float(row.get("loudness")),
        "mode": parse_int(row.get("mode")),
        "speechiness": parse_float(row.get("speechiness")),
        "acousticness": parse_float(row.get("acousticness")),
        "instrumentalness": parse_float(row.get("instrumentalness")),
        "liveness": parse_float(row.get("liveness")),
        "valence": parse_float(row.get("valence")),
        "tempo": parse_float(row.get("tempo")),
        "time_signature": parse_int(row.get("time_signature")),
        "track_genre": track_genre.strip(),
    }


def insert_batch(db, batch: list[dict]) -> int:
    if not batch:
        return 0

    statement = insert(Track).values(batch)

    statement = statement.on_conflict_do_nothing(index_elements=["track_id"])

    result = db.execute(statement)
    db.commit()

    return result.rowcount or 0


def import_tracks(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    db = SessionLocal()

    total_rows = 0
    valid_rows = 0
    inserted_rows = 0
    skipped_rows = 0

    batch = []

    try:
        with csv_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            print(f"Reading CSV from: {csv_path}")
            print(f"CSV columns: {reader.fieldnames}")

            for row in reader:
                total_rows += 1

                normalized = normalize_row(row)

                if normalized is None:
                    skipped_rows += 1
                    continue

                valid_rows += 1
                batch.append(normalized)

                if len(batch) >= BATCH_SIZE:
                    inserted = insert_batch(db, batch)
                    inserted_rows += inserted
                    print(f"Processed {total_rows} rows | Inserted {inserted_rows} rows")
                    batch.clear()

            if batch:
                inserted = insert_batch(db, batch)
                inserted_rows += inserted
                batch.clear()

    finally:
        db.close()

    print("Import completed.")
    print(f"Total CSV rows: {total_rows}")
    print(f"Valid rows: {valid_rows}")
    print(f"Inserted rows: {inserted_rows}")
    print(f"Skipped invalid rows: {skipped_rows}")
    print(f"Skipped duplicates: {valid_rows - inserted_rows}")


if __name__ == "__main__":
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    import_tracks(csv_path)
