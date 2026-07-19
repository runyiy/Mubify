from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.favorite_repository import (
    create_favorite,
    delete_favorite,
    get_favorite,
    get_user_favorites,
)
from app.repositories.track_repository import get_track_by_id
from app.schemas.common import MessageResponse
from app.schemas.favorite import FavoriteRead

router = APIRouter()


@router.get("", response_model=list[FavoriteRead])
def read_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_favorites(
        db=db,
        user_id=current_user.id,
    )


@router.post("/{track_id}", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED)
def add_favorite(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    track = get_track_by_id(
        db=db,
        track_db_id=track_id,
    )

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    existing_favorite = get_favorite(
        db=db,
        user_id=current_user.id,
        track_id=track_id,
    )

    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track already favorited",
        )

    return create_favorite(
        db=db,
        user_id=current_user.id,
        track_id=track_id,
    )


@router.delete("/{track_id}", response_model=MessageResponse)
def remove_favorite(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    favorite = get_favorite(
        db=db,
        user_id=current_user.id,
        track_id=track_id,
    )

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    delete_favorite(
        db=db,
        favorite=favorite,
    )

    return {"message": "Favorite removed successfully"}
