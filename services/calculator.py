"""
Zakat Calculation Engine
========================
Based on classical Islamic jurisprudence (majority/Hanafi positions where noted).

Nisab standard: Silver (612.36g) — more inclusive, widely used.
Zakat rate:     2.5% on most monetary assets.

References:
- Al-Fiqh al-Islami wa Adillatuh (Wahbah al-Zuhayli)
- Reliance of the Traveller (Ahmad ibn Naqib al-Misri)
- AAOIFI Sharia Standards
"""

from models import (
    ZakatRequest, ZakatResponse, AssetZakatDetail,
    NisabInfo, LivestockType, AgricultureIrrigationType
)

# ── Constants ─────────────────────────────────────────────────────────────────

SILVER_NISAB_GRAMS  = 612.36   # 200 dirhams
GOLD_NISAB_GRAMS    = 87.48    # 20 dinars / 85g (some scholars: 87.48g)
TROY_OZ_TO_GRAMS    = 31.1035
STANDARD_RATE       = 0.025    # 2.5%
AGRICULTURE_NISAB_KG = 653.0   # 5 awsuq ≈ 653 kg

# Purity factors for gold karats
GOLD_PURITY = {
    "24k": 1.0,
    "22k": 22/24,
    "18k": 18/24,
}

# ── Livestock Zakat tables ────────────────────────────────────────────────────
# Based on Hanafi/Maliki majority position

def _livestock_zakat_sheep_goat(count: int) -> str:
    """
    Sheep/Goat Zakat (minimum 40 animals).
    40–120:  1 sheep/goat
    121–200: 2 sheep/goats
    201–300: 3 sheep/goats
    Every 100 above 300: +1 sheep/goat
    """
    if count < 40:
        return "No Zakat (below nisab of 40)"
    elif count <= 120:
        return "1 sheep or goat"
    elif count <= 200:
        return "2 sheep or goats"
    elif count <= 300:
        return "3 sheep or goats"
    else:
        base    = 3
        extra   = (count - 300) // 100
        total   = base + extra
        return f"{total} sheep or goats"


def _livestock_zakat_cattle(count: int) -> str:
    """
    Cattle Zakat (minimum 30 animals).
    30–39:  1 tabī' (one-year-old calf)
    40–59:  1 musinnah (two-year-old)
    60–69:  2 tabī'
    Every 30: 1 tabī'; every 40: 1 musinnah
    """
    if count < 30:
        return "No Zakat (below nisab of 30)"
    tabi    = count // 30
    musinna = count // 40
    # Prefer the combination that uses fewer animals
    if count % 30 == 0:
        return f"{tabi} tabī' (one-year-old calves)"
    elif count % 40 == 0:
        return f"{musinna} musinnah (two-year-old cattle)"
    else:
        # Find optimal split
        best = None
        for m in range(count // 40 + 1):
            remainder = count - (m * 40)
            if remainder >= 0 and remainder % 30 == 0:
                t = remainder // 30
                best = (m, t)
                break
        if best:
            m, t = best
            parts = []
            if m: parts.append(f"{m} musinnah")
            if t: parts.append(f"{t} tabī'")
            return " + ".join(parts) if parts else "Consult a scholar"
        return f"Consult a scholar for exact count of {count}"


def _livestock_zakat_camel(count: int) -> str:
    """
    Camel Zakat (minimum 5 camels).
    5–9:   1 sheep/goat
    10–14: 2 sheep/goats
    15–19: 3 sheep/goats
    20–24: 4 sheep/goats
    25–35: 1 bint makhad (1-year she-camel)
    36–45: 1 bint labun (2-year she-camel)
    46–60: 1 hiqqah (3-year she-camel)
    61–75: 1 jadha'ah (4-year she-camel)
    76–90: 2 bint labun
    91–120: 2 hiqqah
    121+:  per 40: 1 bint labun; per 50: 1 hiqqah
    """
    if count < 5:
        return "No Zakat (below nisab of 5)"
    elif count <= 9:  return "1 sheep or goat"
    elif count <= 14: return "2 sheep or goats"
    elif count <= 19: return "3 sheep or goats"
    elif count <= 24: return "4 sheep or goats"
    elif count <= 35: return "1 bint makhad (1-year she-camel)"
    elif count <= 45: return "1 bint labun (2-year she-camel)"
    elif count <= 60: return "1 hiqqah (3-year she-camel)"
    elif count <= 75: return "1 jadha'ah (4-year she-camel)"
    elif count <= 90: return "2 bint labun"
    elif count <= 120: return "2 hiqqah"
    else:
        labun = count // 40
        hiqqah = count // 50
        return f"Per 40 camels: 1 bint labun ({labun} total) OR per 50: 1 hiqqah ({hiqqah} total) — consult a scholar"


# ── Main calculation function ─────────────────────────────────────────────────

async def calculate_zakat(req: ZakatRequest, prices: dict, fx_rate: float) -> ZakatResponse:
    """
    Orchestrates the full Zakat calculation.
    `prices`  — silver/gold price in USD per gram
    `fx_rate` — how many units of req.currency = 1 USD
    """
    silver_usd = prices["silver_usd_per_gram"]
    gold_usd   = prices["gold_usd_per_gram"]

    # Convert metal prices to user's currency
    silver_per_gram = silver_usd * fx_rate
    gold_per_gram   = gold_usd   * fx_rate

    # Nisab in user's currency (silver standard)
    nisab_value = SILVER_NISAB_GRAMS * silver_per_gram

    nisab_info = NisabInfo(
        silver_nisab_grams    = SILVER_NISAB_GRAMS,
        silver_price_per_gram = round(silver_per_gram, 4),
        nisab_value           = round(nisab_value, 2),
        currency              = req.currency,
        price_source          = prices.get("source", "unknown"),
    )

    breakdown: list[AssetZakatDetail] = []
    notes:     list[str]              = []
    total_zakatable = 0.0
    total_zakat     = 0.0

    # ── 1. Cash & Savings ────────────────────────────────────────────────────
    if req.cash:
        c = req.cash
        value = c.cash_on_hand + c.bank_savings + c.foreign_currency
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Cash & Savings",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = "Includes physical cash, bank savings, and foreign currency holdings.",
        ))

    # ── 2. Gold ──────────────────────────────────────────────────────────────
    if req.gold:
        g = req.gold
        total_gold_grams = (
            g.grams_24k * GOLD_PURITY["24k"] +
            g.grams_22k * GOLD_PURITY["22k"] +
            g.grams_18k * GOLD_PURITY["18k"]
        )
        value = total_gold_grams * gold_per_gram
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Gold",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = f"Pure gold equivalent: {round(total_gold_grams, 2)}g at {round(gold_per_gram, 2)} {req.currency}/g. Personal jewellery (for women's adornment) is exempt per many scholars.",
        ))

    # ── 3. Silver ────────────────────────────────────────────────────────────
    if req.silver and req.silver.grams > 0:
        value = req.silver.grams * silver_per_gram
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Silver",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = f"{req.silver.grams}g at {round(silver_per_gram, 4)} {req.currency}/g.",
        ))

    # ── 4. Business Assets ───────────────────────────────────────────────────
    if req.business:
        b = req.business
        value = b.inventory_value + b.receivables + b.cash_in_business
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Business Assets",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = "Trade inventory, receivables (expected to be collected), and business cash. Fixed assets (equipment, property) are NOT zakatable.",
        ))

    # ── 5. Stocks & Investments ──────────────────────────────────────────────
    if req.stocks:
        s = req.stocks
        value = s.trading_portfolio_value + s.longterm_zakatable_value
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Stocks & Investments",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = "Trading stocks: full market value. Long-term holdings: use the zakatable net asset value (liquid assets portion). Consult a scholar for complex portfolios.",
        ))

    # ── 6. Rental Income ─────────────────────────────────────────────────────
    if req.rental and req.rental.annual_net_income > 0:
        value = req.rental.annual_net_income
        zakat = value * STANDARD_RATE
        total_zakatable += value
        total_zakat     += zakat
        breakdown.append(AssetZakatDetail(
            asset_class = "Rental Income",
            total_value = round(value, 2),
            zakat_rate  = "2.5%",
            zakat_due   = round(zakat, 2),
            notes       = "Zakat is on net rental income (after maintenance, mortgage interest where applicable). The property itself is not zakatable.",
        ))

    # ── 7. Agriculture ───────────────────────────────────────────────────────
    agriculture_detail = None
    if req.agriculture and (req.agriculture.produce_kg > 0 or req.agriculture.market_value > 0):
        ag = req.agriculture

        rate_map = {
            AgricultureIrrigationType.RAIN_FED:  (0.10, "10% (ʿUshr — rain-fed)"),
            AgricultureIrrigationType.IRRIGATED: (0.05, "5% (Nisf al-ʿUshr — irrigated)"),
            AgricultureIrrigationType.MIXED:     (0.075, "7.5% (mixed irrigation)"),
        }
        rate, rate_label = rate_map[ag.irrigation_type]

        if ag.produce_kg > 0 and ag.produce_kg < AGRICULTURE_NISAB_KG:
            notes.append(f"Agriculture: {ag.produce_kg}kg is below the nisab of {AGRICULTURE_NISAB_KG}kg — no Zakat due.")
            agriculture_detail = {
                "produce_kg": ag.produce_kg,
                "nisab_kg": AGRICULTURE_NISAB_KG,
                "above_nisab": False,
                "zakat_due": 0,
            }
        else:
            value = ag.market_value if ag.market_value > 0 else 0
            zakat = value * rate if value > 0 else 0
            total_zakat += zakat  # Agriculture Zakat does NOT add to hawl wealth
            agriculture_detail = {
                "produce_kg":      ag.produce_kg,
                "nisab_kg":        AGRICULTURE_NISAB_KG,
                "above_nisab":     True,
                "irrigation_type": ag.irrigation_type,
                "rate":            rate_label,
                "market_value":    round(value, 2),
                "zakat_due":       round(zakat, 2),
            }
            notes.append("Agriculture Zakat (ʿUshr) is due at each harvest and is calculated separately from annual hawl Zakat.")

    # ── 8. Livestock ─────────────────────────────────────────────────────────
    livestock_details = []
    if req.livestock:
        for holding in req.livestock:
            if holding.count == 0:
                continue
            if holding.animal_type == LivestockType.SHEEP_GOAT:
                result = _livestock_zakat_sheep_goat(holding.count)
                animal_name = "Sheep / Goat"
            elif holding.animal_type == LivestockType.CATTLE:
                result = _livestock_zakat_cattle(holding.count)
                animal_name = "Cattle / Buffalo"
            else:
                result = _livestock_zakat_camel(holding.count)
                animal_name = "Camel"

            livestock_details.append({
                "animal":    animal_name,
                "count":     holding.count,
                "zakat_due": result,
            })

        if livestock_details:
            notes.append("Livestock Zakat is paid in kind (animals), not cash, and applies to freely grazing animals not used for labour.")

    # ── Deduct debts ─────────────────────────────────────────────────────────
    debts = req.short_term_debts
    net_zakatable = max(0.0, total_zakatable - debts)

    # Check nisab
    above_nisab = net_zakatable >= nisab_value

    # If below nisab, no monetary Zakat (agriculture/livestock are separate)
    if not above_nisab:
        total_zakat = 0.0
        for item in breakdown:
            item.zakat_due = 0.0
        notes.append(f"Your net zakatable wealth ({round(net_zakatable, 2)} {req.currency}) is below the nisab threshold ({round(nisab_value, 2)} {req.currency}). No Zakat is due on monetary assets.")
    else:
        # Recalculate based on net (after debts)
        if debts > 0:
            ratio       = net_zakatable / total_zakatable if total_zakatable > 0 else 1
            total_zakat = net_zakatable * STANDARD_RATE
            for item in breakdown:
                item.zakat_due = round(item.total_value * ratio * STANDARD_RATE, 2)
            notes.append(f"Short-term debts of {round(debts, 2)} {req.currency} have been deducted from your zakatable wealth.")

    notes.append("This calculation is a guide. Consult a qualified Islamic scholar (ʿālim) for your specific circumstances.")
    notes.append("Hawl (lunar year) must have passed on your wealth for Zakat to be obligatory.")

    return ZakatResponse(
        currency               = req.currency,
        nisab                  = nisab_info,
        total_zakatable_wealth = round(total_zakatable, 2),
        total_debts_deducted   = round(debts, 2),
        net_zakatable_wealth   = round(net_zakatable, 2),
        above_nisab            = above_nisab,
        total_zakat_due        = round(total_zakat, 2),
        asset_breakdown        = breakdown,
        livestock_zakat        = {"holdings": livestock_details} if livestock_details else None,
        agriculture_zakat      = agriculture_detail,
        notes                  = notes,
    )
