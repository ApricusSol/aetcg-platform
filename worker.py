import json
import logging
from redis import Redis
from rq import Queue, Worker
from config.settings import settings

# Use the same Redis connection pattern as in main.py for consistency
redis_connection = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
task_queue = Queue("aetcg_jobs", connection=redis_connection)

def process_pipeline_task(payload: dict):
    from pipeline.orchestrator import StateMachineOrchestrator
    orchestrator = StateMachineOrchestrator()
    result = orchestrator.execute_workflow(payload)

    # Cache the final state result for API lookup
    redis_connection.set(f"cache:{hash(payload['raw_text'])}", json.dumps(result), ex=600)
    return result

def queue_triage_job(payload: dict):
    return task_queue.enqueue(process_pipeline_task, payload)

if __name__ == "__main__":
    # Internal execution target wrapper matching automated Docker environment activations
    from rq.worker import HerokuWorker as ProductionWorker
    logging.basicConfig(level=logging.INFO)
    print(f"[*] Booting AETCG Background Worker Network Layer connecting to Redis on {settings.REDIS_HOST}...")
    worker = Worker([task_queue], connection=redis_connection)
    worker.work()