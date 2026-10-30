from __future__ import annotations

import unittest
from unittest.mock import Mock

from app.config.settings import Settings
from app.llm.client import LLMUnavailableError
from app.models import JokeResponse
from app.services.joke_service import InvalidLLMResponseError, JokeService
from app.state import AppState


class JokeServiceTests(unittest.TestCase):
	def setUp(self) -> None:
		self.service = JokeService(Settings())
		self.service.llm = Mock()

	def test_normalizes_tags_at_state_boundary(self) -> None:
		self.assertEqual(AppState.normalize_tags([" Python ", "python", "AI"]), ["ai", "python"])

	def test_builds_response_and_reuses_cache(self) -> None:
		self.service.llm.complete.return_value = "Заголовок|Текст"

		first = self.service.get_joke(["python"])
		second = self.service.get_joke(["python"])

		self.assertIsInstance(first, JokeResponse)
		self.assertEqual(first, second)
		self.service.llm.complete.assert_called_once()

	def test_rejects_invalid_model_response(self) -> None:
		with self.assertRaises(InvalidLLMResponseError):
			self.service._post_process("Ответ без разделителя", ["python"])

	def test_returns_none_when_model_is_unavailable(self) -> None:
		self.service.llm.complete.side_effect = LLMUnavailableError("Сервис LLM недоступен")

		self.assertIsNone(self.service.get_joke(["python"]))


if __name__ == "__main__":
	unittest.main()
