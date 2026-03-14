# Production deployment guide

This document describes how to deploy Argos CENTIF Immo to production using Docker and docker-compose. It covers required environment variables, starting the stack, and first-run setup.

## Prerequisites

- Docker and docker-compose installed on the server
- A public hostname (or IP) for the API and, if separate, for the frontend (e.g. `api.argos.ci`, `app.argos.ci`)

## Required production environment variables

Set these **before** building or starting the production stack. Use a `.env` file in the project root or export them in the shell. For the API container to receive **CORS_ORIGINS** and **ONBOARDING_BASE_URL**, pass them via your compose setup (e.g. add `env_file: - .env` to the `api` service, or list them in the `environment` section using `${CORS_ORIGINS}` and `${ONBOARDING_BASE_URL}`). For the frontend, **NEXT_PUBLIC_API_BASE_URL** must be passed as a build arg when building the frontend image.

| Variable | Description | Example |
|----------|-------------|---------|
| **CORS_ORIGINS** | Comma-separated list of allowed frontend origins (no spaces). The browser sends the origin of the page making API requests; it must be in this list or requests will be blocked. | `https://app.argos.ci` or `https://app.argos.ci,https://www.argos.ci` |
| **ONBOARDING_BASE_URL** | Public base URL of the API (scheme + host, no path). Used when generating onboarding/KYC upload links sent to clients. Must be the URL end users can reach. | `https://api.argos.ci` |
| **NEXT_PUBLIC_API_BASE_URL** | Public base URL of the API used by the **frontend** in the browser. Must be the same API URL end users use. Set at **build time** for the frontend image. | `https://api.argos.ci` |
| **JWT_SECRET** | Secret used to sign and verify JWT access tokens. Use a long, random value (e.g. 32+ characters). Never use the default `change-me` or `change-this-in-prod`. | Generate with: `openssl rand -hex 32` |
| **ONBOARDING_LINK_SECRET** | Secret used to sign onboarding tokens (KYC upload links). Use a long, random value different from JWT_SECRET. | Generate with: `openssl rand -hex 32` |
| **DATABASE_URL** | PostgreSQL connection URL for the API. Must match the credentials used by the `db` service. | `postgresql+psycopg2://argos:YOUR_DB_PASSWORD@db:5432/argos_centif` |

### Database credentials

`docker-compose.prod.yml` defines the database with:

- **POSTGRES_USER**: `argos`
- **POSTGRES_PASSWORD**: set in the `db` service (default in the file is `argos_password`; change it for production)
- **POSTGRES_DB**: `argos_centif`

The API service must use the same credentials in **DATABASE_URL** (e.g. `postgresql+psycopg2://argos:argos_password@db:5432/argos_centif`). If you change the password in the `db` service, update the API `DATABASE_URL` accordingly.

### Optional but recommended

- **ACCESS_TOKEN_MINUTES**: Token lifetime in minutes (default 720 = 12 hours).
- **ONBOARDING_LINK_TTL_HOURS**: Validity of onboarding links in hours (default 72).

## Starting the production stack

1. Copy `.env.example` to `.env` and set all required variables (see above). Ensure **JWT_SECRET** and **ONBOARDING_LINK_SECRET** are strong and unique, and that **CORS_ORIGINS**, **ONBOARDING_BASE_URL**, and **NEXT_PUBLIC_API_BASE_URL** match your public URLs.

2. Build and start the stack:

   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env up -d --build
   ```

   This starts:

   - **db**: PostgreSQL 16 (port 5432)
   - **api**: FastAPI backend (port 8000)
   - **frontend**: Next.js app (port 3000)

3. Expose the services via your reverse proxy (e.g. Nginx or Traefik) so that:

   - The API is reachable at your chosen public URL (e.g. `https://api.argos.ci`).
   - The frontend is reachable at your chosen public URL (e.g. `https://app.argos.ci`).

   Ensure **CORS_ORIGINS** contains the frontend origin (e.g. `https://app.argos.ci`) and **ONBOARDING_BASE_URL** / **NEXT_PUBLIC_API_BASE_URL** match the API public URL.

## Database migrations (Alembic)

Schema changes are versioned with Alembic. On a **fresh PostgreSQL** database, run migrations before creating the initial user:

```bash
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

This creates all tables and enum types. The API still runs `create_all` at startup (harmless if tables already exist). For an existing database that already has tables (e.g. created by a previous `create_all`), record the current state without applying the initial migration by running: `alembic stamp head`.

## First-run: database and initial admin user

The database starts empty. You must create the initial organization and an admin user before anyone can log in.

1. Ensure the stack is running and the API can reach the database. If the DB is fresh, run `alembic upgrade head` as above first.

2. Run the `create_user` script inside the API container (it uses the same **DATABASE_URL** as the API from docker-compose):

   ```bash
   docker-compose -f docker-compose.prod.yml run --rm api python create_user.py
   ```

   If you use a `.env` file, ensure the `api` service receives the correct **DATABASE_URL** (e.g. by setting it in `.env` and passing it through the compose file). If the database port is published and you prefer to run the script on the host, set **DATABASE_URL** and run: `python create_user.py`.

3. The script creates:

   - An organization named **Argos Demo Agency**
   - An admin user: **email** `admin@argos.ci`, **password** `ChangeMe123!`

4. **Change the default admin password immediately** after first login. Use the application (e.g. profile or admin area) to set a strong password, or create a new admin user and deactivate the default one. Do not leave the default password in use in production.

## Health checks

- **Liveness**: `GET /health` → `{"status": "ok"}` (no dependencies).
- **Readiness**: `GET /ready` → `{"status": "ready"}` if the database is reachable; otherwise 503.

Use these in your orchestrator (e.g. Kubernetes or a reverse proxy) for health and readiness probes.

## Summary checklist

- [ ] Set **CORS_ORIGINS** to your frontend origin(s).
- [ ] Set **ONBOARDING_BASE_URL** and **NEXT_PUBLIC_API_BASE_URL** to your public API URL.
- [ ] Set **JWT_SECRET** and **ONBOARDING_LINK_SECRET** to strong, unique values.
- [ ] Set **DATABASE_URL** (and DB password in the `db` service) to secure values.
- [ ] Start the stack with `docker-compose -f docker-compose.prod.yml up -d --build`.
- [ ] Run the first-run script to create the initial org and admin user.
- [ ] Log in as admin and change the default password immediately.
