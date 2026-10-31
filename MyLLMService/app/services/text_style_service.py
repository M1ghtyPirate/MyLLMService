from __future__ import annotations

import logging
import time

from ..cache.memory import TTLCache
from ..config.settings import Settings
from ..llm.client import (
	LLMAccessError,
	LLMClient,
	LLMNetworkError,
	LLMResponseError,
	LLMServiceError,
)
from ..llm.prompt_builder import SYSTEM_PROMPT, build_style_review_prompt
from ..models import StyleReviewRequest

logger = logging.getLogger(__name__)

EMPTY_TEXT_MESSAGE = "Напишите текст для проверки."
LONG_TEXT_MESSAGE = "Слишком длинный текст — сократите или разбейте на части."
INVALID_STYLE_MESSAGE = "Выберите стиль текста."
ACCESS_ERROR_MESSAGE = "Не настроен доступ к сервису."
SERVICE_ERROR_MESSAGE = "Сервис временно недоступен. Попробуйте позже."
NETWORK_ERROR_MESSAGE = "Не удалось получить ответ. Попробуйте ещё раз."
EMPTY_RESPONSE_MESSAGE = "Пустой ответ модели. Попробуйте проверить другой текст."


class UserInputError(ValueError):
	pass


class StyleReviewError(RuntimeError):
	pass


def validate_input(text: str, style: str) -> StyleReviewRequest:
	normalized_text = (text or "").strip()
	if not normalized_text:
		raise UserInputError(EMPTY_TEXT_MESSAGE)
	if len(normalized_text) > 10000:
		raise UserInputError(LONG_TEXT_MESSAGE)
	try:
		return StyleReviewRequest(text=normalized_text, style=style)
	except ValueError as exc:
		raise UserInputError(INVALID_STYLE_MESSAGE) from exc


class TextStyleService:
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		self.cache = TTLCache(settings.cache_ttl_seconds)
		self.llm = LLMClient(settings)

	@staticmethod
	def _post_process(content: str) -> str:
		result = content.strip()
		if not result:
			raise LLMResponseError(EMPTY_RESPONSE_MESSAGE)
		return result

	def review(self, request: StyleReviewRequest) -> str:
		prompt_started = time.perf_counter()
		prompt = build_style_review_prompt(request.text, request.style)
		logger.info(
			"Промпт для проверки стиля сформирован",
			extra={"event": "prompt_created", "prompt": prompt, "duration_ms": int((time.perf_counter() - prompt_started) * 1000)},
		)
		cache_key = self.cache.make_key(
			text=request.text,
			style=request.style,
			model=self.settings.llm_model,
			temperature=self.settings.llm_temperature,
			system_prompt=SYSTEM_PROMPT,
		)
		cached = self.cache.get(cache_key)
		if cached is not None:
			return cached

		try:
			llm_started = time.perf_counter()
			content = self.llm.complete(prompt)
			logger.info(
				"Ответ модели получен",
				extra={"event": "model_response", "duration_ms": int((time.perf_counter() - llm_started) * 1000)},
			)
			result = self._post_process(content)
		except LLMAccessError as exc:
			logger.warning("Не настроен доступ к сервису", extra={"event": "llm_access_error", "error": str(exc)})
			raise StyleReviewError(ACCESS_ERROR_MESSAGE) from exc
		except LLMServiceError as exc:
			logger.warning("Сервис модели временно недоступен", extra={"event": "llm_service_error", "error": str(exc)})
			raise StyleReviewError(SERVICE_ERROR_MESSAGE) from exc
		except LLMNetworkError as exc:
			logger.warning("Не удалось связаться с моделью", extra={"event": "llm_network_error", "error": str(exc)})
			raise StyleReviewError(NETWORK_ERROR_MESSAGE) from exc
		except LLMResponseError as exc:
			logger.warning("Модель вернула пустой или некорректный ответ", extra={"event": "llm_response_error", "error": str(exc)})
			raise StyleReviewError(EMPTY_RESPONSE_MESSAGE) from exc

		self.cache.set(cache_key, result)
		return result


class StyleReviewHandler:
	def __init__(self, service: TextStyleService | None = None) -> None:
		self.service = service or TextStyleService(Settings())

	def handle(self, text: str, style: str) -> str:
		try:
			request = validate_input(text, style)
			return self.service.review(request)
		except UserInputError as exc:
			return str(exc)
		except StyleReviewError as exc:
			return str(exc)
		except Exception:
			logger.exception("Непредвиденная ошибка обработчика", extra={"event": "handler_error"})
			return "Не удалось проверить текст. Попробуйте ещё раз."
