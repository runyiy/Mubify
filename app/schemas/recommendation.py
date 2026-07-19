from pydantic import BaseModel, ConfigDict, Field

from app.schemas.track import TrackRead


class RecommendationRead(BaseModel):
    track: TrackRead
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class SemanticRecommendationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=50)
    genre: str | None = None


class SemanticRecommendationRead(BaseModel):
    track: TrackRead
    semantic_distance: float
    reason: str

    model_config = ConfigDict(from_attributes=True)


class HybridRecommendationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=50)
    candidate_pool_size: int = Field(default=100, ge=20, le=500)
    genre: str | None = None


class HybridRecommendationRead(BaseModel):
    track: TrackRead
    final_score: float
    semantic_distance: float
    audio_distance: float
    reason: str

    model_config = ConfigDict(from_attributes=True)
