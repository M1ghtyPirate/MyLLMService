from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _CacheEntry:
	value: Any
	expires_at: float


class TTLCache:
	def __init__(self, ttl_seconds: int) -> None:
		self.ttl_seconds = ttl_seconds
		self._items: dict[str, _CacheEntry] = {}

	@staticmethod
	def make_key(*, tags: list[str], model: str, temperature: float, system_prompt: str) -> str:
		payload = {
			"tags": tags,
			"model": model,
			"temperature": temperature,
			"system_prompt": system_prompt,
		}
		encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
		return hashlib.sha256(encoded).hexdigest()

	def get(self, key: str) -> Any | None:
		entry = self._items.get(key)
		if entry is None:
			logger.info("Промах кеша", extra={"event": "cache_miss", "cache_key": key})
			return None
		if entry.expires_at <= time.monotonic():
			self._items.pop(key, None)
			logger.info("Срок действия записи кеша истёк", extra={"event": "cache_expired", "cache_key": key})
			return None
		logger.info("Попадание в кеш", extra={"event": "cache_hit", "cache_key": key})
		return entry.value

	def set(self, key: str, value: Any) -> None:
		self._items[key] = _CacheEntry(value=value, expires_at=time.monotonic() + self.ttl_seconds)
