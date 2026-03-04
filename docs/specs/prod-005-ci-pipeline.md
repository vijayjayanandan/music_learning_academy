# PROD-005: GitHub Actions CI Pipeline

## Status: Done

## Summary
CI pipeline on push/PR to main running system checks, migrations, pytest, and migration conflict detection on Python 3.10 and 3.11.

## Implementation
- Triggers on push to `main` and pull requests targeting `main`
- Matrix strategy: Python 3.10 and 3.11
- Steps: checkout, setup Python, install requirements, Django system check, migrate, run pytest, check for migration conflicts
- Uses SQLite for CI (no external services needed)
- Caches pip dependencies for faster runs

## Files Modified/Created
- `.github/workflows/ci.yml` — full CI workflow definition

## Configuration
- `DJANGO_SETTINGS_MODULE=config.settings.dev` in CI environment
- `SECRET_KEY` set to a test value for CI
- No external services required (SQLite + LocMemCache)

## Verification
- Push to main or open a PR — verify GitHub Actions runs green
- Introduce a broken migration — verify CI catches the conflict
- Introduce a failing test — verify CI fails with clear error output
