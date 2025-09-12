from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import time

@dataclass
class LWWMap:
    """A Last-Write-Wins Map CRDT.

    This class implements a Last-Write-Wins (LWW) Map, which is a
    Conflict-free Replicated Data Type (CRDT). In an LWW-Map, conflicts are
    resolved by taking the value with the highest timestamp.

    Attributes:
        data: A dictionary where the keys are the keys of the map and the
            values are tuples of the form (value, timestamp).
    """
    data: Dict[str, Tuple[Any, float]]

    def __init__(self):
        """Initializes the LWWMap."""
        self.data = {}

    def put(self, key: str, value: Any, ts: float | None = None):
        """Puts a key-value pair into the map.

        If a timestamp is not provided, the current time is used.

        Args:
            key: The key to put.
            value: The value to put.
            ts: The timestamp of the operation.
        """
        ts = ts or time.time()
        self.data[key] = (value, ts)

    def get(self, key: str, default=None):
        """Gets a value from the map.

        Args:
            key: The key to get.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if the
            key is not found.
        """
        return self.data.get(key, (default, 0.0))[0]

    def merge(self, other: "LWWMap"):
        """Merges another LWWMap into this one.

        For each key in the other map, if the key is not in this map or the
        timestamp of the other map's value is greater than the timestamp of
        this map's value, the value from the other map is taken.

        Args:
            other: The other LWWMap to merge.
        """
        for k,(v,t) in other.data.items():
            if k not in self.data or t > self.data[k][1]:
                self.data[k] = (v,t)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the LWWMap to a dictionary.

        Returns:
            A dictionary representation of the LWWMap, without the timestamps.
        """
        return {k:v for k,(v,_) in self.data.items()}
