from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class RubricItem:
    id: str
    label: str
    probes: list[str]
    severity: str

@dataclass
class Rubric:
    name: str
    items: list[RubricItem]

def load_rubric(path: str | Path) -> Rubric:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = [RubricItem(**x) for x in data["items"]]
    return Rubric(name=data.get("name", Path(path).stem), items=items)

def load_rubrics(paths: list[str | Path]) -> Rubric:
    all_items: list[RubricItem] = []
    names: list[str] = []
    for p in paths:
        r = load_rubric(p)
        names.append(r.name)
        all_items.extend(r.items)
    return Rubric(name="+".join(names), items=all_items)
