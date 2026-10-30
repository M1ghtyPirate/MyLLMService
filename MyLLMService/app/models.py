from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PeopleCount = Literal["1", "2", "4", "6"]
OutputFormat = Literal["Список продуктов", "Список + шаги"]


class ShoppingListRequest(BaseModel):
	dish: str = Field(..., min_length=1, max_length=1000)
	people: PeopleCount
	output_format: OutputFormat