# HMI Toolkit & Architecture (MVP)


## Core Simulated Objects (The "Model")

These are the ROV subsystems whose state will be simulated by the backend.

| Object              | Key Attributes                                            | Purpose                                                    |
| :------------------ | :-------------------------------------------------------- | :--------------------------------------------------------- |
| **Power System**    | `charge_percent` (0-100), `status` ('discharging', 'fault') | The main battery. |
| **Propulsion**      | `power_level_percent` (0-100), `status` ('active', 'inactive') | Thrusters (consumes power when active) |
| **Hull Integrity**  | `hull_pressure_kpa` (Number), `status` ('nominal', 'warning', 'critical') | Hull pressure, need to ascend if it gets too high |
| **Manipulator Arm** | `status` ('stowed', 'deployed', 'gripping'), `sample_collected` (boolean) | Tool for collecting the bioluminescent slug. |
| **Environment**     | `depth_meters` (Number), `water_temp_celsius` (Number) | Provides situational awareness of surroundings. |
| **Mission State**   | `status` ('en_route', 'searching', 'collecting', 'returning') | Tracks high-level mission progress. |

---

## 2. WebSocket Service: Real-Time Telemetry

**Purpose**: Continuous firehose of ROV telemetry to the frontend.  
**Endpoint**: `/ws/telemetry`  
**Format**: JSON (for debug visibility during MVP).  

**Frequency**: 1Hz (once per second).  

**Example Message:**

```json
{
  "timestamp": "2025-09-03T14:30:00Z",
  "rov_state": {
    "power": { "charge_percent": 82.5, "status": "discharging" },
    "propulsion": { "power_level_percent": 75.0, "status": "active" },
    "hull_integrity": { "hull_pressure_kpa": 20265, "status": "nominal" },
    "manipulator_arm": { "status": "stowed", "sample_collected": false },
    "environment": { "depth_meters": 2015.7, "water_temp_celsius": 2.8 }
  },
  "mission_state": { "status": "en_route" },
  "active_alert": { "active": false, "severity": null, "message": null }
}

```

--- 


## 3. gRPC Service: On-Demand Historical Data (Stub for MVP)

- **Service:** `AlertService`  
- **Method:** `GetHistoricalAlerts`  
  - **Purpose:** Demonstrates gRPC-Web integration by fetching past alerts.  
  - **Request:** A time window (e.g., last 5 minutes).  
  - **Response:** A list of `Alert` messages.  
  - **MVP Approach:** Proto file + client stub + dummy data response (no real DB integration yet).  

---

## 4. HMI Layout & Component Architecture

The HMI is a single-screen app with a persistent four-quadrant layout. This enforces information hierarchy and constant situational awareness.

### Overall Layout
### Overall Layout

| [ A ] Header: Master Status |
|-----------------------------|

| [ B ] Sidebar: Critical Readouts & Alerts | [ C ] Main Content: System Views (Switchable) |
|-------------------------------------------|-----------------------------------------------|

| [ D ] Footer: Commands |
|------------------------|
---

### Section Breakdown (MVP Focus)

#### A. Header: Master Status
- **`MissionStatusIndicator`**: Displays mission phase (`en_route`, `collecting`, etc.).  
- **`MasterAlarmIndicator`**: Prominent alarm banner, flashes if `alert.active = true`.  

#### B. Sidebar: Critical Readouts & Alerts
- **`KeyReadoutPanel`**: Always-visible indicators for:  
  - Depth  
  - Battery %  
  - Hull Pressure  
- **`LiveAlertFeed`**: Scrolling feed of incoming `alert.message` values.  

#### C. Main Content: System Views
- **`ViewSwitcher`**: Tabs for Level 1 overview vs Level 2 subsystem control.  
- **View 1: `SystemOverview` (Level 1)**  
  - **`InteractiveSystemDiagram`** built with React Flow.  
  - Nodes = Power, Propulsion, Manipulator, Hull.  
  - Node colors update dynamically from telemetry status.  
- **View 2: `SubsystemControls` (Level 2)**  
  - For MVP: Implement Propulsion card fully (show % power + “All Stop” button).  
  - Other subsystems can be stubbed with placeholder cards.  
  - **`GuardedActionButton`** for one critical action only (Deploy Arm).  

#### D. Footer: Commands
- **`HistoricalAlertsButton`**: Opens modal.  
- **`HistoricalAlertsModal`**: Calls gRPC-Web `GetHistoricalAlerts` (stubbed data) and displays results in a simple table.  

---

## 5. Future Expansion (Post-MVP)
- Navigation system with `coordinates` and `heading`.  
- Command sequencer for queued ROV commands.  
- Camera feed placeholder.  
- Database-backed alert history.  