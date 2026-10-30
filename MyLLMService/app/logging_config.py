from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		payload = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"level": record.levelname,
			"logger": record.name,
			"message": record.getMessage(),
		}
		for field in ("event", "request_id", "method", "path", "status_code", "duration_ms", "error", "attempt", "cache_key", "prompt", "response"):
			value = getattr(record, field, None)
			if value is not None:
				payload[field] = value
		return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(log_file: str) -> None:
	directory = os.path.dirname(log_file)
	if directory:
		os.makedirs(directory, exist_ok=True)
	formatter = JsonFormatter()
	root = logging.getLogger()
	root.setLevel(logging.INFO)
	root.handlers.clear()
	console = logging.StreamHandler()
	console.setFormatter(formatter)
	file_handler = logging.FileHandler(log_file, encoding="utf-8")
	file_handler.setFormatter(formatter)
	root.addHandler(console)
	root.addHandler(file_handler)
