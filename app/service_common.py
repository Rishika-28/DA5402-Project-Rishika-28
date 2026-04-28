from __future__ import annotations

import os
from functools import lru_cache

from src.utils import load_params, read_json


@lru_cache(maxsize=1)
def get_params() -> dict:
    return load_params(os.environ.get("PARAMS_PATH", "params.yaml"))


@lru_cache(maxsize=1)
def get_model_metadata() -> dict:
    return read_json("models/model_registry.json", {})

