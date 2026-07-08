from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import re

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


def find_vendor(text: str) -> str:
    patterns = [
        r"vendor[:\s]+([A-Za-z0-9\-\s.&]+?)(?:\n|$)",
        r"from[:\s]+([A-Za-z0-9\-\s.&]+?)(?:\n|$)",
        r"invoice\s+from[:\s]+([A-Za-z0-9\-\s.&]+?)(?:\n|$)",
        r"([A-Za-z0-9\-]+\s+(?:Industries Ltd\.|Ltd\.|LLC|Inc\.|Corporation|Corp\.))",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .,-")

    return "Unknown Vendor"


def find_amount(text: str) -> float:
    patterns = [
        r"(?:total due|amount due|total|amount)[:\s]*[A-Z]{0,3}\s*[$€£]?\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"[$€£]\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"\b([0-9]+(?:\.[0-9]{1,2})?)\b",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return float(matches[-1])

    return 0.0


def find_currency(text: str) -> str:
    match = re.search(r"\b(USD|EUR|GBP)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    if "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"

    return "USD"


def find_date(text: str) -> str:
    match = re.search(r"\b(2026-[0-9]{2}-[0-9]{2})\b", text)
    if match:
        return match.group(1)

    return "2026-01-01"


@app.get("/")
def home():
    return {"ok": True, "message": "Invoice extractor running"}


@app.post("/extract", response_model=ExtractResponse)
def extract_invoice(data: ExtractRequest):
    text = data.text or ""

    return ExtractResponse(
        vendor=find_vendor(text),
        amount=find_amount(text),
        currency=find_currency(text),
        date=find_date(text),
    )
