from __future__ import annotations

import json
from pathlib import Path

from argobrain_memory.cli import main


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "demo-session"


def test_cli_benchmark_all(tmp_path: Path, capsys) -> None:
    code = main(["benchmark", "--fixture", str(FIXTURE), "--output", str(tmp_path), "--mode", "all"])
    assert code == 0

    out = json.loads(capsys.readouterr().out)
    modes = {row["mode"] for row in out}
    assert modes == {"off", "baseline", "cortex", "external"}
    assert (tmp_path / "benchmark-cortex.json").is_file()

