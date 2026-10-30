from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from ..cache.memory import TTLCache
from ..config.settings import Settings
from ..llm.client import LLMClient, LLMUnavailableError
from ..llm.prompt_builder import SYSTEM_PROMPT, build_joke_prompt
from ..models import JokeResponse

logger = logging.getLogger(__name__)


class InvalidLLMResponseError(ValueError):
	pass


class JokeService:
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		self.cache = TTLCache(settings.cache_ttl_seconds)
		self.llm = LLMClient(settings)

	@staticmethod
	def _post_process(content: str, tags: list[str]) -> JokeResponse:
		parts = content.strip().split("|", maxsplit=1)
		if len(parts) != 2:
			raise InvalidLLMResponseError("Ответ LLM имеет неверный формат")
		title, text = (part.strip() for part in parts)
		if not title or not text:
			raise InvalidLLMResponseError("Ответ LLM содержит пустые поля")
		return JokeResponse(
			tags=tags,
			title=title[:100],
			text=text[:5000],
			created_at=datetime.now(timezone.utc),
		)

	def get_joke(self, tags: list[str]) -> JokeResponse | None:
		stage_started = time.perf_counter()
		prompt = build_joke_prompt(tags)
		prompt_duration_ms = int((time.perf_counter() - stage_started) * 1000)
		cache_key = self.cache.make_key(
			tags=tags,
			model=self.settings.llm_model,
			temperature=self.settings.llm_temperature,
			system_prompt=SYSTEM_PROMPT,
		)
		logger.info(
			"Prompt сформирован",
			extra={"event": "prompt_created", "prompt": prompt, "duration_ms": prompt_duration_ms},
		)

		stage_started = time.perf_counter()
		cached = self.cache.get(cache_key)
		cache_duration_ms = int((time.perf_counter() - stage_started) * 1000)
		logger.info(
			"Поиск в кеше завершён",
			extra={"event": "cache_lookup_completed", "cache_key": cache_key, "duration_ms": cache_duration_ms},
		)
		if cached is not None:
			return cached

		stage_started = time.perf_counter()
		try:
			content = self.llm.complete(prompt)
			llm_duration_ms = int((time.perf_counter() - stage_started) * 1000)
			logger.info(
				"Ответ модели получен для обработки",
				extra={"event": "model_response", "response": content, "duration_ms": llm_duration_ms},
			)
			stage_started = time.perf_counter()
			result = self._post_process(content, tags)
			post_process_duration_ms = int((time.perf_counter() - stage_started) * 1000)
			logger.info(
				"Постобработка ответа завершена",
				extra={"event": "response_post_processed", "duration_ms": post_process_duration_ms},
			)
		except (LLMUnavailableError, InvalidLLMResponseError) as exc:
			logger.error("Не удалось сгенерировать анекдот", extra={"event": "joke_generation_failed", "error": str(exc)})
			return None

		self.cache.set(cache_key, result)
		return result
