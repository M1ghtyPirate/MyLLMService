from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.config.settings import Settings
from app.llm.client import LLMClient, LLMNetworkError
from app.models import StyleReviewRequest
from app.services.text_style_service import (
    EMPTY_TEXT_MESSAGE,
    LONG_TEXT_MESSAGE,
    NETWORK_ERROR_MESSAGE,
    StyleReviewHandler,
    TextStyleService,
)


class TextStyleReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TextStyleService(test_settings())
        self.service.llm = Mock()
        self.handler = StyleReviewHandler(self.service)

    def test_empty_input_is_rejected_before_api_call(self) -> None:
        result = self.handler.handle("  ", "научный")

        self.assertEqual(result, EMPTY_TEXT_MESSAGE)
        self.service.llm.complete.assert_not_called()

    def test_long_input_is_rejected_before_api_call(self) -> None:
        result = self.handler.handle("x" * 10001, "научный")

        self.assertEqual(result, LONG_TEXT_MESSAGE)
        self.service.llm.complete.assert_not_called()

    def test_valid_text_returns_remarks(self) -> None:
        self.service.llm.complete.return_value = "- Слово «очень» избыточно. Уберите его для краткости."

        result = self.handler.handle("Это очень важный текст.", "официально-деловой")

        self.assertIn("избыточно", result)
        self.service.llm.complete.assert_called_once()

    def test_identical_request_uses_cache(self) -> None:
        self.service.llm.complete.return_value = "Замечаний нет."
        request = StyleReviewRequest(text="Текст для проверки.", style="научный")

        first = self.service.review(request)
        second = self.service.review(request)

        self.assertEqual(first, second)
        self.service.llm.complete.assert_called_once()

    def test_network_error_is_safe_for_ui(self) -> None:
        self.service.llm.complete.side_effect = LLMNetworkError("secret provider details")

        result = self.handler.handle("Проверяемый текст.", "разговорный")

        self.assertEqual(result, NETWORK_ERROR_MESSAGE)
        self.assertNotIn("secret", result)


class LLMClientTests(unittest.TestCase):
    def test_zero_retries_still_performs_one_attempt(self) -> None:
        client = LLMClient(test_settings(llm_max_retries=0))
        client._get_access_token = Mock(return_value="token")

        with patch("app.llm.client.GigaChat") as gigachat:
            gigachat.return_value.chat.side_effect = TimeoutError()

            with self.assertRaises(LLMNetworkError):
                client.complete("Проверьте текст")

        gigachat.return_value.chat.assert_called_once_with("Проверьте текст")


def test_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "api_access_token_endpoint": "https://example.test/oauth",
        "api_endpoint": "https://example.test/api",
        "authorization_key": "test-key",
    }
    values.update(overrides)
    return Settings(**values)


if __name__ == "__main__":
    unittest.main()
