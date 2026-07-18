from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.track import TrackRead


class FavoriteRead(BaseModel):
    id: int
    user_id: int
    track_id: int
    created_at: datetime
    track: TrackRead

    model_config = ConfigDict(from_attributes=True)
