
# HMI Toolkit & Architecture

This document outlines the technical architecture, data models, communication protocols, and component structure for the Odyssey ROV HMI.

### Developer Quick Start

To get started with the HMI, follow these steps:

1.  **Run the Backend:** Launch the backend service using `docker compose up`. The backend will be available at `localhost:8000`.
2.  **Connect a WebSocket Client:** Use any tool (e.g., a simple script, Postman) to connect to the WebSocket at `ws://localhost:8000/ws/telemetry`.
3.  **Observe the Initial State:** You will immediately receive the `'standby'` telemetry message. This is the starting point for the UI.
4.  **Start a Scenario:** Send a `START_SIMULATION` command (see command table) over the WebSocket to begin receiving live mission data.

---

## 1. Data Models (The "Model")

The entire state of the simulation is defined by a set of Pydantic models. These models form the contract for all data sent from the backend to the frontend.

### Primary Data Models

| Model | Attribute | Type | Description |
| :--- | :--- | :--- | :--- |
| **Power** | `charge_percent` | `float` (0-100) | Current battery charge percentage. |
| | `status` | `'discharging'` \| `'fault'` | Operational status of the power system. |
| **Propulsion** | `power_level_percent` | `float` (0-100) | Current power output of the thrusters. |
| | `status` | `'active'` \| `'inactive'` | Whether the thrusters are currently running. |
| **Hull Integrity** | `hull_pressure_kpa` | `int` | External water pressure on the hull in kilopascals. |
| | `status` | `'nominal'` \| `'warning'` \| `'critical'` | The integrity status based on current pressure. |
| **Manipulator Arm**| `status` | `'stowed'` \| `'deployed'` \| `'gripping'` | The current state of the robotic arm. |
| | `sample_collected` | `bool` | True if the slug has been successfully collected. |
| **Science Package**| `status` | `'attached'` \| `'jettisoned'` | The state of the disposable science hardware. |
| **Environment** | `depth_meters` | `float` | Current depth of the ROV below sea level. |
| | `water_temp_celsius`| `float` | Ambient water temperature. |

### State & Alerting Models

| Model | Attribute | Type | Description |
| :--- | :--- | :--- | :--- |
| **Mission State**| `status` | `'standby'` \| `'en_route'` \| `'searching'` \| `'returning'` \| `'mission_success'` \| `'emergency_ascent'` \| `'mission_failure_hull_breach'` \| `'mission_failure_lost_signal'` | The high-level status of the entire mission. |
| | `operator_override` | `bool` | **True if the operator has manually intervened (e.g., hit "All Stop"), pausing the automated scenario logic.** |
| **Active Alert**| `active` | `bool` | True if there is any active alert. |
| | `severity` | `'INFO'` \| `'WARNING'` \| `'CRITICAL'` \| `null` | The severity level of the current alert. |
| | `message` | `str` \| `null` | The instructional message for the operator. |

---

## 2. WebSocket Service: Real-Time Communication

The primary communication channel is a bidirectional WebSocket connection.

**Endpoint**: `/ws/telemetry`

### Telemetry (Backend -> Frontend)

The backend streams a complete state snapshot to all connected clients at a 1Hz frequency.

**Message Root Object:** `TelemetryMessage`

**Example `TelemetryMessage` Payload:**

```json
{
  "timestamp": "2025-09-03T14:30:00Z",
  "rov_state": {
    "power": { "charge_percent": 82.5, "status": "discharging" },
    "propulsion": { "power_level_percent": 75.0, "status": "active" },
    "hull_integrity": { "hull_pressure_kpa": 20265, "status": "nominal" },
    "manipulator_arm": { "status": "stowed", "sample_collected": false },
    "science_package": { "status": "attached" },
    "environment": { "depth_meters": 2015.7, "water_temp_celsius": 2.8 }
  },
  "mission_state": { "status": "en_route", "operator_override": false },
  "alert": { "active": false, "severity": null, "message": null }
}
```

**Initial Telemetry Message (`standby` state)**

Before any scenario is started, the backend will stream the following message. This represents the initial state the frontend should expect upon connecting.

```json
{
  "timestamp": "2025-09-03T14:29:00Z",
  "rov_state": {
    "power": { "charge_percent": 100.0, "status": "discharging" },
    "propulsion": { "power_level_percent": 0.0, "status": "inactive" },
    "hull_integrity": { "hull_pressure_kpa": 0, "status": "nominal" },
    "manipulator_arm": { "status": "stowed", "sample_collected": false },
    "science_package": { "status": "attached" },
    "environment": { "depth_meters": 0.0, "water_temp_celsius": 18.0 }
  },
  "mission_state": { "status": "standby", "operator_override": false },
  "alert": { "active": false, "severity": null, "message": null }
}
```

### Operator Commands (Frontend -> Backend)

The frontend sends commands to the backend simulator to control the mission flow and respond to events. All commands are JSON objects with a `command` name and an optional `payload`.

| Command Name | Description | Payload Structure | Usage Context |
| :--- | :--- | :--- | :--- |
| `START_SIMULATION` | Tells the backend to begin a specific, pre-scripted scenario. | `{ "scenario": "nominal" \| "pressure_anomaly" \| "power_fault" }` | At the start of a session, to kick off a simulation run. |
| `SET_PROPULSION_STATE` | Turns the ROV's main propulsion on or off. | `{ "status": "active" \| "inactive" }` | In the Pressure Anomaly scenario, to halt descent. |
| `DEPLOY_ARM` | Commands the manipulator arm to move from `stowed` to `deployed`. | `{}` | In the Nominal Mission, after the slug is detected. |
| `COLLECT_SAMPLE` | Commands the deployed arm to grip and secure the sample. | `{}` | In the Nominal Mission, after the arm is deployed. |
| `JETTISON_PACKAGE`| Executes the irreversible emergency action of dropping the science package. | `{}` | In the Critical Power Fault scenario, to save the ROV. |

---

## 3. gRPC Service: On-Demand Mission Event Log

-   **Service:** `MissionLogService`
-   **Method:** `GetMissionLog`
    -   **Purpose:** To demonstrate a robust RPC pattern for fetching structured historical data. The Mission Log provides a comprehensive, time-stamped record of all significant events during a simulation run, which is critical for post-mission analysis.
    -   **Request:** `GetMissionLogRequest` (can be empty for the MVP).
    -   **Response:** `GetMissionLogResponse` containing a list of `LogEntry` messages.
    -   **MVP Approach:** The backend simulator will generate log entries in memory as the simulation runs. This gRPC service will return the list of all entries generated so far for the current session.

### Conceptual Proto Definition (`mission_log.proto`)

```protobuf
syntax = "proto3";

service MissionLogService {
  rpc GetMissionLog(GetMissionLogRequest) returns (GetMissionLogResponse);
}

message GetMissionLogRequest {}

message GetMissionLogResponse {
  repeated LogEntry entries = 1;
}

message LogEntry {
  enum LogLevel {
    INFO = 0;      // System milestones
    WARNING = 1;   // Warnings
    CRITICAL = 2;  // Critical failures
    OPERATOR = 3;  // User-initiated commands
  }

  string timestamp = 1;
  LogLevel level = 2;
  string message = 3;
}
```

---

## 4. HMI Layout & Component Architecture

The HMI is a single-screen app with a persistent structure to maintain constant situational awareness:

| [ A ] Header: Master Status |
| :--- |
| **[ B ] Sidebar: Critical Readouts & Alerts** \| **[ C ] Main Content: System Views** |
| [ D ] Footer: Global Commands & Actions |

---

### Component Breakdown

#### A. Header: Master Status
- **`MissionStatusIndicator`**
  - Displays the current `mission_state.status` from telemetry.
- **`MasterAlarmIndicator`**
  - A banner that reacts to `alert.severity`.
  - **Severity colors**:  
    - INFO → Blue  
    - WARNING → Yellow  
    - CRITICAL → Red  
  - **Flashing behavior**: When severity is `WARNING` or `CRITICAL`, the banner should flash to draw attention.
---

#### B. Sidebar: Critical Readouts & Alerts
- **`KeyReadoutPanel`**
  - Always-visible numerical readouts for:  
    - `environment.depth_meters`  
    - `power.charge_percent`  
    - `hull_integrity.hull_pressure_kpa`
- **`LiveAlertFeed`**
  - Displays new incoming `alert.message` values as a scrolling feed.
  - Each alert is timestamped with the telemetry time.

---

#### C. Main Content: System Views
- **`ScenarioSelector`**
  - Initial view shown when `mission_state.status` = `standby`.
  - Allows the operator to send a `START_SIMULATION` command with a scenario choice (`nominal`, `pressure_anomaly`, `power_fault`).
  - **Scenario Lifecycle**:
    - Once a scenario begins, the selector disappears.
    - At the end of a scenario (`mission_success` or any failure state), the frontend should prompt the user with a **"Return to Scenario Selector"** action that resets the UI to standby.
    - Backend currently resets automatically when `START_SIMULATION` is called again.
- **`ViewSwitcher`**
  - Tabs for toggling between two detail views once a scenario is running.
- **View 1: `SystemOverview` (Level 1)**
  - **`InteractiveSystemDiagram`** (React Flow)  
    - Renders nodes for subsystems: Power, Propulsion, Hull, etc.  
    - Node colors driven by subsystem `status` values in telemetry.
- **View 2: `SubsystemControls` (Level 2)**
  - Cards for direct operator interaction:
    - **Propulsion Card** → Includes **"All Stop"** button (`SET_PROPULSION_STATE: inactive`).
    - **Manipulator Arm Card** → Includes **"Deploy Arm"** and **"Collect Sample"** buttons.
    - **Science Package Card** → Includes **GuardedActionButton** for the **"Jettison Package"** command.
      - **Guarded Action UX**: This button must require confirmation (e.g. click twice, or confirmation modal). The backend expects a plain `JETTISON_PACKAGE` command, so confirmation is a **frontend-only responsibility**.
  - **Note for Frontend - Command Availability**: The backend does not explicitly state which commands are valid at any given time. The frontend is responsible for implementing the UI logic to enable/disable control buttons based on the current system state. For example, the "Collect Sample" button should be disabled until `manipulator_arm.status` is 'deployed'. This prevents user confusion from clicking a button that does nothing.

---

#### D. Footer: Global Commands & Actions
- **`MissionLogButton`**
  - Opens a modal to display the mission event log.
- **`MissionLogModal`**
  - On open, calls the backend log API.  
  - Backend currently provides logs over REST (`/mission-log`); a gRPC service (`MissionLogService.GetMissionLog`) is planned for future compliance.

---

### Notes & Responsibilities

- **Backend responsibilities**:  
  - Provide telemetry at 1 Hz via WebSocket.  
  - Accept operator commands (`START_SIMULATION`, `DEPLOY_ARM`, etc.).  
  - Maintain and expose mission logs.  

- **Frontend responsibilities**:  
  - Animate flashing alerts based on severity.  
  - Implement guarded action UX for irreversible commands.  
  - Manage scenario lifecycle (reset UI to standby when missions end).  
  - Poll mission log via REST until gRPC is available.
  - **Manage Command Availability**: Intelligently enable/disable action buttons based on the current telemetry to guide the operator and prevent invalid actions.
  - **Communicate Operator Override**: Clearly indicate when an automated scenario has been manually overridden by the operator by checking the `mission_state.operator_override` flag. The backend will halt the scenario logic, but the frontend must visually communicate this "manual control" or "paused" state to the user.