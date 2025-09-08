# backend/simulator.py
from datetime import datetime, timezone
from typing import Optional, List, Dict

from backend.models import (
    RovState,
    MissionState,
    ActiveAlert,
    TelemetryMessage,
    Power,
    Propulsion,
    HullIntegrity,
    ManipulatorArm,
    SciencePackage,
    Environment,
)
from backend.logs import LogEntry, LogLevel


class RovSimulator:
    """
    Manages the state and scenario logic for the Odyssey ROV simulation.

    Key behavior changes vs prior version:
    - Pressure Anomaly 'All Stop': no depth snap; we keep current depth but
      immediately clear the alert and mark hull status nominal (UX-friendly).
    - Operator override is honored across scenarios: once set, scenario update
      logic won't force propulsion, nor escalate the anomaly further.
    """

    TARGET_DEPTH = 2000.0
    DESCENT_RATE = 25.0  # meters per second
    ASCENT_RATE = 20.0  # meters per second

    # Pressure constants
    PRESSURE_PER_METER = 9.807  # kPa per meter
    PRESSURE_WARNING_THRESHOLD = TARGET_DEPTH * PRESSURE_PER_METER * 1.1
    PRESSURE_CRITICAL_THRESHOLD = TARGET_DEPTH * PRESSURE_PER_METER * 1.2

    # Ticks-per-second (used by the websocket loop)
    TICKS_PER_SECOND = 5

    def __init__(self):
        self.active_scenario: Optional[str] = None
        self.scenario_timer: int = 0
        self.simulation_running: bool = False
        self.mission_log: List[LogEntry] = []
        self.operator_override: bool = (
            False  # set when operator issues a propulsion command
        )
        self._reset_state()

    # --- Setup & Logging ---

    def _reset_state(self):
        """Reset simulator to standby state."""
        self.rov_state = RovState(
            power=Power(charge_percent=100.0, status="discharging"),
            propulsion=Propulsion(power_level_percent=0.0, status="inactive"),
            hull_integrity=HullIntegrity(hull_pressure_kpa=0, status="nominal"),
            manipulator_arm=ManipulatorArm(status="stowed", sample_collected=False),
            science_package=SciencePackage(status="attached"),
            environment=Environment(depth_meters=0.0, water_temp_celsius=18.0),
        )
        self.mission_state = MissionState(status="standby")
        self.alert = ActiveAlert(active=False)
        self.active_scenario = None
        self.scenario_timer = 0
        self.simulation_running = False
        self.mission_log = []
        self.operator_override = False

    def _add_log_entry(self, level: LogLevel, message: str):
        """Record a new mission log entry."""
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc), level=level, message=message
        )
        self.mission_log.append(entry)

    # --- Public API ---

    def get_telemetry(self) -> TelemetryMessage:
        """Return a snapshot of current telemetry."""
        return TelemetryMessage(
            timestamp=datetime.now(timezone.utc).isoformat(),
            rov_state=self.rov_state,
            mission_state=self.mission_state,
            alert=self.alert,
        )

    def get_mission_log(self) -> List[LogEntry]:
        """Return all mission log entries so far."""
        return self.mission_log

    def handle_command(self, command: Dict):
        """Handle commands from the frontend."""
        command_name = command.get("command")
        payload = command.get("payload", {})

        match command_name:
            case "START_SIMULATION":
                self._handle_start_simulation(payload.get("scenario"))
            case "SET_PROPULSION_STATE":
                self._add_log_entry(
                    LogLevel.OPERATOR,
                    f"Command Sent: SET_PROPULSION_STATE({payload.get('status')}).",
                )
                self._handle_set_propulsion(payload.get("status"))
            case "DEPLOY_ARM":
                self._add_log_entry(LogLevel.OPERATOR, "Command Sent: DEPLOY_ARM.")
                self._handle_deploy_arm()
            case "COLLECT_SAMPLE":
                self._add_log_entry(LogLevel.OPERATOR, "Command Sent: COLLECT_SAMPLE.")
                self._handle_collect_sample()
            case "JETTISON_PACKAGE":
                self._add_log_entry(
                    LogLevel.OPERATOR, "Command Sent: JETTISON_PACKAGE."
                )
                self._handle_jettison_package()
            case "RESET_SIMULATION":
                self._reset_state()
                self._add_log_entry(LogLevel.INFO, "Simulation reset to standby.")
            case _:
                self._add_log_entry(
                    LogLevel.WARNING, f"Unknown command: {command_name}"
                )

    def update(self):
        """Advance simulation by one tick (called by websocket loop)."""
        if not self.simulation_running:
            return

        self.scenario_timer += 1

        updater = getattr(self, f"_update_{self.active_scenario}_scenario", None)
        if updater:
            updater()

        self._update_physics()

    # --- Command Handlers ---

    def _handle_start_simulation(self, scenario: Optional[str]):
        if scenario in ["nominal", "pressure_anomaly", "power_fault"]:
            self._reset_state()
            self.active_scenario = scenario
            self.simulation_running = True
            self.mission_state.status = "en_route"
            self._add_log_entry(
                LogLevel.INFO,
                f"Scenario Started: {scenario.replace('_', ' ').title()}.",
            )
            self._add_log_entry(LogLevel.INFO, "Mission status changed to 'en_route'.")
        else:
            self._add_log_entry(
                LogLevel.WARNING, f"Attempted to start unknown scenario: {scenario}"
            )

    def _handle_set_propulsion(self, status: str):
        if status not in ["active", "inactive"]:
            return

        self.rov_state.propulsion.status = status
        self.operator_override = True  # operator is in control from now on

        # Special handling for Pressure Anomaly: clear the condition without snapping depth
        if self.active_scenario == "pressure_anomaly" and status == "inactive":
            if self.rov_state.hull_integrity.status in ["warning", "critical"]:
                # Keep current depth (no snap), but clear the anomaly and alert.
                self.rov_state.hull_integrity.status = "nominal"
                self.alert = ActiveAlert(active=False)
                self.scenario_timer = 0
                self._add_log_entry(LogLevel.INFO, "Hull pressure returned to nominal.")
                self._add_log_entry(LogLevel.INFO, "Operator intervention successful.")

    def _handle_deploy_arm(self):
        if self.rov_state.manipulator_arm.status == "stowed":
            self.rov_state.manipulator_arm.status = "deployed"
            self._add_log_entry(
                LogLevel.INFO, "Manipulator arm status changed to 'deployed'."
            )

    def _handle_collect_sample(self):
        if self.rov_state.manipulator_arm.status == "deployed":
            self.rov_state.manipulator_arm.status = "gripping"
            self.rov_state.manipulator_arm.sample_collected = True
            self._add_log_entry(LogLevel.INFO, "Sample collected successfully.")

    def _handle_jettison_package(self):
        if self.rov_state.science_package.status == "attached":
            self.rov_state.science_package.status = "jettisoned"
            if self.rov_state.power.status == "fault":
                self.rov_state.power.status = "discharging"
                self.alert = ActiveAlert(active=False)
                self.mission_state.status = "emergency_ascent"
                # Force propulsion on for ascent, but still mark as operator override
                self.rov_state.propulsion.status = "active"
                self.operator_override = True
                self._add_log_entry(
                    LogLevel.INFO, "Science package jettisoned. Power drain stabilized."
                )
                self._add_log_entry(
                    LogLevel.INFO, "Mission status changed to 'emergency_ascent'."
                )

    # --- Scenario Logic ---

    def _update_nominal_scenario(self):
        # Respect operator override: do not force propulsion if the operator has intervened.
        if self.mission_state.status == "en_route":
            if (
                not self.operator_override
                and self.rov_state.environment.depth_meters < self.TARGET_DEPTH
            ):
                self.rov_state.propulsion.status = "active"
            elif self.rov_state.environment.depth_meters >= self.TARGET_DEPTH:
                self.mission_state.status = "searching"
                if not self.operator_override:
                    self.rov_state.propulsion.status = "inactive"
                self.scenario_timer = 0
                self._add_log_entry(
                    LogLevel.INFO, "Mission status changed to 'searching'."
                )

        # Searching prompt
        if (
            self.mission_state.status == "searching"
            and self.scenario_timer > 30
            and not self.alert.active
        ):
            self.alert = ActiveAlert(
                active=True,
                severity="INFO",
                message="Bioluminescent signature detected. Ready to deploy manipulator arm.",
            )
            self._add_log_entry(
                LogLevel.INFO,
                "Bioluminescent signature detected. Awaiting operator action.",
            )

        # Collect sample → return
        if (
            self.rov_state.manipulator_arm.sample_collected
            and self.mission_state.status != "returning"
        ):
            self.mission_state.status = "returning"
            # If operator hasn't explicitly stopped propulsion, turn it on for ascent
            if self.rov_state.propulsion.status != "inactive":
                self.rov_state.propulsion.status = "active"
            self.alert = ActiveAlert(active=False)
            self._add_log_entry(LogLevel.INFO, "Mission status changed to 'returning'.")

        # Surface
        if (
            self.mission_state.status == "returning"
            and self.rov_state.environment.depth_meters <= 0
        ):
            self.mission_state.status = "mission_success"
            self.rov_state.propulsion.status = "inactive"
            self.simulation_running = False
            self._add_log_entry(
                LogLevel.INFO, "Mission status changed to 'mission_success'."
            )

    def _update_pressure_anomaly_scenario(self):
        # If operator has intervened, do not force propulsion or escalate the anomaly any further.
        if self.operator_override:
            return

        if self.mission_state.status == "en_route":
            self.rov_state.propulsion.status = "active"

        # Escalation logic only active if not overridden by operator
        if (
            self.rov_state.hull_integrity.status == "nominal"
            and self.rov_state.hull_integrity.hull_pressure_kpa
            > self.PRESSURE_WARNING_THRESHOLD
        ):
            self.rov_state.hull_integrity.status = "warning"
            self.scenario_timer = 0
            self.alert = ActiveAlert(
                active=True,
                severity="WARNING",
                message="Hull pressure exceeds nominal limits. Halt descent.",
            )
            self._add_log_entry(
                LogLevel.WARNING, "Hull pressure exceeds nominal limits."
            )

        if (
            self.rov_state.hull_integrity.status == "warning"
            and self.scenario_timer > 30
        ):
            self.rov_state.hull_integrity.status = "critical"
            self.scenario_timer = 0
            self.alert = ActiveAlert(
                active=True,
                severity="CRITICAL",
                message="CRITICAL: Hull pressure at dangerous levels!",
            )
            self._add_log_entry(
                LogLevel.CRITICAL, "Hull pressure has reached a critical level!"
            )

        if (
            self.rov_state.hull_integrity.status == "critical"
            and self.scenario_timer > 15
        ):
            self.mission_state.status = "mission_failure_hull_breach"
            self.simulation_running = False
            self._add_log_entry(
                LogLevel.CRITICAL,
                "Mission status changed to 'mission_failure_hull_breach'.",
            )

    def _update_power_fault_scenario(self):
        if (
            self.mission_state.status == "en_route"
            and self.rov_state.environment.depth_meters < self.TARGET_DEPTH
        ):
            # Respect operator override: don't force if they've stopped it.
            if not self.operator_override:
                self.rov_state.propulsion.status = "active"
        elif (
            self.mission_state.status == "en_route"
            and self.rov_state.environment.depth_meters >= self.TARGET_DEPTH
        ):
            self.mission_state.status = "searching"
            if not self.operator_override:
                self.rov_state.propulsion.status = "inactive"
            self.scenario_timer = 0
            self._add_log_entry(LogLevel.INFO, "Mission status changed to 'searching'.")

        if (
            self.mission_state.status == "searching"
            and self.scenario_timer > 10
            and self.rov_state.power.status != "fault"
        ):
            self.rov_state.power.status = "fault"
            self.scenario_timer = 0
            self.alert = ActiveAlert(
                active=True,
                severity="CRITICAL",
                message="Power system fault! Catastrophic drain. Jettison package to save ROV.",
            )
            self._add_log_entry(
                LogLevel.CRITICAL,
                "Power system fault detected. Catastrophic battery drain.",
            )

        if (
            self.rov_state.power.status == "fault"
            and self.rov_state.power.charge_percent <= 0
        ):
            self.mission_state.status = "mission_failure_lost_signal"
            self.simulation_running = False
            self.alert = ActiveAlert(
                active=True, severity="CRITICAL", message="Battery at 0%. Signal lost."
            )
            self._add_log_entry(LogLevel.CRITICAL, "Battery at 0%. Signal lost.")
            self._add_log_entry(
                LogLevel.CRITICAL,
                "Mission status changed to 'mission_failure_lost_signal'.",
            )

        if (
            self.mission_state.status == "emergency_ascent"
            and self.rov_state.environment.depth_meters <= 0
        ):
            self.mission_state.status = "mission_success"
            self.simulation_running = False
            self.alert = ActiveAlert(active=False)
            self._add_log_entry(LogLevel.INFO, "ROV returned to surface successfully.")

    # --- General Physics ---

    def _update_physics(self):
        """Update depth, pressure, and battery drain each tick."""
        current_depth = self.rov_state.environment.depth_meters

        # --- Autopilot enforcement ---
        # Ensure propulsion stays on during ascent phases
        if self.mission_state.status in ["returning", "emergency_ascent"]:
            self.rov_state.propulsion.status = "active"

        # --- Depth updates ---
        if self.rov_state.propulsion.status == "active":
            if self.mission_state.status in ["en_route", "searching"]:
                # Descend, but never beyond 150% target depth
                self.rov_state.environment.depth_meters = min(
                    self.TARGET_DEPTH * 1.5,
                    current_depth + self.DESCENT_RATE,
                )
            elif self.mission_state.status in ["returning", "emergency_ascent"]:
                # Ascend, but never above surface
                self.rov_state.environment.depth_meters = max(
                    0,
                    current_depth - self.ASCENT_RATE,
                )

        # --- Pressure updates ---
        # Always consistent with depth; anomaly "status" may be cleared by override
        self.rov_state.hull_integrity.hull_pressure_kpa = int(
            self.rov_state.environment.depth_meters * self.PRESSURE_PER_METER
        )
        if self.rov_state.propulsion.status == "active":
            self.rov_state.propulsion.power_level_percent = 75.0  # some nominal thrust
        else:
            self.rov_state.propulsion.power_level_percent = 0.0

        # --- Battery drain ---
        drain_rate = 0.01
        if self.rov_state.power.status == "fault":
            drain_rate += 1.5
        elif self.rov_state.propulsion.status == "active":
            drain_rate += 0.1

        self.rov_state.power.charge_percent = max(
            0,
            self.rov_state.power.charge_percent - drain_rate,
        )
