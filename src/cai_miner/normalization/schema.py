"""Canonical data structures for coding-agent interaction sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool", "other"]
ValidationStatus = Literal["accepted", "rejected", "needs_review"]


@dataclass(frozen=True)
class SourceInfo:
    host: str | None = None
    repo_full_name: str | None = None
    repo_url: str | None = None
    file_path: str | None = None
    commit_sha: str | None = None
    license_spdx: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SourceInfo":
        return cls(**{k: v for k, v in (data or {}).items() if k in cls.__dataclass_fields__})


@dataclass(frozen=True)
class ModelInfo:
    raw: str | None = None
    provider: str | None = None
    family: str | None = None
    version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str | None) -> "ModelInfo":
        if isinstance(data, str):
            return cls(raw=data)
        return cls(**{k: v for k, v in (data or {}).items() if k in cls.__dataclass_fields__})


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolDefinition":
        return cls(
            name=str(data.get("name", "")),
            description=data.get("description"),
            parameters=data.get("parameters"),
        )


@dataclass(frozen=True)
class ToolCall:
    id: str | None
    name: str
    arguments: dict[str, Any] | str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCall":
        function = data.get("function") if isinstance(data.get("function"), dict) else {}
        name = data.get("name") or function.get("name") or ""
        arguments = data.get("arguments", function.get("arguments"))
        return cls(id=data.get("id") or data.get("tool_call_id"), name=str(name), arguments=arguments, raw=data)


@dataclass(frozen=True)
class Message:
    role: Role
    content: Any = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        raw_tool_calls = data.get("tool_calls") or data.get("tool_use") or []
        if isinstance(raw_tool_calls, dict):
            raw_tool_calls = [raw_tool_calls]
        tool_calls = [ToolCall.from_dict(item) for item in raw_tool_calls if isinstance(item, dict)]
        return cls(
            role=data.get("role", "other"),
            content=data.get("content"),
            tool_call_id=data.get("tool_call_id") or data.get("tool_use_id"),
            tool_calls=tool_calls,
            metadata=data.get("metadata") or {},
        )


@dataclass(frozen=True)
class Session:
    session_id: str
    messages: list[Message]
    tool_definitions: list[ToolDefinition] = field(default_factory=list)
    model: ModelInfo = field(default_factory=ModelInfo)
    source: SourceInfo = field(default_factory=SourceInfo)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        raw_tools = data.get("tool_definitions") or data.get("tools") or []
        return cls(
            session_id=str(data.get("session_id") or data.get("id") or ""),
            messages=[Message.from_dict(item) for item in data.get("messages", []) if isinstance(item, dict)],
            tool_definitions=[ToolDefinition.from_dict(item) for item in raw_tools if isinstance(item, dict)],
            model=ModelInfo.from_dict(data.get("model") or data.get("model_name")),
            source=SourceInfo.from_dict(data.get("source")),
            metadata=data.get("metadata") or {},
        )


@dataclass(frozen=True)
class RuleFailure:
    rule_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "message": self.message}


@dataclass(frozen=True)
class ValidationResult:
    session_id: str
    status: ValidationStatus
    score: int
    failures: list[RuleFailure]
    warnings: list[RuleFailure]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "score": self.score,
            "failures": [failure.to_dict() for failure in self.failures],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "metrics": self.metrics,
        }
