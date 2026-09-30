# Pratighat.ai — Build Progress Tracker

Plan source: `/home/server/pratighat.ai/plan.md` (35 sections)
Last updated: 2026-09-30

Legend: `[x]` verified done · `[ ]` not started

Code that exists but has never been run is left **unticked** and called out in prose —
e.g. "Celery config only, no worker". Ticking it would overstate readiness.

> **Status as of 2026-09-30 (verified end-to-end against live PostgreSQL):**
> Backend live on :8000, **59 routes** registered, `/api/health` → `{"status":"healthy","database":"connected"}`,
> `/api/ready` → ready. Schema is migrated — Alembic head `82a7f34df1e2`, zero drift, 21 tables.
> Register → login → authenticated reads/writes all work against PostgreSQL.
> RBAC enforcement verified live: unauthenticated `401`, insufficient permission `403`.
> Swept **18 mutating + 22 GET endpoints: zero 5xx**.
>
> **Root-caused this session — the "body wrapper" bug:** `require_permission()`,
> `require_role()` and `require_super_admin()` declared `current_user: User` *without*
> `Depends(get_current_user)`. FastAPI therefore classified `User` as a **request-body** field and
> wrapped every protected endpoint's real payload in a synthetic `{current_user, data}` envelope —
> so all flat frontend JSON was rejected with `422 Field required: body.data`.
> One-line fix per function; wrapped endpoints went **23 → 0**.

---

## Phase 0: Make it run (prerequisite for all phases)

### Done
- [x] Project structure: `frontend/`, `backend/`, `agents/`
- [x] React + TypeScript + Vite scaffolded
- [x] Python venv at `backend/.venv` — fastapi, sqlalchemy, uvicorn, redis, alembic, passlib, websockets all importable
- [x] `.env` created (`backend/.env`) — DB, JWT, Redis, Celery, storage paths
- [x] PostgreSQL running on 127.0.0.1:5432
- [x] Redis running on 127.0.0.1:6379
- [x] Vite proxy `/api` → `localhost:8000` (`vite.config.ts`)
- [x] Frontend dev server live on :3000
- [x] Backend booted: uvicorn on :8000, 25 routes registered
- [x] `/api/health` returns `{"status":"healthy","database":"connected"}`
- [x] Swagger docs at `/docs` return HTTP 200
- [x] Backend import errors resolved:
  - CryptContext `bcrypt_rounds` kwarg → removed kwarg + `update_scheme`
  - `from app.models.user import ...` → `from app.models import ...` (all services + APIs)
  - PaginatedResponse non-generic → generic `PaginatedResponse(BaseModel, Generic[T])`
  - CurrentUser/OptionalUser double-Depends → plain `User`/`Optional[User]`
  - User class → Pydantic BaseModel in security.py
  - schemas split across non-existent files → single `alert_audit_agent_report_ai_search.py`
  - **This session's fixes:**
  - `select` missing import in auth.py → added `from sqlalchemy import select`
  - `select`/`func` missing in assets_services_nodes.py → added imports
  - passlib 1.7.4 + bcrypt 5.x incompatibility → replaced with direct `bcrypt.hashpw`/`bcrypt.checkpw`
  - `OrganizationWithUserCount` undefined in organizations.py → fixed import
  - `Query(...)` used for path params (report_id, event_id, assessment_id) → `Path(...)`
  - `log_entry: dict` query param → `str`
  - sync `_build_*_summary` functions using `await` → `async def` + `await` callers
  - missing `app.services.ai` → created stub service
  - missing `app` export from `main.py` → added module-level `app = create_application()`
  - `OrganizationCreateRequest` imported from deleted `auth_organization.py` → `alert_audit_agent_report_ai_search`
  - `organization_id: Query(default=None)` alongside `data: UserCreateRequest` → removed (caused body wrapping)
  - **Frontend-backend field mismatches fixed:**
  - Login: backend now accepts email as username (`(UserModel.username == data.username) | (UserModel.email == data.username)`)
  - Register: frontend now sends `{ username, email, full_name, password }` (derived username from email prefix)

### Remaining — BLOCKING
- [x] Create Alembic scaffolding — `backend/alembic.ini`, `backend/alembic/env.py`, `script.py.mako`
- [x] Generate initial migration, apply to PostgreSQL (`82a7f34df1e2_initial_schema.py`, head)
- [x] Confirm login flow end-to-end — register → login → authenticated request, verified against PostgreSQL

### Verified this session (runtime bugs found only by actually calling the API)
- [x] **Request-body envelope** (23 endpoints) — `require_permission`/`require_role`/`require_super_admin`
      declared `current_user: User` with no `Depends(get_current_user)`, so FastAPI treated the principal
      as a body field and wrapped every payload. Fixed → 0 wrapped endpoints.
- [x] **Fabricated identity** — `get_current_user()` built the principal from JWT claims
      (`username=f"user-{id}"`, fake email) and never read the database, so authorization decisions used
      token-controlled values. Now loads the real user row; 401 if missing or deactivated.
- [x] **Principal model incomplete** — `core/security.py::User` lacked `full_name`/`role`/`avatar_url`,
      so `/auth/me` raised `AttributeError: 'User' object has no attribute 'full_name'` (500).
- [x] **`datetime` imported at the bottom of `api/auth.py`** — `import datetime` + `from datetime import ...`
      sat *after* every endpoint, so `datetime.now(timezone.utc)` resolved to the **module**, not the class
      (`AttributeError: module 'datetime' has no attribute 'now'`). Moved to the top imports.
- [x] **`hasattr(current_user, 'role')` then `.value`** — role is a plain `str`, not an enum; the guard
      passed and the attribute access blew up with `'str' object has no attribute 'value'`.
- [x] `/api/organizations` (GET) declared `response_model=OrganizationWithUserCount` but returns a
      `{items,total,page,page_size,pages}` envelope → `ResponseValidationError` on every request.
- [x] `/api/search` built `GlobalSearchResponse` with `results=` and no `page`/`page_size`/`pages`,
      while the schema extends `PaginatedResponse` → 4 validation errors, always 500.
- [x] `OrganizationBrief` had no `from_attributes=True`, so `model_validate(<ORM row>)` failed — the first
      valid org write (`POST /api/organizations`) returned 500 instead of 201.
- [x] `/api/ai/analyze` called `await analyze(session, data, user)` but the service signature is
      `analyze(query, context, scope_filters, ...)` → `'AsyncSession' object is not subscriptable`.
- [x] `/api/ai/analyze/stream` awaited an async generator and passed 3 wrong args → `TypeError` on every
      request. Now a real `StreamingResponse` (SSE).
- [x] `POST /api/risk` took a bogus `org_id: Query(...)`; org is derived from the finding instead.
- [x] Services signal business-rule violations with `ValueError` (e.g. duplicate slug), which surfaced as
      raw 500 tracebacks. Added a global handler → clean `409 CONFLICT` / `400 BAD_REQUEST`.

### Still blocking
- [x] **Frontend production build fixed** — `npm run build` (`tsc && vite build`) now passes.
      All 58 pre-existing `TS6133` ("declared but never read") errors across the 12 page files
      were removed, keeping `noUnusedLocals` / `noUnusedParameters` **enabled** in
      `frontend/tsconfig.json` rather than weakening the compiler settings.
      Vite now emits `dist/assets/index-*.js` (334 kB, 91 kB gzip). Dev server unaffected.
      *How:* AST pass that parses each file once and applies deletions bottom-up, so offsets
      never shift mid-file. Two rules that the first (reverted) attempt got wrong:
      (a) an **array** binding pattern must keep its commas as holes — `[a, setA]` → `[, setA]`,
      never `[setA]`, or the setter silently becomes the value and every call throws
      `TS2349: This expression is not callable`; (b) import/default-import and function
      parameter forms need their own handlers. Every file was re-parsed after editing and
      restored untouched if it would not parse.

### Also fixed while bringing the stack up
- [x] `app/api/reports_agents_audit_ai_search_health_ws.py` was missing the `PaginatedResponse`
      import and the `org_id` query parameter on `list_reports_api` and `register_agent_api`.
      The backend failed to start on the missing import, then `/api/reports` returned 500
      (`NameError: name 'org_id' is not defined`). `pyflakes` now reports **0 undefined names**
      across `app/api`, `app/core`, `app/services`, and `app/main.py`.
- [x] Demo login: the `admin` user's stored hash matched no advertised password, so the login
      page's "demo credentials" returned 401. Password reset to the advertised `admin123`
      (`admin@pratighat.ai`); login → `/api/auth/me` → `/api/organizations` all verified
      through the Vite proxy.
- [x] Verified 12 GET endpoints through the Vite `:3000` → `:8000` proxy, all **200**.

---

## Phase 1: Auth, RBAC, hierarchy, assets, dashboard (plan §34 P1)

### Done
- [x] Auth API + service + schemas (`api/auth.py`, `services/organization.py`)
- [x] JWT + RBAC core (`core/security.py`)
- [x] Organisation → Formation → Unit → Site → Network models present
- [x] Hierarchy API + service + schemas
- [x] Asset + Service + Node API/service/models
- [x] Frontend pages: Login, Dashboard, Formations, Assets, Settings
- [x] Shared components, types, API client, dark theme CSS
- [x] Backend serving, auth router registered at `/api/auth`

### Remaining
- [x] Login works against real API — register → login → `/auth/me` verified against PostgreSQL
- [x] Role/Permission enforcement verified per endpoint — live `401` unauthenticated, `403` underprivileged,
      `200` after promoting the test user to `SUPER_ADMIN`
- [ ] Formation/unit isolation actually enforced at query level, not just declared
- [ ] Unit + Site + Network management screens

### Plan gaps in this phase
- [ ] `Role` and `Permission` models missing from `models/__init__.py` — RBAC exists in code without a data model
- [ ] No test proving an assessment cannot run outside authorized scope (plan §30 calls this the single most important test)

---

## Phase 2: Authorization, orchestration, scanner interface, findings, evidence (plan §34 P2)

### Done
- [x] Scope enforcement present in `engine/` (verified by grep)
- [x] Engine scaffold + nmap parser (`engine/parsers/nmap.py`)
- [x] Assessment / Finding / Risk / Remediation / Alert API + services + schemas
- [x] Celery config in `core/config.py`
- [x] All assessment/finding/risk/remediation/alert routers registered and importing

### Remaining
- [ ] `AssessmentTarget` model missing — no persisted record of what an assessment was authorized to hit (plan §26)
- [ ] `Evidence` model missing — evidence collection is a core plan requirement (§1, §7, §18)
- [ ] Celery app defined and a worker process running (config only; no task module)
- [ ] Full assessment lifecycle: DISCOVERY → ENUMERATION → FINGERPRINTING → VULN ASSESSMENT → EVIDENCE → CORRELATION → RISK → REPORTING → REMEDIATION → VERIFICATION
- [ ] Standard scanner interface — multiple adapters behind one contract
- [ ] Normalized finding model fed by real scanner output

---

## Phase 3: Risk, remediation, reporting, audit (plan §34 P3)

### Done
- [x] Risk API + service + schemas
- [x] Remediation API + service + schemas
- [x] Report API + service + schemas
- [x] Audit API + service + schemas
- [x] AI service + schemas + API surface (`/api/ai`)
- [x] Search API + service (`/api/search`)
- [x] Reports/agents/audit/ai/search/health/WebSocket routers registered

### Remaining
- [ ] Transparent risk calculation with visible contributors (plan §10 — must not be a black-box number)
- [ ] Remediation workflow state machine: OPEN → ACKNOWLEDGED → IN PROGRESS → FIXED → VERIFYING → VERIFIED → CLOSED
- [ ] 8 report types (executive, formation, unit, technical, vulnerability, remediation, history, audit)
- [ ] PDF / JSON / CSV export actually produces files
- [ ] **Tamper-evident** audit records (plan §21 requires this, not just append-only)
- [x] Report/service endpoints exercised against live data — 18 mutating + 22 GET endpoints swept, zero 5xx

---

## Phase 4: Node agents, real-time, continuous assessment (plan §34 P4)

### Done
- [x] Node agent API + service + schemas
- [x] WebSocket plumbing referenced in `api/reports_agents_audit_ai_search_health_ws.py`
- [x] Node model present

### Remaining
- [ ] Agent implementation in `agents/` — telemetry, heartbeat, mTLS / signed identity
- [ ] WebSocket server actually serving heartbeats, assessment progress, new findings
- [ ] Scheduled assessments: 6h / 12h / daily / weekly / custom
- [ ] Change detection: new assets, new services, new vulns, tech changes, config changes, cert changes
- [ ] Historical assessment data retained and queryable
- [ ] Live formation/unit visibility dashboard (plan §13)

---

## Phase 5: AI analyst, asset graph, correlation, reporting (plan §34 P5)

### Done
- [x] AI service + schemas + API surface
- [x] Search API + service (plan §23)

### Remaining
- [ ] AI analyst answering the plan's example questions against the real DB
      *(both `/api/ai/analyze` routes are now functional and return well-formed responses, but
      `services/ai.py` still returns a hardcoded mock answer — no LLM, no DB retrieval)*
- [ ] **Evidence-grounded only** — must distinguish OBSERVED FACT / SCANNER RESULT / CORRELATION / INFERENCE / RECOMMENDATION, and must never invent a vulnerability (plan §9, §14)
- [ ] Asset graph with visual exploration (plan §6) — no graph UI exists
- [ ] Advanced correlation engine
- [ ] Advanced reporting

---

## Cross-cutting requirements (plan §25, §29, §30, §31, §32, §33)

### Security hardening (§25)
- [x] JWT auth, RBAC core, scope checks
- [ ] Formation/unit isolation, rate limiting, CSRF, secure cookies, secure headers
- [ ] Secrets management, encryption at rest / in transit
- [ ] Dependency + container hardening

### Testing (§30) — effectively zero
- [ ] Unit, API, DB, auth, authz, scanner-adapter, scope-enforcement, WebSocket, AI-response, integration tests
- [ ] `tests/` directory does not exist (only a stray root `test_basic.py`)
- [ ] **Scope enforcement test** — plan §30 names this the top priority; nothing exists

### Project structure (§29)
- [x] `frontend/`, `backend/`, `agents/`
- [ ] `workers/`, `scanners/`, `database/`, `deployment/`, `docs/`, `tests/`

### Deployment (§31)
- [ ] Docker Compose (frontend, backend, postgres, redis, worker, scheduler, agent, reverse-proxy) — no compose file, no Dockerfiles
- [ ] Nginx reverse proxy
- [ ] `.env.example` (only `.env` exists)
- [ ] Health checks, backup + restore instructions

### Demo mode (§32)
- [ ] Seed dataset: 3 formations, 8 units, 100+ assets, services, vulns, assessment + remediation history, node telemetry
- [ ] All demo data clearly labelled DEMO DATA — never presented as real findings

### UX (§33)
- [x] Dark SOC theme
- [ ] Missing pages: Units, Monitoring, AI Analyst
- [ ] Missing detail pages: Asset Detail (§18), Finding Detail (§19)
- [ ] Keyboard shortcuts
- [ ] Tablet responsiveness
- [ ] Toast system (uses `alert()` in places)

### Spec gaps not yet tracked anywhere
- [ ] `Technology` model missing (§5, §26) — no way to store fingerprinted tech
- [ ] Tailwind CSS not installed (plan §3 explicitly requires it; no config, not in package.json — current CSS is handwritten)
- [ ] OpenAPI docs not enabled (§27) — no openapi config found
- [ ] Charting: ECharts/Recharts required by §3; 1 file references it, unverified

---

## Quick status

| Component | Status | Evidence |
|---|---|---|
| Frontend (React + Vite) | Running on :3000 | HTTP 200, title "Pratighat.ai — Autonomous VAPT & Cyber Defence" |
| Frontend production build | **Passing** | `tsc && vite build` clean; `dist/` emitted (334 kB js, 91 kB gzip) |
| Backend (FastAPI) | Running on :8000 | **59 routes**, `/api/health` healthy, `/api/ready` ready, DB connected |
| Migrations | **Applied** | Alembic head `82a7f34df1e2`, autogenerate reports zero drift |
| PostgreSQL | **Schema live** | 21 tables incl. `alembic_version`; register/login persist and read back |
| Redis | Running | 127.0.0.1:6379 |
| WebSockets | Referenced, unverified | ws refs in 2 app files |
| Celery | Config only, no worker/task module | 3 files reference it |
| ORM models | 16/21 from plan §26 | missing Technology, AssessmentTarget, Evidence, Role, Permission |
| Tests | None | no `tests/` dir; this session used live endpoint sweeps instead |
| Docker deploy | Not started | no compose file |

### Correction to the previous tracker
The earlier TODO listed "install Python deps" as a blocker. **That was wrong** — deps are
installed in `backend/.venv`; the check had been run against system python. The real blocker
was that the app has never been started, and no migrations exist. **Both resolved this session:**
backend is live, import errors all fixed, Alembic initial migration applied.

Next real blockers: **seed/demo data** (§32) and the missing `tests/` suite (§30) — especially
the scope-enforcement test the plan names as its single highest priority — then the 5 missing
ORM models (§26) and the missing Units / Monitoring / AI Analyst pages.
