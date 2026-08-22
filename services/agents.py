import json
import logging
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger("aetcg_agents")

class TriageAgent:
    def __init__(self, client=None):
        # Point the client to your custom endpoint
        self.client = client or OpenAI(
            base_url=settings.LLM_ENDPOINT_URL,
            api_key=settings.LLM_ACCESS_TOKEN
        )
        self.system_prompt = """
        You are an enterprise IT triage analyzer. 
        Read the IT ticket and return ONLY a valid json object with three keys:
        - "risk_score" (integer 1-10)
        - "category" (string)
        - "verdict" (string explaining your reasoning)
        """

    def analyze(self, target_text: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model="gpt-5.4-nano", # Update this if your endpoint requires a specific model name
                # response_format={ "type": "json_object" }, 
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": target_text}
                ],
                timeout=settings.EXTERNAL_API_TIMEOUT_SEC
            )
            raw_result = response.choices[0].message.content
            if not isinstance(raw_result, str):
                raise ValueError("Triage Agent returned empty or non-string content")
            print(f"Triage Agent Result: {raw_result}")
            return self.parse_analysis_result(raw_result)

        except Exception as e:
            logger.error(f"Live LLM call failed at custom endpoint: {str(e)}. Applying fallback.")
            return {
                "risk_score": 5,
                "category": "UNCLASSIFIED_TIMEOUT",
                "verdict": "Network routing timeout encountered during live LLM analysis."
            }

    @staticmethod
    def parse_analysis_result(raw_result: str) -> dict:
        return json.loads(raw_result)

class ComplianceCriticAgent:
    def __init__(self, client=None):
        # Point the client to your custom endpoint
        self.client = client or OpenAI(
            base_url=settings.LLM_ENDPOINT_URL,
            api_key=settings.LLM_ACCESS_TOKEN
        )
        self.system_prompt = """
        You are a senior enterprise risk auditor. 
        Review the Triage Agent's 'risk_score' and 'verdict'.
        
        Governance Rules:
        1. If risk_score >= 7, set audit_passed to false.
        2. If risk_score < 7, evaluate verdict logic. If routine, set audit_passed to true.
        
        Return ONLY a valid json object with exactly two keys:
        - "audit_passed" (boolean)
        - "feedback" (string)
        """

    def critique(self, verdict_text: str, risk_score: int) -> dict:
        try:
            user_content = json.dumps({
                "risk_score": risk_score,
                "triage_verdict": verdict_text
            })

            response = self.client.chat.completions.create(
                model="gpt-5.4-nano", # Update to match your endpoint's model
                # response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                timeout=settings.EXTERNAL_API_TIMEOUT_SEC
            )
            raw_result = response.choices[0].message.content
            if not isinstance(raw_result, str):
                raise ValueError("Critic Agent returned empty or non-string content")
            return self.parse_critique_result(raw_result)

        except Exception as e:
            logger.error(f"Critic Agent custom LLM call failed: {str(e)}. Applying fail-safe fallback.")
            if risk_score >= 7:
                return {"audit_passed": False, "feedback": "FALLBACK TRIGGERED: High risk score. Human review mandated."}
            return {"audit_passed": True, "feedback": "FALLBACK TRIGGERED: Processing cleared for standard autonomous routing."}

    @staticmethod
    def parse_critique_result(raw_result: str) -> dict:
        return json.loads(raw_result)

