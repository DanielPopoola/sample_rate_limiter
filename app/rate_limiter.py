from functools import wraps
from fastapi import Request, HTTPException
from datetime import datetime
from typing import Callable, Optional, Union


class TokenBucket:
    def __init__(self, capacity, refill_rate, refill_time) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_time = refill_time
        self.buckets = {}

    def _refill(self, key):
        tokens, last_time = self.buckets[key]
        now = datetime.now()
        elapsed = (now - last_time).total_seconds()
        added_tokens = (elapsed / self.refill_time) * self.refill_rate
        tokens = min(self.capacity, tokens + added_tokens)
        self.buckets[key] = (tokens, now)

    def allow_request(self, key):
        if key not in self.buckets:
            self.buckets[key] = (self.capacity, datetime.now())

        self._refill(key)
        tokens, last_time = self.buckets[key]

        if tokens >= 1:
            self.buckets[key] = (tokens - 1, last_time)
            return True
        return False
    
    def get_token_info(self, key):
        """Get current token count for a key"""
        if key not in self.buckets:
            self.buckets[key] = (self.capacity, datetime.now())

        self._refill(key)
        return self.buckets[key]
