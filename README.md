# ship-stuff-faster

Django + Next.js scaffold for starting new projects without the week-one tax.

## Stack

- **API**: Django 5, DRF, SimpleJWT, PostgreSQL, Poetry
- **Web**: Next.js 15, React 19, Tailwind 4, shadcn/ui, Vitest

## Starting from this scaffold

### 1. Copy the repo

Clone or copy the directory. Exclude `.git/`, `.beads/`, and `sg-firm/` — those are project-specific. Start fresh:

```bash
git init
```

### 2. Rename project references

Two search-and-replace passes across the repo:

- `ssf` → your short name (e.g. `myapp`) — covers DB name/user defaults in `settings.py` and `.env.example`
- `ship-stuff-faster` → your project slug (e.g. `my-app`) — covers `pyproject.toml`, settings docstrings, and `web/src/app/layout.tsx`

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
