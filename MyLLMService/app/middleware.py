from __future__ import annotations

import time
import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    started = time.perf_counter()
    logger.info(
        "Получен входящий запрос",
        extra={"event": "request_received", "request_id": request_id, "method": request.method, "path": request.url.path},
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Ошибка обработки запроса", extra={"event": "request_failed", "request_id": request_id})
        raise
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    logger.info(
        "Запрос обработан",
        extra={
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": elapsed_ms,
        },
    )
    return response