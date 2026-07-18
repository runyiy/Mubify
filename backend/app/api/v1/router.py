from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    favorites,
    health,
    recommendations,
    tracks,
    users,
)


api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["recommendations"],
)
