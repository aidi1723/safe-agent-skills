from __future__ import annotations

import os
from pathlib import Path


PROJECT_HOME_ENV = "SAFE_AGENT_SKILLS_HOME"


def candidate_project_roots() -> list[Path]:
    roots: list[Path] = []
    env_home = os.environ.get(PROJECT_HOME_ENV)
    if env_home:
        roots.append(Path(env_home))
    cwd = Path.cwd()
    roots.extend([cwd, *cwd.parents])
    module_path = Path(__file__).resolve()
    roots.extend(module_path.parents)

    unique_roots = []
    seen = set()
    for root in roots:
        resolved = root.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_roots.append(resolved)
    return unique_roots


def resolve_project_asset_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    for root in candidate_project_roots():
        resolved = root / candidate
        if resolved.exists():
            return resolved
    return candidate
