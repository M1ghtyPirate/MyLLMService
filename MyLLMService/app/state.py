from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from xml.etree.ElementInclude import include

from pydantic import Tag

from app.config.settings import Settings

from .models import JokeRequest, JokeResponse


@dataclass(slots=True)
class AppState:
    jokes: List[JokeResponse] = field(default_factory=list)
    settings = Settings()

    def normalize_tags(self, tags: List[str]) -> List[str]:
        normalized_tags: List[str] = []
        for tag in tags or []:
            normalized_tag = (tag or "").strip().lower()
            if len(normalized_tag) == 0 or normalized_tag in normalized_tags:
                continue
            normalized_tags.append(normalized_tag)
        normalized_tags.sort()
        return normalized_tags

    def create_joke(self, tags: List[str]) -> JokeResponse:
        joke = JokeResponse(
            tags=tags,
            title="test",
            text= f'test text',
            created_at=datetime.now(timezone.utc),
        )
        self.jokes.append(joke)
        return joke

    def get_joke(self, tags: List[str]) -> JokeResponse | None:
        normalized_tags = self.normalize_tags(tags)
        
        for joke in self.jokes:
            if len(joke.tags) != len(normalized_tags):
                continue
            for i, tag in enumerate(joke.tags):
                if tag != normalized_tags[i]:
                    break
            else:
                return joke
        return self.create_joke(normalized_tags)