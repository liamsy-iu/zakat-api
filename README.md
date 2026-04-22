# Zakat Calculator API

A free, open REST API for calculating Zakat across all major asset classes, based on classical Islamic jurisprudence (majority/Hanafi position).

## Features

- **Full asset coverage** — cash, gold, silver, business inventory, stocks, livestock, agricultural produce, rental income
- **Live nisab** — silver and gold prices fetched in real time for accurate thresholds
- **Multi-currency** — USD, KES, SAR, GBP, EUR
- **Debt deduction** — short-term debts reduce zakatable wealth
- **Livestock in kind** — classical fiqh tables for sheep/goat, cattle, and camel
- **Agriculture** — ʿUshr (10%) and Nisf al-ʿUshr (5%) based on irrigation type
- **Rate limiting** — 60 requests/minute per IP

## Quick Start

```bash
# 1. Clone and enter directory
cd zakat-api

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python -m uvicorn main:app --reload --port 8001
```

Open **http://localhost:8001/docs** for interactive Swagger documentation.

## API Endpoints

| Method | Endpoint                          | Description                           |
| ------ | --------------------------------- | ------------------------------------- |
| POST   | `/zakat/calculate`                | Full Zakat calculation                |
| GET    | `/zakat/nisab`                    | Current nisab threshold (live prices) |
| GET    | `/zakat/livestock/{type}/{count}` | Livestock Zakat                       |
| GET    | `/zakat/rates`                    | All Zakat rates reference             |
| GET    | `/health`                         | Health check                          |

## Example Request

```bash
curl -X POST http://localhost:8001/zakat/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "USD",
    "cash": {
      "cash_on_hand": 500,
      "bank_savings": 8000,
      "foreign_currency": 0
    },
    "gold": {
      "grams_24k": 50,
      "grams_22k": 0,
      "grams_18k": 0
    },
    "silver": { "grams": 400 },
    "short_term_debts": 1000
  }'
```

## Nisab Standard

This API uses the **silver nisab (595g)** — the more inclusive threshold adopted by the majority of contemporary scholars, particularly relevant for lower-income communities.

## Disclaimer

This API is a **calculation guide only**. Always consult a qualified Islamic scholar for your specific circumstances. Livestock and agricultural Zakat in particular have many scholarly differences.

## Built by

**Abdullahi Alinoor** — Software Developer & Islamic Finance Researcher, Islamic University of Madinah
