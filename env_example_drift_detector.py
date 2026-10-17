#!/usr/bin/env python3
"""env-example-drift-detector: find the gap between your `.env.example` and
the environment variables your code actually reads.

Scans Python (os.environ[...], os.getenv(...)), JavaScript/TypeScript
(process.env.X) and shell ($VAR, ${VAR}) sources, compares against the keys
in `.env.example`, and reports:

  MISSING  read in code, absent from the example -> new-dev onboarding breakage
  DEAD     present in the example, never read     -> cruft

Exit code 1 when MISSING vars exist (a CI gate); 0 otherwise. With
--strict, DEAD vars also fail the gate.

Stdlib only.
"""

import argparse
import os
import re
import sys

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Extractors: source text -> set of env var names
# ---------------------------------------------------------------------------

_PY_PATTERNS = [
    # os.environ["X"], os.environ.get('X'), os.getenv("X"), environ["X"]
    re.compile(r'''(?:os\.)?environ(?:\.get)?\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']'''),
    re.compile(r'''os\.getenv\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']'''),
    re.compile(r'''(?:os\.)?environ\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]'''),
]

_JS_PATTERNS = [
    re.compile(r'''process\.env\.([A-Za-z_][A-Za-z0-9_]*)'''),
    re.compile(r'''process\.env\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]'''),
]

# $VAR and ${VAR}; exclude $? $$ $# $1..$9 $0 $! and lowercase one-letter noise.
_SH_PATTERN = re.compile(r'''\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Z][A-Za-z0-9_]{1,}|[A-Z_]{2,})''')

# Directories that never contain project sources.
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".tox", ".eggs", "vendor"}

_PY_EXTS = {".py"}
_JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
_SH_EXTS = {".sh", ".bash", ".zsh", ".env"}  # .env scanned for refs, not as example


def extract_python(text):
    found = set()
    for pat in _PY_PATTERNS:
        found.update(pat.findall(text))
    return found


def extract_js(text):
    found = set()
    for pat in _JS_PATTERNS:
        found.update(pat.findall(text))
    return found


def extract_shell(text):
    found = set()
    for m in re.finditer(r'''\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Z][A-Za-z0-9_]{1,}|[A-Z_]{2,})''', text):
        found.add(m.group(1) or m.group(2))
    return found


def extractor_for(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in _PY_EXTS:
        return extract_python
    if ext in _JS_EXTS:
        return extract_js
    if ext in _SH_EXTS:
        return extract_shell
    if os.path.basename(path) in ("Dockerfile",):
        return extract_shell  # ENV refs, $VAR expansion
    return None


def scan_code(root):
    """Walk root and collect every env var read by any supported source file."""
    used = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            extractor = extractor_for(path)
            if extractor is None:
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    used.update(extractor(f.read()))
            except OSError:
                continue
    return used


# ---------------------------------------------------------------------------
# .env.example parsing
# ---------------------------------------------------------------------------

_EXAMPLE_LINE = re.compile(r'''^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=''')


def parse_env_example(path):
    """Return the set of keys defined in a .env.example file."""
    keys = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = _EXAMPLE_LINE.match(stripped)
            if m:
                keys.add(m.group(1))
    return keys


# ---------------------------------------------------------------------------
# Drift computation
# ---------------------------------------------------------------------------

def compute_drift(used, example_keys):
    """Return (missing, dead): missing = used-but-undocumented,
    dead = documented-but-unused."""
    return used - example_keys, example_keys - used


def find_env_example(root):
    for name in (".env.example", "env.example", ".env.sample"):
        candidate = os.path.join(root, name)
        if os.path.isfile(candidate):
            return candidate
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff .env.example against the env vars your code "
                    "actually reads.")
    parser.add_argument("path", nargs="?", default=".",
                        help="Project root to scan (default: .)")
    parser.add_argument("--env-example",
                        help="Path to the example file (auto-detected by default)")
    parser.add_argument("--strict", action="store_true",
                        help="Also exit 1 when DEAD vars exist")
    parser.add_argument("--json", action="store_true",
                        help="Print findings as JSON")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.path)
    example_path = args.env_example or find_env_example(root)
    if not example_path:
        print("error: no .env.example found under %s (use --env-example)" % root,
              file=sys.stderr)
        return 2

    used = scan_code(root)
    example_keys = parse_env_example(example_path)
    missing, dead = compute_drift(used, example_keys)

    if args.json:
        import json
        print(json.dumps({
            "missing": sorted(missing),
            "dead": sorted(dead),
            "example_file": example_path,
            "scanned_vars": sorted(used),
        }, indent=2))
    else:
        print("Scanning %s  (example: %s)" % (root, example_path))
        print("Vars read in code: %d | vars in example: %d"
              % (len(used), len(example_keys)))
        if missing:
            print("\nMISSING (%d) — read in code, absent from .env.example:"
                  % len(missing))
            for name in sorted(missing):
                print("  - %s" % name)
        else:
            print("\nMISSING (0) — every var your code reads is documented.")
        if dead:
            print("\nDEAD (%d) — in .env.example, never read by code:"
                  % len(dead))
            for name in sorted(dead):
                print("  - %s" % name)
        else:
            print("\nDEAD (0) — no cruft in .env.example.")

    if missing:
        return 1
    if args.strict and dead:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
