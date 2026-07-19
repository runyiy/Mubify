from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str


class DatabaseHealthResponse(BaseModel):
    database: str


class ErrorResponse(BaseModel):
    detail: str
