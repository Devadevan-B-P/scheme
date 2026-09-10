# Current State Audit

## Overview
The platform has been fully consolidated into a single backend and a single frontend. The legacy `backend old` and `frontend 1` codebases were audited, merged where applicable, and then deleted. 

## Project Roots
- `backend/`: The unified FastAPI backend.
- `frontend/`: The unified React + Vite frontend.
- `docs/`: Documentation and provenance records.
- `README.md`: Root configuration and product definition.

## Test Suite Status
- **Test Command**: `uv run pytest -v`
- **Total Tests**: 104
- **Passing**: 104
- **Failing**: 0
- **Skipped/Errors**: 0

## Dependency Audit
- **Backend Environment**: Managed purely via `uv` (`pyproject.toml` and `uv.lock`). No stray `requirements.txt` files remain.
- **Key Backend Dependencies**: FastAPI, Beanie (Async MongoDB), Google GenAI SDK, Pydantic, Pytest.
- **Frontend Environment**: Managed via `npm` (`package.json` and `package-lock.json`).
- **Key Frontend Dependencies**: React, Vite, React Router DOM.
- **Removed**: Docker integration, Motor (replaced by Beanie), Google Cloud Vision (replaced by pure AI extraction pipelines / PaddleOCR planned), old LangChain references.

## Database
- **Provider**: MongoDB (accessed asynchronously via Beanie ODM).
- **Collections mapped**:
  - `User`
  - `BeneficiaryProfile`
  - `Scheme`
  - `Partner`
  - `AuditLog`
  - `ConsentRecord`

## Secrets & Environment
- Environment variables are strictly maintained in `backend/.env`.
- No sensitive keys (`*.key`, `gcp-service-account.json`) are committed to version control. They are gitignored.
