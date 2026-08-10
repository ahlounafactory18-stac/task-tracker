# Deployment Guide

This guide covers running Task Tracker locally, in Docker, and in CI, plus the
constraints and required changes before any non-local deployment.

> **Important scope note.** Task Tracker uses an **in-memory** store with **no
> authentication**. It is designed for local, single-user use. It is **not** ready
> for public/internet deployment as-is. The "Before production" section lists the
> gates that must be cleared first.

---

## 1. Prerequisites

- Python 3.10+ (developed on 3.12; also runs on 3.14).
- `pip` and `venv`.
- (Optional) Docker 20.10+ to run the containerized backend.
- A local static file server for the frontend (VS Code Live Server, or
  `python -m http.server`).

---

## 2. Local development (no Docker)

From the project root (`task-tracker/`):

```bash
# 1. create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows PowerShell

# 2. install dependencies
pip install -r requirements.txt

# 3. (optional) create a local env file
cp .env.example .env              # Linux / macOS
copy .env.example .env            # Windows PowerShell

# 4. run the backend
uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>

Serve the frontend from a second terminal:

```bash
python -m http.server 5500
# open http://localhost:5500/frontend/index.html
```

The frontend calls the API at `http://localhost:8000` (set by `BASE_URL` in
`frontend/index.html`). CORS allows any localhost port, so Live Server on `:5500`
works out of the box.

---

## 3. Docker

A `Dockerfile` and `.dockerignore` are provided. The image runs the **backend** API.

### Build

```bash
# from the project root (where the Dockerfile is)
docker build -t task-tracker:latest .
```

### Run

```bash
docker run --rm -p 8000:8000 task-tracker:latest
```

- The container serves the API on `http://localhost:8000`.
- Verify: `curl http://localhost:8000/health`.
- Swagger UI: <http://localhost:8000/docs>.

### Configuration

- `PORT` (default `8000`) — the port Uvicorn binds inside the container. Override:
  `docker run -e PORT=8080 -p 8080:8080 task-tracker:latest`.
- No secrets are required. Do **not** bake a real `.env` into the image; pass runtime
  config with `-e` or `--env-file`.

### Frontend + Docker

The frontend is a static file. To use the board against the containerized API, serve
`frontend/index.html` from a local static server as in section 2 (the container
exposes the API only). Because the store is in-memory, **stopping the container clears
all tasks.**

### Health check

The image includes a `HEALTHCHECK` that polls `/health`. Inspect it with
`docker inspect --format '{{.State.Health.Status}}' <container>`.

---

## 4. Continuous Integration (GitHub Actions)

The workflow at `.github/workflows/ci.yml` runs on every push and pull request:

1. Checks out the repository.
2. Sets up Python (matrix: 3.10, 3.11, 3.12).
3. Installs dependencies from `requirements.txt` (verifying installation succeeds).
4. Runs the model verification script (`python -m tests.verify_a`).
5. Runs the full test suite (`pytest tests/ -v`).
6. **Fails the build if any test fails**, blocking a merge.

Because the workflow lives at the repository root under `.github/workflows/`, ensure
CI runs from the directory that contains `app/` and `tests/` (the inner
`task-tracker/` if the nested layout is preserved). See the workflow's `working-directory`
note in `README.md`.

---

## 5. Environment variables

| Variable | Default | Purpose | Sensitive? |
|----------|---------|---------|------------|
| `PORT` | `8000` | Port the server binds to | No |
| `APP_ENV` | `development` | Environment label | No |

Copy `.env.example` to `.env` for local use. `.env` is git-ignored and must never be
committed. No secrets exist in this project today.

---

## 6. Operational notes & limitations

- **No persistence.** Restarting the server or container empties all tasks. There is
  no backup/restore because there is no datastore.
- **Single process.** Run with a single worker. The in-memory store is not shared
  across workers/processes and is not thread-safe for concurrent writes, so scaling
  horizontally would give inconsistent results.
- **No migrations, no seed data.** The store always starts empty.

---

## 7. Before production (required changes)

Do **not** deploy publicly until all of these are done (cross-referenced in
`docs/security_review.md`):

1. **Persistence:** introduce a real datastore behind the existing `storage.py`
   interface (so routes/tests barely change).
2. **Authentication & authorization:** the API is currently open; add auth and bind to
   a controlled interface.
3. **CORS:** replace the localhost regex with an explicit allow-list of the real
   frontend origin(s).
4. **Dependency pinning:** commit a lockfile and add `pip-audit`/Dependabot.
5. **Pagination & limits:** add pagination and request-size limits to bounded
   endpoints.
6. **Observability:** structured logging and health/readiness probes wired to the
   orchestrator.
7. **Frontend config:** make `BASE_URL` configurable for the deployed API origin.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Frontend shows the error state | Backend not running | Start `uvicorn app.main:app --port 8000`; click Retry |
| CORS error in the browser console | Frontend not served from `localhost`/`127.0.0.1` | Serve via a local static server, not `file://` |
| `docker run` exits immediately | Port already in use | Change the host port: `-p 8080:8000` |
| `/health` unreachable in Docker | Wrong port mapping | Ensure `-p 8000:8000` and container `PORT` match |
| Tasks disappear after restart | In-memory store (by design) | Expected; no persistence exists |
| Tests fail in CI but pass locally | Python version / dependency drift | Match CI's Python matrix; pin dependencies |
