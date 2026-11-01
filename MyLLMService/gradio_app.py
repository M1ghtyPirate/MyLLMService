from __future__ import annotations

import gradio as gr

from app.config.settings import Settings
from app.logging_config import configure_logging
from app.services.text_style_service import StyleReviewHandler

configure_logging(Settings().log_file)
handler = StyleReviewHandler()


def review_text(text: str, style: str, response_format: str) -> str:
    return handler.handle(text, style, response_format)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Проверка стиля текста") as demo:
        gr.Markdown("# Проверка стиля текста\nВведите текст и выберите желаемый стиль.")
        text = gr.Textbox(
            label="Текст для проверки",
            placeholder="Введите текст объёмом до 10000 символов",
            lines=8,
            max_lines=12,
        )
        style = gr.Dropdown(
            choices=[
                ("Научный", "научный"),
                ("Официально-деловой", "официально-деловой"),
                ("Разговорный", "разговорный"),
            ],
            value="научный",
            label="Стиль текста",
        )
        response_format = gr.Dropdown(
            choices=[
                ("Рекомендации по тексту", "рекомендации по тексту"),
                ("Текст с исправлениями", "текст с исправлениями"),
            ],
            value="рекомендации по тексту",
            label="Формат ответа",
        )
        review_button = gr.Button("Проверить стиль", variant="primary")
        result = gr.Markdown()
        review_button.click(
            fn=review_text,
            inputs=[text, style, response_format],
            outputs=result,
        )
    return demo


demo = build_demo()


if __name__ == "__main__":
    demo.launch()
