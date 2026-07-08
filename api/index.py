from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import re

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


def extract_vendor(text):
    patterns = [
        r"([A-Z][A-Za-z0-9\- ]+ Industries Ltd\.?)",
        r"vendor[:\s]+([A-Za-z0-9\- .&]+)",
        r"from[:\s]+([A-Za-z0-9\- .&]+)",
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip(" .,\n")

    return "Unknown Vendor"


def extract_amount(text):
    m = re.search(
        r"(?:total due|amount due|total|amount)[:\s]*(?:USD|EUR|GBP)?\s*[$€£]?\s*([0-9]+(?:\.[0-9]+)?)",
        text,
        re.I,
    )
    if m:
        return float(m.group(1))

    nums = re.findall(r"\b[0-9]+(?:\.[0-9]+)?\b", text)
    return float(nums[-1]) if nums else 0.0


def extract_currency(text):
    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    if m:
        return m.group(1).upper()

    if "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"

    return "USD"


def extract_date(text):
    m = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)

    return "2026-01-01"


@app.get("/")
def home():
    return {"ok": True}


@app.api_route("/extract", methods=["POST", "OPTIONS"], response_model=ExtractResponse)
async def extract(request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(content={})

    try:
        body = await request.json()
        text = body.get("text", "") if isinstance(body, dict) else ""
    except Exception:
        text = ""

    return ExtractResponse(
        vendor=extract_vendor(text),
        amount=extract_amount(text),
        currency=extract_currency(text),
        date=extract_date(text),
    )
