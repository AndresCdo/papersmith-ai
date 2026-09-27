#!/usr/bin/env python3
"""figure-review: turn an already-compiled figure PDF into pixels, and
compute the geometric facts a raster can actually support.

This front door answers a command, never a session claim
(`figure-raster` spec, `Requirement: Presence Is a Command the Front Door
Answers`). Two verbs today:

    python review_cli.py probe [--json] [--path PATH]
    python review_cli.py raster --pdf <path/to/id.pdf> [--dpi 150]
                                 [--out DIR] [--path PATH] [--timeout SECONDS]

`probe` reports which of the fixed rasterizer chain
(`pdftoppm`, `pdftocairo`, `gs`, `sips`) this machine's `PATH` resolves, or
refuses `RASTER_TOOLCHAIN_ABSENT` naming all four and the exact `PATH`
searched. `raster` produces `<id>.png` and `raster-provenance.json` from an
already-compiled PDF — it compiles nothing, and it never opens a
repair-budget ledger.

A third verb, `measure`, turns that raster into computed findings
(out-of-bounds, overlap, canvas occupancy) — it lands in a later commit;
this front door claims only what it can do today.

`--path` and `--timeout` are test-only injection points, exactly like
`paper_latex.compile`'s own `path=` operand: a caller can point this front
door at a scratch `PATH` holding stub executables, or shorten the per-link
timeout, without touching the real toolchain or the real 60-second bound.

Exit codes: 0 the command answered; 2 a refusal — nothing was written.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import raster  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_core" / "implementation"))
from impl_refusals import Refused  # noqa: E402


def _scratch_dir_for(pdf: Path) -> Path:
    """The same scratch-directory shape `paper_figure.figure_paths` already
    resolves for this figure id — computed independently here, never by
    importing `paper_figure` (design.md: "Never an edge: paper-writing --X-->
    figure-review"). `pdf` is expected at `<paper>/Figures/<id>.pdf`, so the
    paper directory is two levels up."""
    figure_id = pdf.stem
    paper_dir = pdf.resolve().parent.parent
    return paper_dir / ".paper-writing" / "figures" / figure_id


def cmd_probe(args: argparse.Namespace) -> dict:
    return raster.probe(path=args.path)


def cmd_raster(args: argparse.Namespace) -> dict:
    pdf = Path(args.pdf)
    if not pdf.is_file():
        raise Refused("DIAGRAM_SOURCE_ABSENT", f"{pdf} does not exist")
    out_dir = Path(args.out) if args.out else _scratch_dir_for(pdf)
    kwargs: dict = {"dpi": args.dpi, "path": args.path}
    if args.timeout is not None:
        kwargs["timeout"] = args.timeout
    return raster.rasterize(pdf, out_dir, **kwargs)


_COMMANDS = {
    "probe": cmd_probe,
    "raster": cmd_raster,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rasterize an already-compiled figure PDF and report the geometric "
                    "facts a raster can actually support.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_probe = sub.add_parser(
        "probe", help="report which rasterizer link this machine's PATH resolves")
    p_probe.add_argument("--path", default=None, help="override PATH, test-only")
    p_probe.add_argument("--json", action="store_true", help="machine-readable output")
    p_probe.set_defaults(func=cmd_probe)

    p_raster = sub.add_parser(
        "raster", help="rasterize an already-compiled figure PDF to PNG plus provenance")
    p_raster.add_argument("--pdf", required=True, metavar="path", help="the compiled figure PDF")
    p_raster.add_argument("--dpi", type=int, default=raster.DEFAULT_DPI)
    p_raster.add_argument(
        "--out", default=None, metavar="dir",
        help="override the derived scratch directory")
    p_raster.add_argument("--path", default=None, help="override PATH, test-only")
    p_raster.add_argument(
        "--timeout", type=float, default=None,
        help="override the per-link timeout in seconds, test-only")
    p_raster.add_argument("--json", action="store_true", help="machine-readable output")
    p_raster.set_defaults(func=cmd_raster)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = _COMMANDS[args.command](args)
    except Refused as exc:
        print(json.dumps({"status": "refused", "code": exc.code, "detail": exc.detail}))
        return 2
    print(json.dumps({"status": "ok", "command": args.command, **result}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
