from __future__ import annotations

import unittest
from unittest.mock import Mock

from app.config.settings import Settings
from app.llm.client import LLMNetworkError
from app.models import ShoppingListRequest
from app.services.shopping_list_service import (
    EMPTY_DISH_MESSAGE,
    LONG_DISH_MESSAGE,
    NETWORK_ERROR_MESSAGE,
    ShoppingListHandler,
    ShoppingListService,
)


class ShoppingListTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ShoppingListService(Settings())
        self.service.llm = Mock()
        self.handler = ShoppingListHandler(self.service)

    def test_empty_input_is_rejected_before_api_call(self) -> None:
        result = self.handler.handle("  ", "2", "Список продуктов")

        self.assertEqual(result, EMPTY_DISH_MESSAGE)
        self.service.llm.complete.assert_not_called()

    def test_long_input_is_rejected_before_api_call(self) -> None:
        result = self.handler.handle("x" * 1001, "2", "Список продуктов")

        self.assertEqual(result, LONG_DISH_MESSAGE)
        self.service.llm.complete.assert_not_called()

    def test_normal_input_returns_shopping_list(self) -> None:
        self.service.llm.complete.return_value = "Куриное филе — 500 г\nРис — 300 г"

        result = self.handler.handle("Курица с рисом", "4", "Список продуктов")

        self.assertIn("Куриное филе", result)
        self.service.llm.complete.assert_called_once()

    def test_identical_request_uses_cache(self) -> None:
        self.service.llm.complete.return_value = "Мука — 500 г"
        request = ShoppingListRequest(dish="Блины", people="2", output_format="Список продуктов")

        first = self.service.generate(request)
        second = self.service.generate(request)

        self.assertEqual(first, second)
        self.service.llm.complete.assert_called_once()

    def test_network_error_is_safe_for_ui(self) -> None:
        self.service.llm.complete.side_effect = LLMNetworkError("secret provider details")

        result = self.handler.handle("Суп", "2", "Список продуктов")

        self.assertEqual(result, NETWORK_ERROR_MESSAGE)
        self.assertNotIn("secret", result)


if __name__ == "__main__":
    unittest.main()
