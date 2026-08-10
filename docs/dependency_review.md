# Dependency Review Notes

**Scope:** `requirements.txt`. **Verdict:** low-risk, well-chosen dependencies for the
project's scope; the only real concern is reproducibility (lower-bound pins, no
lockfile).

## Declared dependencies

| Package | Constraint | Role | Direct/Transitive | Notes |
|---------|-----------|------|-------------------|-------|
| `fastapi` | `>=0.110` | Web framework / routing | Direct | Core; pulls in Starlette + Pydantic |
| `uvicorn[standard]` | `>=0.27` | ASGI server | Direct | `[standard]` adds websockets, httptools, etc. |
| `pydantic` | `>=2.5` | Validation / data contract | Direct | v2 API only (`ConfigDict`, `field_validator`) |
| `python-dotenv` | `>=1.0` | `.env` loading | Direct | Declared; not yet read at runtime |
| `pytest` | `>=8` | Test runner | Dev/direct | — |
| `httpx` | `>=0.27` | Test client transport | Dev/direct | Used by FastAPI `TestClient` |

All are widely used, actively maintained, permissively licensed (MIT/BSD-family)
packages appropriate for a learning project. There are no obscure or unmaintained
dependencies, and no native/security-sensitive libraries.

## Risks

1. **Lower-bound pins, no lockfile (primary risk).** `>=` constraints mean a fresh
   install can resolve to newer, untested versions, so builds are not reproducible and
   a future release could introduce a breaking change or regression unnoticed.
2. **Deprecation signal.** Under newer `httpx`/`starlette`, the test run emits
   `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`.
   This is a maintenance signal, **not** a vulnerability, and tests still pass. It will
   need attention if the stack is upgraded further.
3. **No automated vulnerability scanning.** Nothing currently checks these dependencies
   against known CVE databases.
4. **`python-dotenv` declared but unused at runtime.** Harmless, but worth either wiring
   up or noting as forward-looking.

## Recommendations

Prioritized; none are release blockers for the local course scope.

1. **Record resolved versions** for reproducibility:
   ```bash
   pip freeze > requirements.lock.txt
   ```
   Commit the lockfile and install from it in CI/Docker for deterministic builds.
2. **Add vulnerability scanning** to CI:
   ```bash
   pip install pip-audit
   pip-audit -r requirements.txt
   ```
   Or enable GitHub Dependabot alerts on the repository.
3. **Pin exact versions** (or use compatible-release `~=`) before any deployment, so the
   deployed artifact is auditable.
4. **Track the `httpx`/`starlette` deprecation** and migrate the test client when
   upgrading the stack.
5. **Keep the dependency set minimal** — no new runtime dependencies were added during
   hardening, and none are needed for the current feature set.

## Current status

- `pip install -r requirements.txt` succeeds; the app runs and **37 tests pass** on
  Python 3.10–3.14.
- No known-vulnerable versions are pinned. (Run `pip-audit` to confirm against the
  live CVE feed at review time.)
