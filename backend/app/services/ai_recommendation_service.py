from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.track import Track


def parse_prompt_to_preferences(prompt: str) -> dict:
    """
    Temporary AI-like intent parser.

    Later this function can be replaced by a real LLM or ChromaDB/RAG pipeline.
    For now, we use keyword-based parsing to convert natural language into
    music feature preferences.
    """
    text = prompt.lower()

    preferences = {
        "genre": None,
        "danceability": 0.5,
        "energy": 0.5,
        "valence": 0.5,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "speechiness": 0.05,
        "liveness": 0.1,
        "tempo": 120.0,
        "popularity": 70,
        "tags": [],
    }

    genre_keywords = {
        "pop": "pop",
        "rock": "rock",
        "hip hop": "hip-hop",
        "hip-hop": "hip-hop",
        "rap": "hip-hop",
        "jazz": "jazz",
        "classical": "classical",
        "country": "country",
        "edm": "edm",
        "electronic": "electronic",
        "acoustic": "acoustic",
        "metal": "metal",
        "r&b": "r-n-b",
        "rnb": "r-n-b",
        "latin": "latin",
    }

    for keyword, genre in genre_keywords.items():
        if keyword in text:
            preferences["genre"] = genre
            preferences["tags"].append(f"{genre} genre")
            break

    if any(word in text for word in ["workout", "gym", "running", "run", "exercise"]):
        preferences["energy"] = 0.9
        preferences["danceability"] = 0.8
        preferences["valence"] = 0.7
        preferences["tempo"] = 135.0
        preferences["tags"].append("workout mood")

    if any(word in text for word in ["party", "dance", "club"]):
        preferences["energy"] = 0.85
        preferences["danceability"] = 0.9
        preferences["valence"] = 0.8
        preferences["tempo"] = 125.0
        preferences["tags"].append("party mood")

    if any(word in text for word in ["sad", "depressed", "heartbreak", "lonely"]):
        preferences["energy"] = 0.35
        preferences["valence"] = 0.2
        preferences["tempo"] = 85.0
        preferences["tags"].append("sad mood")

    if any(word in text for word in ["happy", "cheerful", "positive", "upbeat"]):
        preferences["energy"] = 0.75
        preferences["valence"] = 0.9
        preferences["danceability"] = 0.75
        preferences["tags"].append("happy mood")

    if any(word in text for word in ["chill", "relax", "calm", "sleep", "peaceful"]):
        preferences["energy"] = 0.25
        preferences["danceability"] = 0.35
        preferences["valence"] = 0.45
        preferences["acousticness"] = 0.65
        preferences["tempo"] = 80.0
        preferences["tags"].append("chill mood")

    if any(word in text for word in ["study", "focus", "coding", "work"]):
        preferences["energy"] = 0.35
        preferences["speechiness"] = 0.02
        preferences["instrumentalness"] = 0.4
        preferences["tempo"] = 95.0
        preferences["tags"].append("focus mood")

    if any(word in text for word in ["acoustic", "guitar", "unplugged"]):
        preferences["acousticness"] = 0.85
        preferences["energy"] = min(preferences["energy"], 0.45)
        preferences["tags"].append("acoustic sound")

    if any(word in text for word in ["instrumental", "no lyrics", "without lyrics"]):
        preferences["instrumentalness"] = 0.75
        preferences["speechiness"] = 0.01
        preferences["tags"].append("instrumental sound")

    if not preferences["tags"]:
        preferences["tags"].append("general music preference")

    return preferences


def build_recommendation_reason(track: Track, preferences: dict) -> str:
    tags = ", ".join(preferences["tags"])

    return (
        f"Recommended because it matches your request for {tags}. "
        f"The track has energy={track.energy:.2f}, "
        f"danceability={track.danceability:.2f}, "
        f"valence={track.valence:.2f}, "
        f"tempo={track.tempo:.1f}, "
        f"and genre='{track.track_genre}'."
    )


def get_ai_recommendations(
    db: Session,
    prompt: str,
    limit: int = 20,
) -> list[dict]:
    preferences = parse_prompt_to_preferences(prompt)

    similarity_distance = (
        func.abs(Track.danceability - preferences["danceability"])
        + func.abs(Track.energy - preferences["energy"])
        + func.abs(Track.valence - preferences["valence"])
        + func.abs(Track.acousticness - preferences["acousticness"])
        + func.abs(Track.instrumentalness - preferences["instrumentalness"])
        + func.abs(Track.speechiness - preferences["speechiness"])
        + func.abs(Track.liveness - preferences["liveness"])
        + func.abs(Track.tempo - preferences["tempo"]) / 200.0
        + func.abs(Track.popularity - preferences["popularity"]) / 100.0
    )

    statement = select(
        Track,
        similarity_distance.label("similarity_score"),
    )

    if preferences["genre"]:
        statement = statement.where(Track.track_genre == preferences["genre"])

    statement = statement.order_by(
        similarity_distance.asc(),
        Track.popularity.desc(),
    ).limit(limit)

    rows = db.execute(statement).all()

    return [
        {
            "track": track,
            "similarity_score": round(float(score), 4),
            "reason": build_recommendation_reason(track, preferences),
        }
        for track, score in rows
    ]