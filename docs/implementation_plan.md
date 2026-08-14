# Coding Agent Interaction Miner Implementation Plan

## Goal

Build a system that mines real coding-agent interaction sessions from ordinary GitHub software projects, validates them against the repository's Agent data acceptance standard, and exports accepted sessions as a traceable JSON/JSONL dataset.

The target data is developer-uploaded interaction logs from projects such as games, business systems, apps, libraries, and infrastructure repositories. The target data is not the source code of coding-agent products themselves.

## Acceptance-First Architecture

The system is organized around validation before scale:

1. Source discovery: find candidate GitHub repositories and files.
2. Repository filtering: exclude coding-agent product/framework repositories.
3. Raw collection: store original files, commits, licenses, and discovery evidence.
4. Log detection: identify files that may contain real coding-agent trajectories.
5. Session segmentation: split raw files into single-task sessions.
6. Parsing and normalization: convert Markdown, JSON, JSONL, text, and tool-specific exports into one schema.
7. Acceptance validation: enforce the Agent data acceptance standard as hard rules.
8. Quality scoring: rank realism, completeness, and engineering value.
9. Deduplication: remove exact duplicates and subset fragments.
10. Privacy and license filtering: redact secrets/PII and track redistribution risk.
11. Dataset export: produce UTF-8 JSON/JSONL and tar.gz deliverables with reports.

## Minimum Accepted Session

A session is accepted only if it satisfies all hard rules:

- It has at least two effective interaction turns.
- Its first message role is not `assistant` or `tool`.
- It contains at least one valid structured tool call.
- Every called tool has a complete tool schema.
- Every called tool is declared in the available tool definitions.
- After excluding the final turn, every tool call has a matching tool result.
- Machine turns divided by user turns is less than 25%.
- The model belongs to a supported family and meets the version threshold.
- The session is not roleplay, GUI-only, synthetic-like, contradictory, or based on hallucinated tool output.

## Initial MVP

The first implementation stage validates already-normalized JSON/JSONL sessions before adding GitHub crawling.

### MVP modules

- `normalization.schema`: typed dataclasses for sessions, messages, tools, model info, source info, and validation results.
- `validation.acceptance_validator`: hard-rule validation and rejection reasons.
- `validation.model_validator`: supported model-family and version-threshold checks.
- `validation.tool_validator`: structured tool-call, schema completeness, declaration, and pairing checks.
- `sessionization.turn_counter`: effective-turn and machine-turn ratio calculations.
- `quality.synthetic_detector`: deterministic synthetic/roleplay/GUI red flags.
- `cli`: command-line JSON/JSONL validation and report generation.

### MVP command

```bash
python -m cai_miner.cli validate --input tests/fixtures/valid_session.json --out /tmp/report.json
```

## Later Phases

### Phase 1: GitHub candidate discovery

Implement query packs for Claude Code, Codex, Cursor, Cline/Roo Code, aider, and generic tool-call traces. Rank candidate files by filename, path, content signatures, structured messages, model metadata, and tool-use evidence.

### Phase 2: Tool-specific parsers

Add parsers for Markdown transcripts, JSON/JSONL event logs, Claude Code transcripts, Codex traces, Cursor exports, aider logs, and Cline/Roo Code logs.

### Phase 3: Deduplication and token accounting

Compute exact hashes over system prompt, user messages, assistant messages, tool calls, and tool results. Detect subset fragments and compute effective tokens from messages plus tool definitions while excluding Base64 image payloads.

### Phase 4: Review workflow and export

Add reviewer labels, audit trails, quality reports, source indexes, redaction reports, license reports, and final tar.gz packaging.
