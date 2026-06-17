import argparse
import sys
from pathlib import Path

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.models.track import Track
from app.services.chroma_service import (
    build_track_document,
    build_track_metadata,
    get_track_collection,
)


def index_tracks_to_chroma(limit: int | None = None, batch_size: int = 500) -> None:
    db = SessionLocal()
    collection = get_track_collection()

    total_indexed = 0
    last_id = 0

    try:
        while True:
            current_batch_size = batch_size

            if limit is not None:
                remaining = limit - total_indexed

                if remaining <= 0:
                    break

                current_batch_size = min(batch_size, remaining)

            statement = (
                select(Track)
                .where(Track.id > last_id)
                .order_by(Track.id.asc())
                .limit(current_batch_size)
            )

            tracks = list(db.scalars(statement).all())

            if not tracks:
                break

            ids = []
            documents = []
            metadatas = []

            for track in tracks:
                ids.append(str(track.id))
                documents.append(build_track_document(track))
                metadatas.append(build_track_metadata(track))

            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

            total_indexed += len(tracks)
            last_id = tracks[-1].id

            print(f"Indexed {total_indexed} tracks into ChromaDB...")

    finally:
        db.close()

    print("ChromaDB indexing completed.")
    print(f"Total indexed: {total_indexed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=500)

    args = parser.parse_args()

    index_tracks_to_chroma(
        limit=args.limit,
        batch_size=args.batch_size,
    )