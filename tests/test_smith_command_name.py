"""`smith` is the canonical command name, whichever entry point launched it."""

from __future__ import annotations

import sys

import pytest

from papersmith import cli


@pytest.mark.parametrize("argv0", ["/usr/bin/smith", "/usr/bin/papersmith", "python"])
def test_version_reports_smith_for_every_entry_point(monkeypatch, capsys, argv0):
    monkeypatch.setattr(sys, "argv", [argv0, "--version"])
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.startswith("smith ")


def test_help_usage_names_smith(capsys):
    assert cli.main([]) == 1
    assert capsys.readouterr().out.startswith("usage: smith ")


def test_both_entry_points_stay_installed():
    import tomllib
    from pathlib import Path

    scripts = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    )["project"]["scripts"]
    assert scripts["smith"] == scripts["papersmith"] == "papersmith.cli:main"
