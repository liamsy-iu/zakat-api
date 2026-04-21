from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class Currency(str, Enum):
    USD = "USD"
    KES = "KES"
    SAR = "SAR"
    GBP = "GBP"
    EUR = "EUR"

class LivestockType(str, Enum):
    SHEEP_GOAT = "sheep_goat"
    CATTLE     = "cattle"
    CAMEL      = "camel"

class AgricultureIrrigationType(str, Enum):
    RAIN_FED   = "rain_fed"    # 10% (ushr)
    IRRIGATED  = "irrigated"   # 5%  (nisf al-ushr)
    MIXED      = "mixed"       # 7.5% (average)


# ── Asset Input Models ─────────────────────────────────────────────────────────

class CashAssets(BaseModel):
    """Cash, bank savings, foreign currency holdings."""
    cash_on_hand:    float = Field(0, ge=0, description="Physical cash held")
    bank_savings:    float = Field(0, ge=0, description="Money in bank accounts")
    foreign_currency:float = Field(0, ge=0, description="Foreign currency (converted to base currency)")

class GoldAssets(BaseModel):
    """Gold holdings in grams."""
    grams_24k: float = Field(0, ge=0, description="24-karat gold in grams")
    grams_22k: float = Field(0, ge=0, description="22-karat gold in grams")
    grams_18k: float = Field(0, ge=0, description="18-karat gold in grams")

class SilverAssets(BaseModel):
    """Silver holdings in grams."""
    grams: float = Field(0, ge=0, description="Silver in grams")

class BusinessAssets(BaseModel):
    """Business inventory and trade goods (valued at market/cost price)."""
    inventory_value:   float = Field(0, ge=0, description="Market value of goods for sale")
    receivables:       float = Field(0, ge=0, description="Money owed to you (expected to be paid)")
    cash_in_business:  float = Field(0, ge=0, description="Cash held for business operations")

class StockAssets(BaseModel):
    """
    Stock/share holdings.
    For trading portfolios: use full market value.
    For long-term holdings: use the zakatable portion (net assets per share × shares held).
    """
    trading_portfolio_value: float = Field(0, ge=0, description="Stocks held for trading — use full market value")
    longterm_zakatable_value: float = Field(0, ge=0, description="Long-term stocks — use net asset value (zakatable portion only)")

class LivestockHolding(BaseModel):
    """Livestock holding for a single animal type."""
    animal_type: LivestockType
    count:       int = Field(0, ge=0, description="Number of animals")

class AgricultureAssets(BaseModel):
    """Agricultural produce harvested this season."""
    produce_kg:       float = Field(0, ge=0, description="Weight of produce in kg")
    irrigation_type:  AgricultureIrrigationType = AgricultureIrrigationType.RAIN_FED
    market_value:     float = Field(0, ge=0, description="Market value of produce (used if kg not available)")

class RentalAssets(BaseModel):
    """Rental income received (not the property value itself)."""
    annual_net_income: float = Field(0, ge=0, description="Net rental income after allowable expenses")


# ── Main Request ──────────────────────────────────────────────────────────────

class ZakatRequest(BaseModel):
    """
    Full Zakat calculation request.
    All monetary values should be in the same currency as `currency`.
    Only include assets you own and that have been held for one lunar year (hawl).
    """
    currency:    Currency = Field(Currency.USD, description="Currency for all monetary values")

    # Asset classes
    cash:        Optional[CashAssets]       = None
    gold:        Optional[GoldAssets]       = None
    silver:      Optional[SilverAssets]     = None
    business:    Optional[BusinessAssets]   = None
    stocks:      Optional[StockAssets]      = None
    livestock:   Optional[list[LivestockHolding]] = None
    agriculture: Optional[AgricultureAssets] = None
    rental:      Optional[RentalAssets]     = None

    # Debts reduce zakatable wealth
    short_term_debts: float = Field(0, ge=0, description="Debts due within the year (deducted from zakatable wealth)")

    class Config:
        json_schema_extra = {
            "example": {
                "currency": "USD",
                "cash": {
                    "cash_on_hand": 500,
                    "bank_savings": 8000,
                    "foreign_currency": 200
                },
                "gold": {
                    "grams_24k": 50,
                    "grams_22k": 0,
                    "grams_18k": 0
                },
                "silver": {"grams": 400},
                "business": {
                    "inventory_value": 5000,
                    "receivables": 1500,
                    "cash_in_business": 2000
                },
                "stocks": {
                    "trading_portfolio_value": 3000,
                    "longterm_zakatable_value": 1000
                },
                "livestock": [
                    {"animal_type": "sheep_goat", "count": 45}
                ],
                "agriculture": {
                    "produce_kg": 700,
                    "irrigation_type": "rain_fed",
                    "market_value": 0
                },
                "rental": {"annual_net_income": 4800},
                "short_term_debts": 1000
            }
        }


# ── Response Models ───────────────────────────────────────────────────────────

class AssetZakatDetail(BaseModel):
    """Breakdown for a single asset class."""
    asset_class:       str
    total_value:       float
    zakat_rate:        str
    zakat_due:         float
    notes:             Optional[str] = None

class NisabInfo(BaseModel):
    silver_nisab_grams:  float
    silver_price_per_gram: float
    nisab_value:         float
    currency:            str
    price_source:        str

class ZakatResponse(BaseModel):
    """Full Zakat calculation result."""
    currency:              str
    nisab:                 NisabInfo
    total_zakatable_wealth:float
    total_debts_deducted:  float
    net_zakatable_wealth:  float
    above_nisab:           bool
    total_zakat_due:       float
    asset_breakdown:       list[AssetZakatDetail]
    livestock_zakat:       Optional[dict] = None
    agriculture_zakat:     Optional[dict] = None
    notes:                 list[str]

class LivestockZakatResponse(BaseModel):
    """Standalone livestock Zakat calculation."""
    animal_type:   str
    count:         int
    zakat_due:     str
    details:       str

class NisabResponse(BaseModel):
    """Current nisab threshold."""
    silver_nisab_grams:    float
    gold_nisab_grams:      float
    silver_price_per_gram: float
    gold_price_per_gram:   float
    silver_nisab_value_usd: float
    gold_nisab_value_usd:  float
    source:                str
    disclaimer:            str
