from __future__ import annotations

from pathlib import Path
from typing import Any


def build_task_pack_v3(
    registry_dir: Path,
    task: str,
    bundles_path: Path,
    routing_examples_path: Path,
    *,
    max_candidates: int = 3,
    semantic_provider: object | None = None,
    semantic_mode: str = "shadow",
) -> dict[str, Any]:
    raise NotImplementedError("task-pack v3 pipeline is not complete")
