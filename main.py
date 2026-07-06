import time
import uuid
import logging
import json
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

EMAIL = "23f2004770@ds.study.iitm.ac.in"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

startup = time.time()

# Prometheus Counter
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP Requests"
)

# Keep last 1000 logs
logs = deque(maxlen=1000)

logging.basicConfig(level=logging.INFO)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    REQUEST_COUNTER.inc()

    entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id,
    }

    logs.append(entry)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/work")
def work(n: int = 1):
    # simulate work
    for _ in range(max(0, n)):
        pass

    return {
        "email": EMAIL,
        "done": n,
    }


@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "uptime_s": time.time() - startup,
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest().decode(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/logs/tail")
def tail(limit: int = 10):
    limit = max(0, min(limit, len(logs)))
    return list(logs)[-limit:]
