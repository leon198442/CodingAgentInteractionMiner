"""Model-family and version threshold validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cai_miner.normalization.schema import ModelInfo, RuleFailure

SUPPORTED_THRESHOLDS = {
    "gpt": 5.0,
    "gemini": 3.0,
    "claude": 4.5,
}


@dataclass(frozen=True)
class ModelValidation:
    normalized_family: str | None
    normalized_version: float | None
    meets_threshold: bool
    failure: RuleFailure | None = None


def validate_model(model: ModelInfo) -> ModelValidation:
    raw = " ".join(part for part in [model.raw, model.provider, model.family, model.version] if part)
    normalized = raw.lower().replace("_", "-")
    family = _detect_family(normalized)
    if family is None:
        return ModelValidation(None, None, False, RuleFailure("R008_UNSUPPORTED_MODEL", "Model family is missing or unsupported."))

    version = _detect_version(normalized, family, model.version)
    if version is None:
        return ModelValidation(family, None, False, RuleFailure("R008_UNSUPPORTED_MODEL", "Model version is missing or cannot be verified."))

    threshold = SUPPORTED_THRESHOLDS[family]
    if version < threshold:
        return ModelValidation(family, version, False, RuleFailure("R008_UNSUPPORTED_MODEL", f"Model {family}-{version:g} is below required threshold {threshold:g}."))

    return ModelValidation(family, version, True)


def _detect_family(text: str) -> str | None:
    for family in SUPPORTED_THRESHOLDS:
        if family in text:
            return family
    return None


def _detect_version(text: str, family: str, explicit_version: str | None) -> float | None:
    candidates = []
    if explicit_version:
        candidates.append(explicit_version)
    candidates.append(text)
    pattern = re.compile(rf"{re.escape(family)}[^0-9]*(\d+(?:\.\d+)?)")
    for candidate in candidates:
        match = pattern.search(candidate.lower())
        if match:
            return float(match.group(1))
        if candidate.replace(".", "", 1).isdigit():
            return float(candidate)
    return None
