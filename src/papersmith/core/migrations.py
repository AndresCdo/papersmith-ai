"""Artifact migrations: what a release changes beyond the files it ships.

``upgrade`` synchronizes framework FILES and preserves research state by not
touching it. That holds only while the shape of an artifact never changes. This
module carries a workspace's own artifacts — graph state, derived indices,
scaffolded topology — to the installed release's expectations, so the version a
workspace records is a claim about its artifacts and not only about its skills
tree.

Two kinds of migration share one mechanism:

* A **version-gated** migration (``applies_from`` set) is a shape change
  between releases. It runs once, when the workspace sits below the gate and
  the installed kit sits at or above it, and the applied ledger keeps it from
  running again.
* A **convergence** migration (``applies_from`` is ``None``) makes the
  workspace match the installed release regardless of its history. It is
  evaluated on every upgrade and is never recorded as finished, because the
  next release can change what there is to converge to. Its :meth:`Migration.
  plan` is a probe, so an already-satisfied workspace yields no actions and
  nothing is written.

Nothing here decides whether to write ``.papersmith/version``; ``upgrade`` owns
that, and it is the ordering that makes the whole thing honest — see
:func:`upgrade.upgrade`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from ..errors import SourceError, UserError
from . import fs
from .config import utc_timestamp

#: The applied-migration ledger, workspace state like ``runs_ledger.jsonl``
#: rather than configuration: ``config.json`` carries a validator and is
#: rewritten by ``upgrade`` on every run, and this is history.
LEDGER_REL = ".papersmith/migrations.json"
LEDGER_SCHEMA = 1


def version_order(value: str) -> tuple[int, ...] | None:
    """``value`` as an orderable tuple, or ``None`` when it carries no order.

    Only the leading dot-separated run of integers is read, so ``0.2.0rc1``
    orders beside ``0.2.0`` rather than refusing: a prerelease suffix is a claim
    this function is not equipped to rank, and treating the two as equal
    declines to guess in the direction that blocks nothing. A value with no
    leading integer at all — a branch name, a build label, an empty string —
    returns ``None``, because there is no order to report and inventing one is
    how a downgrade gets waved through.

    Lives here rather than in ``upgrade`` because two callers now need it: the
    downgrade guard and the migration gate, which refuse for the same reason.
    """
    parts: list[int] = []
    for chunk in value.strip().split("."):
        digits = ""
        for character in chunk:
            if not character.isdigit():
                break
            digits += character
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) or None


class Migration:
    """One artifact change a release requires of an existing workspace.

    Subclasses set :attr:`id` — stable forever, because the ledger stores it —
    a one-line :attr:`summary`, and :attr:`applies_from` when the change
    belongs to a specific release. They implement :meth:`plan` as a read-only
    probe and :meth:`apply` as the writer.

    Neither method may raise for a condition the workspace can be in. A missing
    script, an unreadable artifact or a refusing filesystem is a *failure
    returned* by :meth:`apply`, because a migration that raises aborts a run
    that has already synchronized files, and the operator is left with no
    report of what did happen.
    """

    #: Stable identity recorded in the ledger. Renaming one re-runs it.
    id: str = ""
    #: The release whose shape this migration establishes, or ``None`` for a
    #: convergence step with no gate.
    applies_from: str | None = None
    #: One line, shown by ``--plan-migrations`` and by the upgrade report.
    summary: str = ""

    def plan(self, workspace: Path) -> list[str]:
        """Human-readable actions this migration would take, read-only.

        An empty list means the workspace already satisfies it; ``apply`` is
        then never called.
        """
        raise NotImplementedError

    def apply(self, workspace: Path) -> tuple[list[str], list[str]]:
        """Perform the migration. Returns ``(actions_done, failures)``."""
        raise NotImplementedError


@dataclass(frozen=True)
class Outcome:
    """What one migration did, and why it could not finish."""

    migration_id: str
    applies_from: str | None
    actions: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def recordable(self) -> bool:
        """Only a successful gated migration is finished for good."""
        return self.applies_from is not None and self.ok


@dataclass(frozen=True)
class RunReport:
    """The result of one migration pass, for ``upgrade`` to report and gate on."""

    applied: list[Outcome] = field(default_factory=list)
    satisfied: list[str] = field(default_factory=list)
    undetermined: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    recorded: bool = False

    @property
    def ok(self) -> bool:
        """Undetermined is not failure: nothing was attempted and nothing lied."""
        return not self.failures


@dataclass(frozen=True)
class PlanReport:
    """What a pass WOULD do, having written nothing."""

    pending: list[Outcome] = field(default_factory=list)
    satisfied: list[str] = field(default_factory=list)
    undetermined: list[str] = field(default_factory=list)


def ledger_path(workspace: Path) -> Path:
    return workspace / LEDGER_REL


def read_applied(workspace: Path) -> list[dict]:
    """Every migration this workspace has recorded as finished.

    A damaged ledger refuses rather than reading as empty, mirroring
    ``manifest.load_manifest``. The run ledger can afford to degrade because a
    lost run record costs a line of history; this one cannot, because reading
    it as empty re-applies every version-gated migration it was holding.
    """
    path = ledger_path(workspace)
    if not fs.is_regular_file(path):
        if fs.exists(path):
            raise UserError(f"corrupted migrations ledger {path}: not a readable regular file")
        return []
    text = fs.read_text(path)
    if text is None:
        raise UserError(f"corrupted migrations ledger {path}: unreadable or not valid UTF-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UserError(f"corrupted migrations ledger {path}: {exc}") from None
    if not isinstance(data, dict) or data.get("kind") != "migrations":
        raise UserError(f"corrupted migrations ledger {path}: missing migrations envelope")
    if data.get("schema") != LEDGER_SCHEMA:
        raise UserError(f"corrupted migrations ledger {path}: unsupported schema")
    applied = data.get("applied")
    if not isinstance(applied, list) or any(
        not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
        for entry in applied
    ):
        raise UserError(f"corrupted migrations ledger {path}: malformed applied list")
    return applied


def _write_applied(workspace: Path, applied: Sequence[dict]) -> bool:
    """Record the ledger, or report that it could not be recorded.

    Returns False rather than raising: by the time this runs the migrations
    have already happened, and an unwritable ledger must be reported beside
    them instead of discarding the report of work that is already done. The
    caller refuses to advance the version marker, so a later run retries.
    """
    document = {
        "schema": LEDGER_SCHEMA,
        "kind": "migrations",
        "applied": list(applied),
        "updated_at": utc_timestamp(),
    }
    return fs.write_text(ledger_path(workspace), json.dumps(document, indent=2) + "\n")


def _gate_order(migration: Migration) -> tuple[int, ...]:
    order = version_order(migration.applies_from or "")
    if order is None:
        raise SourceError(
            f"migration {migration.id!r} declares an unorderable applies_from "
            f"({migration.applies_from!r}): a gate nobody can place is a defect "
            "in the installed framework, not in this workspace")
    return order


def _select(registry: Sequence[Migration], *, recorded: str, kit_version: str,
            applied_ids: set[str]) -> tuple[list[Migration], list[str]]:
    """Partition the registry into what to evaluate and what cannot be placed.

    Registry order is preserved, because a later migration may depend on an
    earlier one having run.
    """
    pending: list[Migration] = []
    undetermined: list[str] = []
    recorded_order = version_order(recorded)
    kit_order = version_order(kit_version)
    for migration in registry:
        if migration.applies_from is None:
            # Convergence: it asks the filesystem, so no version can withhold it.
            pending.append(migration)
            continue
        gate = _gate_order(migration)
        if migration.id in applied_ids:
            continue
        if kit_order is None or recorded_order is None:
            # Either side missing leaves the gate unplaceable. Reported, never
            # applied — the refusal `_refuse_a_downgrade` makes for files.
            undetermined.append(migration.id)
            continue
        if kit_order < gate:
            # The release that introduced this migration has not reached this
            # workspace; its artifacts would outrun its files.
            continue
        if recorded_order >= gate:
            continue
        pending.append(migration)
    return pending, undetermined


def plan(workspace: Path, *, recorded: str, kit_version: str,
         registry: Sequence[Migration] | None = None) -> PlanReport:
    """What a migration pass would do, having written nothing."""
    entries = REGISTRY if registry is None else registry
    applied_ids = {entry["id"] for entry in read_applied(workspace)}
    selected, undetermined = _select(entries, recorded=recorded, kit_version=kit_version,
                                     applied_ids=applied_ids)
    pending: list[Outcome] = []
    satisfied: list[str] = []
    for migration in selected:
        actions = migration.plan(workspace)
        if not actions:
            satisfied.append(migration.id)
            continue
        pending.append(Outcome(migration.id, migration.applies_from, tuple(actions)))
    return PlanReport(pending=pending, satisfied=satisfied, undetermined=undetermined)


def run(workspace: Path, *, recorded: str, kit_version: str,
        registry: Sequence[Migration] | None = None) -> RunReport:
    """Apply every selected migration and report what happened.

    The ledger is read first and in full, so a damaged one refuses before any
    artifact is touched. Only successful gated migrations are recorded: a
    recorded failure would retire a migration that never ran, leaving old
    artifacts under a new version with nothing left to notice.
    """
    entries = REGISTRY if registry is None else registry
    ledger = read_applied(workspace)
    applied_ids = {entry["id"] for entry in ledger}
    selected, undetermined = _select(entries, recorded=recorded, kit_version=kit_version,
                                     applied_ids=applied_ids)

    applied: list[Outcome] = []
    satisfied: list[str] = []
    failures: list[str] = []
    additions: list[dict] = []
    for migration in selected:
        planned = migration.plan(workspace)
        if not planned:
            satisfied.append(migration.id)
            if migration.applies_from is not None:
                # The gate is passed with nothing to do. Recording it is what
                # keeps the probe from being re-run for every later release.
                additions.append(_entry(migration, kit_version, ()))
            continue
        actions, problems = migration.apply(workspace)
        outcome = Outcome(migration.id, migration.applies_from, tuple(actions), tuple(problems))
        applied.append(outcome)
        failures.extend(f"{migration.id}: {problem}" for problem in problems)
        if outcome.recordable:
            additions.append(_entry(migration, kit_version, outcome.actions))

    wrote = False
    if additions:
        wrote = _write_applied(workspace, [*ledger, *additions])
        if not wrote:
            failures.append(
                f"could not record applied migrations in {ledger_path(workspace)}; "
                "they would be re-applied on the next run")
    return RunReport(applied=applied, satisfied=satisfied, undetermined=undetermined,
                     failures=failures, recorded=wrote)


def _entry(migration: Migration, kit_version: str, actions: Sequence[str]) -> dict:
    return {
        "id": migration.id,
        "version": migration.applies_from,
        "kit_version": kit_version,
        "applied_at": utc_timestamp(),
        "actions": list(actions),
    }


#: Every migration this release ships, in the order they must run.
#:
#: A gate at or below the current version would never be selected for a
#: workspace already on it and would fire for every older one without the
#: release that introduced it ever existing — ``test_the_shipped_registry_
#: declares_no_gate_at_or_below_this_release`` holds the rule.
REGISTRY: tuple[Migration, ...] = ()
