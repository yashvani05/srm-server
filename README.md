# srm-server

Service Request Management API. Django 5, Django REST Framework, PostgreSQL, Redis, Celery.

## Local setup

Requires Python 3.12+, PostgreSQL and Redis.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# create a .env file with the variables below
python manage.py migrate
python manage.py runserver 8000
```

Background jobs (overdue check) need a worker and scheduler:

```sh
celery -A config worker -l info
celery -A config beat -l info
```

API docs are served at `/api-docs/` (basic auth: `SWAGGER_USER` / `SWAGGER_PASS`).

Tests: `python manage.py test`

## Environment variables

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Required when `DJANGO_DEBUG` is false |
| `DJANGO_DEBUG` | `true` for local development |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts, e.g. `my-server.vercel.app` |
| `CORS_ORIGIN` | Comma-separated client origins, e.g. `https://my-client.vercel.app` |
| `DATABASE_URL` | Postgres URL. If unset, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` are used |
| `DB_SSL` | `true` for hosted databases such as Supabase |
| `REDIS_URL` | Cache and Celery broker |
| `JWT_SECRET` | Defaults to `DJANGO_SECRET_KEY` |
| `JWT_EXPIRES_SECONDS` | Token lifetime |
| `SWAGGER_USER`, `SWAGGER_PASS` | Basic auth for `/api-docs/` |
| `CRON_SECRET` | Shared secret for cron-triggered endpoints |
| `OVERDUE_CHECK_INTERVAL_SECONDS` | Default 60 |
| `DASHBOARD_CACHE_TTL_SECONDS` | Default 60 |
| `LOGIN_RATE_LIMIT_MAX`, `TRUST_PROXY`, `LOG_LEVEL` | Optional tuning |

## Deploy (Vercel)

Framework preset: **Other**. `vercel.json` routes all requests to `api/index.py`.

1. Use a hosted Postgres (Supabase Session pooler URL) and Redis (e.g. Upstash).
2. Set the variables above in the Vercel project, including `DB_SSL=true`.
3. Run `python manage.py migrate` once against the hosted database.

Celery workers cannot run on Vercel; run them on another host or trigger the overdue check with a Vercel Cron job.
