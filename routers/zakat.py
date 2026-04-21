from fastapi import APIRouter, HTTPException
from models import ZakatRequest, ZakatResponse, NisabResponse, LivestockZakatResponse, LivestockType
from services.calculator import (
    calculate_zakat,
    SILVER_NISAB_GRAMS, GOLD_NISAB_GRAMS,
    _livestock_zakat_sheep_goat, _livestock_zakat_cattle, _livestock_zakat_camel,
)
from services.prices import get_metal_prices_usd, get_exchange_rate

router = APIRouter(prefix="/zakat", tags=["Zakat"])


@router.post(
    "/calculate",
    response_model=ZakatResponse,
    summary="Calculate full Zakat",
    description="""
Calculate Zakat across all asset classes.

**Asset classes supported:**
- Cash, bank savings, foreign currency
- Gold (24k, 22k, 18k)
- Silver
- Business inventory, receivables, cash in business
- Stocks (trading + long-term)
- Livestock (sheep/goat, cattle, camel)
- Agricultural produce
- Rental income

**Nisab standard:** Silver (612.36g) — the more inclusive threshold used by the majority.

**Currency:** All monetary values must be in the same currency. Supported: USD, KES, SAR, GBP, EUR.

**Note:** This is a calculation guide. Consult a qualified scholar for your specific situation.
""",
)
async def calculate(req: ZakatRequest):
    try:
        prices  = await get_metal_prices_usd()
        fx_rate = await get_exchange_rate(req.currency)
        return await calculate_zakat(req, prices, fx_rate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get(
    "/nisab",
    response_model=NisabResponse,
    summary="Get current Nisab threshold",
    description="Returns the current Nisab threshold in USD based on live silver and gold prices.",
)
async def get_nisab():
    try:
        prices = await get_metal_prices_usd()
        silver = prices["silver_usd_per_gram"]
        gold   = prices["gold_usd_per_gram"]
        return NisabResponse(
            silver_nisab_grams     = SILVER_NISAB_GRAMS,
            gold_nisab_grams       = GOLD_NISAB_GRAMS,
            silver_price_per_gram  = round(silver, 4),
            gold_price_per_gram    = round(gold, 4),
            silver_nisab_value_usd = round(SILVER_NISAB_GRAMS * silver, 2),
            gold_nisab_value_usd   = round(GOLD_NISAB_GRAMS   * gold,   2),
            source                 = prices.get("source", "unknown"),
            disclaimer             = "Prices are fetched from public APIs and may be slightly delayed. Not financial advice.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/livestock/{animal_type}/{count}",
    summary="Calculate livestock Zakat",
    description="""
Calculate Zakat due on livestock.

**Animal types:** `sheep_goat`, `cattle`, `camel`

**Nisab (minimum):**
- Sheep/Goat: 40 animals
- Cattle:     30 animals
- Camel:      5 camels

Livestock Zakat is paid in kind (animals), not cash.
""",
)
async def livestock_zakat(animal_type: LivestockType, count: int):
    if count < 0:
        raise HTTPException(status_code=400, detail="Count must be non-negative.")

    if animal_type == LivestockType.SHEEP_GOAT:
        result = _livestock_zakat_sheep_goat(count)
        name   = "Sheep / Goat"
        detail = "Nisab: 40 animals. Zakat is paid in kind. Based on Hanafi/majority position."
    elif animal_type == LivestockType.CATTLE:
        result = _livestock_zakat_cattle(count)
        name   = "Cattle / Buffalo"
        detail = "Nisab: 30 cattle. Zakat paid as calves (tabī' or musinnah). Based on Hanafi/majority position."
    else:
        result = _livestock_zakat_camel(count)
        name   = "Camel"
        detail = "Nisab: 5 camels. Zakat is paid as smaller animals for lower counts, then she-camels for higher counts."

    return {
        "animal_type": name,
        "count":       count,
        "zakat_due":   result,
        "details":     detail,
        "note":        "Applies to freely grazing animals not used for labour or income-generating work.",
    }


@router.get(
    "/rates",
    summary="Get Zakat rates reference",
    description="Returns all Zakat rates and thresholds for reference.",
)
async def get_rates():
    return {
        "standard_rate": "2.5%",
        "nisab_standard": "Silver (612.36g) — more inclusive",
        "asset_rates": {
            "cash_and_savings":  "2.5%",
            "gold":              "2.5% of market value",
            "silver":            "2.5% of market value",
            "business_assets":   "2.5% (inventory + receivables + cash)",
            "stocks_trading":    "2.5% of market value",
            "stocks_longterm":   "2.5% of net zakatable assets",
            "rental_income":     "2.5% of net annual income",
            "agriculture_rain":  "10% (ʿUshr) of produce value",
            "agriculture_irrig": "5% (Nisf al-ʿUshr) of produce value",
            "agriculture_mixed": "7.5% of produce value",
            "livestock":         "In kind — see /zakat/livestock endpoint",
        },
        "livestock_nisab": {
            "sheep_goat": "40 animals",
            "cattle":     "30 animals",
            "camel":      "5 camels",
        },
        "agriculture_nisab": "653 kg (5 awsuq)",
        "note": "Rates based on classical fiqh — Hanafi/majority position. Consult a scholar for your specific situation.",
    }
