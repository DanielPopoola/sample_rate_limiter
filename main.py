from fastapi import FastAPI, Request
from app.rate_limiter import rate_limit

app = FastAPI()


# Basic usage - rate limit by IP
@app.get("/basic")
@rate_limit("5/minute")
def basic_endpoint(request: Request):
    return {"message": "Basic rate limiting by IP"}


# Numeric format
@app.get("/numeric")
@rate_limit(10, 5, 60)
def numeric_endpoint(request: Request):
    return {"message": "Numeric rate limiting"}


# Custom key function - rate limit by user ID
def get_user_id(request):
    return request.headers.get("X-User-ID", "anonymous")

@app.get("/user")
@rate_limit("20/hour", key_func=get_user_id)
def user_endpoint(request: Request):
    return {"message": "Rate limiting by user ID"}

# Custom key function - rate limit by API key
def get_api_key(request):
    return request.headers.get("X-API-Key", "no-key")

@app.get("/api")
@rate_limit("100/hour", key_func=get_api_key)
def api_endpoint(request: Request):
    return {"message": "Rate limiting by API key"}