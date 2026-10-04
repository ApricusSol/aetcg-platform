import json
import redis
from pipeline.validation import DataSanitizationPipeline
from services.agents import TriageAgent, ComplianceCriticAgent
from config.settings import settings

class StateMachineOrchestrator:
    def __init__(self):
        self.scrubber = DataSanitizationPipeline()
        self.triage_agent = TriageAgent()
        self.critic_agent = ComplianceCriticAgent()
        # Use settings for Redis configuration consistently
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )

    def execute_workflow(self, raw_job_data: dict) -> dict:
        # Step 1: Ingestion & Sanitization
        clean_text = self.scrubber.scrub_pii(raw_job_data["raw_text"])

        # State Initialization
        state = {
            "ticket_id": raw_job_data["ticket_id"],
            "sanitized_text": clean_text,
            "risk_score": 0,
            "triage_verdict": "",
            "critic_feedback": "",
            "human_approval": "PENDING",
            "status": "PROCESSING"
        }

        # Step 2: Probabilistic Multi-Agent Analysis Execution Loop
        triage_output = self.triage_agent.analyze(state["sanitized_text"])
        state["risk_score"] = triage_output["risk_score"]
        state["triage_verdict"] = triage_output["verdict"]

        # Step 3: Governance Feedback Iteration Check
        critic_output = self.critic_agent.critique(state["triage_verdict"], state["risk_score"])
        state["critic_feedback"] = critic_output["feedback"]

        # Step 4: Conditional Routing Gate Based on Risk Thresholds
        if state["risk_score"] >= 7:
            state["status"] = "PAUSED_FOR_REVIEW"
            # Serialize state frame to Redis cache to allow human callback resumption
            self.redis_client.set(f"state:{raw_job_data['ticket_id']}", json.dumps(state))
            return state

        state["status"] = "COMPLETED"
        return state