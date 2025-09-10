from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import time

@dataclass
class LWWMap:
    data: Dict[str, Tuple[Any, float]]

    def __init__(self):
        self.data = {}

    def put(self, key: str, value: Any, ts: float | None = None):
        ts = ts or time.time()
        self.data[key] = (value, ts)

    def get(self, key: str, default=None):
        return self.data.get(key, (default, 0.0))[0]

    def merge(self, other: "LWWMap"):
        for k,(v,t) in other.data.items():
            if k not in self.data or t > self.data[k][1]:
                self.data[k] = (v,t)

    def to_dict(self) -> Dict[str, Any]:
        return {k:v for k,(v,_) in self.data.items()}
