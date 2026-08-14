import json
from pathlib import Path

from cai_miner.cli import main


def test_validate_cli_writes_report(tmp_path: Path):
    report = tmp_path / "report.json"
    code = main(["validate", "--input", "tests/fixtures/valid_session.json", "--out", str(report)])
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["summary"]["accepted"] == 1
    assert payload["results"][0]["status"] == "accepted"
