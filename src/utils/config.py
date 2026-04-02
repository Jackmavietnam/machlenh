from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml


def load_yaml(path: str | Path) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def resolve_project_paths(root: str | Path = '.') -> Dict[str, Path]:
    base = Path(root).resolve()
    cfg = load_yaml(base / 'config' / 'paths.yaml')
    result: Dict[str, Path] = {}
    for key, value in cfg.items():
        result[key] = (base / value).resolve() if value != '.' else base
    return result
