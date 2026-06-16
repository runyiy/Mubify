from pydantic import BaseModel, ConfigDict, Field

from app.schemas.track import TrackRead


class RecommendationRead(BaseModel):
    track: TrackRead
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class AIRecommendationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class AIRecommendationRead(BaseModel):
    track: TrackRead
    similarity_score: float
    reason: str

    model_config = ConfigDict(from_attributes=True)