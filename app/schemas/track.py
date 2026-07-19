from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrackBase(BaseModel):
    track_id: str
    artists: str
    album_name: str
    track_name: str
    popularity: int
    duration_ms: int
    explicit: bool
    danceability: float
    energy: float
    key: int
    loudness: float
    mode: int
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    time_signature: int
    track_genre: str


class TrackCreate(TrackBase):
    pass


class TrackRead(TrackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedTracksResponse(BaseModel):
    items: list[TrackRead]
    total: int
    skip: int
    limit: int
    has_next: bool
