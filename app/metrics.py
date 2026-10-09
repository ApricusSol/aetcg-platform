"""
Prometheus metrics collection for AETCG platform.
This module provides standardized metrics collection throughout the application.
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import threading
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aetcg_metrics")

# Create a custom registry to avoid conflicts with other libraries
REGISTRY = CollectorRegistry()

# Application Performance Metrics
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'http_version'],
    registry=REGISTRY
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

HTTP_REQUEST_SIZE_BYTES = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Workflow & Processing Metrics
TICKET_INGESTION_TOTAL = Counter(
    'ticket_ingestion_total',
    'Total tickets ingested',
    ['status'],  # success, failure
    registry=REGISTRY
)

TICKET_PROCESSING_TOTAL = Counter(
    'ticket_processing_total',
    'Total tickets processed',
    ['status'],  # success, failure
    registry=REGISTRY
)

TICKET_PROCESSING_TIME_SECONDS = Histogram(
    'ticket_processing_time_seconds',
    'Time taken to process a ticket from ingestion to completion',
    ['status'],  # success, failure
    registry=REGISTRY
)

QUEUE_DEPTH_JOBS = Gauge(
    'queue_depth_jobs',
    'Number of pending jobs in queue',
    ['queue_name'],
    registry=REGISTRY
)

QUEUE_PROCESSING_JOBS = Gauge(
    'queue_processing_jobs',
    'Number of jobs currently being processed',
    ['queue_name'],
    registry=REGISTRY
)

QUEUE_FAILED_JOBS_TOTAL = Counter(
    'queue_failed_jobs_total',
    'Total number of failed jobs',
    ['queue_name', 'failure_reason'],
    registry=REGISTRY
)

WORKER_STATUS = Gauge(
    'worker_status',
    'Worker health (1=healthy, 0=unhealthy)',
    ['worker_id'],
    registry=REGISTRY
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio (hits/(hits+misses))',
    ['cache_type'],
    registry=REGISTRY
)

CACHE_HITS_TOTAL = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=REGISTRY
)

CACHE_MISSES_TOTAL = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=REGISTRY
)

# LLM API Metrics
LLM_API_CALLS_TOTAL = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['agent_name', 'status'],  # success, failure
    registry=REGISTRY
)

LLM_API_DURATION_SECONDS = Histogram(
    'llm_api_duration_seconds',
    'LLM API call duration in seconds',
    ['agent_name'],
    registry=REGISTRY
)

LLM_API_TOKEN_USAGE = Histogram(
    'llm_api_token_usage',
    'LLM API token usage',
    ['agent_name', 'token_type'],  # input, output
    registry=REGISTRY
)

# Business Metrics
TICKET_RISK_SCORE_DISTRIBUTION = Histogram(
    'ticket_risk_score_distribution',
    'Distribution of ticket risk scores',
    buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    registry=REGISTRY
)

TICKET_CATEGORY_TOTAL = Counter(
    'ticket_category_total',
    'Total tickets by category',
    ['category'],
    registry=REGISTRY
)

HUMAN_APPROVAL_WAIT_TIME_SECONDS = Histogram(
    'human_approval_wait_time_seconds',
    'Time tickets wait for human approval',
    registry=REGISTRY
)

TICKET_APPROVAL_TOTAL = Counter(
    'ticket_approval_total',
    'Total tickets approved',
    registry=REGISTRY
)

TICKET_REJECTION_TOTAL = Counter(
    'ticket_rejection_total',
    'Total tickets rejected',
    registry=REGISTRY
)

COMPLIANCE_PASS_TOTAL = Counter(
    'compliance_pass_total',
    'Total compliance checks passed',
    registry=REGISTRY
)

COMPLIANCE_FAIL_TOTAL = Counter(
    'compliance_fail_total',
    'Total compliance checks failed',
    registry=REGISTRY
)

# System Health Metrics
REDIS_CONNECTED = Gauge(
    'redis_connected',
    'Redis connection status (1=connected, 0=disconnected)',
    registry=REGISTRY
)

REDIS_LATENCY_SECONDS = Histogram(
    'redis_latency_seconds',
    'Redis operation latency in seconds',
    ['operation'],  # get, set, etc.
    registry=REGISTRY
)

EXTERNAL_API_AVAILABLE = Gauge(
    'external_api_available',
    'External API availability (1=available, 0=unavailable)',
    registry=REGISTRY
)

EXTERNAL_API_LATENCY_SECONDS = Histogram(
    'external_api_latency_seconds',
    'External API call latency in seconds',
    registry=REGISTRY
)

# Process metrics (if psutil is available)
psutil: Any = None
try:
    import psutil  # type: ignore[import-not-found]
    PROCESS_CPU_SECONDS = Counter(
        'process_cpu_seconds',
        'Process CPU time spent',
        registry=REGISTRY
    )

    PROCESS_RESIDENT_MEMORY_BYTES = Gauge(
        'process_resident_memory_bytes',
        'Process resident memory size in bytes',
        registry=REGISTRY
    )

    PROCESS_OPEN_FILES = Gauge(
        'process_open_files',
        'Number of open file descriptors',
        registry=REGISTRY
    )

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, process metrics disabled")

# Thread lock for thread-safe operations
_LOCK = threading.Lock()


def increment_counter(counter: Counter, labels: Optional[Dict[str, str]] = None, amount: float = 1):
    """
    Safely increment a counter with optional labels.

    Args:
        counter: Prometheus Counter instance
        labels: Dictionary of label names and values
        amount: Amount to increment by (default: 1)
    """
    with _LOCK:
        if labels:
            counter.labels(**labels).inc(amount)
        else:
            counter.inc(amount)


def observe_histogram(histogram: Histogram, value: float, labels: Optional[Dict[str, str]] = None):
    """
    Safely observe a value in a histogram with optional labels.

    Args:
        histogram: Prometheus Histogram instance
        value: Value to observe
        labels: Dictionary of label names and values
    """
    with _LOCK:
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)


def set_gauge(gauge: Gauge, value: float, labels: Optional[Dict[str, str]] = None):
    """
    Safely set a gauge value with optional labels.

    Args:
        gauge: Prometheus Gauge instance
        value: Value to set
        labels: Dictionary of label names and values
    """
    with _LOCK:
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.

    Returns:
        Bytes containing Prometheus-formatted metrics
    """
    # Update process metrics if psutil is available
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            set_gauge(PROCESS_RESIDENT_MEMORY_BYTES, process.memory_info().rss)
            set_gauge(PROCESS_OPEN_FILES, process.num_fds())
            # Note: CPU time is cumulative, so we increment by the difference
            # This is a simplification - in practice you'd track last measurement
        except Exception as e:
            logger.debug(f"Failed to update process metrics: {e}")

    return generate_latest(REGISTRY)


class MetricsMiddleware:
    """
    Middleware to collect HTTP request metrics.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request information
        method = scope["method"]
        path = scope["path"]
        http_version = scope.get("http_version", "1.1")

        start_time = time.time()

        # Intercept the capture response
        status_code = 500  # Default to error
        response_headers = []

        def send_wrapper(message):
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = message.get("headers", [])
                # Add Prometheus content-type if this is the metrics endpoint
                if path == "/metrics":
                    response_headers.append([b"content-type", b"text/plain; version=0.0.4"])
            elif message["type"] == "http.response.body":
                # Request completed, record metrics
                request_duration = time.time() - start_time

                labels = {
                    "method": method,
                    "endpoint": path,
                    "status_code": str(status_code),
                    "http_version": http_version
                }

                increment_counter(HTTP_REQUESTS_TOTAL, labels)
                observe_histogram(HTTP_REQUEST_DURATION_SECONDS,
                                request_duration,
                                {"method": method, "endpoint": path})

                # Try to get request size (approximate)
                # This is simplified - in practice you'd need to read the body
                observe_histogram(HTTP_REQUEST_SIZE_BYTES, 0,
                                {"method": method, "endpoint": path})
                observe_histogram(HTTP_RESPONSE_SIZE_BYTES, 0,
                                {"method": method, "endpoint": path})

            return send(message)

        await self.app(scope, receive, send_wrapper)