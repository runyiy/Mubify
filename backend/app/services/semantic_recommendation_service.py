from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.track import Track
from app.services.chroma_service import get_track_collection


def build_semantic_reason(query: str, track: Track, distance: float) -> str:
    return (
        f"Recommended because it semantically matches the query '{query}'. "
        f"The song is '{track.track_name}' by {track.artists}, "
        f"with genre '{track.track_genre}', energy={track.energy:.2f}, "
        f"danceability={track.danceability:.2f}, and valence={track.valence:.2f}. "
        f"Chroma semantic distance: {distance:.4f}."
    )


def semantic_track_search(
    db: Session,
    query: str,
    limit: int = 20,
    genre: str | None = None,
) -> list[dict]:
    collection = get_track_collection()

    where_filter = None

    if genre:
        where_filter = {"track_genre": genre}

    results = collection.query(
        query_texts=[query],
        n_results=limit,
        where=where_filter,
        include=["metadatas", "documents", "distances"],
    )

    result_ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not result_ids:
        return []

    track_db_ids = [int(track_id) for track_id in result_ids]

    statement = select(Track).where(Track.id.in_(track_db_ids))
    tracks = list(db.scalars(statement).all())

    tracks_by_id = {track.id: track for track in tracks}

    response = []

    for raw_id, distance in zip(result_ids, distances):
        track_id = int(raw_id)
        track = tracks_by_id.get(track_id)

        if not track:
            continue

        response.append(
            {
                "track": track,
                "semantic_distance": round(float(distance), 4),
                "reason": build_semantic_reason(
                    query=query,
                    track=track,
                    distance=float(distance),
                ),
            }
        )

    return response