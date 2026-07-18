from dataclasses import dataclass

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


@dataclass
class CandidateTrack:
    track: Track
    semantic_distance: float
    audio_distance: float = 0.0
    final_score: float = 0.0


AUDIO_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "liveness",
]


def min_max_normalize(values: list[float]) -> list[float]:
    if not values:
        return []

    min_value = min(values)
    max_value = max(values)

    if max_value == min_value:
        return [0.0 for _ in values]

    return [(value - min_value) / (max_value - min_value) for value in values]


def get_chroma_candidates(
    query: str,
    candidate_pool_size: int,
    genre: str | None = None,
) -> tuple[list[int], list[float]]:
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
            n_results=candidate_pool_size,
            where=where_filter,
            include=["metadatas", "distances"],
        )
    except Exception as exc:
        raise RecommendationDependencyUnavailableError(CHROMA_UNAVAILABLE_MESSAGE) from exc

    raw_ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    try:
        track_ids = [int(raw_id) for raw_id in raw_ids]
    except (TypeError, ValueError) as exc:
        raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE) from exc

    try:
        semantic_distances = [float(distance) for distance in distances]
    except (TypeError, ValueError) as exc:
        raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE) from exc

    return track_ids, semantic_distances


def fetch_tracks_by_ids(
    db: Session,
    track_ids: list[int],
) -> dict[int, Track]:
    if not track_ids:
        return {}

    statement = select(Track).where(Track.id.in_(track_ids))

    try:
        tracks = list(db.scalars(statement).all())
    except SQLAlchemyError as exc:
        raise RecommendationDependencyUnavailableError(DATABASE_UNAVAILABLE_MESSAGE) from exc

    return {track.id: track for track in tracks}


def build_candidates(
    db: Session,
    track_ids: list[int],
    semantic_distances: list[float],
) -> list[CandidateTrack]:
    tracks_by_id = fetch_tracks_by_ids(db=db, track_ids=track_ids)

    candidates = []

    for track_id, semantic_distance in zip(track_ids, semantic_distances):
        track = tracks_by_id.get(track_id)

        if not track:
            continue

        candidates.append(
            CandidateTrack(
                track=track,
                semantic_distance=semantic_distance,
            )
        )

    if track_ids and not candidates:
        raise RecommendationIndexCorruptError(INDEX_CORRUPT_MESSAGE)

    return candidates


def infer_target_audio_profile(
    candidates: list[CandidateTrack],
    top_k: int = 20,
) -> dict[str, float]:
    """
    Instead of using keyword rules, infer the desired audio profile
    from the top semantic matches returned by ChromaDB.

    This makes the system more AI-like:
    semantic retrieval decides the rough meaning,
    audio-feature reranking makes the final recommendation consistent.
    """
    if not candidates:
        return {}

    top_candidates = candidates[:top_k]

    weighted_sum = {}
    total_weight = 0.0

    for rank, candidate in enumerate(top_candidates):
        weight = 1.0 / (rank + 1)
        total_weight += weight

        track = candidate.track

        for feature in AUDIO_FEATURES:
            weighted_sum[feature] = weighted_sum.get(feature, 0.0) + (
                getattr(track, feature) * weight
            )

        weighted_sum["tempo"] = weighted_sum.get("tempo", 0.0) + (track.tempo * weight)

    target_profile = {feature: weighted_sum[feature] / total_weight for feature in weighted_sum}

    return target_profile


def calculate_audio_distance(
    track: Track,
    target_profile: dict[str, float],
) -> float:
    if not target_profile:
        return 0.0

    distance = 0.0

    for feature in AUDIO_FEATURES:
        distance += abs(getattr(track, feature) - target_profile[feature])

    distance += abs(track.tempo - target_profile["tempo"]) / 200.0

    return float(distance)


def build_hybrid_reason(
    query: str,
    candidate: CandidateTrack,
    target_profile: dict[str, float],
) -> str:
    track = candidate.track

    return (
        f"Recommended for query '{query}' because it was semantically retrieved "
        f"by ChromaDB and then reranked using audio features. "
        f"The track has genre='{track.track_genre}', "
        f"energy={track.energy:.2f}, danceability={track.danceability:.2f}, "
        f"valence={track.valence:.2f}, and tempo={track.tempo:.1f}. "
        f"Hybrid score={candidate.final_score:.4f}."
    )


def hybrid_recommendation_search(
    db: Session,
    query: str,
    limit: int = 20,
    candidate_pool_size: int = 100,
    genre: str | None = None,
) -> list[dict]:
    track_ids, semantic_distances = get_chroma_candidates(
        query=query,
        candidate_pool_size=candidate_pool_size,
        genre=genre,
    )

    candidates = build_candidates(
        db=db,
        track_ids=track_ids,
        semantic_distances=semantic_distances,
    )

    if not candidates:
        return []

    target_profile = infer_target_audio_profile(candidates)

    for candidate in candidates:
        candidate.audio_distance = calculate_audio_distance(
            track=candidate.track,
            target_profile=target_profile,
        )

    normalized_semantic_distances = min_max_normalize(
        [candidate.semantic_distance for candidate in candidates]
    )
    normalized_audio_distances = min_max_normalize(
        [candidate.audio_distance for candidate in candidates]
    )

    for index, candidate in enumerate(candidates):
        popularity_penalty = 1.0 - (candidate.track.popularity / 100.0)

        candidate.final_score = (
            0.55 * normalized_semantic_distances[index]
            + 0.35 * normalized_audio_distances[index]
            + 0.10 * popularity_penalty
        )

    candidates.sort(key=lambda candidate: candidate.final_score)

    top_candidates = candidates[:limit]

    return [
        {
            "track": candidate.track,
            "final_score": round(candidate.final_score, 4),
            "semantic_distance": round(candidate.semantic_distance, 4),
            "audio_distance": round(candidate.audio_distance, 4),
            "reason": build_hybrid_reason(
                query=query,
                candidate=candidate,
                target_profile=target_profile,
            ),
        }
        for candidate in top_candidates
    ]
