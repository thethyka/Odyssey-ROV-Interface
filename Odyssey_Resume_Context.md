# Odyssey ROV HMI — Resume Reference Document

## Project Overview

**Odyssey ROV HMI** is a self-motivated, full-stack Human-Machine Interface (HMI) application for controlling and monitoring a simulated deep-sea Remotely Operated Vehicle (ROV). The operator uses the interface to navigate the ROV to a target depth of 2,000m, collect a specimen using a robotic manipulator arm, and return safely — while monitoring live telemetry and responding to system alerts.

The project was built entirely from scratch as a personal engineering challenge, with two explicit goals: to explore **high-performance HMI design principles** and to demonstrate the ability to architect and deliver a complete full-stack application independently.

---

## Motivation

- **Self-initiated** — no course requirement, no team, no deadline
- Driven by a desire to explore the design philosophy behind **mission-critical, operator-facing interfaces** (avionics, maritime, industrial control systems)
- Used as a vehicle to hone full-stack engineering skills: system design, API architecture, real-time data streaming, and frontend component engineering
- Deliberately chose a technically challenging domain (ROV control, real-time telemetry, bidirectional comms) to push beyond standard CRUD application patterns

---

## HMI Design Philosophy

A core focus of this project was applying rigorous, research-informed HMI design principles — not just building a functional UI:

- **Attention as a finite resource** — monochrome greyscale base palette; colour used exclusively for alerts and warnings to avoid desensitisation
- **Situational awareness over aesthetics** — data presented in context (e.g. pressure shown alongside a nominal/warning/critical indicator, not just a raw number)
- **Hierarchy of information** — UI structured across two levels: Level 1 (overall system health, mission status, active alerts) and Level 2 (subsystem detail: propulsion, power, claw, navigation)
- **Perception → Comprehension → Projection** — interface designed to make data clear, contextualise normal vs abnormal states, and predict future ROV states before they become critical
- Icons kept deliberately simple and 2D to reduce cognitive load under high-stress conditions

---

## Tech Stack

### Frontend
- **Framework:** React 19 with TypeScript
- **Build tool:** Vite 7
- **Styling:** Tailwind CSS v4
- **State management:** Zustand
- **Real-time comms:** WebSocket client (native browser API) consuming live telemetry stream
- **gRPC:** `grpc-web` + `protobufjs` for typed communication with the alert/mission log service
- **UI components:** Phosphor Icons, `clsx`, `tailwind-merge`
- **Diagramming:** ReactFlow (for subsystem topology views)

### Backend
- **Language & framework:** Python 3.11, FastAPI
- **Real-time:** WebSocket endpoint (`/ws/telemetry`) streaming full ROV state snapshots at a configurable tick rate (2 Hz)
- **Data validation:** Pydantic v2 models with typed enums, field constraints, and custom validators (e.g. `AfterValidator` for decimal rounding)
- **Simulation engine:** Custom `RovSimulator` class managing all ROV state, scenario logic, physics approximations, and operator command handling
- **gRPC service:** `MissionLogService` defined via Protocol Buffers — serves historical alert/mission log data with typed request/response contracts
- **REST:** FastAPI REST endpoints for health checks and mission log access
- **ASGI server:** Uvicorn

### Infrastructure
- **Containerisation:** Docker + Docker Compose
- **Services:** Backend (Python 3.11 slim) + Frontend (Node 22 Alpine) with hot reload in dev
- **Architecture:** Bidirectional WebSocket for real-time control and telemetry; gRPC-Web for structured historical data queries

---

## Technical Scope

### Simulation Engine
- Built a stateful ROV simulator from scratch managing: power (battery drain), propulsion, hull integrity (pressure-based, depth-derived), manipulator arm, science package, and environmental readings (depth, water temperature)
- Simulated physics: depth calculated from descent/ascent rates, pressure derived from depth (`9.807 kPa/m`), with warning and critical thresholds
- Scenario system: multiple injectable failure/event scenarios (e.g. pressure anomaly, lost signal, emergency ascent) with timer-driven progression
- Operator override logic: operator commands pause automated scenario logic, preserving operator authority over the system

### Real-Time Architecture
- Backend streams a complete `TelemetryMessage` state snapshot to all connected clients at 2 ticks/second over a persistent WebSocket connection
- Commands flow back from the frontend to the backend over the same bidirectional WebSocket (e.g. `START_SIMULATION`, `ALL_STOP`, `DEPLOY_ARM`)
- gRPC (via Protocol Buffers) used for the `MissionLogService` — demonstrates use of two distinct communication protocols in one application

### Data Modelling
- All ROV state modelled as strict Pydantic schemas with typed literals for status fields (e.g. `"nominal" | "warning" | "critical"`), validated field ranges, and automatic rounding validators
- Mission state machine with 8 discrete states covering full mission lifecycle: `standby → en_route → searching → returning → mission_success / emergency_ascent / mission_failure_*`
- Alert model with severity levels: `INFO`, `WARNING`, `CRITICAL`, `OPERATOR`

### Frontend Architecture
- Feature-based folder structure: `alerting`, `dashboard`, `mission-control`, `rov-systems`
- Zustand store for global telemetry state, decoupled from WebSocket service layer
- Typed WebSocket service abstraction and gRPC alert service (`alertService.ts`) kept separate from UI components
- ReactFlow used for subsystem topology visualisation

---

## Key Skills & Competencies Demonstrated

- **Solo full-stack delivery** — designed and built the entire system independently, end-to-end
- **Systems design** — chose and justified multiple communication protocols (REST, WebSocket, gRPC) for distinct use cases within a single application
- **Domain-driven design** — applied real HMI/UX principles from safety-critical industries to a software project
- **Real-time systems** — bidirectional WebSocket architecture with stateful server-side simulation
- **Protocol Buffers / gRPC** — defined typed service contracts and implemented gRPC-Web on the client
- **Pydantic data modelling** — strict, validated data contracts shared across the full stack
- **State machine design** — mission lifecycle modelled as a discrete finite state machine
- **TypeScript + React** — modern component architecture with typed service layers and Zustand state management
- **Dockerised development environment** — multi-service Compose setup with hot reload

---

## Key Phrases for Resume Use

- *Full-stack HMI application built from scratch*
- *Real-time ROV telemetry streaming via WebSocket*
- *Dual-protocol architecture: WebSocket (real-time) + gRPC (historical data)*
- *High-performance, mission-critical interface design*
- *Custom simulation engine with stateful scenario logic*
- *Pydantic-validated data contracts across full stack*
- *React 19 + FastAPI + Protocol Buffers*
- *Self-directed; sole developer from architecture to deployment*
- *Applied aviation/maritime HMI design principles (attention management, information hierarchy)*
- *Dockerised multi-service development environment*

---

## Framing Notes

- This project signals **engineering initiative and intellectual curiosity** — it's not a tutorial project, it's a self-designed challenge with a real design philosophy behind it
- The **HMI design angle** is rare and differentiating — it shows awareness of human factors, not just code output
- The **dual-protocol architecture** (WebSocket + gRPC in the same app) demonstrates deliberate technical decision-making, not just defaulting to REST for everything
- Depending on the role, lean into: systems/backend engineering (simulator, state machine, protocols), frontend engineering (React, real-time UI, Zustand), or design/UX (HMI philosophy, information hierarchy)
- The **solo delivery** point is strong for roles that value autonomy and self-direction
