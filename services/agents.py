"""
AI Agent Services for AETCG Platform

This module contains the AI agent implementations for triage and compliance analysis.
Each agent interacts with a configurable LLM endpoint to perform specialized analysis tasks.
"""
import json
import logging
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from config.settings import settings
from app.metrics import (
    LLM_API_CALLS_TOTAL,
    LLM_API_DURATION_SECONDS,
    LLM_API_TOKEN_USAGE,
    increment_counter,
    observe_histogram,
)

logger = logging.getLogger("aetcg_agents")


class TriageAgent:
    """
    Analyzes IT tickets to produce risk scores, categories, and reasoning.

    The agent evaluates ticket content and returns a structured assessment
    including risk level (1-10), category classification, and explanatory verdict.
    """

    def __init__(self, client: Optional[OpenAI] = None):
        """
        Initialize the Triage Agent with optional OpenAI client.

        Args:
            client: Pre-configured OpenAI client. If None, creates new client
                   using settings from configuration.
        """
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

    def analyze(self, target_text: str) -> Dict[str, Any]:
        """
        Analyze IT ticket text to produce risk assessment.

        Args:
            target_text: The sanitized ticket text to analyze

        Returns:
            Dictionary containing:
                - risk_score: Integer from 1-10 indicating risk level
                - category: String classifying the ticket type
                - verdict: String explaining the reasoning behind the assessment

        Note:
            On failure, returns a fallback response with medium risk score
            and UNCLASSIFIED_TIMEOUT category.
        """
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model="gpt-5.4-nano",  # Update this if your endpoint requires a specific model name
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

            # Record successful LLM API call metrics
            call_duration = time.time() - start_time
            increment_counter(LLM_API_CALLS_TOTAL, {"agent_name": "triage", "status": "success"})
            observe_histogram(LLM_API_DURATION_SECONDS, call_duration, {"agent_name": "triage"})

            # Try to extract token usage if available (this depends on the LLM provider)
            # For now, we'll skip token usage as it's not consistently available across providers
            # In a real implementation, you'd extract this from response.usage if available

            logger.debug(f"Triage Agent Result: {raw_result}")
            return self.parse_analysis_result(raw_result)

        except Exception as e:
            # Record failed LLM API call metrics
            call_duration = time.time() - start_time
            increment_counter(LLM_API_CALLS_TOTAL, {"agent_name": "triage", "status": "failure"})
            observe_histogram(LLM_API_DURATION_SECONDS, call_duration, {"agent_name": "triage"})

            logger.error(f"Live LLM call failed at custom endpoint: {str(e)}. Applying fallback.")
            return {
                "risk_score": 5,
                "category": "UNCLASSIFIED_TIMEOUT",
                "verdict": "Network routing timeout encountered during live LLM analysis."
            }

    @staticmethod
    def parse_analysis_result(raw_result: str) -> Dict[str, Any]:
        """
        Parse raw LLM response into structured dictionary.

        Args:
            raw_result: JSON string from LLM response

        Returns:
            Parsed dictionary with risk_score, category, and verdict keys

        Raises:
            json.JSONDecodeError: If raw_result is not valid JSON
        """
        return json.loads(raw_result)


class ComplianceCriticAgent:
    """
    Reviews triage agent output for governance compliance.

    The agent evaluates triage results against governance rules to determine
    if human review is required and provides feedback on the assessment.
    """

    def __init__(self, client: Optional[OpenAI] = None):
        """
        Initialize the Compliance Critic Agent with optional OpenAI client.

        Args:
            client: Pre-configured OpenAI client. If None, creates new client
                   using settings from configuration.
        """
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

    def critique(self, verdict_text: str, risk_score: int) -> Dict[str, Any]:
        """
        Review triage agent output for compliance governance.

        Args:
            verdict_text: The verdict string from TriageAgent analysis
            risk_score: The risk score integer (1-10) from TriageAgent analysis

        Returns:
            Dictionary containing:
                - audit_passed: Boolean indicating if governance review passed
                - feedback: String explaining the compliance decision

        Note:
            On failure, returns fail-safe response based on risk score:
            - High risk (>=7): audit fails, mandating human review
            - Low risk (<7): audit passes, allowing standard routing
        """
        start_time = time.time()
        try:
            user_content = json.dumps({
                "risk_score": risk_score,
                "triage_verdict": verdict_text
            })

            response = self.client.chat.completions.create(
                model="gpt-5.4-nano",  # Update to match your endpoint's model
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

            # Record successful LLM API call metrics
            call_duration = time.time() - start_time
            increment_counter(LLM_API_CALLS_TOTAL, {"agent_name": "critic", "status": "success"})
            observe_histogram(LLM_API_DURATION_SECONDS, call_duration, {"agent_name": "critic"})

            # Try to extract token usage if available (this depends on the LLM provider)
            # For now, we'll skip token usage as it's not consistently available across providers
            # In a real implementation, you'd extract this from response.usage if available

            return self.parse_critique_result(raw_result)

        except Exception as e:
            # Record failed LLM API call metrics
            call_duration = time.time() - start_time
            increment_counter(LLM_API_CALLS_TOTAL, {"agent_name": "critic", "status": "failure"})
            observe_histogram(LLM_API_DURATION_SECONDS, call_duration, {"agent_name": "critic"})

            logger.error(f"Critic Agent custom LLM call failed: {str(e)}. Applying fail-safe fallback.")
            if risk_score >= 7:
                return {"audit_passed": False, "feedback": "FALLBACK TRIGGERED: High score. Human review mandated."}
            return {"audit_passed": True, "feedback": "FALLBACK TRIGGERED: Processing cleared for standard autonomous routing."}

    @staticmethod
    def parse_critique_result(raw_result: str) -> Dict[str, Any]:
        """
        Parse raw LLM response into structured dictionary.

        Args:
            raw_result: JSON string from LLM response

        Returns:
            Parsed dictionary with audit_passed and feedback keys

        Raises:
            json.JSONDecodeError: If raw_result is not valid JSON
        """
        return json.loads(raw_result)

