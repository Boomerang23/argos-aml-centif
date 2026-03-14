# Argos CENTIF Immo – Full Technical Audit Report

**Date:** March 2026  
**Scope:** Full repository (backend, frontend, Docker, config, tests)  
**Focus:** Architecture, security, performance, maintainability, scalability, best practices.

---

## 1. System architecture overview

### 1.1 High-level layout

- **Backend:** FastAPI app (`app/`) with SQLAlchemy 2, PostgreSQL (or SQLite for tests), JWT (python-jose), Argon2 (argon2-cffi). Single process, no task queue.
- **Frontend:** Next.js (App Router), TypeScript, TanStack Query, shadcn/ui. Calls backend via `NEXT_PUBLIC_API_BASE_URL`.
- **Data:** PostgreSQL 16 in Docker; Alembic for migrations; `init_db` / `create_all` for schema bootstrap.
- **Deployment:** Docker Compose (dev: db + api; prod: db + api + frontend). No reverse proxy or ingress in repo.

### 1.2 Main backend modules

| Module | Responsibility |
|--------|----------------|
| `app/main.py` | App factory, CORS, immutability setup, `Base.metadata.create_all`, router registration |
| `app/config.py` | Pydantic Settings, production secret validation (JWT/ONBOARDING) |
| `app/db.py` | Engine, SessionLocal, DeclarativeBase |
| `app/models.py` | Organizations, Users, Cases, Parties, Documents, Screenings, AuditLog (enums, relationships) |
| `app/security.py` | Password hashing (Argon2), JWT create/decode |
| `app/deps.py` | get_db, get_current_user (OAuth2PasswordBearer) |
| `app/routers/auth.py` | Login (rate-limited), /me |
| `app/routers/health.py` | /health (liveness), /ready (DB check, no raw exception leak) |
| `app/routers/cases.py` | CRUD cases, parties, audit list, compliance decision; RBAC (org + agent scope) |
| `app/routers/screening.py` | Run screening (OpenSanctions), persist result, apply scoring |
| `app/routers/reports.py` | PDF export (reportlab), FileResponse |
| `app/routers/onboarding.py` | Token-based upload page (HTML), status, upload (size + type checks), KYC checklist, document list |
| `app/routers/admin.py` | Org CRUD, user CRUD (admin only) |
| `app/routers/dashboard.py` | Summary KPIs (counts by status/decision) |
| `app/services/audit.py` | Append-only audit log with hash chaining |
| `app/services/onboarding.py` | HMAC-SHA256 onboarding tokens with expiry |
| `app/services/screening.py` | OpenSanctions API (or mock), risk detection |
| `app/services/scoring.py` | Risk scoring rules, status (DRAFT/ORANGE/GREEN/RED) |
| `app/services/kyc_checklist.py` | Required docs per party, recompute case status with KYC |
| `app/services/pdf_report.py` | Generate case PDF to `storage/reports` |
| `app/immutability.py` | SQLAlchemy listeners to block AuditLog update/delete |

### 1.3 Data and auth flow

- **Auth:** Login → JWT in `Authorization: Bearer`; frontend stores token in `localStorage`. No refresh token.
- **RBAC:** Org-scoped (all routes check `case.org_id == user.org_id`); agents see only their own cases (`created_by_user_id`).
- **Onboarding:** Time-limited signed token (case_id, party_id, exp); public endpoints `/onboarding/status`, `/onboarding/upload` (no JWT).

---

## 2. Code structure evaluation

**Strengths**

- Clear split: routers → deps/schemas, services for business logic, models centralized.
- Pydantic schemas for API contracts; enums for status/roles.
- Audit log with hash chaining and immutability enforced at ORM level (`app/immutability.py`).
- Production secret validation and readiness hardening already in place.

**Weaknesses**

- **`app/routers/__init__.py`** only exports `auth, cases, screening, reports, onboarding`; `admin`, `dashboard`, `health` are imported directly in `main.py`. Inconsistent and can confuse tooling.
- **Duplicate RBAC logic:** Case access (org + agent) is repeated in many route handlers (e.g. `cases.py`, `screening.py`, `reports.py`) instead of a shared dependency (e.g. `get_case_with_access(case_id, user)`).
- **Mixed language:** Comments and UI strings in French; code and config in English. Not wrong but can complicate onboarding for English-only contributors.
- **create_user.py** and **init_db.py** live at repo root and depend on `app`; no CLI group (e.g. `python -m app.cli create_user`), so discovery and env handling are ad hoc.

---

## 3. Security risks

### 3.1 High / medium

- **JWT in localStorage:** Token is stored in `localStorage` (`argos-frontend/src/lib/auth.ts`). XSS can steal it. Prefer httpOnly cookies for access (or short-lived access + refresh in cookie) if XSS is in scope.
- **Production secret validation opt-in:** Secret validation runs only when `ENVIRONMENT=production` (or `prod`). `docker-compose.prod.yml` does **not** set `ENVIRONMENT`; if deployers forget to set it, the app starts with placeholder secrets in prod. **Recommendation:** Set `ENVIRONMENT=production` in prod compose and document it in DEPLOYMENT.md.
- **Login rate limit not shared across workers:** Rate limiting is in-memory per process (`app/routers/auth.py`). Multi-worker (e.g. `uvicorn --workers 4`) or multi-replica deployments will have separate counters; an attacker can multiply effective attempts by the number of workers/replicas.
- **Case reference globally unique:** `Case.reference` is unique across all orgs (`app/models.py`). Two organizations cannot use the same reference (e.g. "2025-001"). If the product intent is “unique per org”, this is a bug and can cause 409 for unrelated orgs.

### 3.2 Lower / already mitigated

- **Readiness:** Raw DB exception no longer exposed; generic "Database unavailable" + server-side logging (`app/routers/health.py`).
- **Upload:** Size limit (configurable), extension + content-type allowlist (PDF, JPG, PNG) in onboarding upload.
- **Onboarding token:** HMAC-SHA256, expiry, constant-time compare.
- **Passwords:** Argon2 via argon2-cffi; no raw passwords in responses.

### 3.3 Gaps

- **No document download endpoint:** Stored files are written to `storage/` and `storage_key` is returned in list; there is no backend route to download by ID. If one is added later, it must resolve path from DB and validate case access; otherwise path traversal or cross-tenant access is likely.
- **create_user.py default password:** Script uses a hardcoded default password (`create_user.py`). Safe only for first-run; doc should stress changing it immediately and not reusing in prod.

---

## 4. Performance risks

- **create_all at every startup:** `main.py` calls `Base.metadata.create_all(bind=engine)` on each API startup. With Alembic in use, this is redundant in prod and can mask migration issues. Prefer “Alembic only” in production and optional create_all only in dev.
- **No connection pooling tuning:** `db.py` uses default engine; no `pool_size` / `max_overflow` for PostgreSQL. Under load, connection exhaustion is possible.
- **Dashboard summary N+0 but heavy:** `dashboard_summary` runs several separate count queries (by status, by decision). Correct but could be one or two queries with conditional aggregation to reduce round-trips.
- **PDF generation synchronous:** `generate_case_pdf` is CPU and I/O bound; called in request thread. Large cases or many concurrent exports can block workers. Consider background task or queue for heavy reports.
- **Screening HTTP timeout:** OpenSanctions call uses 30s timeout (`app/services/screening.py`). Slow API can hold the request; consider non-blocking or background job for screening.

---

## 5. Maintainability issues

- **Unused dependencies:** `requirements.txt` includes `passlib[bcrypt]` and `bcrypt`; authentication uses **Argon2** only. Dead weight and possible confusion; remove if no other code uses them.
- **S3 config unused:** `config.py` defines S3_*; onboarding upload writes only to local `storage/`. Either implement S3 or remove/deprecate S3 settings to avoid “why doesn’t S3 work?”.
- **Hardcoded risk rules:** `app/services/scoring.py` uses in-code sets (e.g. `RISK_COUNTRIES`, `CASH_VALUES`, `vague_keywords`). Changing rules requires code change and deploy. Consider DB or config-driven rules for flexibility.
- **apiFetch error handling:** Frontend `apiFetch` throws with stringified JSON body on non-2xx; backend often returns `detail` (string or list). Parsing `detail` for display is inconsistent; 429/413 messages may not be shown clearly (e.g. “File too large”).
- **Login page console.log:** `argos-frontend/src/app/login/page.tsx` logs login response and errors to console; remove in production to avoid leaking tokens or stack traces in support scenarios.

---

## 6. Scalability issues

- **Single-instance assumptions:** In-memory login rate limit; no distributed session or cache. Horizontal scaling (multiple API replicas) will not share rate limit state and can weaken brute-force protection.
- **Local file storage:** Uploads and PDF reports live on the API container’s filesystem. With multiple replicas, storage is not shared; no object store (S3) in use. Replicas will have inconsistent files unless a shared volume or external store is introduced.
- **No async DB driver:** Using `psycopg2` (sync). Under high concurrency, async (e.g. `asyncpg`) would allow more concurrent requests per process; current design is acceptable for moderate load but can become a bottleneck.

---

## 7. Missing best practices

- **ENVIRONMENT in prod:** Not set in `docker-compose.prod.yml`; production secret validation will not run unless set explicitly. Document and set `ENVIRONMENT=production` in prod.
- **Health/ready not at root:** Health endpoints are under default prefix (e.g. `/ready`, `/health`). Many orchestrators expect a single readiness URL; ensure it’s documented and, if needed, exposed at a stable path (e.g. `/health/ready` or root-level).
- **No request ID / correlation ID:** No middleware or header for tracing a request across logs. Harder to debug in production.
- **Tests:** Only `tests/test_smoke.py` (single flow with SQLite and overridden get_db). No unit tests for services (scoring, audit, onboarding token), no auth/rate-limit/upload tests, no frontend tests. Regression risk is high.
- **Logging:** No structured logging or log level configuration; `logger.exception` used in readiness only. Rest of app relies on uvicorn default.
- **Admin update_user:** Uses `setattr(u, k, v)` from `payload.model_dump(exclude_unset=True)`. Currently `UserUpdate` only has `role` and `is_active`, so safe. If new fields are added (e.g. password), explicit allowlist is safer than mass assignment.
- **Duplicate commit after log_audit:** Several routes call `log_audit`, then `db.commit()` again. Audit service does `db.add` + `flush`; the extra commit is correct but easy to forget elsewhere; a small helper (e.g. `log_audit_and_commit`) could reduce mistakes.

---

## 8. Recommendations

- Set **ENVIRONMENT=production** in production Compose and document it; consider failing startup if critical env vars are missing in prod.
- Add a **shared “get case with access” dependency** and use it everywhere case access is checked to avoid duplication and mistakes.
- **Remove or replace** JWT storage from localStorage (e.g. httpOnly cookie or short-lived token + refresh) and document XSS mitigations.
- **Document** that login rate limiting is per-process and recommend Redis (or similar) for multi-worker/multi-replica.
- **Clarify case reference uniqueness:** If per-org uniqueness is required, change to unique on `(org_id, reference)` and add a migration.
- **Run Alembic only in production** and remove or gate `create_all` to dev so prod schema is migration-driven only.
- **Remove unused dependencies** (passlib, bcrypt) and either implement S3 for uploads/reports or remove S3 config from docs.
- **Add tests:** Service-level tests (scoring, audit, onboarding token), one integration test for auth/rate limit/upload, and document how to run tests in CI.
- **Structured logging and request ID** for production troubleshooting.
- **Frontend:** Remove login console.log; improve error handling for 4xx (e.g. 429, 413) so backend `detail` is shown to the user.

---

## 9. Prioritized top 10 improvements

| # | Priority | Improvement | Rationale |
|---|----------|-------------|-----------|
| 1 | **P0** | Set **ENVIRONMENT=production** in prod Compose and in DEPLOYMENT.md | Ensures production secret validation runs; avoids starting with placeholder secrets. |
| 2 | **P0** | **Clarify case reference uniqueness** (global vs per-org); if per-org, add unique (org_id, reference) and migration | Prevents 409 conflicts between orgs and aligns DB with product intent. |
| 3 | **P1** | **Introduce shared dependency** for “get case with access” (e.g. get_case_for_user) and use it in all case-scoped routes | Reduces duplication and RBAC mistakes. |
| 4 | **P1** | **Document/login rate limit** and add Redis (or shared store) for multi-worker/multi-replica | Restores brute-force protection when scaling out. |
| 5 | **P1** | **Remove create_all in production** (or run only when ENVIRONMENT != production) and rely on Alembic | Ensures prod schema is migration-only and avoids drift. |
| 6 | **P2** | **Remove unused dependencies** (passlib, bcrypt) from requirements.txt | Less surface area and clearer auth stack. |
| 7 | **P2** | **Add tests:** scoring, audit, onboarding token, one auth/upload flow | Catches regressions and documents expected behavior. |
| 8 | **P2** | **Stop storing JWT in localStorage** or document XSS mitigations; consider httpOnly cookie or short-lived token | Reduces impact of XSS on token theft. |
| 9 | **P3** | **Implement S3 (or remove S3 config)** for uploads/reports if multi-replica or durable storage is required | Aligns config with behavior and supports scaling. |
| 10 | **P3** | **Structured logging + request ID** and remove login console.log in frontend | Improves production debugging and avoids leaking tokens in console. |

---

*End of audit report. No code was rewritten; analysis and recommendations only.*
