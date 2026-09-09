"""Runtime configuration for the Web MVP; values are safe to expose only through behaviour."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _port(value: str | None, default: int = 8000) -> int:
    try:
        port = int(value) if value is not None else default
    except ValueError as exc:
        raise ValueError("PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    return port


@dataclass(frozen=True)
class WebSettings:
    host: str = "127.0.0.1"
    port: int = 8000
    development: bool = True

    @classmethod
    def from_environment(cls) -> "WebSettings":
        return cls(
            host=os.getenv("HOST", "127.0.0.1"),
            port=_port(os.getenv("PORT")),
            development=os.getenv("WEB_DEBUG", "0") == "1",
        )
