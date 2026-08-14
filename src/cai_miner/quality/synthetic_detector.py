"""Deterministic red flags for synthetic, roleplay, and GUI-only sessions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cai_miner.normalization.schema import RuleFailure, Session

PLACEHOLDER_PATTERNS = [
    re.compile(r"/home/user/project", re.IGNORECASE),
    re.compile(r"example\.com", re.IGNORECASE),
    re.compile(r"完整.*系统.*功能清单"),
]
ROLEPLAY_PATTERNS = [re.compile(r"role\s*play", re.IGNORECASE), re.compile(r"角色扮演")]
GUI_PATTERNS = [re.compile(r"\bGUI\b", re.IGNORECASE), re.compile(r"截图"), re.compile(r"界面点击")]


@dataclass(frozen=True)
class SyntheticDetection:
    failures: list[RuleFailure]
    warnings: list[RuleFailure]
    signals: list[str]


def detect_synthetic(session: Session) -> SyntheticDetection:
    text = "\n".join(str(message.content or "") for message in session.messages)
    signals: list[str] = []
    failures: list[RuleFailure] = []
    warnings: list[RuleFailure] = []

    if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
        signals.append("placeholder_or_template_content")
    if any(pattern.search(text) for pattern in ROLEPLAY_PATTERNS):
        signals.append("roleplay_like")
        failures.append(RuleFailure("R009_ROLEPLAY_OR_GUI", "Session appears to be roleplay-like."))
    if any(pattern.search(text) for pattern in GUI_PATTERNS):
        signals.append("gui_scene_like")
        failures.append(RuleFailure("R009_ROLEPLAY_OR_GUI", "Session appears to be GUI-scene-like."))

    if _all_tool_results_successful(session) and _has_tool_results(session):
        signals.append("all_tool_results_successful")

    if len(signals) >= 2 and "placeholder_or_template_content" in signals:
        failures.append(RuleFailure("R010_SYNTHETIC_LIKE", "Session has multiple synthetic-data red flags."))
    elif signals:
        warnings.append(RuleFailure("W_SYNTHETIC_SIGNALS", f"Synthetic-data signals found: {', '.join(signals)}."))

    return SyntheticDetection(failures=failures, warnings=warnings, signals=signals)


def _has_tool_results(session: Session) -> bool:
    return any(message.role == "tool" for message in session.messages)


def _all_tool_results_successful(session: Session) -> bool:
    tool_messages = [message for message in session.messages if message.role == "tool"]
    if not tool_messages:
        return False
    failure_words = ("error", "failed", "失败", "异常", "permission denied", "not found")
    return not any(any(word in str(message.content or "").lower() for word in failure_words) for message in tool_messages)
