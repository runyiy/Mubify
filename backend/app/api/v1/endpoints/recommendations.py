from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.recommendation_repository import get_similar_tracks
from app.schemas.recommendation import (
    HybridRecommendationRead,
    HybridRecommendationRequest,
    RecommendationRead,
    SemanticRecommendationRead,
    SemanticRecommendationRequest,
)
from app.services.hybrid_recommendation_service import hybrid_recommendation_search
from app.services.semantic_recommendation_service import semantic_track_search


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


@router.post("/semantic", response_model=list[SemanticRecommendationRead])
def read_semantic_recommendations(
    request: SemanticRecommendationRequest,
    db: Session = Depends(get_db),
):
    return semantic_track_search(
        db=db,
        query=request.query,
        limit=request.limit,
        genre=request.genre,
    )


@router.post("/hybrid", response_model=list[HybridRecommendationRead])
def read_hybrid_recommendations(
    request: HybridRecommendationRequest,
    db: Session = Depends(get_db),
):
    return hybrid_recommendation_search(
        db=db,
        query=request.query,
        limit=request.limit,
        candidate_pool_size=request.candidate_pool_size,
        genre=request.genre,
    )