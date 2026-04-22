"""
Fetches live gold and silver spot prices.
Primary source: open.er-api.com (free, no key needed for XAG/XAU).
Fallback:       hard-coded reasonable estimates with a clear disclaimer.
"""
import httpx
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Fallback prices (updated periodically — not for financial advice) ─────────
FALLBACK_SILVER_USD_PER_GRAM = 0.96   # ~$30/oz ÷ 31.1g
FALLBACK_GOLD_USD_PER_GRAM   = 96.45  # ~$3000/oz ÷ 31.1g

# Simple in-memory cache (price + timestamp)
_cache: dict = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


async def get_metal_prices_usd() -> dict:
    """
    Returns silver and gold prices in USD per gram.
    Caches results for 1 hour to avoid hammering external APIs.
    """
    now = time.time()
    if _cache.get("fetched_at") and (now - _cache["fetched_at"]) < CACHE_TTL_SECONDS:
        return _cache["prices"]

    prices = await _fetch_from_exchangerate_api()
    if not prices:
        prices = await _fetch_from_metals_dev()
    if not prices:
        logger.warning("All price sources failed — using fallback prices.")
        prices = {
            "silver_usd_per_gram": FALLBACK_SILVER_USD_PER_GRAM,
            "gold_usd_per_gram":   FALLBACK_GOLD_USD_PER_GRAM,
            "source": "fallback",
        }

    _cache["prices"]     = prices
    _cache["fetched_at"] = now
    return prices


async def _fetch_from_exchangerate_api() -> Optional[dict]:
    """
    Uses exchangerate-api free endpoint.
    XAG = troy oz of silver in USD, XAU = troy oz of gold in USD.
    """
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get("https://open.er-api.com/v6/latest/USD")
            data = resp.json()

        rates = data.get("rates", {})
        xag   = rates.get("XAG")  # oz of silver per 1 USD → invert for USD/oz
        xau   = rates.get("XAU")  # oz of gold  per 1 USD → invert for USD/oz

        if not xag or not xau:
            return None

        TROY_OZ_TO_GRAMS = 31.1035
        return {
            "silver_usd_per_gram": (1 / xag) / TROY_OZ_TO_GRAMS,
            "gold_usd_per_gram":   (1 / xau) / TROY_OZ_TO_GRAMS,
            "source": "open.er-api.com",
        }
    except Exception as e:
        logger.warning(f"exchangerate-api fetch failed: {e}")
        return None


async def _fetch_from_metals_dev() -> Optional[dict]:
    """
    Fallback: metals.live (free, no key).
    """
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get("https://api.metals.live/v1/spot")
            data = resp.json()

        silver_oz = next((x["silver"] for x in data if "silver" in x), None)
        gold_oz   = next((x["gold"]   for x in data if "gold"   in x), None)

        if not silver_oz or not gold_oz:
            return None

        TROY_OZ_TO_GRAMS = 31.1035
        return {
            "silver_usd_per_gram": silver_oz / TROY_OZ_TO_GRAMS,
            "gold_usd_per_gram":   gold_oz   / TROY_OZ_TO_GRAMS,
            "source": "metals.live",
        }
    except Exception as e:
        logger.warning(f"metals.live fetch failed: {e}")
        return None


# ── Currency conversion ───────────────────────────────────────────────────────

EXCHANGE_RATES_USD: dict = {}
_fx_cache_time: float = 0

async def get_exchange_rate(currency: str) -> float:
    """Returns how many units of `currency` equal 1 USD."""
    global _fx_cache_time, EXCHANGE_RATES_USD

    if currency == "USD":
        return 1.0

    now = time.time()
    if EXCHANGE_RATES_USD and (now - _fx_cache_time) < CACHE_TTL_SECONDS:
        return EXCHANGE_RATES_USD.get(currency, 1.0)

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get("https://open.er-api.com/v6/latest/USD")
            data = resp.json()
        EXCHANGE_RATES_USD = data.get("rates", {})
        _fx_cache_time = now
        return EXCHANGE_RATES_USD.get(currency, 1.0)
    except Exception as e:
        logger.warning(f"FX fetch failed: {e}")
        return 1.0

async def get_live_metal_prices(currency: str = "USD") -> dict:
    """
    Get live metal prices in the requested currency.
    Returns prices per gram for gold and silver.
    """
    # Get USD prices first
    usd_prices = await get_metal_prices_usd()
    
    # Convert to requested currency
    if currency == "USD":
        return {
            "silver_per_gram": usd_prices["silver_usd_per_gram"],
            "gold_per_gram": usd_prices["gold_usd_per_gram"],
            "source": usd_prices["source"]
        }
    
    # Get exchange rate
    exchange_rate = await get_exchange_rate(currency)
    
    return {
        "silver_per_gram": usd_prices["silver_usd_per_gram"] * exchange_rate,
        "gold_per_gram": usd_prices["gold_usd_per_gram"] * exchange_rate,
        "source": usd_prices["source"]
    }