from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TextStyle = Literal["научный", "официально-деловой", "разговорный"]


class StyleReviewRequest(BaseModel):
	text: str = Field(..., min_length=1, max_length=10000)
	style: TextStyle
