# API Migration & Contract

## Target Architecture
- **Primary Routes**: `/api/v1/*` (or standard root prefix)
- **Compatibility Routes**: `app/compatibility/` (wraps legacy routes to new services)

## Current Endpoint Surface

| Method | Route | Purpose | Used By | Status |
|--------|-------|---------|---------|--------|
| POST | `/auth/signup` | Register user | Frontend Auth | Active |
| POST | `/auth/login` | Authenticate user | Frontend Auth | Active |
| GET | `/auth/profile/{user_id}` | Fetch profile | Frontend Profile | Active |
| PUT | `/auth/profile/{user_id}` | Update profile | Frontend Profile | Active |
| POST | `/api/chat` | Main conversational flow | Frontend Chat | Active |
| GET | `/api/schemes` | Fetch schemes | Frontend Admin/Results | Active |
| POST | `/api/schemes/ingest` | Scrape & Ingest schemes | Frontend Admin | Active |
| POST | `/api/partners/nearest` | Find nearest partners | Frontend Partners | Active |

## Frontend ↔ Backend Contracts

- **Base URL**: The frontend is configured to point to `http://localhost:8000` via a centralized `api/client.js`.
- **Authentication**: Uses `localStorage` to store user sessions and attaches tokens/user_id to required backend requests.
- **Data Formats**: All bodies and responses are strict JSON matching Pydantic/Beanie models on the backend.
  - *Example*: The `/api/schemes` route returns a list of serialized `Scheme` documents exactly as expected by the frontend state store.
