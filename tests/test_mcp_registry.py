"""Capability-roster drift: the MCP surface stays deliberate, never partial."""

from __future__ import annotations

import argparse
import ast
import json
import shlex
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_series import build_workspace, call_many, tool_call

from papersmith.cli import build_parser, parse_argv
from papersmith.mcp import registry, server
from papersmith.mcp.bridge import ChildResult
from papersmith.mcp.server import catalog

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_CLI = REPO_ROOT / "skills" / "paper-writing" / "scripts" / "paper_cli.py"
SKILL_SCRIPTS = REPO_ROOT / "skills" / "paper-writing" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
import paper_cli  # noqa: E402


def _paper_cli_commands() -> tuple[str, ...]:
    tree = ast.parse(PAPER_CLI.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == "COMMANDS" for target in node.targets
        ):
            return tuple(ast.literal_eval(node.value))
    raise AssertionError("paper_cli.COMMANDS was not found")


def _cli_commands() -> tuple[str, ...]:
    parser = build_parser()
    action = next(
        candidate
        for candidate in parser._actions
        if isinstance(candidate, argparse._SubParsersAction)
    )
    return tuple(action.choices)


def _paper_cli_subparser(tokens: tuple[str, ...]) -> argparse.ArgumentParser:
    """Walk `paper_cli.build_parser()`'s nested `_SubParsersAction`s down a
    verb-token path — the same walk `_cli_commands()` uses at one level,
    carried through `bib build` / `mark revisions` / `mark class`."""
    parser = paper_cli.build_parser()
    for token in tokens:
        action = next(
            candidate
            for candidate in parser._actions
            if isinstance(candidate, argparse._SubParsersAction)
        )
        parser = action.choices[token]
    return parser


def _paper_build_plan(spec: registry.ToolSpec) -> tuple[tuple[str, ...], tuple[registry.Flag, ...]]:
    """The exact verb tokens and `Flag` tuple the tool's builder ships with.

    `_paper_builder(verb, flags)` captures both in its closure; the two
    module-level builders (`_build_readiness`, `_build_full_text`) close
    over nothing and read `_READINESS_FLAGS`/`_FULL_TEXT_FLAGS` globals,
    resolved here by identity against the registry surface they live in.
    """
    closure = spec.build.__closure__
    if closure:
        cells = [cell.cell_contents for cell in closure]
        tokens = next(
            value for value in cells
            if isinstance(value, tuple) and all(isinstance(item, str) for item in value)
        )
        flags = next(
            value for value in cells
            if isinstance(value, tuple) and all(isinstance(item, registry.Flag) for item in value)
        )
        return tokens, flags
    if spec.build is registry._build_readiness:
        return ("readiness",), registry._READINESS_FLAGS
    if spec.build is registry._build_full_text:
        return ("full_text",), registry._FULL_TEXT_FLAGS
    raise AssertionError(f"cannot derive the build plan for {spec.name}")


#: CLI-only option strings the paper subparsers accept but the MCP surface
#: deliberately does not spell, per tool name. The parity test pins exactly
#: this named difference rather than weakening to a subset check, so a flag
#: rename on either side still fails the suite. There is no registry-only
#: option in the other direction.
_PAPER_CLI_ONLY_FLAGS: dict[str, frozenset[str]] = {
    # `observe` omits the optional disk-truth reconciliation half of the CLI.
    "papersmith.paper_observe": frozenset({"--experiments", "--implementation", "--proposals"}),
    # `declare` withholds the decline-with-condition surface and the
    # --sections override.
    "papersmith.paper_declare": frozenset({"--condition", "--decline", "--reason", "--sections"}),
    "papersmith.paper_bib_build": frozenset({"--guidance"}),
    "papersmith.paper_write": frozenset({"--grounding"}),
    "papersmith.paper_validate": frozenset({"--min-sources"}),
}


def test_registry_labels_match_the_real_paper_cli_roster() -> None:
    assert registry.PAPER_VERBS == _paper_cli_commands()


def test_registry_labels_match_the_real_cli_roster() -> None:
    assert set(registry.CLI_COMMANDS) == set(_cli_commands())


def test_every_paper_verb_has_a_disposition() -> None:
    assert set(registry.PAPER_DISPOSITIONS) == set(registry.PAPER_VERBS)


def test_every_cli_command_has_a_disposition() -> None:
    assert set(registry.CLI_DISPOSITIONS) == set(registry.CLI_COMMANDS)


def test_dispositions_use_only_the_declared_vocabulary() -> None:
    allowed = {"exposed", "deferred", "out"}
    assert set(registry.PAPER_DISPOSITIONS.values()) <= allowed
    assert set(registry.CLI_DISPOSITIONS.values()) <= allowed


def test_the_server_host_is_declared_out_not_exposed() -> None:
    assert registry.CLI_DISPOSITIONS["mcp"] == "out"
    assert not any(spec.verb == "mcp" for spec in registry.TOOLS)


def test_exposed_paper_tools_are_exactly_the_exposed_dispositions() -> None:
    exposed_tools = {spec.verb for spec in registry.TOOLS if spec.surface == "paper"}
    exposed_declared = {
        verb for verb, state in registry.PAPER_DISPOSITIONS.items() if state == "exposed"
    }
    assert exposed_tools == exposed_declared


def test_every_tool_name_is_namespaced_and_unique() -> None:
    names = [spec.name for spec in registry.TOOLS]
    assert len(names) == len(set(names))
    assert all(name.startswith("papersmith.") for name in names)


def test_every_input_schema_is_a_closed_object() -> None:
    for spec in registry.TOOLS:
        schema = spec.input_schema
        assert schema["type"] == "object", spec.name
        assert schema["additionalProperties"] is False, spec.name
        for required in schema.get("required", []):
            assert required in schema["properties"], spec.name


def test_every_tool_declares_all_four_annotation_hints() -> None:
    for spec in registry.TOOLS:
        for hint in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
            assert isinstance(spec.annotations[hint], bool), (spec.name, hint)


def test_read_only_and_destructive_are_never_both_true() -> None:
    for spec in registry.TOOLS:
        if spec.annotations["readOnlyHint"]:
            assert spec.annotations["destructiveHint"] is False, spec.name


def test_target_check_is_open_world_despite_being_read_only() -> None:
    spec = registry.TOOLS_BY_NAME["papersmith.target_check"]
    assert spec.annotations["readOnlyHint"] is True
    assert spec.annotations["openWorldHint"] is True


def test_paper_validate_is_exposed_but_never_read_only() -> None:
    # C1: `validate` appends evidence and can substitute the block body.
    spec = registry.TOOLS_BY_NAME["papersmith.paper_validate"]
    assert spec.annotations["readOnlyHint"] is False
    assert spec.annotations["destructiveHint"] is True
    assert registry.PAPER_DISPOSITIONS["validate"] == "exposed"


def test_paper_observe_is_exposed_read_only() -> None:
    spec = registry.TOOLS_BY_NAME["papersmith.paper_observe"]
    assert spec.annotations["readOnlyHint"] is True
    assert registry.PAPER_DISPOSITIONS["observe"] == "exposed"


def test_only_resolve_and_render_remain_deferred() -> None:
    deferred = {
        verb for verb, state in registry.PAPER_DISPOSITIONS.items() if state == "deferred"
    }
    # `resolve` reaches the network and caches metadata; `render` shells out to
    # latexmk. Both are named, never silently dropped.
    assert deferred == {"resolve", "render"}


def test_no_deferred_cli_command_remains() -> None:
    assert not [
        command
        for command, state in registry.CLI_DISPOSITIONS.items()
        if state == "deferred"
    ]
    assert registry.CLI_DISPOSITIONS["mcp"] == "out"


def test_catalog_tools_match_the_registry_order() -> None:
    assert [tool["name"] for tool in catalog()["tools"]] == [
        spec.name for spec in registry.TOOLS
    ]


def test_paper_tool_flags_match_the_cli_subparsers() -> None:
    """Flag-level parity between every paper `ToolSpec` and the real parser.

    The verb-name and disposition tests pin the roster, but nothing pinned
    the FLAGS a tool's builder spells against the option strings the CLI
    subparser accepts — so a rename on either side used to stay green while
    breaking the MCP tool at runtime. Every paper tool's flags must be
    exactly its subparser's option strings, no more and no less, with the
    sole sanctioned difference the CLI-only options withheld by name in
    `_PAPER_CLI_ONLY_FLAGS`.

    `spec.verb` is not enough to reach the subparser (both `bib build` and
    `mark revisions`/`mark class` nest), so the walk uses the verb tokens
    the tool's builder actually ships with.
    """
    for spec in (spec for spec in registry.TOOLS if spec.surface == "paper"):
        tokens, flags = _paper_build_plan(spec)
        subparser = _paper_cli_subparser(tokens)
        spelled = {flag.flag for flag in flags}
        accepted = {
            option
            for action in subparser._actions
            if not isinstance(action, (argparse._SubParsersAction, argparse._HelpAction))
            for option in action.option_strings
        }
        forgiven = _PAPER_CLI_ONLY_FLAGS.get(spec.name, frozenset())
        assert not (spelled - accepted), (
            f"{spec.name} spells flags its subparser does not accept: "
            f"{sorted(spelled - accepted)}"
        )
        assert accepted - spelled == forgiven, (
            f"{spec.name} subparser accepts options the tool does not spell "
            f"(beyond the named exceptions): {sorted(accepted - spelled - forgiven)}"
        )


def test_run_builder_emits_a_positional_profile(tmp_path: Path) -> None:
    # Given a profile whose name differs from the old literal positional token.
    spec = registry.TOOLS_BY_NAME["papersmith.run"]
    # When the registry builds the child command.
    plan = spec.build({"profile": "sentinel_smoke", "dry_run": True}, tmp_path)
    # Then the profile occupies exactly one positional slot.
    assert plan.kind == "cli"
    assert plan.tokens == ("run", "sentinel_smoke", "--dry-run")


def test_run_builder_tokens_parse_with_the_real_cli(tmp_path: Path) -> None:
    # Given a target override and the first shard (which must not disappear).
    arguments = {"profile": "sentinel_smoke", "target": "local-test", "shard": 0, "dry_run": True}
    # When the real CLI parses the registry's tokens without executing them.
    plan = registry.TOOLS_BY_NAME["papersmith.run"].build(arguments, tmp_path)
    parsed = build_parser().parse_args(plan.tokens)
    # Then both positional and option values survive the boundary.
    assert (parsed.profile_name, parsed.target, parsed.shard, parsed.dry_run) == (
        "sentinel_smoke",
        "local-test",
        0,
        True,
    )


@pytest.mark.parametrize("consent", [False, True], ids=["without-consent", "with-consent"])
def test_run_builder_defaults_to_dry_run(tmp_path: Path, consent: bool) -> None:
    # Given omitted dry_run, even when consent is present.
    arguments = {"profile": "sentinel_smoke"}
    if consent:
        arguments["consent"] = "test-consent"
    # When building the plan.
    plan = registry.TOOLS_BY_NAME["papersmith.run"].build(arguments, tmp_path)
    # Then omission is materialized as the safe CLI flag.
    assert "--dry-run" in plan.tokens


def test_run_builder_leaves_its_input_unchanged(tmp_path: Path) -> None:
    # Given caller-owned arguments without a dry_run key.
    arguments = {"profile": "sentinel_smoke", "shard": 0}
    original = arguments.copy()
    # When building the plan.
    registry.TOOLS_BY_NAME["papersmith.run"].build(arguments, tmp_path)
    # Then default insertion must not mutate the caller's dictionary.
    assert arguments == original


@pytest.mark.parametrize(
    "options,allowed,dry_run",
    [
        ({}, True, True),
        ({"consent": "test-consent"}, True, True),
        ({"dry_run": True}, True, True),
        ({"dry_run": False, "consent": "test-consent"}, True, False),
        ({"dry_run": False}, False, False),
    ],
    ids=["omitted", "omitted-with-consent", "explicit-true", "approved-false", "refused-false"],
)
def test_run_execution_gates_the_child_boundary(
    tmp_path: Path, options, allowed: bool, dry_run: bool
) -> None:
    # Given an inert process seam: approved non-dry calls never execute a job.
    arguments = {"profile": "sentinel_smoke", **options}
    with patch.object(server, "run_plan", return_value=ChildResult([], 0, "", "")) as child:
        # When executing through the server's validation and consent gate.
        result = server.execute_tool(registry.TOOLS_BY_NAME["papersmith.run"], arguments, tmp_path)
    # Then refusal launches nothing; accepted calls agree with the safe default.
    assert child.call_count == int(allowed)
    assert result["isError"] is not allowed
    if allowed:
        assert ("--dry-run" in child.call_args.args[0].tokens) is dry_run
    else:
        assert result["structuredContent"]["code"] == "CONSENT_REQUIRED"


@pytest.mark.parametrize("explicit", [False, True], ids=["omitted-with-consent", "explicit-true"])
def test_run_stdio_dry_run_never_executes_the_local_entrypoint(
    tmp_path: Path, explicit: bool
) -> None:
    # Given a real temporary workspace with only a harmless local sentinel job.
    workspace = build_workspace(tmp_path)
    sentinel = workspace / "job-executed"
    entrypoint = workspace / "sentinel.py"
    entrypoint.write_text(
        "from pathlib import Path\nPath('job-executed').touch()\n", encoding="utf-8"
    )
    command = shlex.join([sys.executable, str(entrypoint)])
    (workspace / "papersmith.yaml").write_text(
        f'version: "1"\nname: "{workspace.name}"\ntitle: "MCP run test"\n'
        "compute_targets:\n  default: local-test\n  targets:\n"
        "    local-test:\n      provider: local\nexecution_profiles:\n"
        f"  sentinel_smoke:\n    target: local-test\n    entrypoint: {json.dumps(command)}\n"
        "    timeout_seconds: 30\n",
        encoding="utf-8",
    )
    arguments = {"profile": "sentinel_smoke", "consent": "test-consent"}
    if explicit:
        arguments["dry_run"] = True
    # When the real stdio server spawns the real CLI child.
    response = call_many(workspace, [tool_call("papersmith.run", arguments)])[0]["result"]
    # Then planning succeeds without executing the job (ledger writes are allowed).
    assert not sentinel.exists(), "dry-run executed the local entrypoint"
    assert response["isError"] is False, response
    payload = json.loads(response["content"][0]["text"])
    assert payload["profile"] == "sentinel_smoke"
    assert payload["jobs"]
    assert all(job["dry_run"] is True for job in payload["jobs"])


# --------------------------------------------------------------------------- #
# The argument boundary (#59): positionals, the declared default, types
# --------------------------------------------------------------------------- #

GENERIC_CLI_TOOLS = [spec for spec in registry.TOOLS if isinstance(spec.build, registry.CliBuilder)]
#: Pass-through tokens; they must arrive verbatim and never as the directory.
PASSTHROUGH = ["first", "7", "tail"]


def _subparser(command: str) -> argparse.ArgumentParser:
    parser = build_parser()
    action = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    return action.choices[command]


def _sample(flag: registry.Flag, workspace: Path):
    if flag.kind == "bool":
        return True
    if flag.kind == "int":
        return 3
    if flag.kind == "list":
        return list(PASSTHROUGH) if flag.positional else ["a1", "a2"]
    if flag.choices:
        return flag.choices[0]
    return f"sub/{flag.name}" if flag.path else f"v-{flag.name}"


def test_every_generic_tool_is_covered() -> None:
    assert {spec.name for spec in GENERIC_CLI_TOOLS} >= {
        "papersmith.implement", "papersmith.run", "papersmith.remote"}


@pytest.mark.parametrize("spec", GENERIC_CLI_TOOLS, ids=lambda spec: spec.name)
def test_generic_tool_argv_parses_with_the_real_cli(tmp_path: Path, spec) -> None:
    # Given every argument the tool declares, pass-through items included.
    builder = spec.build
    arguments = {flag.name: _sample(flag, tmp_path) for flag in builder.flags}
    # When the real CLI parses the built argv the way `papersmith` itself does.
    plan = builder(arguments, tmp_path)
    parsed = parse_argv(build_parser(), list(plan.tokens))
    # Then each value lands in its own destination, and nothing else moves.
    sub = _subparser(builder.tokens[0])
    named_positionals = [a.dest for a in sub._actions
                         if not a.option_strings and a.dest not in ("directory", "extra")]
    scalars = [flag for flag in builder.flags if flag.positional and flag.kind != "list"]
    assert len(scalars) == len(named_positionals), spec.name
    for flag, dest in zip(scalars, named_positionals):
        assert getattr(parsed, dest) == arguments[flag.name], (spec.name, flag.name)
    for flag in builder.flags:
        if flag.positional:
            continue
        got = getattr(parsed, sub._option_string_actions[flag.flag].dest)
        want = arguments[flag.name]
        if flag.path:
            want = str((tmp_path / want).resolve())
        if flag.kind == "list":
            assert got == want, (spec.name, flag.name)
        elif flag.kind == "bool":
            assert got is True, (spec.name, flag.name)
        else:
            assert str(got) == str(want), (spec.name, flag.name)
    passthrough = [flag for flag in builder.flags if flag.positional and flag.kind == "list"]
    if passthrough:
        assert parsed.extra == PASSTHROUGH, spec.name
    assert getattr(parsed, "directory", ".") == ".", spec.name


def test_remote_operation_reaches_the_cli_as_its_positional(tmp_path: Path) -> None:
    plan = registry.TOOLS_BY_NAME["papersmith.remote"].build({"operation": "status"}, tmp_path)
    assert plan.tokens == ("remote", "status")


def test_implement_passthrough_never_becomes_the_directory(tmp_path: Path) -> None:
    arguments = {"action": "plan", "extra": ["first", "7"]}
    plan = registry.TOOLS_BY_NAME["papersmith.implement"].build(arguments, tmp_path)
    assert plan.tokens == ("implement", "--action", "plan", ".", "--", "first", "7")


@pytest.mark.parametrize("tool,arguments", [
    ("papersmith.implement", {"action": "apply", "plan": "plan.json",
                              "extra": ["--plan", "/elsewhere/plan.json"]}),
    ("papersmith.implement", {"action": "plan", "extra": ["--pla=/elsewhere"]}),
    ("papersmith.remote", {"operation": "pull", "extra": ["--dest", "/elsewhere"]}),
], ids=["override-a-confined-plan", "abbreviated-option", "unconfined-remote-dest"])
def test_an_option_never_rides_the_passthrough(tmp_path: Path, tool, arguments) -> None:
    # Given an option smuggled as a pass-through item, past the typed arguments.
    result, child = _executes(tool, arguments, tmp_path)
    # Then it is refused before any child could parse it as an option.
    assert child.call_count == 0
    assert result["structuredContent"]["code"] == "INVALID_ARGUMENT"


def test_the_dry_run_default_is_declared_once_and_published() -> None:
    schema = registry.TOOLS_BY_NAME["papersmith.run"].input_schema
    assert schema["properties"]["dry_run"]["default"] is True


def _executes(spec_name: str, arguments: dict, workspace: Path):
    with patch.object(server, "run_plan", return_value=ChildResult([], 0, "", "")) as child:
        result = server.execute_tool(registry.TOOLS_BY_NAME[spec_name], arguments, workspace)
    return result, child


@pytest.mark.parametrize("profile", ["-h", "--dry-run", "-"])
def test_an_option_like_positional_is_refused_before_spawning(tmp_path: Path, profile) -> None:
    result, child = _executes("papersmith.run", {"profile": profile}, tmp_path)
    assert child.call_count == 0
    assert result["structuredContent"]["code"] == "INVALID_ARGUMENT"


def test_mcp_boolean_arguments_reject_string_false(tmp_path: Path) -> None:
    # Given the string "false", which Python reads as true.
    result, child = _executes("papersmith.workspace_upgrade", {"force": "false"}, tmp_path)
    # Then it is refused at the boundary and never becomes --force.
    assert child.call_count == 0
    assert result["isError"] is True
    assert result["structuredContent"]["code"] == "INVALID_ARGUMENT"
    plan = registry.TOOLS_BY_NAME["papersmith.workspace_upgrade"].build({"force": False}, tmp_path)
    assert "--force" not in plan.tokens


#: For each declared JSON type, values a JSON client can send that are not it.
WRONG_VALUES = {
    "boolean": ["false", 0, 1],
    "integer": ["1", True, 1.5],
    "string": [1, True, ["x"]],
    "array": ["a", [1], [True]],
}


def test_mcp_invalid_argument_types_do_not_execute(tmp_path: Path) -> None:
    accepted = []
    for spec in registry.TOOLS:
        for name, declared in spec.input_schema.get("properties", {}).items():
            wrong = list(WRONG_VALUES[declared["type"]])
            if "enum" in declared:
                wrong.append("not-a-declared-choice")
            for value in wrong:
                result, child = _executes(spec.name, {name: value}, tmp_path)
                code = result.get("structuredContent", {}).get("code")
                if child.call_count or code != "INVALID_ARGUMENT":
                    accepted.append((spec.name, name, value, code))
    assert accepted == []


def test_every_declared_type_is_one_the_boundary_checks() -> None:
    for spec in registry.TOOLS:
        for name, declared in spec.input_schema.get("properties", {}).items():
            assert declared["type"] in WRONG_VALUES, (spec.name, name)
            if declared["type"] == "array":
                assert declared["items"] == {"type": "string"}, (spec.name, name)


def test_a_well_typed_call_still_reaches_its_child(tmp_path: Path) -> None:
    result, child = _executes("papersmith.run", {"profile": "smoke", "shard": 0, "dry_run": True}, tmp_path)
    assert child.call_count == 1, result
    assert child.call_args.args[0].tokens == ("run", "smoke", "--dry-run", "--shard", "0")

