from fastapi import APIRouter, HTTPException
from models import ZakatRequest
from services.calculator import calculate_zakat
from services.prices import get_live_metal_prices
import logging

router = APIRouter(prefix="/zakat", tags=["Zakat Calculator"])
logger = logging.getLogger(__name__)

@router.post("/calculate")
async def calculate_zakat_endpoint(request: ZakatRequest):
    """
    Calculate Zakat based on all asset categories.
    Silver nisab standard: 595 grams.
    """
    try:
        # Get live metal prices
        prices = await get_live_metal_prices(request.currency)
        
        # Calculate Zakat
        result = calculate_zakat(
            currency=request.currency,
            gold=request.gold.dict() if request.gold else {},
            silver=request.silver.dict() if request.silver else {},
            money=request.money.dict() if request.money else {},
            salary=request.salary.dict() if request.salary else {},
            receivables=request.receivables.dict() if request.receivables else {},
            stocks=request.stocks.dict() if request.stocks else {},
            sukuk=request.sukuk.dict() if request.sukuk else {},
            investment_funds=request.investment_funds.dict() if request.investment_funds else {},
            land=request.land.dict() if request.land else {},
            commercial_offerings=request.commercial_offerings.dict() if request.commercial_offerings else {},
            gold_price_per_gram=prices["gold_per_gram"],
            silver_price_per_gram=prices["silver_per_gram"]
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Zakat calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nisab")
async def get_nisab_threshold(currency: str = "USD"):
    """Get current nisab threshold based on live silver prices (595g standard)."""
    try:
        prices = await get_live_metal_prices(currency)
        nisab_value = 595.0 * prices["silver_per_gram"]
        
        return {
            "currency": currency,
            "silver_nisab_grams": 595.0,
            "silver_price_per_gram": round(prices["silver_per_gram"], 2),
            "nisab_value": round(nisab_value, 2),
            "price_source": "Live market data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rates")
async def get_metal_rates(currency: str = "USD"):
    """Get current gold and silver prices per gram."""
    try:
        prices = await get_live_metal_prices(currency)
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))