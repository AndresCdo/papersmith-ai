"""B6: the array backend is declared, not inferred from incidental imports.

The kit's `tests/conftest.py` and `tests/sweep.py` imported numpy for a seeded
generator, so a target whose modules compute in torch read as `mixed` by
import inference and `probe` routed it to `convert` forever. The kit files are
now backend-neutral, a target may state its backend in `src/<Package>/
__init__.py` (`__backend__`), import inference stays the fallback when nothing
is declared, and `env --torch cpu|gpu` provisions the torch variant (plain
`torch` from PyPI pulls CUDA wheels; CPU needs the PyTorch CPU index and an
exact `+cpu` pin).
"""

from __future__ import annotations

import argparse
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FORGE = Path(__file__).resolve().parents[1]
ENGINE = FORGE / "skills/_core/implementation/engine/implementation_engine.py"
sys.path.insert(0, str(ENGINE.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_profile import seeded_profile  # noqa: E402  (path set above)
with seeded_profile(FORGE / "skills/proposal-implementation/impl_profile.py"):
    import implementation_engine as impl  # noqa: E402  (path set above)
from impl_refusals import Refused  # noqa: E402

KIT = FORGE / "skills/proposal-implementation/assets"
ARRAY_BACKENDS = {"numpy", *impl.TENSOR_BACKENDS}
NAME = "Some-Method"
PACKAGE = impl.package_name(NAME)


class KitIsBackendNeutralTests(unittest.TestCase):
    def test_the_shared_test_helpers_import_no_array_backend(self) -> None:
        for rel in ("kit/tests/conftest.py", "kit/tests/sweep.py"):
            with self.subTest(file=rel):
                text = (KIT / rel).read_text(encoding="utf-8").replace("{{SEED}}", "7")
                scratch = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, scratch)
                (scratch / "f.py").write_text(text, encoding="utf-8")
                self.assertEqual(impl.imported_modules(scratch / "f.py") & ARRAY_BACKENDS, set())

    def test_the_scaffold_pyprojects_depend_on_no_array_backend(self) -> None:
        for label, text in (("template", (KIT / "pyproject.template.toml").read_text(encoding="utf-8")),
                            ("default", impl._DEFAULT_PYPROJECT)):
            with self.subTest(pyproject=label):
                line = next(row for row in text.splitlines() if row.startswith("dependencies"))
                self.assertFalse(any(name in line for name in ARRAY_BACKENDS), line)


class BackendDeclarationTests(unittest.TestCase):
    def target(self, *, init: str = "", module: str = "import torch\n",
               conftest: str = "import numpy as np\n") -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "src" / PACKAGE).mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "src" / PACKAGE / "__init__.py").write_text(init, encoding="utf-8")
        (root / "src" / PACKAGE / "model.py").write_text(module, encoding="utf-8")
        (root / "tests" / "conftest.py").write_text(conftest, encoding="utf-8")
        return root

    def test_undeclared_falls_back_to_import_inference(self) -> None:
        state = impl.backend_state(self.target(), NAME)
        self.assertEqual(state["state"], "mixed")
        self.assertEqual(state["source"], "imports")
        self.assertIsNone(state["declared"])
        self.assertFalse(state["trainable"])

    def test_a_declared_tensor_backend_is_read_over_incidental_imports(self) -> None:
        state = impl.backend_state(self.target(init='__backend__ = "torch"\n'), NAME)
        self.assertEqual(state["state"], "tensor")
        self.assertEqual(state["source"], "declared")
        self.assertEqual(state["declared"], "torch")
        self.assertTrue(state["trainable"])
        self.assertEqual(state["numpyFiles"], ["tests/conftest.py"])

    def test_a_declared_tensor_backend_no_module_computes_with_is_not_trainable(self) -> None:
        state = impl.backend_state(
            self.target(init='__backend__ = "torch"\n', module="import numpy\n"), NAME)
        self.assertEqual(state["state"], "declared-unmet")
        self.assertFalse(state["trainable"])

    def test_a_declared_numpy_backend_is_not_trainable(self) -> None:
        state = impl.backend_state(self.target(init='__backend__ = "numpy"\n'), NAME)
        self.assertEqual(state["state"], "numpy")
        self.assertFalse(state["trainable"])

    def test_an_unrecognized_declaration_fails_closed(self) -> None:
        for raw in ('"pytorch"', "3", "f()"):
            with self.subTest(value=raw):
                state = impl.backend_state(self.target(init=f"__backend__ = {raw}\n"), NAME)
                self.assertEqual(state["state"], "unrecognized-backend")
                self.assertFalse(state["trainable"])
                self.assertIn("declarationError", state)

    def test_none_reads_as_undeclared(self) -> None:
        state = impl.backend_state(self.target(init="__backend__ = None\n"), NAME)
        self.assertEqual(state["source"], "imports")


class TorchVariantTests(unittest.TestCase):
    def target(self, files=()) -> Path:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        for name, text in files:
            (root / name).write_text(text, encoding="utf-8")
        return root

    def test_no_variant_adds_nothing(self) -> None:
        self.assertEqual(impl.torch_provisioning(self.target(), None, None)["args"], [])

    def test_cpu_uses_the_cpu_index_and_an_exact_local_pin(self) -> None:
        found = impl.torch_provisioning(self.target(), "cpu", "2.4.1")
        self.assertEqual(found["args"], ["--extra-index-url", impl.TORCH_CPU_INDEX, "torch==2.4.1+cpu"])
        self.assertEqual(found["requirement"], "torch==2.4.1+cpu")

    def test_cpu_reads_the_exact_pin_a_manifest_carries(self) -> None:
        root = self.target([("requirements.txt", "numpy\ntorch==2.3.0\n")])
        found = impl.torch_provisioning(root, "cpu", None)
        self.assertEqual(found["requirement"], "torch==2.3.0+cpu")

    def test_cpu_without_an_exact_version_refuses(self) -> None:
        root = self.target([("requirements.txt", "torch>=2\n")])
        with self.assertRaises(Refused) as caught:
            impl.torch_provisioning(root, "cpu", None)
        self.assertEqual(caught.exception.code, "TORCH_VERSION_REQUIRED")

    def test_gpu_takes_the_default_index(self) -> None:
        self.assertEqual(impl.torch_provisioning(self.target(), "gpu", None)["args"], ["torch"])
        self.assertEqual(impl.torch_provisioning(self.target(), "gpu", "2.4.1")["args"],
                         ["torch==2.4.1"])

    def test_a_version_that_is_not_a_plain_release_refuses(self) -> None:
        with self.assertRaises(Refused) as caught:
            impl.torch_provisioning(self.target(), "cpu", "2.4.1 --index-url x")
        self.assertEqual(caught.exception.code, "TORCH_VERSION_REQUIRED")

    def test_env_appends_the_variant_to_its_printed_install(self) -> None:
        target = FORGE / "implementations" / f"_backend_env_{os.getpid()}"
        shutil.rmtree(target, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(target)], check=True)
        self.addCleanup(shutil.rmtree, target, ignore_errors=True)
        result = impl.cmd_env(argparse.Namespace(
            target=str(target), python=sys.executable, torch="cpu", torch_version="2.4.1"))
        self.assertTrue(result["nextCommand"].endswith(
            f"--extra-index-url {impl.TORCH_CPU_INDEX} torch==2.4.1+cpu"), result["nextCommand"])
        self.assertEqual(result["torch"]["variant"], "cpu")


class EnvParserTests(unittest.TestCase):
    CLI = FORGE / "skills/proposal-implementation/scripts/implementation_cli.py"

    def run_env(self, *extra: str) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if k != "IMPLEMENTATION_DOMAIN_PROFILE"}
        return subprocess.run([sys.executable, str(self.CLI), "env", "--target", "/nonexistent-b6",
                               *extra], capture_output=True, text=True, env=env)

    def test_env_accepts_the_torch_flags(self) -> None:
        proc = self.run_env("--torch", "gpu", "--torch-version", "2.4.1")
        self.assertIn("OUTSIDE_WORKSPACE", proc.stdout, proc.stderr)

    def test_env_refuses_an_unknown_variant_at_parse_time(self) -> None:
        proc = self.run_env("--torch", "tpu")
        self.assertEqual(proc.returncode, 2, proc.stdout)


if __name__ == "__main__":
    unittest.main()
