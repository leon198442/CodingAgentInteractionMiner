"""Tool schema, tool-call, and tool-result validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from cai_miner.normalization.schema import Message, RuleFailure, Session, ToolCall, ToolDefinition

AMBIGUOUS_TOOL_NAMES = {"tool1", "tool", "helper", "action", "do", "run"}


@dataclass(frozen=True)
class ToolValidation:
    failures: list[RuleFailure]
    metrics: dict[str, Any]


def validate_tools(session: Session) -> ToolValidation:
    failures: list[RuleFailure] = []
    tool_definitions = {tool.name: tool for tool in session.tool_definitions}
    tool_calls = _collect_tool_calls(session.messages)
    tool_results = _collect_tool_results(session.messages)

    if not any(_is_structured_tool_call(call) for call in tool_calls):
        failures.append(RuleFailure("R003_NO_STRUCTURED_TOOL_CALL", "Session has no valid structured tool call."))

    incomplete_tools = [tool.name for tool in session.tool_definitions if not _is_complete_tool_schema(tool)]
    if incomplete_tools:
        failures.append(RuleFailure("R004_MISSING_TOOL_SCHEMA", f"Tool schema is incomplete for: {', '.join(sorted(incomplete_tools))}."))

    undeclared = sorted({call.name for call in tool_calls if call.name not in tool_definitions})
    if undeclared:
        failures.append(RuleFailure("R005_UNDECLARED_TOOL", f"Tool calls reference undeclared tools: {', '.join(undeclared)}."))

    paired_count, pairing_rate = _pairing_rate_without_tail(session.messages, tool_calls, tool_results)
    if tool_calls and pairing_rate != 1.0:
        failures.append(RuleFailure("R006_TOOL_PAIRING_NOT_100", "Tool call/result pairing rate is not 100% after excluding the final turn."))

    return ToolValidation(
        failures=failures,
        metrics={
            "tool_definition_count": len(session.tool_definitions),
            "tool_call_count": len(tool_calls),
            "tool_result_count": len(tool_results),
            "paired_tool_call_count_without_tail": paired_count,
            "tool_pairing_rate_without_tail": pairing_rate,
        },
    )


def _collect_tool_calls(messages: list[Message]) -> list[ToolCall]:
    return [call for message in messages for call in message.tool_calls]


def _collect_tool_results(messages: list[Message]) -> dict[str, Message]:
    return {message.tool_call_id: message for message in messages if message.role == "tool" and message.tool_call_id}


def _is_complete_tool_schema(tool: ToolDefinition) -> bool:
    if not tool.name or tool.name.lower() in AMBIGUOUS_TOOL_NAMES:
        return False
    if not tool.description:
        return False
    parameters = tool.parameters
    if not isinstance(parameters, dict):
        return False
    if parameters.get("type") != "object":
        return False
    properties = parameters.get("properties")
    if not isinstance(properties, dict):
        return False
    for definition in properties.values():
        if isinstance(definition, dict) and ("type" not in definition or "description" not in definition):
            return False
    return True


def _is_structured_tool_call(call: ToolCall) -> bool:
    if not call.name:
        return False
    if isinstance(call.arguments, dict):
        return True
    if isinstance(call.arguments, str):
        try:
            parsed = json.loads(call.arguments)
        except json.JSONDecodeError:
            return False
        return isinstance(parsed, dict)
    return False


def _pairing_rate_without_tail(messages: list[Message], tool_calls: list[ToolCall], tool_results: dict[str, Message]) -> tuple[int, float]:
    if not tool_calls:
        return 0, 0.0
    last_index = len(messages) - 1
    call_message_index: dict[str, int] = {}
    for index, message in enumerate(messages):
        for call in message.tool_calls:
            if call.id:
                call_message_index[call.id] = index
    eligible_calls = [call for call in tool_calls if call.id and call_message_index.get(call.id, last_index) < last_index]
    if not eligible_calls:
        return 0, 1.0
    paired = sum(1 for call in eligible_calls if call.id in tool_results)
    return paired, paired / len(eligible_calls)
