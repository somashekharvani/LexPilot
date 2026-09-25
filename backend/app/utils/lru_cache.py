"""
LexPilot - High-Efficiency LRU & Memoization Cache
--------------------------------------------------
Prevents memory leaks and reduces CPU consumption by:
  - Enforcing a maximum session capacity with Least-Recently-Used (LRU) eviction
  - Automatically expiring stale sessions after a configurable TTL
  - Memoizing full pipeline analyses via SHA-256 document hashing for <1ms response times
"""

import time
import hashlib
import threading
from collections import OrderedDict
from typing import Dict, Any, Optional, Tuple

class LRUSessionCache:
    """
    Thread-safe LRU Cache with TTL expiration for document analysis sessions.
    Guarantees bounded memory footprint and automatic cleanup.
    """
    def __init__(self, maxsize: int = 50, ttl_seconds: int = 7200):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a session by key if present and not expired.
        Moves accessed item to the end (most recently used).
        """
        now = time.time()
        with self._lock:
            if key not in self._cache:
                return None

            data, timestamp = self._cache[key]
            # Check TTL
            if now - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None

            # Mark as recently used
            self._cache.move_to_end(key)
            return data

    def put(self, key: str, value: Dict[str, Any]) -> None:
        """
        Stores a session with current timestamp.
        Evicts oldest item if capacity is exceeded.
        """
        now = time.time()
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, now)

            # Evict LRU entries if capacity exceeded
            while len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def __getitem__(self, key: str) -> Dict[str, Any]:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        self.put(key, value)

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def keys(self):
        with self._lock:
            return list(self._cache.keys())

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class PipelineMemoizer:
    """
    In-memory memoization cache indexed by document content SHA-256 hash.
    Enables instant retrieval for identical contracts without re-running NLP pipelines.
    """
    def __init__(self, max_items: int = 30):
        self.max_items = max_items
        self._hash_cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def compute_hash(file_bytes: bytes, filename: str) -> str:
        h = hashlib.sha256()
        h.update(file_bytes)
        h.update(filename.encode("utf-8", errors="ignore"))
        return h.hexdigest()

    def get(self, doc_hash: str) -> Optional[Any]:
        with self._lock:
            if doc_hash in self._hash_cache:
                self._cache_hit = True
                self._hash_cache.move_to_end(doc_hash)
                return self._hash_cache[doc_hash]
            return None

    def put(self, doc_hash: str, analysis_response: Any) -> None:
        with self._lock:
            if doc_hash in self._hash_cache:
                self._hash_cache.move_to_end(doc_hash)
            self._hash_cache[doc_hash] = analysis_response

            while len(self._hash_cache) > self.max_items:
                self._hash_cache.popitem(last=False)
