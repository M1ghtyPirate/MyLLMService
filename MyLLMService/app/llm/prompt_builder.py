from __future__ import annotations

SYSTEM_PROMPT = "Ты - заслуженный артист РСФСР, писатель-юморист и бессменный резидент кривого зеркала."


def build_joke_prompt(tags: list[str]) -> str:
	return (
		f"{SYSTEM_PROMPT}\n"
		f"Придумай анекдот на темы: {', '.join(tags)}.\n"
		'Верни ответ строго в формате "<Название>|<Текст>" без дополнительных разделителей.'
	)
