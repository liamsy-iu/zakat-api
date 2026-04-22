"""Zakat calculation engine based on Islamic jurisprudence."""
from typing import Dict, Any, List

# Silver nisab standard: 595 grams
SILVER_NISAB_GRAMS = 595.0

# Standard Zakat rate: 2.5% (1/40)
STANDARD_ZAKAT_RATE = 0.025

def calculate_gold_value(gold_data: Dict, gold_price_per_gram: float) -> float:
    """Calculate total value of gold holdings."""
    grams_24k = gold_data.get('grams_24k', 0) or 0
    grams_22k = gold_data.get('grams_22k', 0) or 0
    grams_18k = gold_data.get('grams_18k', 0) or 0
    
    # Adjust for purity (24k = 100%, 22k = 91.67%, 18k = 75%)
    pure_gold_grams = (grams_24k * 1.0) + (grams_22k * 0.9167) + (grams_18k * 0.75)
    
    return pure_gold_grams * gold_price_per_gram

def calculate_silver_value(silver_data: Dict, silver_price_per_gram: float) -> float:
    """Calculate total value of silver holdings."""
    grams = silver_data.get('grams', 0) or 0
    return grams * silver_price_per_gram

def calculate_money_value(money_data: Dict) -> float:
    """Calculate total liquid money."""
    cash = money_data.get('cash_on_hand', 0) or 0
    savings = money_data.get('bank_savings', 0) or 0
    foreign = money_data.get('foreign_currency', 0) or 0
    return cash + savings + foreign

def calculate_salary_value(salary_data: Dict) -> float:
    """Calculate saved salary."""
    return salary_data.get('saved_salary', 0) or 0

def calculate_receivables_value(receivables_data: Dict) -> float:
    """Calculate receivables (debts owed TO you)."""
    return receivables_data.get('amount_within_12_months', 0) or 0

def calculate_stocks_value(stocks_data: Dict) -> float:
    """Calculate total stock value - both types zakatable in Kenya."""
    trading = stocks_data.get('trading_shares_value', 0) or 0
    investment = stocks_data.get('investment_shares_value', 0) or 0
    return trading + investment

def calculate_sukuk_value(sukuk_data: Dict) -> float:
    """Calculate Sukuk investment value."""
    units = sukuk_data.get('number_of_instruments', 0) or 0
    price = sukuk_data.get('market_value_per_instrument', 0) or 0
    return units * price

def calculate_investment_funds_value(funds_data: Dict) -> float:
    """Calculate investment funds value."""
    units = funds_data.get('number_of_units', 0) or 0
    price = funds_data.get('price_per_unit', 0) or 0
    return units * price

def calculate_land_value(land_data: Dict) -> float:
    """Calculate land and rental property value."""
    sale_value = land_data.get('land_for_sale_value', 0) or 0
    rental_property = land_data.get('rental_property_value', 0) or 0
    rental_income = land_data.get('rental_income_saved', 0) or 0
    return sale_value + rental_property + rental_income

def calculate_commercial_offerings_value(offerings_data: Dict) -> float:
    """Calculate commercial inventory value."""
    return offerings_data.get('inventory_value', 0) or 0

def calculate_zakat(
    currency: str,
    gold: Dict,
    silver: Dict,
    money: Dict,
    salary: Dict,
    receivables: Dict,
    stocks: Dict,
    sukuk: Dict,
    investment_funds: Dict,
    land: Dict,
    commercial_offerings: Dict,
    gold_price_per_gram: float,
    silver_price_per_gram: float
) -> Dict[str, Any]:
    """
    Calculate Zakat based on all asset categories.
    """
    
    # Calculate nisab threshold (595g of silver)
    nisab_value = SILVER_NISAB_GRAMS * silver_price_per_gram
    
    # Calculate each asset category
    asset_breakdown = []
    
    gold_value = calculate_gold_value(gold, gold_price_per_gram)
    if gold_value > 0:
        asset_breakdown.append({
            "asset_class": "Gold (for savings)",
            "total_value": gold_value,
            "zakat_rate": "2.5%",
            "zakat_due": gold_value * STANDARD_ZAKAT_RATE
        })
    
    silver_value = calculate_silver_value(silver, silver_price_per_gram)
    if silver_value > 0:
        asset_breakdown.append({
            "asset_class": "Silver (for savings)",
            "total_value": silver_value,
            "zakat_rate": "2.5%",
            "zakat_due": silver_value * STANDARD_ZAKAT_RATE
        })
    
    money_value = calculate_money_value(money)
    if money_value > 0:
        asset_breakdown.append({
            "asset_class": "Money (cash & bank accounts)",
            "total_value": money_value,
            "zakat_rate": "2.5%",
            "zakat_due": money_value * STANDARD_ZAKAT_RATE
        })
    
    salary_value = calculate_salary_value(salary)
    if salary_value > 0:
        asset_breakdown.append({
            "asset_class": "Saved Salary",
            "total_value": salary_value,
            "zakat_rate": "2.5%",
            "zakat_due": salary_value * STANDARD_ZAKAT_RATE
        })
    
    receivables_value = calculate_receivables_value(receivables)
    if receivables_value > 0:
        asset_breakdown.append({
            "asset_class": "Receivables (debts owed to you)",
            "total_value": receivables_value,
            "zakat_rate": "2.5%",
            "zakat_due": receivables_value * STANDARD_ZAKAT_RATE
        })
    
    stocks_value = calculate_stocks_value(stocks)
    if stocks_value > 0:
        asset_breakdown.append({
            "asset_class": "Stocks (trading & investment)",
            "total_value": stocks_value,
            "zakat_rate": "2.5%",
            "zakat_due": stocks_value * STANDARD_ZAKAT_RATE
        })
    
    sukuk_value = calculate_sukuk_value(sukuk)
    if sukuk_value > 0:
        asset_breakdown.append({
            "asset_class": "Sukuk (investment instruments)",
            "total_value": sukuk_value,
            "zakat_rate": "2.5%",
            "zakat_due": sukuk_value * STANDARD_ZAKAT_RATE
        })
    
    funds_value = calculate_investment_funds_value(investment_funds)
    if funds_value > 0:
        asset_breakdown.append({
            "asset_class": "Investment Funds",
            "total_value": funds_value,
            "zakat_rate": "2.5%",
            "zakat_due": funds_value * STANDARD_ZAKAT_RATE
        })
    
    land_value = calculate_land_value(land)
    if land_value > 0:
        asset_breakdown.append({
            "asset_class": "Land & Rental Properties",
            "total_value": land_value,
            "zakat_rate": "2.5%",
            "zakat_due": land_value * STANDARD_ZAKAT_RATE
        })
    
    commercial_value = calculate_commercial_offerings_value(commercial_offerings)
    if commercial_value > 0:
        asset_breakdown.append({
            "asset_class": "Commercial Offerings (inventory)",
            "total_value": commercial_value,
            "zakat_rate": "2.5%",
            "zakat_due": commercial_value * STANDARD_ZAKAT_RATE
        })
    
    # Calculate totals
    total_zakatable_wealth = sum(item["total_value"] for item in asset_breakdown)
    total_zakat_due = sum(item["zakat_due"] for item in asset_breakdown)
    above_nisab = total_zakatable_wealth >= nisab_value
    
    # Notes
    notes = []
    if not above_nisab:
        notes.append(f"Total wealth ({total_zakatable_wealth:.2f} {currency}) is below nisab threshold ({nisab_value:.2f} {currency}). No Zakat is due.")
    notes.append("Gold and silver Zakat applies only to savings, not jewelry for personal use.")
    notes.append("Receivables: Only debts owed TO you that are collectible within 12 months.")
    notes.append("In Kenya, both trading and investment shares are zakatable.")
    
    return {
        "currency": currency,
        "nisab": {
            "silver_nisab_grams": SILVER_NISAB_GRAMS,
            "silver_price_per_gram": round(silver_price_per_gram, 2),
            "nisab_value": round(nisab_value, 2),
            "price_source": "Live market data"
        },
        "total_zakatable_wealth": round(total_zakatable_wealth, 2),
        "above_nisab": above_nisab,
        "total_zakat_due": round(total_zakat_due, 2) if above_nisab else 0,
        "asset_breakdown": asset_breakdown if above_nisab else [],
        "notes": notes
    }