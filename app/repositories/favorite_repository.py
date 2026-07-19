from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.favorite import Favorite


def get_favorite(
    db: Session,
    user_id: int,
    track_id: int,
) -> Favorite | None:
    statement = (
        select(Favorite)
        .options(selectinload(Favorite.track))
        .where(
            Favorite.user_id == user_id,
            Favorite.track_id == track_id,
        )
    )

    return db.scalar(statement)


def get_user_favorites(
    db: Session,
    user_id: int,
) -> list[Favorite]:
    statement = (
        select(Favorite)
        .options(selectinload(Favorite.track))
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
    )

    return list(db.scalars(statement).all())


def create_favorite(
    db: Session,
    user_id: int,
    track_id: int,
) -> Favorite:
    favorite = Favorite(
        user_id=user_id,
        track_id=track_id,
    )

    db.add(favorite)
    db.commit()

    return get_favorite(
        db=db,
        user_id=user_id,
        track_id=track_id,
    )


def delete_favorite(
    db: Session,
    favorite: Favorite,
) -> None:
    db.delete(favorite)
    db.commit()
