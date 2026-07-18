from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.track import Track
from app.services.chroma_service import get_track_collection
from app.services.recommendation_errors import (
    RecommendationDependencyUnavailableError,
    RecommendationIndexCorruptError,
    RecommendationIndexNotReadyError,
)


INDEX_NOT_READY_MESSAGE = (
    "Recommendation index is not ready. Import tracks and run Chroma indexing first."
)
CHROMA_UNAVAILABLE_MESSAGE = "ChromaDB recommendation index is unavailable."
DATABASE_UNAVAILABLE_MESSAGE = "Track database is unavailable."
INDEX_CORRUPT_MESSAGE = "Recommendation index is inconsistent with the track database."


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
    try:
        collection = get_track_collection()
        index_count = collection.count()
    except Exception as exc:
        raise RecommendationDependencyUnavailableError(CHROMA_UNAVAILABLE_MESSAGE) from exc

    if index_count == 0:
        raise RecommendationIndexNotReadyError(INDEX_NOT_READY_MESSAGE)

    where_filter = None

    if genre:
        where_filter = {"track_genre": genre}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["metadatas", "documents", "distances"],
        )
    except Exception as exc:
        raise RecommendationDependencyUnavailableError(CHROMA_UNAVAILABLE_MESSAGE) from exc

    result_ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not result_ids:
        return []

    try:
        track_db_ids = [int(track_id) for track_id in result_ids]
    except (TypeError, ValueError) as exc:
        raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE) from exc

    statement = select(Track).where(Track.id.in_(track_db_ids))

    try:
        tracks = list(db.scalars(statement).all())
    except SQLAlchemyError as exc:
        raise RecommendationDependencyUnavailableError(DATABASE_UNAVAILABLE_MESSAGE) from exc

    tracks_by_id = {track.id: track for track in tracks}

    response = []

    for raw_id, distance in zip(result_ids, distances):
        track_id = int(raw_id)
        track = tracks_by_id.get(track_id)

        if not track:
            continue

        try:
            semantic_distance = float(distance)
        except (TypeError, ValueError) as exc:
            raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE) from exc

        response.append(
            {
                "track": track,
                "semantic_distance": round(semantic_distance, 4),
                "reason": build_semantic_reason(
                    query=query,
                    track=track,
                    distance=semantic_distance,
                ),
            }
        )

    if not response:
        raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE)

    return response
