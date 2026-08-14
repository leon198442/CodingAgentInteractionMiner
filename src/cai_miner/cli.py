"""Command-line interface for Coding Agent Interaction Miner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from cai_miner.normalization.schema import Session
from cai_miner.validation.acceptance_validator import AcceptanceValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cai-miner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate normalized session JSON/JSONL files.")
    validate_parser.add_argument("--input", required=True, help="Input JSON or JSONL file.")
    validate_parser.add_argument("--out", required=True, help="Output validation report JSON file.")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(Path(args.input), Path(args.out))
    return 1


def _validate(input_path: Path, output_path: Path) -> int:
    validator = AcceptanceValidator()
    sessions = [Session.from_dict(item) for item in _read_json_or_jsonl(input_path)]
    results = [validator.validate(session).to_dict() for session in sessions]
    summary = {
        "total": len(results),
        "accepted": sum(1 for item in results if item["status"] == "accepted"),
        "rejected": sum(1 for item in results if item["status"] == "rejected"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if summary["rejected"] == 0 else 2


def _read_json_or_jsonl(path: Path) -> Iterable[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return parsed
    return [parsed]


if __name__ == "__main__":
    raise SystemExit(main())
