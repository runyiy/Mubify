from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.track_repository import (
    get_track_by_id,
    get_track_by_spotify_id,
    get_tracks,
)
from app.schemas.track import TrackRead

router = APIRouter()


@router.get("", response_model=list[TrackRead])
def read_tracks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    genre: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return get_tracks(
        db=db,
        skip=skip,
        limit=limit,
        genre=genre,
        search=search,
    )


@router.get("/spotify/{spotify_track_id}", response_model=TrackRead)
def read_track_by_spotify_id(
    spotify_track_id: str,
    db: Session = Depends(get_db),
):
    track = get_track_by_spotify_id(db=db, spotify_track_id=spotify_track_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return track


@router.get("/{track_db_id}", response_model=TrackRead)
def read_track(
    track_db_id: int,
    db: Session = Depends(get_db),
):
    track = get_track_by_id(db=db, track_db_id=track_db_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return track