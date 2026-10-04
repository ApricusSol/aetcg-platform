import time
import logging
import json
import re
from typing import Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config.settings import settings
from pipeline.validation import TicketIngestionSchema
from worker import queue_triage_job
import redis

# Milestone 4: Structured JSON Telemetry Configurations
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("aetcg_telemetry")

app = FastAPI(
    title="Autonomous Enterprise Triage & Compliance Guard (AETCG)",
    version="1.0.0-rc1"
)

# Add CORS middleware with environment-based configuration
origins = ["*"] if settings.APP_ENV == "development" else ["https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# Milestone 6: Redis Connection Pool for In-Memory Caching
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

# Simple in-memory request tracking for rate limiting (use Redis in production)
_request_counts: Dict[str, list] = {}

def check_rate_limit(request: Request) -> bool:
    """Basic rate limiting by IP address"""
    if not settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
        return True

    client_ip = request.client.host
    current_time = time.time()

    # Clean old requests (older than 1 minute)
    if client_ip in _request_counts:
        _request_counts[client_ip] = [
            req_time for req_time in _request_counts[client_ip]
            if current_time - req_time < 60
        ]
    else:
        _request_counts[client_ip] = []

    # Check if rate limit exceeded
    if len(_request_counts[client_ip]) >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
        return False

    # Add current request
    _request_counts[client_ip].append(current_time)
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to enforce rate limiting"""
    # Skip rate limiting for health checks or internal endpoints if needed
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)

    if not check_rate_limit(request):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"}
        )

    response = await call_next(request)
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # In production, add HSTS: response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.post("/api/v1/triage", status_code=status.HTTP_202_ACCEPTED)
async def ingest_ticket(request: Request, payload: TicketIngestionSchema):
    start_time = time.time()
    payload_hash = hash(payload.raw_text)

    # Milestone 6: Optimization / Query Caching Layer
    cached_result = redis_client.get(f"cache:{payload_hash}")
    if cached_result:
        logger.info(json.dumps({
            "event": "cache_hit",
            "latency_ms": (time.time() - start_time) * 1000
        }))
        return json.loads(cached_result)

    # Additional input sanitization beyond PII scrubbing
    # Remove potential script tags or dangerous HTML (basic XSS protection)
    if isinstance(payload.raw_text, str):
        # Remove script tags and their contents
        clean_text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', payload.raw_text, flags=re.IGNORECASE)
        # Remove on* attributes (onclick, onload, etc.)
        clean_text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', clean_text, flags=re.IGNORECASE)
        # Update payload with sanitized text if changes were made
        if clean_text != payload.raw_text:
            payload.raw_text = clean_text
            # Re-hash the sanitized payload
            payload_hash = hash(payload.raw_text)
            # Check cache again with sanitized payload
            cached_result = redis_client.get(f"cache:{payload_hash}")
            if cached_result:
                logger.info(json.dumps({
                    "event": "cache_hit_after_sanitization",
                    "latency_ms": (time.time() - start_time) * 1000
                }))
                return json.loads(cached_result)

    try:
        # Milestone 4: Enqueue task asynchronously to decouple runtime processing
        job = queue_triage_job(payload.model_dump())

        logger.info(json.dumps({
            "event": "ticket_ingested_and_queued",
            "job_id": job.id,
            "latency_ms": (time.time() - start_time) * 1000
        }))
        return {"status": "queued", "job_id": job.id, "message": "Ticket verification initiated."}

    except Exception as e:
        logger.error(json.dumps({"event": "ingestion_failure", "error": str(e)}))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal messaging backbone unreached."
        )

# State Check Endpoint
@app.get("/api/v1/state/{job_id}")
async def get_state(job_id: str):
    # Input validation for job_id
    if not job_id or not isinstance(job_id, str) or len(job_id) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format")

    state_key = f"state:{job_id}"
    ticket_state = redis_client.get(state_key)
    if not ticket_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State vector context unrecovered.")

    return json.loads(ticket_state)

# Milestone 5: Human-In-The-Loop Interactive Webhook Routing
@app.put("/api/v1/approve/{job_id}", status_code=status.HTTP_200_OK)
async def administrative_approval_gate(request: Request, job_id: str, action: str, supervisor_token: str):
    # Input validation
    if not job_id or not isinstance(job_id, str) or len(job_id) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format")

    if action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action. Must be APPROVE or REJECT")

    # Use token from settings instead of hardcoded value
    if supervisor_token != settings.SUPERVISOR_TOKEN:
        logger.warning(json.dumps({
            "event": "unauthorized_gate_access_attempt",
            "job_id": job_id,
            "client_ip": request.client.host if request.client else "unknown"
        }))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized gate access.")

    # Simulate loading state container from database/Redis cache and advancing graph
    state_key = f"state:{job_id}"
    cached_state = redis_client.get(state_key)
    if not cached_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State vector context unrecovered.")

    state = json.loads(cached_state)
    state["human_approval"] = action
    state["status"] = "COMPLETED" if action == "APPROVE" else "REJECTED"

    redis_client.set(state_key, json.dumps(state))

    logger.info(json.dumps({"event": "human_gate_resolved", "job_id": job_id, "decision": action}))
    return {"status": "state_resumed", "final_disposition": state["status"]}
