from functools import wraps
from fastapi import Request, HTTPException
from datetime import datetime
from typing import Callable, Optional, Union


class TokenBucket:
    def __init__(self, capacity, refill_rate, refill_time):
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
            return self.capacity, datetime.now()
        
        self._refill(key)
        return self.buckets[key]


def parse_rate_limit_string(rate_string):
    """Parse strings like '10/minute' into capacity, refill_rate, refill_time"""
    if '/' not in rate_string:
        raise ValueError("Rate limit string must be in format 'N/period'")
    
    requests, period = rate_string.split('/')
    requests = int(requests)
    
    period_map = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400
    }
    
    if period not in period_map:
        raise ValueError(f"Unsupported period: {period}. Use: {list(period_map.keys())}")
    
    refill_time = period_map[period]
    capacity = requests
    refill_rate = requests
    
    return capacity, refill_rate, refill_time


def rate_limit(
    limit: Union[int, str], 
    refill_rate: Optional[int] = None, 
    refill_time: Optional[int] = None, 
    key_func: Optional[Callable[[Request], str]] = None
):
    """
    Rate limiting decorator for FastAPI endpoints.
    
    Args:
        limit: Either an integer (capacity) or string like "10/minute"
        refill_rate: Tokens to add per refill period (if using numeric format)
        refill_time: Seconds between refills (if using numeric format)
        key_func: Function to extract user identifier from request
    
    Examples:
        @rate_limit("10/minute")
        @rate_limit(10, 5, 60)
        @rate_limit("20/hour", key_func=lambda req: req.headers.get("X-API-Key"))
    """
    if isinstance(limit, str):
        if refill_rate is not None or refill_time is not None:
            raise ValueError("Cannot specify refill_rate or refill_time with string format")
        capacity, refill_rate, refill_time = parse_rate_limit_string(limit)
    else:
        capacity = limit
        if refill_rate is None or refill_time is None:
            raise ValueError("Must specify refill_rate and refill_time with numeric format")

    bucket = TokenBucket(capacity, refill_rate, refill_time)
    
    def default_key_func(request):
        if hasattr(request, 'client') and hasattr(request.client, 'host'):
            return request.client.host
        elif hasattr(request,'remote_addr'):
            return request.remote_addr
        else:
            return "test-client"
        
    get_key = key_func or default_key_func
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = None
            
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'headers'):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'client') and hasattr(value, 'headers'):
                        request = value
                        break

            if not request:
                available_types = [type(arg).__name__ for arg in args] + [type(v).__name__ for v in kwargs.values()]
                raise ValueError(
                    f"No Request object found in function parameters. "
                    f"Available parameter types: {available_types}. "
                    f"Make sure your function includes 'request: Request' as a parameter."
                )

            user_key = get_key(request)
            
            if bucket.allow_request(user_key):
                return func(*args, **kwargs)
            else:
                tokens, _ = bucket.get_token_info(user_key)
                
                seconds_until_next_token = bucket.refill_time / bucket.refill_rate
                retry_after = int(seconds_until_next_token)
                
                headers = {
                    "X-RateLimit-Limit": str(bucket.capacity),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                    "Retry-After": str(retry_after)
                }
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Rate limit exceeded",
                        "limit": bucket.capacity,
                        "remaining": 0,
                        "reset_in_seconds": retry_after
                    },
                    headers=headers
                )
        
        return wrapper
    return decorator