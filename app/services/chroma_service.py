from functools import lru_cache
from pathlib import Path

import chromadb

from app.models.track import Track

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
CHROMA_COLLECTION_NAME = "spotify_tracks"


@lru_cache
def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


@lru_cache
def get_track_collection():
    client = get_chroma_client()

    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={
            "description": "Spotify tracks semantic search collection",
        },
    )


def describe_energy(value: float) -> str:
    if value >= 0.75:
        return "high energy"
    if value >= 0.45:
        return "medium energy"
    return "low energy"


def describe_danceability(value: float) -> str:
    if value >= 0.75:
        return "very danceable"
    if value >= 0.45:
        return "moderately danceable"
    return "not very danceable"


def describe_valence(value: float) -> str:
    if value >= 0.7:
        return "happy and positive"
    if value >= 0.4:
        return "neutral mood"
    return "sad or melancholic"


def describe_acousticness(value: float) -> str:
    if value >= 0.7:
        return "acoustic sound"
    if value >= 0.4:
        return "some acoustic elements"
    return "mostly electronic or produced sound"


def describe_instrumentalness(value: float) -> str:
    if value >= 0.7:
        return "mostly instrumental with little or no vocals"
    if value >= 0.3:
        return "partly instrumental"
    return "vocal-focused"


def describe_speechiness(value: float) -> str:
    if value >= 0.5:
        return "speech-heavy or rap-like vocals"
    if value >= 0.15:
        return "some spoken or rhythmic vocal elements"
    return "low speechiness"


def describe_liveness(value: float) -> str:
    if value >= 0.7:
        return "strong live performance feeling"
    if value >= 0.3:
        return "some live performance feeling"
    return "studio-like sound"


def describe_tempo(value: float) -> str:
    if value >= 130:
        return "fast tempo"
    if value >= 100:
        return "medium tempo"
    return "slow tempo"


def build_track_document(track: Track) -> str:
    """
    Converts a database Track object into a natural-language document
    that ChromaDB can embed and search semantically.
    """
    explicit_text = "explicit" if track.explicit else "non-explicit"

    return (
        f"Song: {track.track_name}. "
        f"Artists: {track.artists}. "
        f"Album: {track.album_name}. "
        f"Genre: {track.track_genre}. "
        f"Popularity score: {track.popularity}. "
        f"This is a {explicit_text} track. "
        f"The track has {describe_energy(float(track.energy))}, "
        f"is {describe_danceability(float(track.danceability))}, "
        f"has a {describe_valence(float(track.valence))} mood, "
        f"and has {describe_acousticness(float(track.acousticness))}. "
        f"It is {describe_instrumentalness(float(track.instrumentalness))}, "
        f"has {describe_speechiness(float(track.speechiness))}, "
        f"and has {describe_liveness(float(track.liveness))}. "
        f"The tempo is {track.tempo} BPM, which is a {describe_tempo(float(track.tempo))}. "
        f"Audio features: danceability={track.danceability}, "
        f"energy={track.energy}, valence={track.valence}, "
        f"acousticness={track.acousticness}, "
        f"instrumentalness={track.instrumentalness}, "
        f"speechiness={track.speechiness}, "
        f"liveness={track.liveness}, "
        f"tempo={track.tempo}."
    )


def build_track_metadata(track: Track) -> dict:
    """
    Chroma metadata should stay simple.
    PostgreSQL remains the source of truth.
    """
    return {
        "track_db_id": int(track.id),
        "spotify_track_id": str(track.track_id),
        "track_name": str(track.track_name),
        "artists": str(track.artists),
        "album_name": str(track.album_name),
        "track_genre": str(track.track_genre),
        "popularity": int(track.popularity),
        "duration_ms": int(track.duration_ms),
        "explicit": bool(track.explicit),
        "tempo": float(track.tempo),
        "energy": float(track.energy),
        "danceability": float(track.danceability),
        "valence": float(track.valence),
        "acousticness": float(track.acousticness),
        "instrumentalness": float(track.instrumentalness),
        "speechiness": float(track.speechiness),
        "liveness": float(track.liveness),
    }


def upsert_track_to_chroma(track: Track):
    """
    Inserts or updates a single track in ChromaDB.
    """
    collection = get_track_collection()

    collection.upsert(
        ids=[str(track.id)],
        documents=[build_track_document(track)],
        metadatas=[build_track_metadata(track)],
    )
