from datetime import datetime, timedelta
import time

class TokenBucket:

    def __init__(self, capacity, refill_rate, refill_time):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_time = refill_time
        self.buckets = {}

    def _refill(self, key):
        tokens, last_time = self.buckets[key]
        now = datetime.now()
        elapsed = (now  - last_time).total_seconds()

        added_tokens = (elapsed / self.refill_time) * self.refill_rate
        tokens = min(self.capacity, tokens + added_tokens)

        self.buckets[key] = (tokens, now)

    def allow_request(self, key):
        if key not in self.buckets:
            self.buckets[key] = (self.capacity, datetime.now())

        self._refill(key)
        tokens, last_time  = self.buckets[key]

        if tokens >= 1:
            self.buckets[key] = (tokens - 1, last_time)
            return True
        return False
    

"""
bucket =  TokenBucket(capacity=10, refill_rate=5, refill_time=60)

result1 = bucket.allow_request("user1")
print(f"Request 1: {result1}")
print(f"Tokens left: {bucket.buckets["user1"][0]}")

for i in range(9):
    bucket.allow_request("user1")

print(f"After 10 requests: {bucket.buckets["user1"][0]}")

result11 = bucket.allow_request("user1")  # Should be False
print(f"Request 11: {result11}")
"""

"""
 ❌ Situation 1: We don't update the timestamp even if no tokens were added
    🔥 What goes wrong:
    The next refill wrongly thinks more time has passed

    So it overfills the bucket, even when it shouldn’t

"""
class BrokenTokenBucket1:
    def __init__(self, capacity, refill_rate_per_sec):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = 0  # Starts empty
        self.timestamp = datetime.now()

    def refill(self):
        now = datetime.now()
        elapsed = (now - self.timestamp).total_seconds()
        tokens_to_add = self.refill_rate * elapsed
        print(f"\n[Refill] Elapsed time: {elapsed:.6f}s")
        print(f"[Refill] Tokens before: {self.tokens:.2f}")
        print(f"[Refill] Tokens to add (before min): {tokens_to_add:.2f}")

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        print(f"[Refill] Tokens after: {self.tokens:.2f}")

        # ❌ BUG: we forgot to update the timestamp
        self.timestamp = now
        print(f"Current timestamp: {self.timestamp:.6f}")

    def allow_request(self):
        self.refill()
        if self.tokens >= 1:
            self.tokens -= 1
            print("[Request] Allowed! Tokens left:", self.tokens)
            return True
        print("[Request] Denied. Tokens left:", self.tokens)
        return False
    

"""
bucket = BrokenTokenBucket1(capacity=5, refill_rate_per_sec=1)

# Simulate 2 seconds in the past (without real waiting)
bucket.timestamp -= timedelta(seconds=2)
bucket.allow_request()  # Should allow and refill 2 tokens

print(f"[1] Tokens after pretend call: {bucket.tokens:.2f}")

# Again simulate 2 more seconds back (4 total since actual timestamp)
bucket.timestamp -= timedelta(seconds=2)
bucket.allow_request()  # Should overfill since timestamp is stale

print(f"[2] Tokens after second pretend call: {bucket.tokens:.2f}")
"""

"""
❌ Situation 3: We don’t call refill if we’re going to deny the request anyway
🔥 What goes wrong:
Tokens are never added back during denied requests

So the bucket stays stale forever, even though time has passed
"""


class BrokenTokenBucket2:
    def __init__(self, capacity, refill_rate_per_sec):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = 0
        self.timestamp = datetime.now()

    def allow_request(self):
        if self.tokens < 1:
            # ❌ BUG: We skip refill if we plan to deny
            return False

        self.refill()
        self.tokens -= 1
        return True

    def refill(self):
        now = datetime.now()
        elapsed = (now - self.timestamp).total_seconds()
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.timestamp = now

bucket = BrokenTokenBucket2(capacity=5, refill_rate_per_sec=1)

# Simulate a long wait, but we don’t refill because we immediately deny
bucket.timestamp -= timedelta(seconds=5)

# Try request (it’ll be denied and no refill is done!)
print(f"Allowed? {bucket.allow_request()}")
print(f"Tokens: {bucket.tokens:.2f}")  # Still 0!
