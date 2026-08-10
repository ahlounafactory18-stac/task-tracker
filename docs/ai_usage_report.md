# AI Usage & Governance Report

This report documents how AI assistance was used to build and harden Task Tracker,
how its output was validated, the human review process, the risks of AI-generated
code, and a final ownership statement. It fulfils the course's AI-governance
requirement.

---

## 1. How AI was used

AI assistance was used in two clearly separated modes:

**A. As a planner / advisor.** Before writing code, the assistant was asked to
reconstruct the expected Module 1–3 baseline from the course prompt libraries and to
propose the smallest end-to-end features for the mid-course project. Its most useful
contribution was noticing that both chosen features — *Due dates + overdue filter*
and *Search + combined filters* — live in the same `GET /tasks` query path, which kept
the change surface to a single endpoint and a single data field.

**B. As a code generator, per layer.** For each layer (model field, storage, business
rule, endpoint, frontend, tests) the assistant produced a **draft** that was then
read, run, and break-tested before acceptance. It was never allowed to commit code
directly; every block passed through human review.

A full prompt-by-prompt record — including deliberately weak prompts rewritten into
strong ones — is preserved in `docs/midcourse/prompt-log.md`.

**Release-hardening phase (this submission).** AI assistance was also used to audit the
finished repository and generate the release documentation, CI workflow, Dockerfile,
and hygiene files in this submission. No product features or business rules were
changed during hardening; all changes are additive (docs, tests guidance, CI, Docker,
config). Every generated file was reviewed against the actual code before inclusion,
and factual claims (e.g. the frontend's `escapeHtml` usage, the passing test count)
were verified by reading the source and running the suite.

---

## 2. Validation process

Every accepted AI contribution went through the same gates:

1. **Read before run.** The diff was inspected for correctness and scope creep before
   execution — this is how two real problems were caught (below), not from failing
   tests.
2. **Run the suite.** `pytest tests/ -v` and `python -m tests.verify_a` after each
   accepted block. Current status: **37 passed**, 8/8 model checks.
3. **Live contract checks.** Endpoints were exercised with `curl` / Swagger UI against
   a running server (health, CRUD, filters, transitions, 404/422/204, CORS preflight).
4. **Break Test.** Production code was deliberately broken to confirm the *specific*
   protecting test failed, then restored. Examples: removing the `Done` exemption in
   `is_overdue` fails `test_completed_task_is_not_overdue`; dropping `.lower()` in
   search fails `test_search_is_case_insensitive`. A passing suite alone was never
   treated as proof.
5. **Fact-check for docs.** Claims in generated documentation were checked against the
   source (not assumed), and the test suite was re-run to confirm the reported numbers.

---

## 3. Human review process

- **Ownership stayed with the human author.** The assistant proposed; the author
  decided. Nothing merged without a read-through.
- **Scope enforcement.** The author rejected out-of-scope AI suggestions repeatedly —
  e.g. a dedicated `/search` endpoint and browser-only filtering (both rejected in
  favor of extending `GET /tasks`), and searching the `assignee` field (rejected as
  out of the story set).
- **Correctness enforcement.** The author corrected AI logic errors — most notably the
  first `is_overdue` draft that flagged *completed* past-due tasks as overdue; the
  author added the `Done` exemption and a regression test to lock it in.
- **Every documentation claim in this submission was verified against the code** before
  being stated.

---

## 4. Concrete examples of AI errors caught by review

| Issue | AI's output | Human correction |
|-------|-------------|------------------|
| Overdue logic | `is_overdue` flagged any past-due task, including `Done` | Added `status is Done` exemption + `test_completed_task_is_not_overdue` |
| Scope creep | Proposed a new `/search` endpoint | Rejected; extended existing `GET /tasks` with `q` |
| Wrong architecture | Proposed client-side-only filtering | Rejected; filtering enforced and tested on the backend |
| Scope creep | Proposed searching the `assignee` field | Rejected; not in the story set |
| UX detail | Fired a request on every keystroke | Edited to debounce search at 250 ms |

These are documented in `docs/midcourse/prompt-log.md`, `reflection.md`, and
`user-stories.md`.

---

## 5. Risks of AI-generated code (and mitigations)

| Risk | How it manifests here | Mitigation applied |
|------|----------------------|--------------------|
| **Plausible-but-wrong logic** | The `is_overdue` bug — and the AI wrote a test that matched its own flawed assumption, so the suite passed | Read-before-run + Break Test caught it; regression test added |
| **Scope creep** | Extra endpoints/fields beyond the stories | Explicit scope rejection during review |
| **Over-engineering** | Suggesting databases/frameworks outside Module scope | Constraints stated in prompts; suggestions rejected |
| **Silent test collusion** | A test that only confirms the AI's own (wrong) behavior | Break Test verifies the test protects *intended* behavior, not the implementation |
| **Stale/incorrect docs** | Generated docs asserting things the code does not do | Every claim verified against source; suite re-run |
| **Dependency risk** | Suggested loose version ranges | Documented in `docs/dependency_review.md`; pinning recommended |
| **Security blind spots** | Open API / permissive CORS presented as fine | Flagged explicitly in `docs/security_review.md` with pre-deployment gates |

---

## 6. Final ownership statement

The human author retains full ownership of and responsibility for this codebase. AI
was used as an assistant — a planner and a draft generator — under continuous human
review. Every line that was accepted was read, run, and (for critical rules) break-
tested by the author. AI suggestions that were incorrect, out of scope, or unsafe were
rejected and are documented as such. All release documentation in this submission was
verified against the actual source code and a passing test suite (**37 passed**) before
being finalized.

The author understands how the system works, why each design decision was made, and
what its limitations are, and can maintain and extend it without AI assistance. The AI
did not make final decisions; the author did.
