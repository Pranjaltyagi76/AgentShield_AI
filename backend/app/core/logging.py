"""Small JSON formatter; callers log metadata, never credentials or request bodies."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in ("request_id", "method", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    logger = logging.getLogger("agentshield")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
