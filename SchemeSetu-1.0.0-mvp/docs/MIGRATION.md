# Migration Map

This document records the migration decisions made when consolidating the legacy `backend old` and `frontend 1` into the current unified structure.

## Backend Migration Mapping

| Old Component | Status | Target Destination | Reason |
|---|---|---|---|
| `backend old/app/gemini.py` | REPLACE | `backend/app/agent/gemini_client.py` | Migrated to the new `google-genai` SDK and strictly limited to data extraction. |
| `backend old/eligibility.py` | KEEP/MERGE | `backend/app/engine/eligibility.py` | Proven deterministic logic; merged into the new engine structure. |
| `backend old/chat.py` | MERGE | `backend/app/services/chat_service.py` | Restructured to separate API routing from core business logic. |
| `backend old/models/` | REPLACE | `backend/app/models/` | Rewritten from bare PyMongo/Motor dicts to strictly typed Beanie ODM documents. |
| `backend old/scraper/` | REPLACE | `backend/app/services/firecrawl_service.py` | Outdated web scraping replaced with a Firecrawl pipeline and HTTPX fallback. |
| `backend old/docker-compose.yml` | DELETE | N/A | Removed Docker integration as per updated product requirements. |

## Frontend Migration Mapping

| Old Component | Status | Target Destination | Reason |
|---|---|---|---|
| `frontend 1/` | DELETE | `frontend/` | Fully discarded in favor of a clean Vite + React + Vanilla CSS application. |
| Legacy Auth | REPLACE | `frontend/src/pages/Auth.jsx` | Rewritten to support proper JWT/Session handling with the new backend. |
| Admin Dashboard | NEW | `frontend/src/pages/AdminDashboard.jsx` | Built from scratch to support scheme ingestion and governance logging. |
