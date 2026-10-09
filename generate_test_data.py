#!/usr/bin/env python3
"""
Test data generator for AETCG platform.
This script generates test tickets to populate the dashboard with meaningful data.
"""
import json
import time
import requests
import random
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPERVISOR_TOKEN = "SECURE_GOVERNANCE_TOKEN_XYZ"  # Must match .env file

# Test data templates
TICKET_TEMPLATES = [
    {
        "ticket_id": "TCK-{prefix}-{seq:04d}",
        "reporter_email": "{name}@enterprise.com",
        "raw_text": "{description}"
    }
]

NAMES = [
    "alice", "bob", "charlie", "diana", "eve", "frank", "grace", "henry",
    "iris", "jack", "karen", "leo", "mia", "nathan", "olivia", "peter",
    "quinn", "rachel", "sam", "tina", "umar", "victoria", "walt", "xena",
    "yara", "zach"
]

DESCRIPTIONS = [
    "User reported slow application response times during peak hours.",
    "Database connection pool exhaustion observed in monitoring alerts.",
    "Security audit flagged potential vulnerability in authentication module.",
    "Customer complaint regarding incorrect billing amount on invoice #{}.",
    "System logs show repeated timeout errors when accessing external API.",
    "Memory leak detected in Java application causing OOM crashes.",
    "Network latency spikes observed between web and application tiers.",
    "Failed deployment due to missing environment configuration variables.",
    "Data backup job failed repeatedly over the last 24 hours.",
    "SSL certificate expiration warning for domain *.example.com",
    "Unexpected restart of microservice container in Kubernetes cluster.",
    "Queue backup detected - message processing lag exceeds threshold.",
    "Cache miss ratio increased significantly affecting response times.",
    "Disk space alert: /var/log directory at 95% capacity.",
    "Failed login attempts spike suggests potential brute force attack.",
    "API rate limit exceeded for third-party service integration.",
    "Inconsistent data observed between primary and replica databases.",
    "Service health check failures detected in load balancer logs.",
    "Configuration drift detected between staging and production environments.",
    "User session timeout issues reported in mobile application.",
    "Email notification service experiencing delivery delays.",
    "File upload functionality failing for files larger than 100MB.",
    "Search functionality returning irrelevant results for specific queries.",
    "Payment processing gateway returning intermittent timeout errors.",
    "Log aggregation service falling behind by approximately 15 minutes.",
    "Container image scan reveals outdated base image with security patches.",
    "Feature flag configuration causing unexpected behavior in production.",
    "Database query performance degradation observed after schema migration."
]

def generate_ticket_data(seq_num):
    """Generate a single ticket data payload"""
    template = random.choice(TICKET_TEMPLATES)
    name = random.choice(NAMES)
    description = random.choice(DESCRIPTIONS).format(random.randint(1000, 9999))

    ticket_id = template["ticket_id"].format(prefix="TEST", seq=seq_num)
    reporter_email = template["reporter_email"].format(name=name)
    raw_text = template["raw_text"].format(description=description)

    return {
        "ticket_id": ticket_id,
        "reporter_email": reporter_email,
        "raw_text": raw_text
    }

def generate_batch_tickets(count, delay_between_requests=0.1):
    """Generate a batch of test tickets"""
    print(f"Generating {count} test tickets...")
    print(f"Target API: {API_BASE_URL}")
    print(f"Delay between requests: {delay_between_requests}s")
    print("-" * 50)

    successful = 0
    failed = 0

    for i in range(count):
        ticket_data = generate_ticket_data(i + 1)

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/triage",
                json=ticket_data,
                timeout=10
            )

            if response.status_code in [200, 202]:
                successful += 1
                if (i + 1) % 10 == 0 or i == 0:
                    print(f"[{i+1:3d}/{count}] ✓ {ticket_data['ticket_id']} - {response.status_code}")
            else:
                failed += 1
                print(f"[{i+1:3d}/{count}] ✗ {ticket_data['ticket_id']} - {response.status_code}")

        except requests.exceptions.RequestException as e:
            failed += 1
            print(f"[{i+1:3d}/{count}] ✗ {ticket_data['ticket_id']} - Error: {str(e)}")

        # Delay between requests to avoid overwhelming the system
        if delay_between_requests > 0:
            time.sleep(delay_between_requests)

    print("-" * 50)
    print(f"Results: {successful} successful, {failed} failed")
    print(f"Success rate: {(successful/count)*100:.1f}%")

    return successful, failed

def generate_approval_tickets(job_ids, approval_rate=0.7):
    """Generate approval actions for existing jobs"""
    print(f"Generating approvals for {len(job_ids)} jobs...")
    print(f"Approval rate: {approval_rate*100:.0f}%")
    print("-" * 50)

    approved = 0
    rejected = 0
    failed = 0

    for job_id in job_ids:
        # Randomly decide to approve or reject based on approval_rate
        action = "APPROVE" if random.random() < approval_rate else "REJECT"

        try:
            response = requests.put(
                f"{API_BASE_URL}/api/v1/approve/{job_id}",
                params={
                    "action": action,
                    "supervisor_token": SUPERVISOR_TOKEN
                },
                timeout=10
            )

            if response.status_code == 200:
                if action == "APPROVE":
                    approved += 1
                    print(f"[{job_id}] ✓ Approved")
                else:
                    rejected += 1
                    print(f"[{job_id}] ✗ Rejected")
            else:
                failed += 1
                print(f"[{job_id}] ✗ {action} failed - {response.status_code}")

        except requests.exceptions.RequestException as e:
            failed += 1
            print(f"[{job_id}] ✗ {action} failed - Error: {str(e)}")

    print("-" * 50)
    print(f"Results: {approved} approved, {rejected} rejected, {failed} failed")

    return approved, rejected, failed

def check_system_status():
    """Check if the system is ready to accept test data"""
    try:
        # Check health endpoint
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Health check failed")
            return False

        health_data = health_response.json()
        if health_data.get("status") != "healthy":
            print(f"❌ System unhealthy: {health_data}")
            return False

        # Check metrics endpoint
        metrics_response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        if metrics_response.status_code != 200:
            print("❌ Metrics endpoint not accessible")
            return False

        print("✅ System health check passed")
        print(f"   Status: {health_data.get('status')}")
        print(f"   Checks: {json.dumps(health_data.get('checks', {}), indent=2)}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to system: {str(e)}")
        return False

def main():
    """Main function to run the test data generator"""
    print("AETCG Platform Test Data Generator")
    print("=" * 50)

    # Check system status first
    if not check_system_status():
        print("\nPlease ensure the AETCG platform is running and accessible.")
        print("You can start it with: uvicorn main:app --host 0.0.0.0 --port 8000")
        return

    print("\nSelect test data generation option:")
    print("1. Generate batch of test tickets")
    print("2. Generate approvals for existing jobs (requires job IDs)")
    print("3. Continuous ticket generation (press Ctrl+C to stop)")
    print("4. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()

            if choice == "1":
                count = int(input("Number of tickets to generate (default 50): ") or "50")
                delay = float(input("Delay between requests in seconds (default 0.2): ") or "0.2")
                generate_batch_tickets(count, delay)

            elif choice == "2":
                job_ids_input = input("Enter job IDs (comma-separated): ").strip()
                if job_ids_input:
                    job_ids = [jid.strip() for jid in job_ids_input.split(",")]
                    approval_rate = float(input("Approval rate 0.0-1.0 (default 0.7): ") or "0.7")
                    generate_approval_tickets(job_ids, approval_rate)
                else:
                    print("No job IDs provided")

            elif choice == "3":
                print("Starting continuous ticket generation (Press Ctrl+C to stop)...")
                count = 0
                try:
                    while True:
                        batch_size = 10
                        successful, failed = generate_batch_tickets(batch_size, 0.5)
                        count += batch_size
                        print(f"Total tickets generated so far: {count}")
                        time.sleep(2)  # Pause between batches
                except KeyboardInterrupt:
                    print(f"\nStopped. Total tickets generated: {count}")

            elif choice == "4":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()