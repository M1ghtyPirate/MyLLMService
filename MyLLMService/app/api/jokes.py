from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from ..models import JokeRequest, JokeResponse
from ..state import AppState

router = APIRouter(prefix="/jokes", tags=["jokes"])


def _state(request: Request) -> AppState:
    return request.app.state.state


@router.get(
    "/get_joke/",
    response_model=JokeResponse,
    responses={
        200: {
            "tags": "Анекдот получен",
            "content": {
                "application/json": {
                    "example": {
                        "tags": ["Пример темы 1", "Пример темы 2", "Пример темы 3"],
                        "title": "Пример темы анедота",
                        "text": "Пример анедота",
                        "created_at": "2024-01-01T12:00:00"
                    }
                }
            },
        },
        503: {
            "description": "Эндпойнт LLM недоступен",
            "content": {
                "application/json": {
                    "example": {"detail": "Эндпойнт LLM недоступен"}
                }
            },
        },
        422: {
            "description": "Ошибка валидации параметров запроса или пути",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка валидации параметров запроса или пути"}
                }
            },
        },
    },
)
async def get_joke(joke_request: Annotated[JokeRequest, Query()], request: Request) -> JokeResponse:
    """Получить анекдот на темы.

    request: объект запроса, используется для доступа к приложению и состоянию.
    Возвращает JokeResponse при успешном нахождении записи.
    """

    state = _state(request)
    if joke_request is None:
        raise HTTPException(
            status_code=422,
            detail="Empty request",
        )
    normalized_tags = state.normalize_tags(joke_request.tags)
    if len(normalized_tags) == 0:
        raise HTTPException(
            status_code=422,
            detail="Empty tags collection in request",
        )
    joke = state.get_joke(normalized_tags)
    if joke is None:
        raise HTTPException(
            status_code=503,
            detail="Эндпойнт LLM недоступен",
        )
    return joke