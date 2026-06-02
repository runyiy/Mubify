from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.track import Track


def get_similar_tracks(
    db: Session,
    track_id: int,
    limit: int = 20,
    same_genre_only: bool = False,
) -> list[tuple[Track, float]] | None:
    target_track = db.get(Track, track_id)

    if target_track is None:
        return None

    genre_penalty = case(
        (Track.track_genre == target_track.track_genre, 0.0),
        else_=0.5,
    )

    similarity_distance = (
        func.abs(Track.danceability - target_track.danceability)
        + func.abs(Track.energy - target_track.energy)
        + func.abs(Track.valence - target_track.valence)
        + func.abs(Track.acousticness - target_track.acousticness)
        + func.abs(Track.instrumentalness - target_track.instrumentalness)
        + func.abs(Track.speechiness - target_track.speechiness)
        + func.abs(Track.liveness - target_track.liveness)
        + func.abs(Track.tempo - target_track.tempo) / 200.0
        + func.abs(Track.popularity - target_track.popularity) / 100.0
    )

    if not same_genre_only:
        similarity_distance = similarity_distance + genre_penalty

    statement = select(
        Track,
        similarity_distance.label("similarity_score"),
    ).where(
        Track.id != target_track.id,
    )

    if same_genre_only:
        statement = statement.where(
            Track.track_genre == target_track.track_genre,
        )

    statement = statement.order_by(
        similarity_distance.asc(),
        Track.popularity.desc(),
    ).limit(limit)

    rows = db.execute(statement).all()

    return [(track, float(score)) for track, score in rows]