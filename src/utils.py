from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any


def load_params(path: str | os.PathLike[str]) -> dict[str, Any]:
    import yaml

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def ensure_parent(path: str | os.PathLike[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def write_json(path: str | os.PathLike[str], payload: Any) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, default=_json_default)


def read_json(path: str | os.PathLike[str], fallback: Any = None) -> Any:
    if not Path(path).exists():
        return fallback
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_text(path: str | os.PathLike[str], value: str) -> None:
    ensure_parent(path)
    Path(path).write_text(value, encoding="utf-8")


def append_jsonl(path: str | os.PathLike[str], payload: Any) -> None:
    ensure_parent(path)
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(payload, default=_json_default) + "\n")


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
