from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.recommendation_repository import get_similar_tracks
from app.schemas.recommendation import (
    AIRecommendationRead,
    AIRecommendationRequest,
    RecommendationRead,
)
from app.services.ai_recommendation_service import get_ai_recommendations


router = APIRouter()


@router.get("/similar/{track_id}", response_model=list[RecommendationRead])
def read_similar_tracks(
    track_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    same_genre_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    results = get_similar_tracks(
        db=db,
        track_id=track_id,
        limit=limit,
        same_genre_only=same_genre_only,
    )

    if results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    return [
        {
            "track": track,
            "similarity_score": round(score, 4),
        }
        for track, score in results
    ]


@router.post("/ai", response_model=list[AIRecommendationRead])
def read_ai_recommendations(
    request: AIRecommendationRequest,
    db: Session = Depends(get_db),
):
    return get_ai_recommendations(
        db=db,
        prompt=request.prompt,
        limit=request.limit,
    )