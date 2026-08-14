"""Effective-turn and machine-turn calculations."""

from __future__ import annotations

import re

from cai_miner.normalization.schema import Message

SENTINELS = {"", ".", "..", "...", "ok", "okay", "yes", "继续", "好的", "嗯"}


def count_effective_turns(messages: list[Message]) -> int:
    turns = 0
    for message in messages:
        if message.role == "user" and _has_substantive_content(message):
            turns += 1
        elif message.role == "assistant" and message.tool_calls:
            turns += 1
    return turns


def machine_turn_ratio(messages: list[Message]) -> tuple[int, int, float]:
    user_messages = [message for message in messages if message.role == "user"]
    user_turns = len(user_messages)
    machine_turns = sum(1 for message in user_messages if is_no_reply_user_turn(message))
    ratio = machine_turns / user_turns if user_turns else 1.0
    return machine_turns, user_turns, ratio


def is_no_reply_user_turn(message: Message) -> bool:
    return not _has_substantive_content(message)


def _has_substantive_content(message: Message) -> bool:
    text = str(message.content or "").strip().lower()
    if text in SENTINELS:
        return False
    if re.fullmatch(r"[\W_]+", text or ""):
        return False
    return True
