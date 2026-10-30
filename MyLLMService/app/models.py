from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JokeRequest(BaseModel):
    """Входная модель для получения анекдота."""

    tags: List[str] = Field(..., min_length=1, max_length=5, description="Темы анекдота")


class JokeResponse(BaseModel):
    """Модель ответа для представления анекдота."""

    tags: List[str] = Field(..., min_length=1, max_length=5, description="Темы анекдота")
    title: str = Field(..., min_length=1, max_length=100, description="Название анекдота")
    text: str = Field(..., min_length=1, max_length=5000, description="Текст анекдота")
    created_at: datetime = Field(..., description="Метка времени генерации анекдота")