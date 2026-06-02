from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spotify dataset fields
    track_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    artists: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    album_name: Mapped[str] = mapped_column(Text, nullable=False)
    track_name: Mapped[str] = mapped_column(Text, index=True, nullable=False)

    popularity: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    explicit: Mapped[bool] = mapped_column(Boolean, nullable=False)

    danceability: Mapped[float] = mapped_column(Float, nullable=False)
    energy: Mapped[float] = mapped_column(Float, nullable=False)
    key: Mapped[int] = mapped_column(Integer, nullable=False)
    loudness: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[int] = mapped_column(Integer, nullable=False)
    speechiness: Mapped[float] = mapped_column(Float, nullable=False)
    acousticness: Mapped[float] = mapped_column(Float, nullable=False)
    instrumentalness: Mapped[float] = mapped_column(Float, nullable=False)
    liveness: Mapped[float] = mapped_column(Float, nullable=False)
    valence: Mapped[float] = mapped_column(Float, nullable=False)
    tempo: Mapped[float] = mapped_column(Float, nullable=False)
    time_signature: Mapped[int] = mapped_column(Integer, nullable=False)

    track_genre: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # App fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    favorites = relationship(
        "Favorite",
        back_populates="track",
        cascade="all, delete-orphan",
    )