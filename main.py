from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from routers import zakat
import logging
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Zakat Calculator API",
    description="""
## Zakat Calculator API

A free, open Zakat calculation API based on classical Islamic jurisprudence.

### Features
- ✅ Full asset coverage: cash, gold, silver, business, stocks, livestock, agriculture, rental income
- ✅ Live silver & gold prices for accurate nisab thresholds
- ✅ Multi-currency support (USD, KES, SAR, GBP, EUR)
- ✅ Silver nisab standard (612.36g) — more inclusive, widely used
- ✅ Livestock Zakat in kind (per classical fiqh tables)
- ✅ Agriculture Zakat (ʿUshr / Nisf al-ʿUshr)
- ✅ Debt deduction from zakatable wealth

### Important Disclaimer
This API is a **guide only**. It implements the majority/Hanafi position for most rulings.
Always consult a qualified Islamic scholar (ʿālim) for your specific circumstances.

### Built by
Abdullahi Alinoor — Software Developer & Islamic Finance Researcher
""",
    version="1.0.0",
    contact={
        "name":  "Abdullahi Alinoor",
        "url":   "https://abdullahialinoor.com",
        "email": "hello@abdullahialinoor.com",
    },
    license_info={
        "name": "MIT",
        "url":  "https://opensource.org/licenses/MIT",
    },
)

# ── Rate limit handler ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(zakat.router)

# ── Root & health ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "name":        "Zakat Calculator API",
        "version":     "1.0.0",
        "docs":        "/docs",
        "endpoints": {
            "calculate": "POST /zakat/calculate",
            "nisab":     "GET  /zakat/nisab",
            "livestock": "GET  /zakat/livestock/{animal_type}/{count}",
            "rates":     "GET  /zakat/rates",
        }
    }

@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy"}

# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
