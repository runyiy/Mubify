from scripts.import_spotify_tracks import (
    normalize_row,
    parse_bool,
    parse_float,
    parse_int,
)


def test_parse_bool_true_values():
    assert parse_bool("true") is True
    assert parse_bool("True") is True
    assert parse_bool("1") is True
    assert parse_bool("yes") is True


def test_parse_bool_false_values():
    assert parse_bool("false") is False
    assert parse_bool("False") is False
    assert parse_bool("0") is False
    assert parse_bool("no") is False
    assert parse_bool("") is False
    assert parse_bool(None) is False


def test_parse_int_valid_values():
    assert parse_int("10") == 10
    assert parse_int("10.0") == 10
    assert parse_int(15) == 15


def test_parse_int_invalid_returns_default():
    assert parse_int("not-a-number") == 0
    assert parse_int(None) == 0
    assert parse_int("not-a-number", default=-1) == -1


def test_parse_float_valid_values():
    assert parse_float("0.75") == 0.75
    assert parse_float(1) == 1.0


def test_parse_float_invalid_returns_default():
    assert parse_float("not-a-number") == 0.0
    assert parse_float(None) == 0.0
    assert parse_float("not-a-number", default=-1.5) == -1.5


def test_normalize_row_valid_row():
    row = {
        "track_id": "spotify123",
        "artists": "Test Artist",
        "album_name": "Test Album",
        "track_name": "Test Song",
        "popularity": "80",
        "duration_ms": "210000",
        "explicit": "False",
        "danceability": "0.75",
        "energy": "0.82",
        "key": "5",
        "loudness": "-5.2",
        "mode": "1",
        "speechiness": "0.05",
        "acousticness": "0.20",
        "instrumentalness": "0.00",
        "liveness": "0.12",
        "valence": "0.70",
        "tempo": "120.0",
        "time_signature": "4",
        "track_genre": "pop",
    }

    normalized = normalize_row(row)

    assert normalized is not None
    assert normalized["track_id"] == "spotify123"
    assert normalized["artists"] == "Test Artist"
    assert normalized["album_name"] == "Test Album"
    assert normalized["track_name"] == "Test Song"
    assert normalized["popularity"] == 80
    assert normalized["duration_ms"] == 210000
    assert normalized["explicit"] is False
    assert normalized["danceability"] == 0.75
    assert normalized["energy"] == 0.82
    assert normalized["track_genre"] == "pop"


def test_normalize_row_missing_required_field_returns_none():
    row = {
        "track_id": "",
        "artists": "Test Artist",
        "album_name": "Test Album",
        "track_name": "Test Song",
        "track_genre": "pop",
    }

    normalized = normalize_row(row)

    assert normalized is None
