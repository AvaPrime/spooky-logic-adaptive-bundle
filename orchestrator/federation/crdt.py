from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import time

@dataclass
class LWWMap:
    """A Last-Write-Wins Map CRDT."""
    data: Dict[str, Tuple[Any, float]]

    def __init__(self):
        """Initializes the LWWMap."""
        self.data = {}

    def put(self, key: str, value: Any, ts: float | None = None):
        """
        Puts a key-value pair into the map.

        Args:
            key (str): The key to put.
            value (Any): The value to put.
            ts (float | None, optional): The timestamp of the operation. Defaults to None.
        """
        ts = ts or time.time()
        self.data[key] = (value, ts)

    def get(self, key: str, default=None):
        """
        Gets a value from the map.

        Args:
            key (str): The key to get.
            default (_type_, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            The value associated with the key, or the default value if the key is not found.
        """
        return self.data.get(key, (default, 0.0))[0]

    def merge(self, other: "LWWMap"):
        """
        Merges another LWWMap into this one.

        Args:
            other (LWWMap): The other LWWMap to merge.
        """
        for k,(v,t) in other.data.items():
            if k not in self.data or t > self.data[k][1]:
                self.data[k] = (v,t)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the LWWMap to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the LWWMap.
        """
        return {k:v for k,(v,_) in self.data.items()}
