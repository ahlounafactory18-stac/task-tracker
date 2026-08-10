# Security Review

**Scope:** backend (`app/`), config files, and frontend (`frontend/index.html`).
**Threat model:** a local, single-user learning project with no authentication and an
in-memory store. This review assesses the code as-is and flags what must change
*before* any non-local deployment.
**Overall risk rating for the intended (local) scope:** **Low.**

---

## Summary table

| Area | Rating | Notes |
|------|--------|-------|
| Secrets handling | ✅ Low | No secrets in code or history; `.env` is git-ignored |
| Environment variables | ✅ Low | Only non-sensitive `PORT`/`APP_ENV`; example file provided |
| Input validation | ✅ Strong | Strict Pydantic v2 at every boundary |
| Authentication / authorization | ⚠️ By design absent | No auth — acceptable only for local scope |
| CORS | ⚠️ Localhost-only | Safe locally; must tighten before deployment |
| Dependency risks | ⚠️ Medium | Lower-bound pins, no lockfile |
| Logging | ✅ Low | No sensitive data logged; also no audit logging |
| Data protection | ℹ️ N/A | No persistence, no PII beyond a free-text assignee string |

---

## 1. Secrets handling

- **No hardcoded secrets** anywhere in `app/`, `frontend/`, tests, or config. There are
  no API keys, tokens, passwords, or connection strings — the app has no external
  services or database.
- `.env` is listed in `.gitignore`; only `.env.example` (containing non-sensitive
  placeholders) is committed.
- **Recommendation:** keep it this way. If a secret is ever introduced (e.g. a DB URL),
  it must go through environment variables, never source. Add a secret-scanning step
  (e.g. `gitleaks`) to CI if the project grows.

## 2. Environment variables

- Current variables (`.env.example`): `PORT=8000`, `APP_ENV=development`. Both are
  non-sensitive operational settings.
- `python-dotenv` is a declared dependency for loading `.env`, though the current code
  does not read these variables at runtime — they are informational/forward-looking.
- **Recommendation:** if/when these are read, validate/parse them defensively (e.g.
  integer `PORT`, enum `APP_ENV`). Never place secrets in `.env.example`.

## 3. Input validation

**This is the app's strongest security property.** Every request boundary is guarded by
strict Pydantic v2 models:

- Enums (`TaskStatus`, `TaskPriority`) reject any out-of-set value with 422.
- `extra="forbid"` rejects unknown fields and blocks clients from setting
  server-managed fields (`id`, `created_at`, `updated_at`) — prevents mass-assignment.
- Title validation: non-blank, stripped, ≤ 200 characters.
- Dates are parsed by Pydantic; malformed dates → 422.
- The storage layer re-validates the merged record before committing, so even a value
  that bypassed the input model cannot corrupt the store (surfaced as 422, not 500).
- Query filters are typed (`status`, `priority`, `overdue`, `q`); invalid enum values →
  422.

**Injection posture:** there is no SQL, no shell execution, and no template rendering of
user input on the server, so classic injection vectors do not apply. Search is an
in-memory Python substring match.

**XSS note (frontend):** `frontend/index.html` renders task cards via an `innerHTML`
template, but **every user-supplied field is passed through an `escapeHtml()` helper
first** — title, description, assignee, due_date, and priority are all escaped before
interpolation (see `renderCard` in the file). Status banners and counts use
`textContent`. This is the correct posture and no action is required. **Maintenance
note:** any future field added to a card template must also go through `escapeHtml()`;
keep this invariant if the frontend is extended.

## 4. Authentication & authorization

- **There is no authentication or authorization** — every endpoint is open. This is an
  explicit Module 1–3 scope decision (single shared list, no accounts).
- **Risk:** acceptable **only** because the server binds to localhost for local use. If
  this were exposed on a network, anyone could read/modify/delete all tasks.
- **Required before any deployment:** add authentication (at minimum an API key or
  session/JWT auth) and bind to a controlled interface. Until then, do **not** deploy to
  a public host.

## 5. CORS

- Policy: `allow_origin_regex = http://(localhost|127.0.0.1)(:\d+)?`, all methods, all
  headers. Credentials are not enabled.
- **Local scope:** appropriate — it lets the static frontend on any localhost port call
  the API without port-mismatch failures, while still excluding non-local origins.
- **Before deployment:** replace the regex with an explicit allow-list of the real
  frontend origin(s), restrict methods/headers to what is used, and never combine a
  wildcard origin with credentials.

## 6. Dependency risks

- Dependencies are pinned as **lower bounds** (`>=`) with **no lockfile**, so an install
  can pull newer, untested versions. See `docs/dependency_review.md` for the full
  analysis and remediation.
- No automated vulnerability scanning is configured.
- **Recommendations:**
  - Commit resolved versions (`pip freeze > requirements.lock`) or pin exact versions
    for reproducible, auditable builds.
  - Add `pip-audit` (or GitHub Dependabot) to CI to flag known CVEs.
  - Note: a `StarletteDeprecationWarning` about `httpx`/`starlette.testclient` appears
    under newer versions — a maintenance signal, not a vulnerability.

## 7. Logging risks

- The app relies on Uvicorn's default access/error logs; it does not log request bodies,
  task contents, or any secret. **No sensitive-data-in-logs risk.**
- Conversely, there is **no audit logging** of create/update/delete actions. For this
  scope that is fine; a multi-user version should add structured, non-sensitive audit
  logs.
- **Recommendation:** if logging is expanded, never log full request bodies or the
  `assignee` field at INFO level without a reason; keep logs free of PII.

## 8. Denial-of-service / resource use

- Unbounded list growth: there is no pagination or size cap on the store or on
  `GET /tasks`. In-memory and single-user, this is not a practical risk, but a deployed
  version should add pagination and request-size limits.
- No rate limiting (not needed locally; required if exposed).

---

## Prioritized recommendations

**For the current (local, course) scope — already satisfied:**
- ✅ No secrets in source; `.env` ignored.
- ✅ Strict input validation at every boundary.
- ✅ CORS scoped to localhost.

**Before any deployment (must-do):**
1. Add authentication/authorization; do not expose an unauthenticated API.
2. Replace the localhost CORS regex with an explicit origin allow-list.
3. Pin dependencies (lockfile) and add `pip-audit`/Dependabot.
4. Add pagination and request-size limits.
5. Keep the frontend's `escapeHtml()` invariant on any newly added card fields
   (already correct for all current fields).

**Nice-to-have hardening:**
- Secret scanning (`gitleaks`) in CI.
- Structured audit logging for mutations.

**Conclusion:** For its intended local, single-user learning scope, the application has
a **low** security risk profile, anchored by genuinely strong input validation. The
open API and permissive-but-localhost CORS are safe only because the app is not
deployed; the items above are the gate that must be cleared before it ever is.
