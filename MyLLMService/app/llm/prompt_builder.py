from __future__ import annotations

SYSTEM_PROMPT = "Ты — кулинарный помощник. Отвечай кратко, понятно и только по запросу пользователя."


def build_shopping_list_prompt(dish: str, people: str, output_format: str) -> str:
	steps_instruction = "Добавь после списка 5–8 коротких шагов приготовления." if output_format == "Список + шаги" else "Не добавляй шаги приготовления."
	return (
		f"{SYSTEM_PROMPT}\n"
		f"Блюдо: {dish}\n"
		f"Количество человек: {people}\n"
		f"Формат: {output_format}\n"
		"Составь список покупок: один продукт на строку, с количеством.\n"
		f"{steps_instruction}"
	)
