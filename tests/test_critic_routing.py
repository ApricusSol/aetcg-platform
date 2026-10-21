import json
from unittest.mock import MagicMock

from pipeline import orchestrator


def test_failed_compliance_audit_pauses_low_risk_ticket(monkeypatch):
    # Simulate the AI triage response.
    triage = MagicMock()
    triage.analyze.return_value = {
        "risk_score": 3,
        "category": "ROUTINE",
        "verdict": "Low-risk IT support request"
    }

    # Simulate the compliance critic rejecting it.
    critic = MagicMock()
    critic.critique.return_value = {
        "audit_passed": False,
        "feedback": "Governance policy violation"
    }

    # Replace the real agents, avoiding external LLM calls.
    monkeypatch.setattr(
        orchestrator, "TriageAgent", lambda: triage
    )
    monkeypatch.setattr(
        orchestrator, "ComplianceCriticAgent", lambda: critic
    )

    # Replace Redis with an in-memory mock.
    fake_redis = MagicMock()
    monkeypatch.setattr(
        orchestrator.redis, "Redis",
        lambda **kwargs: fake_redis
    )

    workflow = orchestrator.StateMachineOrchestrator()

    result = workflow.execute_workflow({
        "ticket_id": "TCK-F03",
        "raw_text": "Routine support ticket"
    })

    assert result["status"] == "PAUSED_FOR_REVIEW"
    assert result["human_approval"] == "PENDING"

    # A paused result should also be persisted.
    fake_redis.set.assert_called_once()
