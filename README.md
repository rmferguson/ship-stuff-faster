# ship-stuff-faster

A Django + Next.js scaffold built to get a solo founder or small team to a live product with a real customer — in week one, not week eight. It skips the tooling a mid-size team eventually needs (Celery, Redis, CI/CD, Sentry, brute-force defense, type-safe API client generation), because a pre-launch product doesn't need any of that yet.

The closest comparable is Vinta's django-react-boilerplate (~2.3k GitHub stars), which ships all of the above out of the box — that's the week-eight scope this project deliberately skips. The concrete difference: this scaffold runs on Next.js App Router (SSR, file-based routing), not a React SPA on a Webpack build.

Built for developers who already know what they're doing and want the auth, proxy, and database plumbing done correctly on day one: Django 5 + DRF + SimpleJWT auth, a Next.js httpOnly-cookie + proxy pattern instead of raw JWT in localStorage, shadcn/ui, and a Django test suite with Hypothesis-based property tests and IDOR tests already in place. Spend your time on the product, not on rebuilding boilerplate.

## Stack

- **API**: Django 5, DRF, SimpleJWT, PostgreSQL, Poetry
- **Web**: Next.js 15, React 19, Tailwind 4, shadcn/ui, Vitest

## Starting from this scaffold

### 1. Copy the repo

Clone or copy the directory. Exclude `.git/`, `.dolt/`, `.claude/`, and `sg-firm/` — those are project-specific. Start fresh:

```bash
git init
```

### 2. Rename project references

Two search-and-replace passes across the repo:

- `ssf` → your short name (e.g. `myapp`) — covers DB name/user defaults in `settings.py` and `.env.example`
- `ship-stuff-faster` → your project slug (e.g. `my-app`) — covers the docstrings in `settings.py` and `test_settings.py`, and `web/src/app/layout.tsx`

`api/pyproject.toml`'s `description` field uses title case (`"Ship Stuff Faster — Django API"`), so the search-and-replace above won't catch it — update that line by hand if you want it renamed too.

### 3. Create a PostgreSQL database

```bash
createuser -P your_app_user
createdb -O your_app_user your_db
```

### 4. Configure environment

```bash
cp .env.example .env
```

Fill in at minimum:

- `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DATABASE_PASSWORD`

### 5. Install dependencies and migrate

```bash
cd api && poetry install && python manage.py migrate
cd ../web && npm install
```

### 6. Run

```bash
# API (from api/)
python manage.py runserver

# Web (from web/)
npm run dev
```

API runs at `http://localhost:8000`, web at `http://localhost:3000`.

## Development

```bash
# API tests
cd api && poetry run pytest

# Web tests
cd web && npm test

# Linting / type-check
cd api && poetry run ruff check . && poetry run mypy .
cd web && npm run type-check
```
