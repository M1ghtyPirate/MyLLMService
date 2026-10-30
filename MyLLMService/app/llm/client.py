from __future__ import annotations

import logging
import time
from typing import Any

from gigachat import GigaChat
import requests

from ..config.settings import Settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
	pass


class LLMAccessError(LLMError):
	pass


class LLMServiceError(LLMError):
	pass


class LLMNetworkError(LLMError):
	pass


class LLMResponseError(LLMError):
	pass


class LLMClient:
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		self._access_token: str | None = None

	def _get_access_token(self) -> str:
		if self._access_token:
			return self._access_token
		auth_client = GigaChat(
			base_url=self.settings.api_access_token_endpoint,
			credentials=self.settings.authorization_key,
			timeout=self.settings.llm_timeout,
			verify_ssl_certs=False,
			max_retries=0,
		)
		self._access_token = auth_client.get_token().access_token
		return self._access_token

	def complete(self, prompt: str) -> str:
		last_error: Exception | None = None
		for attempt in range(1, self.settings.llm_max_retries + 1):
			try:
				client = GigaChat(
					base_url=self.settings.api_endpoint,
					model=self.settings.llm_model,
					access_token=self._get_access_token(),
					timeout=self.settings.llm_timeout,
					verify_ssl_certs=False,
					max_retries=0,
				)
				response: Any = client.chat(prompt)
				content = response.choices[0].message.content
				if not isinstance(content, str) or not content.strip():
					raise LLMResponseError("Модель вернула пустой ответ")
				logger.info("Ответ от модели получен", extra={"event": "llm_response_received", "attempt": attempt})
				return content
			except (TimeoutError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
				last_error = exc
				logger.warning(
					"Ошибка вызова LLM",
					extra={"event": "llm_call_failed", "attempt": attempt, "error": str(exc)},
				)
				if attempt < self.settings.llm_max_retries:
					time.sleep(self.settings.llm_retry_backoff * (2 ** (attempt - 1)))
			except requests.exceptions.RequestException as exc:
				last_error = exc
				status_code = getattr(getattr(exc, "response", None), "status_code", 0)
				logger.error("Ошибка вызова LLM", extra={"event": "llm_call_failed", "attempt": attempt, "error": str(exc)})
				if status_code < 500:
					raise LLMAccessError("Ошибка доступа к сервису модели") from exc
				if attempt >= self.settings.llm_max_retries:
					raise LLMServiceError("Сервис модели недоступен") from exc
				time.sleep(self.settings.llm_retry_backoff * (2 ** (attempt - 1)))
			except LLMResponseError:
				raise
			except Exception as exc:
				last_error = exc
				logger.exception("Ошибка вызова LLM", extra={"event": "llm_call_failed", "attempt": attempt})
				break
		raise LLMNetworkError("Не удалось связаться с сервисом модели") from last_error
