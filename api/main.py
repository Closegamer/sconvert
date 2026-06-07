import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PRICE_CACHE_KEY = "btc:price:v1"
PRICE_TTL = 60
CURRENCY_CACHE_KEY = "currency:rates:v1"
CURRENCY_TTL = 3600
CURRENCY_URL = "https://open.er-api.com/v6/latest/USD"

_redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        await _redis.ping()
    except Exception:
        _redis = None
    yield
    if _redis:
        await _redis.aclose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/btc/price")
async def btc_price():
    if _redis is not None:
        try:
            cached = await _redis.get(PRICE_CACHE_KEY)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd,rub"},
            )
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"price fetch failed: {exc}")

    result = {
        "usd": raw["bitcoin"]["usd"],
        "rub": raw["bitcoin"]["rub"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
    }

    if _redis is not None:
        try:
            await _redis.setex(PRICE_CACHE_KEY, PRICE_TTL, json.dumps(result))
        except Exception:
            pass

    return result


@app.get("/api/currency/rates")
async def currency_rates():
    if _redis is not None:
        try:
            cached = await _redis.get(CURRENCY_CACHE_KEY)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(CURRENCY_URL)
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"currency rates fetch failed: {exc}")

    result = {
        "base": "USD",
        "rates": raw.get("rates", {}),
        "updated_at": raw.get("time_last_update_utc", datetime.now(timezone.utc).isoformat()),
        "cached": False,
    }

    if _redis is not None:
        try:
            await _redis.setex(CURRENCY_CACHE_KEY, CURRENCY_TTL, json.dumps(result))
        except Exception:
            pass

    return result
