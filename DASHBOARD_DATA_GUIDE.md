# How to Generate Data for the AETCG Platform Dashboard

This guide explains how to generate test data to populate the AETCG platform dashboard with meaningful metrics.

## Prerequisites

1. **Platform Running**: Ensure the AETCG platform is running:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Worker Running**: Ensure the worker is processing tickets:
   ```bash
   python worker.py
   ```

3. **Redis Available**: Ensure Redis is running and accessible at the configured host/port.

## Quick Start

The easiest way to generate test data is to use the provided script:

```bash
python generate_test_data.py
```

This will present an interactive menu to generate test tickets in various ways.

## Understanding the Dashboard Metrics

The dashboard displays several categories of metrics:

### 1. System Health (Gauges)
- **Redis**: Shows if Redis connection is active (`REDIS_CONNECTED`)
- **LLM API**: Shows if external API is available (`EXTERNAL_API_AVAILABLE`)
- **Worker**: Shows worker health based on its Redis heartbeat (`WORKER_STATUS`; 1 = healthy, 0 = unhealthy)

### 2. Throughput (Counters - rates calculated)
- **Req/sec**: HTTP request rate (`HTTP_REQUESTS_TOTAL`)
- **Tickets/min**: Ticket ingestion rate (`TICKET_INGESTION_TOTAL`)
- **Approvals/min**: Ticket approval rate (`TICKET_APPROVAL_TOTAL`)

### 3. Latency (Histograms - averages shown)
- **Request (ms)**: Average HTTP request duration (`HTTP_REQUEST_DURATION_SECONDS`)
- **Processing (ms)**: Average ticket processing time (`TICKET_PROCESSING_TIME_SECONDS`)
- **LLM API (ms)**: Average LLM API call duration (`LLM_API_DURATION_SECONDS`)

### 4. Queue & Workers (Gauges/Counters)
- **Pending Jobs**: Number of jobs in queue (`QUEUE_DEPTH_JOBS`)
- **Healthy Workers**: Number of healthy workers (`WORKER_STATUS`)
- **Cache Hit %**: Cache effectiveness (`CACHE_HIT_RATIO` gauge)

### 5. Risk Score Distribution (Histogram)
- Shows distribution of ticket risk scores across 1-10 range (`TICKET_RISK_SCORE_DISTRIBUTION`)

### 6. Ticket Categories (Counter)
- Shows count of tickets by category (`TICKET_CATEGORY_TOTAL`)

### 7. Error Rates (Calculated)
- **HTTP 5xx%**: Percentage of HTTP 5xx errors
- **Job Failure%**: Percentage of failed job processing
- **LLM Error%**: Percentage of LLM API failures

## Generating Test Data Effectively

To see meaningful data in the dashboard, you need to generate sufficient volume and variety of test data:

### Recommended Approach

1. **Start with a batch of tickets**:
   ```bash
   python generate_test_data.py
   # Choose option 1, generate 50-100 tickets with 0.2s delay
   ```

2. **Generate approvals** for some tickets to see approval metrics:
   - Note down some job IDs from the ticket generation output
   - Use option 2 to generate approvals

3. **Monitor the dashboard** at `http://localhost:8000/dashboard`

4. **Generate more data continuously** if needed:
   ```bash
   python generate_test_data.py
   # Choose option 3 for continuous generation
   ```

## Manual Testing with curl

You can also manually test endpoints:

### Ingest a Ticket
```bash
curl -X POST "http://localhost:8000/api/v1/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TCK-MANUAL-001",
    "reporter_email": "test@enterprise.com",
    "raw_text": "Manual test ticket for dashboard data"
  }'
```

### Approve a Ticket
```bash
curl -X PUT "http://localhost:8000/api/v1/approve/TICKET-JOB-ID-HERE" \
  -d "action=APPROVE&supervisor_token=SECURE_GOVERNANCE_TOKEN_XYZ"
```

### Check System Status
```bash
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/metrics"
```

## Tips for Better Dashboard Visualization

1. **Generate in batches**: Sending tickets in bursts creates more visible spikes in rate metrics
2. **Mix approvals and rejections**: This creates visible approval/rejection metrics
3. **Wait between batches**: Allows you to see metrics decay and then rise again
4. **Monitor worker logs**: Ensure tickets are actually being processed
5. **Check Redis directly**: Use `redis-cli monitor` to see queue activity

## Expected Dashboard Behavior

As you generate test data:

- **System Health**: Should show all green/healthy if services are running
- **Throughput Metrics**: Should show increasing rates as you send requests
- **Latency Metrics**: Should show processing times (mostly from simulated delays)
- **Queue Metrics**: Should show fluctuating pending jobs as tickets are processed
- **Cache Metrics**: Should show improved hit ratio as duplicate tickets are sent
- **Distribution Charts**: Should populate as tickets get processed and scored

## Troubleshooting

### No Data Showing in Dashboard?

1. **Check if metrics are enabled**: Verify `METRICS_ENABLED=true` in .env
2. **Check if worker is running**: Tickets won't be processed without the worker
3. **Check Redis connection**: Both API and worker need Redis access
4. **Generate more data**: Very low volume may not register clearly on charts
5. **Check browser console**: Look for JavaScript errors in dashboard loading

### Metrics Not Updating?

1. **Verify endpoint accessibility**: Can you reach `/metrics` endpoint?
2. **Check Prometheus format**: The metrics endpoint should return plain text
3. **Look at raw metrics**: Visit `http://localhost:8000/metrics` directly
4. **Check application logs**: Look for errors in metric recording

## Test Data Generator Features

The `generate_test_data.py` script includes:

- **Interactive menu**: Easy selection of generation modes
- **Realistic ticket data**: Varied descriptions, ticket IDs, and email addresses
- **Configurable delays**: Prevent overwhelming the system
- **Approval generation**: Create approval/rejection actions for tickets
- **Continuous mode**: Generate data indefinitely until stopped
- **Error handling**: Graceful handling of connection issues
- **Progress tracking**: Clear feedback on generation success rates

## Safety Notes

- The test data uses clearly identifiable test patterns (TCK-TEST- prefix)
- All emails use the @enterprise.com domain to pass validation
- Designed to be safe for development/test environments
- Not intended for production use without modification

---

Happy testing! Generate plenty of data and watch those dashboard metrics come alive! 🚀