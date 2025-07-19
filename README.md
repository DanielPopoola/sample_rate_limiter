# Sample FastAPI Rate Limiter

This project provides a simple and flexible rate limiter for FastAPI applications, implemented using the token bucket algorithm.

## Features

- **Token Bucket Algorithm:** Efficiently handles rate limiting with bursts.
- **Flexible Configuration:** Set rate limits using simple strings (e.g., "10/minute") or numeric values.
- **Custom Key Functions:** Rate limit based on IP address, user ID, API key, or any other request attribute.
- **FastAPI Integration:** Easy to use as a decorator on your FastAPI endpoints.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/DanielPopoola/sample_rate_limiter.git
    cd sample-rate-limiter
    ```

2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the FastAPI application:
    ```bash
    uvicorn main:app --reload
    ```

2.  The application will be available at `http://127.0.0.1:8000`.

### Using the `@rate_limit` decorator

You can apply rate limiting to any FastAPI endpoint using the `@rate_limit` decorator.

#### Basic Usage (by IP address)

```python
from fastapi import FastAPI, Request
from app.rate_limiter import rate_limit

app = FastAPI()

@app.get("/basic")
@rate_limit("5/minute")
def basic_endpoint(request: Request):
    return {"message": "This endpoint is rate limited to 5 requests per minute per IP."}
```

#### Custom Key Function (by API Key)

```python
def get_api_key(request: Request):
    return request.headers.get("X-API-Key", "anonymous")

@app.get("/api")
@rate_limit("100/hour", key_func=get_api_key)
def api_endpoint(request: Request):
    return {"message": "This endpoint is rate limited by API key."}
```

## API Endpoints

The `main.py` file provides the following example endpoints:

-   `GET /basic`: Rate limited to 5 requests per minute, identified by IP address.
-   `GET /numeric`: Rate limited to 10 requests with a refill rate of 5 tokens every 60 seconds, identified by IP address.
-   `GET /user`: Rate limited to 20 requests per hour, identified by the `X-User-ID` header.
-   `GET /api`: Rate limited to 100 requests per hour, identified by the `X-API-Key` header.

## How It Works

The rate limiter uses the **Token Bucket** algorithm. Each unique client (identified by the key function) has a bucket of tokens.

1.  **Tokens:** Each request from a client consumes one token from their bucket.
2.  **Capacity:** Each bucket has a maximum capacity of tokens.
3.  **Refill Rate:** Tokens are added back to the bucket at a constant rate.
4.  **Rate Limiting:** If a client's bucket is empty, their request is denied (HTTP 429 Too Many Requests) until new tokens are added.

This approach allows for bursts of requests while still enforcing an average rate limit over time.
