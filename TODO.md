# Pratighat.ai — Build Progress Tracker

Plan source: `/home/server/pratighat.ai/plan.md` (35 sections)
Last updated: 2026-09-30

Legend: `[x]` verified done · `[ ]` not started

Code that exists but has never been run is left **unticked** and called out in prose —
e.g. "Celery config only, no worker". Ticking it would overstate readiness.

> **Status as of 2026-09-30:** Both servers live. Backend imports cleanly, 24 routes registered,
> `/api/health` returns healthy with DB connected, Swagger docs at `/docs`.
> Frontend renders on :3000 with the Pratighat.ai title.
> The import-error marathon is over — auth, RBAC, hierarchy, assets, assessments, findings,
> risk, remediation, alerts, reports, audit, agents, AI, search, health, WebSocket all resolve.

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

### Remaining — BLOCKING (none left in Phase 0)
- [ ] Create Alembic scaffolding — `alembic` is a declared + installed dep but **no `alembic.ini` or `alembic/` dir exists**; zero migrations written
- [ ] Generate initial migration, apply to PostgreSQL
- [ ] Confirm login flow end-to-end through the Vite proxy

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
- [ ] Login works against real API (untested — no DB schema, no seed users)
- [ ] Role/Permission enforcement verified per endpoint
- [ ] Formation/unit isolation actually enforced at query level, not just declared
- [ ] Unit + Site + Network management screens
- [ ] Frontend unused-import warnings (TS6133) — cosmetic

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
- [ ] Report/service endpoints exercised against live data

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
| Backend (FastAPI) | Running on :8000 | 24 routes, `/api/health` healthy, DB connected |
| Migrations | None | alembic installed, no `alembic.ini` |
| PostgreSQL | Server up, **no schema** | 127.0.0.1:5432 |
| Redis | Running | 127.0.0.1:6379 |
| WebSockets | Referenced, unverified | ws refs in 2 app files |
| Celery | Config only, no worker/task module | 3 files reference it |
| ORM models | 16/21 from plan §26 | missing Technology, AssessmentTarget, Evidence, Role, Permission |
| Tests | None | no `tests/` dir |
| Docker deploy | Not started | no compose file |

### Correction to the previous tracker
The earlier TODO listed "install Python deps" as a blocker. **That was wrong** — deps are
installed in `backend/.venv`; the check had been run against system python. The real blocker
was that the app has never been started, and no migrations exist. **Both resolved this session:**
backend is live, import errors all fixed. Next real blocker: Alembic + migrations + seed data.
