# env-example-drift-detector

**Your `.env.example` is lying to every new developer who clones your repo.**

Code reads `STRIPE_SECRET`. `.env.example` never mentions it. The new hire spends a day debugging a crash that a diff would have caught in CI. This tool scans your code for the env vars it actually reads — Python (`os.environ[...]`, `os.getenv(...)`), JavaScript/TypeScript (`process.env.X`), shell (`$VAR`, `${VAR}`) — and diffs them against `.env.example`. It reports **MISSING** (read in code, absent from the example → onboarding breakage) and **DEAD** (in the example, never read → cruft), and exits 1 when MISSING vars exist so it works as a CI gate.

## Quickstart (30 seconds)

```bash
python3 env_example_drift_detector.py /path/to/your/project
```

Zero dependencies — stdlib only. Add it to CI and it fails the build the moment a PR reads an undocumented env var:

```yaml
- run: python env_example_drift_detector.py .
```

## Example output

Real output from running against the bundled fixture project (`fixtures/sample-project`, which ships with 2 missing and 1 dead var):

```
Scanning /tmp/wave8/env-example-drift-detector/fixtures/sample-project  (example: /tmp/wave8/env-example-drift-detector/fixtures/sample-project/.env.example)
Vars read in code: 6 | vars in example: 5

MISSING (2) — read in code, absent from .env.example:
  - REDIS_URL
  - STRIPE_SECRET

DEAD (1) — in .env.example, never read by code:
  - OLD_TOKEN
```

(exit code 1 — the CI gate trips on the two MISSING vars.)

## What it does NOT do

- It does **not** read your real `.env` values or validate them — only key names in `.env.example` and key references in code.
- It does **not** follow dynamically-constructed variable names (`os.environ[prefix + "_KEY"]`, template literals) — only literal string references.
- It does **not** understand config libraries (pydantic-settings, dotenv-vault, convict) that declare vars outside plain `process.env`/`os.environ` reads.
- It does **not** know which vars are required vs optional — every undocumented read is flagged MISSING, including ones with defaults.
- Exit codes: 1 when MISSING vars exist (the CI gate), 0 otherwise; `--strict` also fails on DEAD vars.

## Flags

- `--env-example <path>` — point at the example file explicitly (auto-detects `.env.example`, `env.example`, `.env.sample` by default)
- `--strict` — exit 1 on DEAD vars too
- `--json` — machine-readable findings

## Tests

15 tests, stdlib `unittest` — extractor unit tests per language, parser tests, drift computation, the fixture mini-project asserting the exact findings (2 missing, 1 dead), and exit-code behavior including `--strict`:

```bash
python3 -m unittest discover -s tests -v
```

## Built by Ingenious AI

- DisclosureGuard — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20DisclosureGuard.
- ModelMinder — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ModelMinder.
- TermsWatch — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20TermsWatch.
- Vibe-Code Audit — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Vibe-Code%20Audit.
- Rogue-Agent Defense — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Rogue-Agent%20Defense.
- BreachHunter — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20BreachHunter.
- ChatBreaker — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ChatBreaker.
- Agent Flight Recorder — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Agent%20Flight%20Recorder.
- Agent Auth Gateway — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20Agent%20Auth%20Gateway.
- DomainGuard — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20DomainGuard.
- ContentCraft AI — https://wa.me/5016691053?text=Hi%20Ingenious%20AI%21%20I%20want%20early%20access%20to%20ContentCraft%20AI.

Built with Muse — try it free: invite code 2HCQH1

## License

MIT — see [LICENSE](LICENSE).
