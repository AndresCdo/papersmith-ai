"""The `hyperparameter-search` skill: a nested, equal-budget hyperparameter
search the experimental deliberation judged worthwhile, recorded per arm and
outer fold with its importance, contour and history figures.

The stdlib CLI is driven as a real subprocess, the way an agent drives it. The
one end-to-end report test needs an interpreter that has optuna and matplotlib;
it runs only when `HPO_TEST_PYTHON` names one, and skips otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "hyperparameter-search"
CLI_PATH = SKILL / "scripts" / "hpo_cli.py"
REPORT_PATH = SKILL / "scripts" / "optuna_report.py"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def load_cli():
    spec = importlib.util.spec_from_file_location("hpo_cli_under_test", CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CLI = load_cli()


class Run:
    """One CLI subprocess: exit code, stdout, stderr, parsed JSON of each."""

    def __init__(self, *argv: str) -> None:
        proc = subprocess.run([sys.executable, str(CLI_PATH), *argv],
                              capture_output=True, text=True, timeout=600)
        self.code, self.out, self.err = proc.returncode, proc.stdout, proc.stderr
        self.json = json.loads(self.out) if self.out.strip().startswith("{") else None
        self.error = json.loads(self.err) if self.err.strip().startswith("{") else None


def valid_plan(**overrides) -> dict:
    plan = {
        "schema": 1,
        "objective": {"metric": "val_loss", "direction": "minimize"},
        "sampler": {"name": "TPESampler", "seed": 42},
        "pruner": {"name": "MedianPruner", "nStartupTrials": 5, "nWarmupSteps": 2},
        "nTrials": 20,
        "maxEpochs": 10,
        "nested": {"outerFolds": 5,
                   "innerValidation": "a subject-wise split of each outer fold's training subjects"},
        "arms": ["proposed", "baseline-a"],
        "space": [
            {"name": "lr", "kind": "float", "low": 1e-4, "high": 1e-1, "log": True},
            {"name": "layers", "kind": "int", "low": 1, "high": 4, "log": False},
            {"name": "optimizer", "kind": "categorical", "choices": ["adam", "sgd"]},
        ],
        "fixed": ["n_qubits"],
        "importance": {"evaluator": "fanova", "seed": 0, "check": "ped-anova"},
    }
    plan.update(overrides)
    return plan


class Base(unittest.TestCase):
    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name).resolve()
        self.target = self.root / "target"
        (self.target / "Method" / "hpo").mkdir(parents=True)

    def write_plan(self, plan: dict) -> Path:
        path = self.target / "Method" / "hpo" / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def plan(self, plan: dict, *extra: str) -> Run:
        return Run("plan", "--file", str(self.write_plan(plan)), *extra)

    def assertRefuses(self, run: Run, code: str) -> None:
        self.assertEqual(run.code, 2, run.out + run.err)
        self.assertIsNotNone(run.error, run.err)
        self.assertEqual(run.error["error"], code, run.err)
        self.assertTrue(run.error["message"])
        self.assertEqual(run.error["objective"], CLI.OBJECTIVE_FLOW)


# ------------------------------------------------------------- plan rules
class PlanTests(Base):
    def test_a_valid_plan_passes_and_names_one_study_per_arm_and_fold(self) -> None:
        run = self.plan(valid_plan())
        self.assertEqual(run.code, 0, run.err)
        result = run.json
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["studies"]), 10)
        self.assertIn("proposed-fold1", result["studies"])
        self.assertIn("baseline-a-fold5", result["studies"])
        self.assertEqual(result["trialsPerStudy"], 20)
        self.assertEqual(result["trialsTotal"], 200)
        self.assertTrue(result["storage"].startswith("sqlite:///"))
        self.assertTrue(result["storage"].endswith("/Method/hpo/studies.db"))
        self.assertEqual(result["importance"]["evaluator"], "fanova")
        self.assertIs(result["launchAuthorization"], False)

    def test_a_missing_plan_file_is_refused(self) -> None:
        self.assertRefuses(Run("plan", "--file", str(self.root / "none.json")), "plan-missing")

    def test_a_plan_that_is_not_schema_1_is_refused(self) -> None:
        self.assertRefuses(self.plan(valid_plan(schema=2)), "plan-invalid")
        plan = valid_plan()
        del plan["objective"]
        self.assertRefuses(self.plan(plan), "plan-invalid")
        self.assertRefuses(self.plan(valid_plan(objective={"metric": "acc", "direction": "up"})),
                           "plan-invalid")
        path = self.target / "Method" / "hpo" / "plan.json"
        path.write_text("{not json", encoding="utf-8")
        self.assertRefuses(Run("plan", "--file", str(path)), "plan-invalid")

    def test_a_trial_budget_per_arm_is_refused(self) -> None:
        self.assertRefuses(self.plan(valid_plan(nTrials={"proposed": 50, "baseline-a": 10})),
                           "unequal-budget")
        self.assertRefuses(self.plan(valid_plan(nTrials=0)), "plan-invalid")

    def test_an_unseeded_sampler_is_refused(self) -> None:
        self.assertRefuses(self.plan(valid_plan(sampler={"name": "TPESampler"})), "unseeded-sampler")
        self.assertRefuses(self.plan(valid_plan(sampler={"name": "TPESampler", "seed": None})),
                           "unseeded-sampler")

    def test_each_space_rule_is_refused(self) -> None:
        bad_spaces = {
            "empty": [],
            "inverted bounds": [{"name": "lr", "kind": "float", "low": 0.1, "high": 0.01, "log": False}],
            "log at zero": [{"name": "lr", "kind": "float", "low": 0.0, "high": 0.1, "log": True}],
            "one choice": [{"name": "opt", "kind": "categorical", "choices": ["adam"]}],
            "unknown kind": [{"name": "lr", "kind": "uniform", "low": 0.0, "high": 1.0}],
            "duplicate": [{"name": "lr", "kind": "float", "low": 0.1, "high": 0.2, "log": False}] * 2,
        }
        for label, space in bad_spaces.items():
            with self.subTest(case=label):
                self.assertRefuses(self.plan(valid_plan(space=space)), "bad-space")

    def test_a_tested_independent_variable_is_never_tuned(self) -> None:
        self.assertRefuses(self.plan(valid_plan(fixed=["lr"])), "tunes-fixed")

    def test_several_outer_folds_need_the_inner_validation_statement(self) -> None:
        self.assertRefuses(self.plan(valid_plan(nested={"outerFolds": 5, "innerValidation": ""})),
                           "not-nested")
        one_fold = self.plan(valid_plan(nested={"outerFolds": 1, "innerValidation": ""}))
        self.assertEqual(one_fold.code, 0, one_fold.err)

    def test_the_importance_evaluator_is_declared_and_seeded(self) -> None:
        self.assertRefuses(self.plan(valid_plan(importance={"evaluator": "shap", "seed": 0, "check": None})),
                           "bad-evaluator")
        self.assertRefuses(self.plan(valid_plan(importance={"evaluator": "fanova", "check": None})),
                           "bad-evaluator")
        self.assertRefuses(self.plan(valid_plan(importance={"evaluator": "mean-decrease-impurity",
                                                            "seed": None, "check": None})),
                           "bad-evaluator")
        self.assertRefuses(self.plan(valid_plan(importance={"evaluator": "fanova", "seed": 0,
                                                            "check": "fanova"})),
                           "bad-evaluator")
        ped = self.plan(valid_plan(importance={"evaluator": "ped-anova", "seed": None, "check": None}))
        self.assertEqual(ped.code, 0, ped.err)

    def test_a_seeded_check_evaluator_needs_the_seed_too(self) -> None:
        self.assertRefuses(self.plan(valid_plan(importance={"evaluator": "ped-anova", "seed": None,
                                                            "check": "fanova"})),
                           "bad-evaluator")
        seeded = self.plan(valid_plan(importance={"evaluator": "ped-anova", "seed": 7, "check": "fanova"}))
        self.assertEqual(seeded.code, 0, seeded.err)


# ------------------------------------------------------------- estimate
class EstimateTests(Base):
    def timing(self, measurements: list[dict]) -> Path:
        path = self.target / "Method" / "Results" / "timing.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema": 1, "measurements": measurements,
                                    "scales": {"poc": {"arms": 2, "folds": 1, "seeds": 1, "epochs": 1},
                                               "full": {"arms": 2, "folds": 5, "seeds": 3, "epochs": 10}}}),
                        encoding="utf-8")
        return path

    @staticmethod
    def measurement(seconds: float, host: str = "local", device: str = "cpu", arm: str = "proposed") -> dict:
        return {"measuredAt": "2026-10-25T10:00:00Z", "host": host, "device": device, "arm": arm,
                "unit": "epoch", "secondsPerUnit": seconds, "unitsMeasured": 1}

    def test_the_estimate_is_trials_arms_folds_epochs_seconds_with_its_range(self) -> None:
        timing = self.timing([self.measurement(2.0), self.measurement(4.0, arm="baseline-a")])
        run = self.plan(valid_plan(), "--timing", str(timing), "--host", "gpu:alice")
        self.assertEqual(run.code, 0, run.err)
        local = run.json["estimate"]["local"]
        # 20 trials x 2 arms x 5 folds x 10 epochs x mean(2, 4) = 6000 s.
        self.assertEqual(local["seconds"], 6000)
        self.assertEqual(local["low"], 4800)
        self.assertEqual(local["high"], 7200)
        self.assertIn("20 trials", local["formula"])
        self.assertEqual(run.json["estimate"]["gpu:alice"], "unmeasured")
        self.assertIn("upper bound", run.json["range"])
        self.assertIn("pruning", run.json["range"])

    def test_a_missing_or_malformed_timing_record_is_refused(self) -> None:
        self.assertRefuses(self.plan(valid_plan(), "--timing", str(self.root / "none.json")), "timing-missing")
        bad = self.timing([dict(self.measurement(2.0), unit="step")])
        self.assertRefuses(self.plan(valid_plan(), "--timing", str(bad)), "timing-invalid")

    def test_a_host_without_a_timing_record_is_refused_not_ignored(self) -> None:
        self.assertRefuses(self.plan(valid_plan(), "--host", "remote:bob"), "timing-missing")

    def test_one_host_on_two_devices_is_refused(self) -> None:
        timing = self.timing([self.measurement(2.0), self.measurement(3.0, device="mps")])
        self.assertRefuses(self.plan(valid_plan(), "--timing", str(timing)), "mixed-devices")


# ------------------------------------------------------------- status and report
def summary(study: str, arm: str, fold, **overrides) -> dict:
    record = {
        "schema": 1, "study": study, "arm": arm, "fold": fold,
        "objective": {"metric": "val_loss", "direction": "minimize"},
        "sampler": {"name": "TPESampler", "seed": 42}, "pruner": "MedianPruner",
        "nTrials": 20, "complete": 18, "pruned": 2, "failed": 0,
        "bestValue": 0.25, "bestParams": {"lr": 0.01, "layers": 2},
        "space": valid_plan()["space"],
        "importance": {"evaluator": "fanova", "seed": 0, "values": {"lr": 0.7, "layers": 0.3}},
        "importanceCheck": None, "contourParams": ["lr", "layers"],
        "figures": {"contour": "contour.png", "importance": "importance.png", "history": "history.png"},
        "optunaVersion": "5.0.0", "generatedAt": "2026-10-25T10:00:00+00:00",
    }
    record.update(overrides)
    return record


class StatusTests(Base):
    def put_summary(self, record: dict) -> Path:
        folder = self.target / "Method" / "Results" / "hpo" / record["study"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "summary.json").write_text(json.dumps(record), encoding="utf-8")
        for name in (record.get("figures") or {}).values():
            if name:
                (folder / name).write_bytes(PNG_MAGIC + b"x")
        return folder

    def test_status_lists_each_study_with_its_best_value_and_top_parameter(self) -> None:
        self.put_summary(summary("proposed-fold1", "proposed", 1))
        folder = self.put_summary(summary("baseline-a-fold1", "baseline-a", 1, bestValue=0.4,
                                          importance={"evaluator": "fanova", "seed": 0,
                                                      "values": {"lr": 0.1, "layers": 0.9}}))
        (folder / "history.png").unlink()
        run = Run("status", "--target", str(self.target), "--name", "Method")
        self.assertEqual(run.code, 0, run.err)
        rows = {row["study"]: row for row in run.json["studies"]}
        self.assertEqual(set(rows), {"proposed-fold1", "baseline-a-fold1"})
        self.assertEqual(rows["proposed-fold1"]["arm"], "proposed")
        self.assertEqual(rows["proposed-fold1"]["fold"], 1)
        self.assertEqual(rows["proposed-fold1"]["trials"], 20)
        self.assertEqual(rows["proposed-fold1"]["bestValue"], 0.25)
        self.assertEqual(rows["proposed-fold1"]["topParameter"], "lr")
        self.assertEqual(rows["baseline-a-fold1"]["topParameter"], "layers")
        self.assertEqual(rows["baseline-a-fold1"]["missingFigures"], ["history"])
        # A missing figure keeps the search behind `reported`.
        self.assertEqual(run.json["stage"], "searched")
        (folder / "history.png").write_bytes(PNG_MAGIC + b"x")
        again = Run("status", "--target", str(self.target), "--name", "Method")
        self.assertEqual(again.json["stage"], "reported")

    def test_status_with_a_plan_names_the_studies_still_missing(self) -> None:
        self.write_plan(valid_plan(nested={"outerFolds": 1, "innerValidation": ""}))
        self.put_summary(summary("proposed-fold1", "proposed", 1))
        run = Run("status", "--target", str(self.target), "--name", "Method")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.json["missingStudies"], ["baseline-a-fold1"])
        self.assertNotEqual(run.json["stage"], "reported")

    def test_status_on_a_missing_target_or_a_bad_name_is_refused(self) -> None:
        self.assertRefuses(Run("status", "--target", str(self.root / "nope"), "--name", "Method"),
                           "target-missing")
        self.assertRefuses(Run("status", "--target", str(self.target), "--name", "../x"), "bad-name")


class ReportRefusalTests(Base):
    def test_report_without_the_target_venv_is_refused(self) -> None:
        self.write_plan(valid_plan())
        (self.target / "Method" / "hpo" / "studies.db").write_bytes(b"")
        self.assertRefuses(Run("report", "--target", str(self.target), "--name", "Method"), "venv-missing")

    def test_report_without_optuna_is_refused(self) -> None:
        self.write_plan(valid_plan())
        (self.target / "Method" / "hpo" / "studies.db").write_bytes(b"")
        # The interpreter running this suite carries no optuna.
        probe = subprocess.run([sys.executable, "-I", "-c", "import optuna"], capture_output=True)
        if probe.returncode == 0:
            self.skipTest("this interpreter has optuna")
        self.assertRefuses(Run("report", "--target", str(self.target), "--name", "Method",
                               "--python", sys.executable), "optuna-missing")

    def test_report_without_a_plan_or_storage_is_refused(self) -> None:
        self.assertRefuses(Run("report", "--target", str(self.target), "--name", "Method"), "plan-missing")
        self.write_plan(valid_plan())
        self.assertRefuses(Run("report", "--target", str(self.target), "--name", "Method"), "storage-missing")


HPO_PYTHON = os.environ.get("HPO_TEST_PYTHON")

SEARCH_SCRIPT = r"""
import sys, warnings, optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
storage = sys.argv[1]
for arm, shift in (("proposed", 0.0), ("baseline-a", 0.5)):
    for fold in (1, 2):
        study = optuna.create_study(study_name=f"{arm}-fold{fold}", storage=storage,
                                    direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42 + fold),
                                    pruner=optuna.pruners.MedianPruner(n_startup_trials=3))
        def objective(trial):
            lr = trial.suggest_float("lr", 1e-4, 1e-1, log=True)
            layers = trial.suggest_int("layers", 1, 4)
            opt = trial.suggest_categorical("optimizer", ["adam", "sgd"])
            return (lr - 0.01) ** 2 * 100 + 0.1 * layers + (0.05 if opt == "sgd" else 0.0) + shift
        study.optimize(objective, n_trials=12)
"""


@unittest.skipUnless(HPO_PYTHON, "HPO_TEST_PYTHON names no interpreter with optuna and matplotlib")
class ReportEndToEndTests(Base):
    def test_report_writes_each_summary_and_its_three_figures(self) -> None:
        plan = valid_plan(nTrials=12, nested={"outerFolds": 2, "innerValidation": "inner subject split"})
        self.write_plan(plan)
        db = self.target / "Method" / "hpo" / "studies.db"
        subprocess.run([HPO_PYTHON, "-I", "-c", SEARCH_SCRIPT, f"sqlite:///{db}"], check=True,
                       capture_output=True, timeout=600)
        run = Run("report", "--target", str(self.target), "--name", "Method", "--python", HPO_PYTHON)
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(len(run.json["summaries"]), 4)
        record = json.loads((self.target / "Method" / "Results" / "hpo" / "proposed-fold1"
                             / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(record["schema"], 1)
        self.assertEqual(record["study"], "proposed-fold1")
        self.assertEqual(record["arm"], "proposed")
        self.assertEqual(record["fold"], 1)
        self.assertEqual(record["objective"], plan["objective"])
        self.assertEqual(record["sampler"], {"name": "TPESampler", "seed": 42})
        self.assertEqual(record["pruner"], "MedianPruner")
        self.assertEqual(record["nTrials"], 12)
        self.assertEqual(record["complete"] + record["pruned"] + record["failed"], 12)
        self.assertIsInstance(record["bestValue"], float)
        self.assertEqual(set(record["bestParams"]), {"lr", "layers", "optimizer"})
        self.assertEqual(record["space"], plan["space"])
        self.assertEqual(record["importance"]["evaluator"], "fanova")
        self.assertEqual(record["importance"]["seed"], 0)
        self.assertEqual(set(record["importance"]["values"]), {"lr", "layers", "optimizer"})
        self.assertEqual(record["importanceCheck"]["evaluator"], "ped-anova")
        self.assertEqual(len(record["contourParams"]), 3)
        self.assertTrue(re.match(r"^\d+\.\d+\.\d+", record["optunaVersion"]))
        self.assertTrue(record["generatedAt"])
        folder = self.target / "Method" / "Results" / "hpo" / "proposed-fold1"
        for kind in ("contour", "importance", "history"):
            with self.subTest(figure=kind):
                self.assertEqual(record["figures"][kind], f"{kind}.png")
                png = (folder / f"{kind}.png").read_bytes()
                self.assertTrue(png.startswith(PNG_MAGIC))
                self.assertGreater(len(png), 1000)
                self.assertGreater((folder / f"{kind}.pdf").stat().st_size, 0)
        status = Run("status", "--target", str(self.target), "--name", "Method")
        self.assertEqual(status.code, 0, status.err)
        self.assertEqual(status.json["stage"], "reported")
        self.assertEqual(status.json["missingStudies"], [])


# ------------------------------------------------------------- doctrine
def _table_rows(doc: str, heading: str) -> list[list[str]]:
    """The cells of the first Markdown table after `heading`."""
    start = doc.index(heading)
    rows, seen = [], False
    for line in doc[start:].splitlines()[1:]:
        if line.startswith("|"):
            seen = True
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            rows.append(cells)
        elif seen:
            break
    return rows[1:]


class DoctrineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.flat = " ".join(self.doc.split())

    def test_frontmatter_names_the_skill_and_its_trigger(self) -> None:
        self.assertTrue(self.doc.startswith("---\nname: hyperparameter-search\n"))
        header = self.doc.split("---", 2)[1]
        match = re.search(r'^description: "(.+)"$', header, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertTrue(match.group(1).startswith("Trigger: "))

    def test_the_objective_flow_table_equals_the_code(self) -> None:
        rows = _table_rows(self.doc, "## The objective flow")
        declared = [[f"`{s['stage']}`", s["establishes"], s["behindWhen"]]
                    for s in CLI.OBJECTIVE_FLOW["stages"]]
        self.assertEqual(rows, declared)
        self.assertEqual([s["stage"] for s in CLI.OBJECTIVE_FLOW["stages"]],
                         ["planned", "searched", "reported"])
        self.assertIn(f"**Arrival:** {CLI.OBJECTIVE_FLOW['arrival']}.", self.flat)

    def test_the_error_code_table_equals_the_code(self) -> None:
        rows = _table_rows(self.doc, "### Error codes")
        documented = [row[0].strip("`") for row in rows]
        self.assertEqual(documented, list(CLI.ERROR_CODES))
        source = CLI_PATH.read_text(encoding="utf-8")
        raised = set(re.findall(r'Refusal\(\s*"([a-z-]+)"', source))
        self.assertEqual(raised, set(CLI.ERROR_CODES))

    def test_every_documented_verb_is_real(self) -> None:
        rows = _table_rows(self.doc, "## Accepted operations")
        documented = [row[0].strip("`") for row in rows]
        self.assertEqual(documented, list(CLI.VERBS))
        for verb in CLI.VERBS:
            with self.subTest(verb=verb):
                proc = subprocess.run([sys.executable, str(CLI_PATH), verb, "--help"],
                                      capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 0, proc.stderr)
        unknown = subprocess.run([sys.executable, str(CLI_PATH), "launch"],
                                 capture_output=True, text=True, timeout=60)
        self.assertEqual(unknown.returncode, 2)

    def test_the_doctrine_states_the_search_rules(self) -> None:
        for fragment in ("worthwhile", "training subjects", "test subjects are never seen",
                         "equal trial budget", "baselines included", "`fixed`",
                         "seeded sampler", "PED-ANOVA", "fANOVA",
                         "https://proceedings.mlr.press/v32/hutter14.html",
                         "10.1145/3292500.3330701", "descriptive", "never a hypothesis test",
                         "frozen per outer fold", "every seed of the full run",
                         "remote-execution", "never launches", "Claude Code, OpenCode and Pi",
                         "<arm>-fold<k>", "Results/hpo/<study>/summary.json"):
            self.assertIn(fragment, self.flat, fragment)

    def test_the_skill_delegates_to_no_agent(self) -> None:
        self.assertNotIn("delegates to the `", self.doc)

    def test_the_cli_is_stdlib_only(self) -> None:
        allowed = set(sys.stdlib_module_names) | {"__future__"}
        text = CLI_PATH.read_text(encoding="utf-8")
        for name in re.findall(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", text, re.MULTILINE):
            self.assertIn(name, allowed, name)

    def test_the_skill_ships_no_forbidden_vocabulary(self) -> None:
        sys.path.insert(0, str(ROOT / "tests"))
        import forge_vocabulary  # noqa: E402  (path set above)
        for path in sorted(SKILL.rglob("*")):
            if path.is_file() and forge_vocabulary.is_scannable_text(path):
                with self.subTest(path=path.name):
                    self.assertEqual(forge_vocabulary.leaks_in(path.read_text(encoding="utf-8")), [])


class HostDoctrineTests(unittest.TestCase):
    def test_the_deliberation_says_when_to_declare_a_search(self) -> None:
        doc = " ".join((ROOT / "skills" / "experimental-deliberation" / "SKILL.md")
                       .read_text(encoding="utf-8").split())
        for fragment in ("Hyperparameter Search", "worthwhile", "published defaults",
                         "fair comparison", "sampler seed", "evaluator", "never tunes",
                         "`hyperparameter-search`"):
            self.assertIn(fragment, doc, fragment)

    def test_the_implementation_places_the_step_before_the_full_runs(self) -> None:
        doc = " ".join((ROOT / "skills" / "experimental-implementation" / "SKILL.md")
                       .read_text(encoding="utf-8").split())
        for fragment in ("/hyperparameter-search", "after the proof of concept",
                         "timing estimate", "before the full runs", "frozen per outer fold",
                         "remote-execution"):
            self.assertIn(fragment, doc, fragment)


if __name__ == "__main__":
    unittest.main()
