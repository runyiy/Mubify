from pydantic import BaseModel, ConfigDict

from app.schemas.track import TrackRead


class RecommendationRead(BaseModel):
    track: TrackRead
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)