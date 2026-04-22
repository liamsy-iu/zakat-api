from pydantic import BaseModel, Field
from typing import Optional, Literal

class GoldInput(BaseModel):
    grams_24k: float = Field(default=0, ge=0)
    grams_22k: float = Field(default=0, ge=0)
    grams_18k: float = Field(default=0, ge=0)

class SilverInput(BaseModel):
    grams: float = Field(default=0, ge=0)

class MoneyInput(BaseModel):
    cash_on_hand: float = Field(default=0, ge=0)
    bank_savings: float = Field(default=0, ge=0)
    foreign_currency: float = Field(default=0, ge=0)

class SalaryInput(BaseModel):
    saved_salary: float = Field(default=0, ge=0, description="Saved portion of salary")

class ReceivablesInput(BaseModel):
    amount_within_12_months: float = Field(default=0, ge=0, description="Debts owed TO you collectible within 12 months")

class StocksInput(BaseModel):
    trading_shares_value: float = Field(default=0, ge=0, description="Shares for trading (mudarabah)")
    investment_shares_value: float = Field(default=0, ge=0, description="Investment shares - both types zakatable in Kenya")

class SukukInput(BaseModel):
    number_of_instruments: int = Field(default=0, ge=0)
    market_value_per_instrument: float = Field(default=0, ge=0)

class InvestmentFundsInput(BaseModel):
    number_of_units: int = Field(default=0, ge=0)
    price_per_unit: float = Field(default=0, ge=0)

class LandInput(BaseModel):
    land_for_sale_value: float = Field(default=0, ge=0, description="Land prepared for resale")
    rental_property_value: float = Field(default=0, ge=0, description="Buildings/dwellings for rent")
    rental_income_saved: float = Field(default=0, ge=0, description="Saved rental income from properties")

class CommercialOfferingsInput(BaseModel):
    inventory_value: float = Field(default=0, ge=0, description="Goods held for sale at current market value")

class ZakatRequest(BaseModel):
    currency: Literal["USD", "KES", "SAR", "GBP", "EUR"] = "USD"
    
    # Asset categories
    gold: Optional[GoldInput] = GoldInput()
    silver: Optional[SilverInput] = SilverInput()
    money: Optional[MoneyInput] = MoneyInput()
    salary: Optional[SalaryInput] = SalaryInput()
    receivables: Optional[ReceivablesInput] = ReceivablesInput()
    stocks: Optional[StocksInput] = StocksInput()
    sukuk: Optional[SukukInput] = SukukInput()
    investment_funds: Optional[InvestmentFundsInput] = InvestmentFundsInput()
    land: Optional[LandInput] = LandInput()
    commercial_offerings: Optional[CommercialOfferingsInput] = CommercialOfferingsInput()