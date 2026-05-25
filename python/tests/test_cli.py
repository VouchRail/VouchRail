"""Tests for the Python CLI."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from vouchrail import AuditLogger, InlineSigner, LocalStorageBackend
from vouchrail.cli.main import main

TEST_SECRET = "test-secret-key-with-enough-length-1234567890"


def _seed(dir_: str, system_id: str = "sys-cli") -> AuditLogger:
    audit = AuditLogger(
        system_id=system_id,
        storage=LocalStorageBackend(dir=dir_),
        signer=InlineSigner(TEST_SECRET),
    )
    for i in range(3):
        cid = audit.start_call(
            case_id=f"case-{i % 2}",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet",
            model_version="20241022",
            prompt_template_id="tpl",
            prompt_template_version="1.0.0",
            operator_id="op",
            input={"i": i},
        )
        audit.end_call(cid, output_decision={"i": i}, reason_codes=["OK"])
    audit.close()
    return audit


@pytest.fixture()
def seeded() -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-") as d:
        _seed(d)
        yield d, "sys-cli"


def test_verify_clean_chain(seeded: tuple[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    dir_, sys_id = seeded
    code = main(["--system-id", sys_id, "--storage-dir", dir_, "verify"])
    captured = capsys.readouterr()
    assert code == 0
    assert "✔ Chain valid" in captured.out
    assert "3 entries verified" in captured.out


def test_verify_json(seeded: tuple[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    dir_, sys_id = seeded
    code = main(["--system-id", sys_id, "--storage-dir", dir_, "--json", "verify"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out.strip())
    assert payload["systemId"] == sys_id
    assert payload["entriesChecked"] == 3
    assert payload["result"]["valid"] is True


def test_query_filters_by_case(
    seeded: tuple[str, str], capsys: pytest.CaptureFixture[str],
) -> None:
    dir_, sys_id = seeded
    code = main(["--system-id", sys_id, "--storage-dir", dir_, "query", "--case-id", "case-0"])
    captured = capsys.readouterr()
    assert code == 0
    # case-0 receives 2 of 3 entries (i in {0, 2}).
    assert captured.err.count("Matched") == 1
    assert "2 entries" in captured.err


def test_export_requires_a_bound(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-") as d:
        _seed(d)
        code = main(["--system-id", "sys-cli", "--storage-dir", d, "export"])
        captured = capsys.readouterr()
        assert code == 2
        assert "pass --case-id or --from/--to" in captured.err


def test_export_to_file(seeded: tuple[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    dir_, sys_id = seeded
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-out-") as out_dir:
        out_path = Path(out_dir) / "evidence.jsonl"
        code = main(
            [
                "--system-id",
                sys_id,
                "--storage-dir",
                dir_,
                "export",
                "--case-id",
                "case-0",
                "--output",
                str(out_path),
            ],
            cwd=Path(out_dir),
        )
        assert code == 0
        lines = out_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        for line in lines:
            assert json.loads(line)["caseId"] == "case-0"


def test_init_writes_starter_config(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-init-") as d:
        cfg_path = Path(d) / "vouchrail.config.json"
        code = main(["init"], cwd=Path(d))
        captured = capsys.readouterr()
        assert code == 0
        assert cfg_path.exists()
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        assert data["storage"]["type"] == "local"
        assert "Wrote config" in captured.out


def test_init_refuses_to_overwrite(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-init-") as d:
        cfg_path = Path(d) / "vouchrail.config.json"
        cfg_path.write_text("{}", encoding="utf-8")
        code = main(["init"], cwd=Path(d))
        captured = capsys.readouterr()
        assert code == 2
        assert "Refusing to overwrite" in captured.err


def test_explicit_config_with_traversal_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-") as d:
        code = main(["--config", "../escape.json", "verify"], cwd=Path(d))
        captured = capsys.readouterr()
        assert code == 1
        assert "must not contain '..'" in captured.err


def test_verify_report_json(seeded: tuple[str, str], capsys: pytest.CaptureFixture[str]) -> None:
    dir_, sys_id = seeded
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-rep-") as out_dir:
        code = main(
            [
                "--system-id",
                sys_id,
                "--storage-dir",
                dir_,
                "verify",
                "--report",
                "report.json",
            ],
            cwd=Path(out_dir),
        )
        assert code == 0
        report = json.loads((Path(out_dir) / "report.json").read_text(encoding="utf-8"))
        assert report["systemId"] == sys_id
        assert report["entriesVerified"] == 3
        assert report["firstSequence"] == 0
        assert report["lastSequence"] == 2
        assert report["chain"] == {"valid": True}
        assert report["signatureCheck"]["method"] == "not-performed"
        assert isinstance(report["generatedAt"], str)
        assert isinstance(report["cliVersion"], str)


def test_verify_report_markdown(
    seeded: tuple[str, str], capsys: pytest.CaptureFixture[str],
) -> None:
    dir_, sys_id = seeded
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-rep-") as out_dir:
        code = main(
            [
                "--system-id",
                sys_id,
                "--storage-dir",
                dir_,
                "verify",
                "--report",
                "report.md",
            ],
            cwd=Path(out_dir),
        )
        assert code == 0
        md = (Path(out_dir) / "report.md").read_text(encoding="utf-8")
        assert md.startswith("# VouchRail verification report")
        assert "Status**: VALID" in md
        assert "Entries verified: 3" in md


def test_verify_report_records_broken_chain(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-") as d:
        _seed(d)
        # Tamper with a JSONL line.
        jsonl_files = sorted(Path(d).rglob("*.jsonl"))
        assert jsonl_files, "expected at least one JSONL after seeding"
        first_file = jsonl_files[0]
        lines = first_file.read_text(encoding="utf-8").splitlines()
        entry = json.loads(lines[0])
        entry["outputDecision"] = {"tampered": True}
        lines[0] = json.dumps(entry, separators=(",", ":"))
        first_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with tempfile.TemporaryDirectory(prefix="vouchrail-cli-rep-") as out_dir:
            code = main(
                [
                    "--system-id",
                    "sys-cli",
                    "--storage-dir",
                    d,
                    "verify",
                    "--report",
                    "report.json",
                ],
                cwd=Path(out_dir),
            )
            assert code == 1
            report = json.loads((Path(out_dir) / "report.json").read_text(encoding="utf-8"))
            assert report["chain"]["valid"] is False
            assert report["chain"]["brokenAt"] == 0
            assert report["chain"]["reason"] == "entry_hash_mismatch"
            assert isinstance(report["chain"]["detail"], str)


def test_anchor_emits_chain_head(
    seeded: tuple[str, str], capsys: pytest.CaptureFixture[str],
) -> None:
    dir_, sys_id = seeded
    code = main(["--system-id", sys_id, "--storage-dir", dir_, "anchor"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out.strip())
    assert payload["systemId"] == sys_id
    assert payload["sequence"] == 2
    assert payload["entryCount"] == 3
    assert payload["recordHash"].startswith("sha256:")
    assert payload["algorithm"] == "sha256"
    assert isinstance(payload["signature"], str)
    assert payload["signature"]
    assert isinstance(payload["anchoredAt"], str)
    assert isinstance(payload["cliVersion"], str)


def test_anchor_writes_to_file(
    seeded: tuple[str, str], capsys: pytest.CaptureFixture[str],
) -> None:
    dir_, sys_id = seeded
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-anchor-") as out_dir:
        out_path = Path(out_dir) / "chain-head.json"
        code = main(
            ["--system-id", sys_id, "--storage-dir", dir_, "anchor", "--output", str(out_path)],
            cwd=Path(out_dir),
        )
        captured = capsys.readouterr()
        assert code == 0
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        assert payload["entryCount"] == 3
        assert "Wrote anchor" in captured.err


def test_anchor_returns_2_when_empty(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="vouchrail-cli-") as d:
        code = main(["--system-id", "sys-empty", "--storage-dir", d, "anchor"], cwd=Path(d))
        captured = capsys.readouterr()
        assert code == 2
        assert "no entries found" in captured.err
