from __future__ import annotations

import logging
import time

from ..cache.memory import TTLCache
from ..config.settings import Settings
from ..llm.client import LLMAccessError, LLMNetworkError, LLMResponseError, LLMServiceError, LLMClient
from ..llm.prompt_builder import SYSTEM_PROMPT, build_shopping_list_prompt
from ..models import ShoppingListRequest

logger = logging.getLogger(__name__)

EMPTY_DISH_MESSAGE = "Напишите, что хотите приготовить."
LONG_DISH_MESSAGE = "Слишком длинный текст — сократите или разбейте на части."
ACCESS_ERROR_MESSAGE = "Не настроен доступ к сервису."
SERVICE_ERROR_MESSAGE = "Сервис временно недоступен. Попробуйте позже."
NETWORK_ERROR_MESSAGE = "Не удалось получить ответ. Попробуйте ещё раз."
EMPTY_RESPONSE_MESSAGE = "Пустой ответ модели. Попробуйте переформулировать вопрос."


class UserInputError(ValueError):
	pass


class ShoppingListError(RuntimeError):
	pass


def validate_input(dish: str, people: str, output_format: str) -> ShoppingListRequest:
	normalized_dish = (dish or "").strip()
	if not normalized_dish:
		raise UserInputError(EMPTY_DISH_MESSAGE)
	if len(normalized_dish) > 1000:
		raise UserInputError(LONG_DISH_MESSAGE)
	try:
		return ShoppingListRequest(dish=normalized_dish, people=people, output_format=output_format)
	except ValueError as exc:
		raise UserInputError("Выберите количество человек и формат ответа.") from exc


class ShoppingListService:
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

	def generate(self, request: ShoppingListRequest) -> str:
		prompt_started = time.perf_counter()
		prompt = build_shopping_list_prompt(request.dish, request.people, request.output_format)
		logger.info(
			"Запрос к модели сформирован",
			extra={"event": "prompt_created", "prompt": prompt, "duration_ms": int((time.perf_counter() - prompt_started) * 1000)},
		)
		cache_key = self.cache.make_key(
			dish=request.dish,
			people=request.people,
			output_format=request.output_format,
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
			raise ShoppingListError(ACCESS_ERROR_MESSAGE) from exc
		except LLMServiceError as exc:
			logger.warning("Сервис модели временно недоступен", extra={"event": "llm_service_error", "error": str(exc)})
			raise ShoppingListError(SERVICE_ERROR_MESSAGE) from exc
		except LLMNetworkError as exc:
			logger.warning("Не удалось связаться с моделью", extra={"event": "llm_network_error", "error": str(exc)})
			raise ShoppingListError(NETWORK_ERROR_MESSAGE) from exc
		except LLMResponseError as exc:
			logger.warning("Модель вернула пустой или некорректный ответ", extra={"event": "llm_response_error", "error": str(exc)})
			raise ShoppingListError(EMPTY_RESPONSE_MESSAGE) from exc

		self.cache.set(cache_key, result)
		return result


class ShoppingListHandler:
	def __init__(self, service: ShoppingListService | None = None) -> None:
		self.service = service or ShoppingListService(Settings())

	def handle(self, dish: str, people: str, output_format: str) -> str:
		try:
			request = validate_input(dish, people, output_format)
			return self.service.generate(request)
		except UserInputError as exc:
			return str(exc)
		except ShoppingListError as exc:
			return str(exc)
		except Exception:
			logger.exception("Непредвиденная ошибка обработчика", extra={"event": "handler_error"})
			return "Не удалось обработать запрос. Попробуйте ещё раз."
