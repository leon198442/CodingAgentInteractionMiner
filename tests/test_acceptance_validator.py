import json
from pathlib import Path

from cai_miner.normalization.schema import Session
from cai_miner.validation.acceptance_validator import AcceptanceValidator

FIXTURES = Path(__file__).parent / "fixtures"


def load_session(name: str) -> Session:
    return Session.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def failure_ids(result):
    return {failure.rule_id for failure in result.failures}


def test_accepts_valid_session():
    result = AcceptanceValidator().validate(load_session("valid_session.json"))
    assert result.status == "accepted"
    assert result.metrics["effective_turns"] >= 2
    assert result.metrics["tool_pairing_rate_without_tail"] == 1.0
    assert result.metrics["model_meets_threshold"] is True


def test_rejects_session_without_structured_tool_call():
    result = AcceptanceValidator().validate(load_session("invalid_no_tool_call.json"))
    assert result.status == "rejected"
    assert "R003_NO_STRUCTURED_TOOL_CALL" in failure_ids(result)


def test_rejects_bad_first_role():
    result = AcceptanceValidator().validate(load_session("invalid_bad_first_role.json"))
    assert result.status == "rejected"
    assert "R002_BAD_FIRST_ROLE" in failure_ids(result)
