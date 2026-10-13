"""X8b: one test file cannot leave process state behind for the next.

The suite runs in one process. A test that leaves a variable in `os.environ`,
a changed working directory, or a cached `impl_domain_profile` module changes
what every later test reads -- measured as a later test handing `os.environ`
to the other skill's launcher and reading the wrong holder, green alone and red
in the change-selected tier. `tests/conftest.py` restores that state after
every test and every module.

Proven on the real conftest, in a child pytest run: a first file leaks through
each path a test can take (test body, `setUp`, `setUpClass`, `setUpModule`)
and a second file asserts it sees none of it. The same run without the conftest
is the control: it must fail, or the probe would be proving nothing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

CONFTEST = Path(__file__).resolve().parent / "conftest.py"

LEAKS = textwrap.dedent('''
    import os
    import sys
    import types
    import unittest

    def setUpModule():
        os.environ["X8B_PROBE_MODULE"] = "leaked"
        sys.modules["impl_domain_profile"] = types.ModuleType("impl_domain_profile")

    class Leaks(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            os.environ["X8B_PROBE_CLASS"] = "leaked"
            os.environ["X8B_PROBE_KEPT"] = "changed"

        def setUp(self):
            os.environ["X8B_PROBE_SETUP"] = "leaked"

        def test_leaks(self):
            os.environ["X8B_PROBE_BODY"] = "leaked"
            os.environ.pop("X8B_PROBE_REMOVED", None)
            os.chdir(os.path.dirname(__file__) + "/elsewhere")
''')

READS = textwrap.dedent('''
    import os
    import sys
    import unittest

    class Reads(unittest.TestCase):
        def test_nothing_leaked(self):
            for key in ("X8B_PROBE_MODULE", "X8B_PROBE_CLASS",
                        "X8B_PROBE_SETUP", "X8B_PROBE_BODY"):
                self.assertNotIn(key, os.environ)
            self.assertEqual(os.environ.get("X8B_PROBE_KEPT"), "original")
            self.assertEqual(os.environ.get("X8B_PROBE_REMOVED"), "original")
            self.assertEqual(os.path.basename(os.getcwd()), "suite")
            self.assertNotIn("impl_domain_profile", sys.modules)
''')


class ProcessStateIsolationTests(unittest.TestCase):

    def _run(self, *, with_conftest: bool) -> subprocess.CompletedProcess:
        root = Path(tempfile.mkdtemp(prefix="x8b-isolation-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        suite = root / "suite"
        (suite / "elsewhere").mkdir(parents=True)
        (suite / "test_a_leaks.py").write_text(LEAKS, encoding="utf-8")
        (suite / "test_b_reads.py").write_text(READS, encoding="utf-8")
        if with_conftest:
            shutil.copy2(CONFTEST, suite / "conftest.py")
        env = {"PATH": "/usr/bin:/bin", "X8B_PROBE_KEPT": "original",
               "X8B_PROBE_REMOVED": "original"}
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "-p", "no:randomly", "-p", "no:xdist", "test_a_leaks.py",
             "test_b_reads.py"],
            cwd=suite, env=env, capture_output=True, text=True, check=False)

    def test_the_conftest_restores_what_a_file_left_behind(self):
        proc = self._run(with_conftest=True)
        self.assertEqual(proc.returncode, 0, proc.stdout[-3000:] + proc.stderr[-2000:])

    def test_without_the_conftest_the_probe_sees_the_leak(self):
        proc = self._run(with_conftest=False)
        self.assertEqual(proc.returncode, 1, proc.stdout[-3000:])
        self.assertIn("test_nothing_leaked", proc.stdout)


if __name__ == "__main__":
    unittest.main()
