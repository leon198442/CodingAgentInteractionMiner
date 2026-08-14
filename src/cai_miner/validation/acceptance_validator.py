"""Hard-rule acceptance validation for normalized sessions."""

from __future__ import annotations

from cai_miner.normalization.schema import RuleFailure, Session, ValidationResult
from cai_miner.quality.synthetic_detector import detect_synthetic
from cai_miner.sessionization.turn_counter import count_effective_turns, machine_turn_ratio
from cai_miner.validation.model_validator import validate_model
from cai_miner.validation.tool_validator import validate_tools


class AcceptanceValidator:
    """Validate one normalized coding-agent session against hard acceptance rules."""

    def validate(self, session: Session) -> ValidationResult:
        failures: list[RuleFailure] = []
        warnings: list[RuleFailure] = []
        metrics: dict[str, object] = {}

        if not session.session_id:
            failures.append(RuleFailure("R000_MISSING_SESSION_ID", "Session is missing session_id."))

        effective_turns = count_effective_turns(session.messages)
        metrics["effective_turns"] = effective_turns
        if effective_turns < 2:
            failures.append(RuleFailure("R001_MIN_TURNS", "Session has fewer than two effective turns."))

        first_role = session.messages[0].role if session.messages else None
        metrics["first_role"] = first_role
        if first_role in {"assistant", "tool"} or first_role is None:
            failures.append(RuleFailure("R002_BAD_FIRST_ROLE", "First message role must not be assistant or tool."))

        machine_turns, user_turns, ratio = machine_turn_ratio(session.messages)
        metrics.update({"machine_turns": machine_turns, "user_turns": user_turns, "machine_turn_ratio": ratio})
        if ratio >= 0.25:
            failures.append(RuleFailure("R007_MACHINE_TURN_RATIO_HIGH", "Machine turn ratio must be less than 25%."))

        model_validation = validate_model(session.model)
        metrics.update(
            {
                "model_family": model_validation.normalized_family,
                "model_version": model_validation.normalized_version,
                "model_meets_threshold": model_validation.meets_threshold,
            }
        )
        if model_validation.failure:
            failures.append(model_validation.failure)

        tool_validation = validate_tools(session)
        failures.extend(tool_validation.failures)
        metrics.update(tool_validation.metrics)

        synthetic_detection = detect_synthetic(session)
        failures.extend(synthetic_detection.failures)
        warnings.extend(synthetic_detection.warnings)
        metrics["synthetic_signals"] = synthetic_detection.signals

        score = 100 if not failures else 0
        status = "accepted" if not failures else "rejected"
        return ValidationResult(
            session_id=session.session_id,
            status=status,
            score=score,
            failures=failures,
            warnings=warnings,
            metrics=metrics,
        )
