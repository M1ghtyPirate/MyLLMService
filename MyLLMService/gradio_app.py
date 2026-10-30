from __future__ import annotations

import gradio as gr

from app.config.settings import Settings
from app.logging_config import configure_logging
from app.services.shopping_list_service import ShoppingListHandler


configure_logging(Settings().log_file)
handler = ShoppingListHandler()


def generate_shopping_list(dish: str, people: str, output_format: str) -> str:
	return handler.handle(dish, people, output_format)


def build_demo() -> gr.Blocks:
	with gr.Blocks(title="Список покупок по блюду") as demo:
		gr.Markdown("# Список покупок по блюду\nУкажите блюдо, количество человек и формат ответа.")
		dish = gr.Textbox(
			label="Что приготовить",
			placeholder="Например: паста карбонара",
			lines=4,
			max_lines=8,
		)
		people = gr.Dropdown(
			choices=["1", "2", "4", "6"],
			value="2",
			label="На сколько человек",
		)
		output_format = gr.Dropdown(
			choices=["Список продуктов", "Список + шаги"],
			value="Список продуктов",
			label="Формат",
		)
		generate_button = gr.Button("Сгенерировать список покупок", variant="primary")
		result = gr.Markdown()
		generate_button.click(
			fn=generate_shopping_list,
			inputs=[dish, people, output_format],
			outputs=result,
		)
	return demo


demo = build_demo()


if __name__ == "__main__":
	demo.launch()
