# Odyssey HMI Development Plan

This document outlines the current scope of work (tracked as GitHub issues) and a roadmap of possible extensions to expand the project beyond the MVP.

---

## Phase 1: Setup & Project Structure
- **Issue #1: [Setup] Initialise Project Structure & Git Repo**
  - Create `frontend/`, `backend/`, `docs/`, `proto/` directories.
  - Initialise GitHub repo with `main` branch and populated `README.md`.
  - Populate `docs/` with scenario and architecture specifications.

- **Issue #2: [Setup] Implement Docker Compose for Dev Environment**
  - Multi-service dev environment with hot reload for frontend and backend.
  - Frontend served at `http://localhost:5173`, backend at `http://localhost:8000`.

---

## Phase 2: Backend Foundations
- **Issue #3: [Backend] Create WebSocket Endpoint**
  - FastAPI `/ws/telemetry` endpoint streaming simulator data.
  - Backend maintains active connections.

- **Issue #19: [Backend] Implement Scenario-Based ROV State Simulator**
  - Implements the three pre-scripted mission scenarios.
  - State machine + Pydantic models.
  - Generates in-memory mission logs.

- **Issue #20: [Backend] Stream Telemetry**
  - Broadcast full `TelemetryMessage` JSON to connected clients at 1Hz.
  - Matches schema in the architecture docs.

---

## Phase 3: Frontend Foundations
- **Issue #4: [Frontend] Build Static HMI Layout Shell**
  - Header, sidebar, main content, and footer scaffolding.
  - Placeholder components (e.g. `MissionStatusIndicator`, `KeyReadoutPanel`).

- **Issue #21: [Frontend] State Management & WebSocket Client**
  - Zustand store holds telemetry state.
  - WebSocket client service connects to backend and updates store.

- **Issue #22: [Frontend] Display Live Data**
  - Bind UI components to telemetry (depth, power, pressure, alerts).
  - Flashing master alarm indicator implemented in frontend logic.

---

## Phase 4: Interactivity & Control
- **Issue #23: [Backend] Implement WebSocket Command Handler**
  - Simulator responds to commands: `START_SIMULATION`, `SET_PROPULSION_STATE`, etc.
  - Operator actions recorded in mission log.

- **Issue #24: [Frontend] Implement Scenario Selector**
  - UI to choose a mission scenario.
  - Sends `START_SIMULATION` command over WebSocket.
  - Frontend resets UI back to standby when missions complete.

- **Issue #25: [Frontend] Interactive System Diagram (React Flow)**
  - Visual diagram of subsystems (Power, Propulsion, Hull, etc.).
  - Node colors driven by telemetry.
  - Optional: node clicks navigate to controls.

- **Issue #24: [Frontend] Subsystem Control Buttons**
  - All Stop, Deploy Arm, Collect Sample, and guarded Jettison Package.
  - Guarded button requires explicit confirmation in the UI.

---

## Phase 5: Mission Logs
- **Issue #26: [Proto] Define gRPC Service**
  - Create `mission_log.proto` file for MissionLogService.

- **Issue #27: [Backend] Implement gRPC Mission Log Service**
  - Python gRPC server serving mission log data.
  - REST `/mission-log` available as fallback.

- **Issue #28: [Frontend] Mission Log Modal**
  - Modal fetches mission log (REST now, gRPC-Web later).
  - Displays structured log entries.

---

## Phase 6: Documentation & Deployment
- **Issue #29: [Documentation] Finalize README & Demo**
  - Update README with summary, stack, quickstart.
  - Add animated demo GIF.

- **Issue #17: [Deployment] Deploy to Fly.io**
  - Separate `fly.toml` for frontend and backend.
  - Configure CORS for cross-service connections.
  - Publish live demo URL.

---

# Extensions & Future Work

The following features are not required for MVP but can flesh out the project into a richer, production-grade simulation.

### Frontend Enhancements
- **UI Polish**
  - Add dark/light theme switcher.
  - Improve alert feed (filtering, severity icons).
- **Scenario Replay**
  - Allow operators to replay completed missions from logs.
  - Scrubber/timeline UI to move through telemetry snapshots.
- **Analytics View**
  - Charts for depth vs. time, battery drain, pressure curves.

### Backend Enhancements
- **Persistence**
  - Store mission logs in SQLite/Postgres instead of in-memory.
  - Allow fetching logs from past sessions.
- **Scenario Authoring**
  - Configurable/custom scenarios loaded from JSON or YAML files.
  - Parameterized missions (depth, rates, failure timings).
- **Scalability**
  - Broadcast telemetry to many clients reliably.
  - Support multiple independent ROV simulations per user.

### Protocol Improvements
- **gRPC-Web Full Adoption**
  - Replace REST with gRPC entirely once frontend tooling is stable.
- **GraphQL Gateway**
  - Optional GraphQL API to query telemetry/logs more flexibly.

### Testing & Tooling
- **Load Testing**
  - Simulate multiple concurrent operators.
- **Integration Tests**
  - Full E2E tests connecting frontend + backend.
- **CI/CD**
  - GitHub Actions workflows for linting, tests, deployment.

### Deployment Extensions
- **Cloud Infrastructure**
  - Deploy to AWS/GCP/Azure with managed services.
- **Offline Demo**
  - Package as a single Docker image (frontend + backend) for easy demo distribution.

---

# Roadmap Summary
- **MVP**: Implement issues #1–#17.  
- **Phase 2**: Add persistence + configurable scenarios.  
- **Phase 3**: Polish UI, replay/analytics, full gRPC adoption.  
- **Phase 4**: Scale deployments + CI/CD for production-readiness.