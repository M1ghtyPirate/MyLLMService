from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .config.settings import Settings
from .models import JokeResponse
from .services.joke_service import JokeService


@dataclass(slots=True)
class AppState:
	settings: Settings
	joke_service: JokeService

	def __init__(self) -> None:
		self.settings = Settings()
		self.joke_service = JokeService(self.settings)

	@staticmethod
	def normalize_tags(tags: List[str]) -> List[str]:
		normalized_tags = {tag.strip().lower() for tag in tags if tag and tag.strip()}
		return sorted(normalized_tags)

	def get_joke(self, tags: List[str]) -> JokeResponse | None:
		return self.joke_service.get_joke(self.normalize_tags(tags))