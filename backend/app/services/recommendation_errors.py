class RecommendationError(Exception):
    """Base class for recommendation service errors."""


class RecommendationDependencyUnavailableError(RecommendationError):
    """Raised when a required dependency such as ChromaDB or PostgreSQL fails."""


class RecommendationIndexNotReadyError(RecommendationError):
    """Raised when the ChromaDB recommendation index is empty or not prepared."""


class RecommendationIndexCorruptError(RecommendationError):
    """Raised when ChromaDB index data cannot be matched to PostgreSQL tracks."""
