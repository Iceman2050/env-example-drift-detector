"""Tests for env_example_drift_detector.

Covers the extractors for Python/JS/shell, the .env.example parser, drift
computation, the fixture mini-project (2 missing, 1 dead), and exit codes.
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, ".")
import env_example_drift_detector as edd

FIXTURE = os.path.join("fixtures", "sample-project")


class TestPythonExtractor(unittest.TestCase):
    def test_all_python_forms(self):
        text = '''
import os
a = os.environ["BRACKET_VAR"]
b = os.environ.get('GET_VAR')
c = os.getenv("GETENV_VAR")
from os import environ
d = environ["DIRECT_VAR"]
'''
        found = edd.extract_python(text)
        self.assertEqual(found, {"BRACKET_VAR", "GET_VAR", "GETENV_VAR",
                                 "DIRECT_VAR"})

    def test_ignores_dynamic_keys(self):
        self.assertEqual(edd.extract_python('x = os.environ[some_var]'), set())
        self.assertEqual(edd.extract_python('x = os.environ.get(name)'), set())


class TestJsExtractor(unittest.TestCase):
    def test_dot_and_bracket_forms(self):
        text = '''
const a = process.env.DOT_VAR;
const b = process.env['BRACKET_VAR'];
'''
        self.assertEqual(edd.extract_js(text), {"DOT_VAR", "BRACKET_VAR"})


class TestShellExtractor(unittest.TestCase):
    def test_bare_and_braced(self):
        text = 'echo $BARE_VAR and ${BRACED_VAR} and $ANOTHER_ONE'
        self.assertEqual(edd.extract_shell(text),
                         {"BARE_VAR", "BRACED_VAR", "ANOTHER_ONE"})

    def test_ignores_special_params(self):
        # $? $$ $1 $0 $! are positional/special params, not env vars
        self.assertEqual(edd.extract_shell('echo $? $$ $1 $0 $!'), set())


class TestEnvExampleParser(unittest.TestCase):
    def test_parses_keys_ignores_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".example",
                                         delete=False) as f:
            f.write("# comment\n\nexport API_KEY=1\nDATABASE_URL=2\n  SPACED =3\n")
            path = f.name
        try:
            self.assertEqual(edd.parse_env_example(path),
                             {"API_KEY", "DATABASE_URL", "SPACED"})
        finally:
            os.unlink(path)


class TestDriftComputation(unittest.TestCase):
    def test_missing_and_dead(self):
        missing, dead = edd.compute_drift(
            {"A", "B", "C"}, {"B", "C", "D"})
        self.assertEqual(missing, {"A"})
        self.assertEqual(dead, {"D"})

    def test_no_drift(self):
        missing, dead = edd.compute_drift({"A"}, {"A"})
        self.assertEqual(missing, set())
        self.assertEqual(dead, set())


class TestFixtureProject(unittest.TestCase):
    def test_fixture_has_exactly_2_missing_1_dead(self):
        used = edd.scan_code(FIXTURE)
        example_keys = edd.parse_env_example(
            os.path.join(FIXTURE, ".env.example"))
        missing, dead = edd.compute_drift(used, example_keys)
        self.assertEqual(missing, {"STRIPE_SECRET", "REDIS_URL"})
        self.assertEqual(dead, {"OLD_TOKEN"})

    def test_fixture_exit_codes(self):
        # MISSING present -> exit 1
        proc = subprocess.run([sys.executable, "env_example_drift_detector.py",
                               FIXTURE], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("STRIPE_SECRET", proc.stdout)
        # --strict also 1 (dead exists too)
        proc = subprocess.run([sys.executable, "env_example_drift_detector.py",
                               "--strict", FIXTURE],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)


class TestCleanProjectExitCodes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        with open(os.path.join(self.tmp.name, ".env.example"), "w") as f:
            f.write("CLEAN_VAR=x\nDEAD_ONLY_FOR_STRICT=y\n")
        with open(os.path.join(self.tmp.name, "a.py"), "w") as f:
            f.write('import os\nx = os.getenv("CLEAN_VAR")\n')

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, "env_example_drift_detector.py", *args,
             self.tmp.name], capture_output=True, text=True)

    def test_clean_project_exits_0(self):
        # no MISSING -> 0 even though a DEAD var exists
        self.assertEqual(self._run().returncode, 0)

    def test_strict_fails_on_dead(self):
        self.assertEqual(self._run("--strict").returncode, 1)

    def test_no_example_file_exits_2(self):
        os.unlink(os.path.join(self.tmp.name, ".env.example"))
        self.assertEqual(self._run().returncode, 2)


class TestFindEnvExample(unittest.TestCase):
    def test_finds_dotted_example(self):
        self.assertTrue(edd.find_env_example(FIXTURE).endswith(".env.example"))

    def test_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(edd.find_env_example(d))


if __name__ == "__main__":
    unittest.main()
