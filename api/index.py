from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import math
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

with open(DATA_PATH, "r") as f:
    data = json.load(f)

@app.get("/")
def home():
    return {"message": "POST to /api"}

@app.post("/api")
async def analytics(request: Request):
    body = await request.json()

    regions = body["regions"]
    threshold = body["threshold_ms"]

    result = {}

    for region in regions:
        rows = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime"] for r in rows]

        latencies_sorted = sorted(latencies)
        p95_index = math.ceil(0.95 * len(latencies_sorted)) - 1

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": latencies_sorted[p95_index],
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(1 for x in latencies if x > threshold)
        }

    return result
