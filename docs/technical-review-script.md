# WindLens UK: Technical Lead Architecture & Code Review Script

**Target Audience**: Senior Technical Lead, Lead Data Engineer, Solutions Architect  
**Total Target Duration**: 4 minutes 45 seconds (Strictly under 5:00 minutes)  
**Presenter**: Senior Full-Stack Software Engineer & DevOps Lead  

---

## Timed Walkthrough

### 0:00 – 0:40 | Repository Structure & Architecture Overview
* **Visual**: VS Code / IDE showing file tree (`backend/app`, `frontend/src`, `docs/`, `docker-compose.yml`).
* **Speaker Script**:
  > "Welcome to the technical code walkthrough of WindLens UK.
  >
  > The system is architected as a clean decoupled stack:
  > - **Backend (`/backend`)**: Python 3.11 with FastAPI, Pydantic v2 schemas, and structlog for structured JSON logging.
  > - **Frontend (`/frontend`)**: React 18 with Vite, TypeScript in strict mode, Tailwind CSS, and Recharts.
  > - **Separation of Concerns**: Ingestion, normalization, point-in-time selection, and metric calculations are isolated in distinct services under `backend/app/services/` with zero framework lock-in.
  > - **Docker & Local Execution**: One-command orchestration via `docker-compose.yml` with health checks and isolated networking."

---

### 0:40 – 1:30 | Elexon Ingestion, Schemas, Validation & Caching
* **Visual**: Open `backend/app/services/elexon/fuelhh_client.py` and `windfor_client.py`, and `backend/app/core/cache.py`.
* **Speaker Script**:
  > "Let's inspect data ingestion. We connect to two official Elexon BMRS streams:
  > - In `fuelhh_client.py`, we query the `FUELHH` stream and strictly filter records by `fuelType == 'WIND'`. Non-wind generation is immediately dropped before serialization.
  > - In `windfor_client.py`, we parse multi-run forecast records, extracting both delivery period `startTime` and model `publishTime`.
  > - Notice how both parsers normalize incoming payloads into our shared Pydantic models: `ActualRecord` and `ForecastRecord` in `data_models.py`.
  > - To protect Elexon's endpoints from redundant downstream calls, `cache.py` implements an in-memory thread-safe LRU cache with configurable TTL (default 1800s). Incomplete or failed responses are never cached."

---

### 1:30 – 2:20 | Point-in-Time Forecast Selection & Timezone Engine
* **Visual**: Open `backend/app/services/analytics/forecast_selection.py` and `backend/app/core/timezone.py`.
* **Speaker Script**:
  > "Here in `forecast_selection.py` is the core point-in-time selection engine.
  >
  > For every delivery period, the engine identifies the configured gate cutoff on the prior day (default 11:00 D-1 Europe/London).
  > It filters all WINDFOR publications targeting that delivery hour where `publish_time_utc <= cutoff_dt_utc` and selects `max(eligible, key=lambda f: f.publish_time_utc)`.
  >
  > Note line 99: Forecasts published after the cutoff are segregated into `post_cutoff` versions. They are retained strictly for hindsight auditing in the Forecast Explorer and are mathematically blocked from the decision evaluation.
  >
  > In `timezone.py`, we use `pytz.timezone('Europe/London')` for all calendar calculations. We never hardcode fixed UTC offsets, ensuring full compliance across Daylight Saving transitions."

---

### 2:20 – 3:10 | Analytics Module & Metric Edge Cases
* **Visual**: Open `backend/app/services/analytics/metrics.py`.
* **Speaker Script**:
  > "Turning to `metrics.py`:
  > - Error sign convention is strictly defined on line 9: `error_mw = forecast_mw - actual_mw`. Positive indicates over-forecast; negative indicates under-forecast.
  > - All four core metrics—MAE, RMSE, Bias, and MAPE—are computed over identical eligible pairs where both forecast and actual data exist.
  > - Now look at lines 74–92 for `compute_mape`:
  >   If actual generation is 0 MW, dividing by zero produces infinity or crashes. Rather than substituting a fake number or reporting 0%, we isolate zero-actual periods into `n_excluded`, compute MAPE solely on nonzero observations, and explicitly return the exclusion count in our API schema."

---

### 3:10 – 4:10 | Automated Test Suite & Quality Verification
* **Visual**: Terminal executing `pytest` in `backend/` and `npm run build` in `frontend/`.
* **Speaker Script**:
  > "Quality assurance is validated through 45 automated pytest suites covering every core module:
  > - Unit tests for FuelHH and WindFor parsing and error handling.
  > - Point-in-time selection tests verifying that post-cutoff forecasts are rejected.
  > - Mathematical tests for MAE, RMSE, signed bias, and zero-actual MAPE edge cases.
  > - Integration tests verifying all FastAPI endpoints (`/health`, `/overview`, `/forecast`, `/forecast/versions`, `/analytics/accuracy`, `/settlement-periods`, and `/scenarios/residual-demand`).
  >
  > Running `pytest` gives 45 passed tests in 12 seconds.
  > Running `npm run build` executes TypeScript static analysis with zero lint or typing errors, outputting the minified production bundle."

---

### 4:10 – 5:00 | Docker, Deployment Configuration & Next Steps
* **Visual**: Open `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and `frontend/vercel.json`.
* **Speaker Script**:
  > "For local and staging execution:
  > - Running `docker compose up --build` starts both containers with automated backend health checking.
  > - The backend is deployment-ready for any containerized Python service (Render, Cloud Run, AWS ECS), while the frontend includes `vercel.json` for edge static deployment with API proxy rewrites.
  >
  > Known limitations and production roadmap:
  > 1. Authentication: the pilot is unauthenticated; production rollout will add OAuth2/OIDC with role-based access.
  > 2. Persistent Storage: current pilot uses in-memory caching; production will attach Redis and PostgreSQL for multi-year multi-gigabyte historical archive queries.
  >
  > All documentation, including `architecture.md` and `data-methodology.md`, is available in the repository. Thank you."

---

## Technical Review Checklist & Verification Commands
- [ ] Run backend tests:
  ```bash
  cd backend
  pytest
  # Verified: 45 passed
  ```
- [ ] Run frontend production build:
  ```bash
  cd frontend
  npm run build
  # Verified: 0 TypeScript errors, bundle generated
  ```
- [ ] Run via Docker Compose:
  ```bash
  docker compose up --build
  # Frontend on http://localhost:80
  # Backend on http://localhost:8000
  # OpenAPI documentation on http://localhost:8000/api/docs
  ```
- [ ] Verify API health endpoint:
  ```bash
  curl http://localhost:8000/api/health
  # Returns {"status": "ok", "version": "1.0.0", ...}
  ```
