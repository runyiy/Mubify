from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.track import Track


def get_track_by_id(db: Session, track_db_id: int) -> Track | None:
    statement = select(Track).where(Track.id == track_db_id)
    return db.scalar(statement)


def get_track_by_spotify_id(db: Session, spotify_track_id: str) -> Track | None:
    statement = select(Track).where(Track.track_id == spotify_track_id)
    return db.scalar(statement)


def get_tracks(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    genre: str | None = None,
    search: str | None = None,
) -> list[Track]:
    statement = select(Track)

    if genre:
        statement = statement.where(Track.track_genre == genre)

    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Track.track_name.ilike(search_pattern),
                Track.artists.ilike(search_pattern),
                Track.album_name.ilike(search_pattern),
            )
        )

    statement = (
        statement
        .order_by(Track.popularity.desc(), Track.id.asc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())