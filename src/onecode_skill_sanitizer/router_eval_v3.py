from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def load_eval_dataset_v3(path: Path) -> list[dict[str, Any]]:
    raise NotImplementedError("router v3 evaluation loader is not complete")


def evaluate_router_v3(
    cases: list[dict[str, Any]],
    route_builder: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    raise NotImplementedError("router v3 evaluation is not complete")
