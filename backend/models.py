from pydantic import BaseModel, Field, AfterValidator
from typing import Annotated, Literal, Optional

def round_dp(num_decimals: int):
    """Returns a function that rounds a float to the specified number of decimal places."""
    def _round_float(v: float) -> float:
        return round(v, num_decimals)
    return _round_float


class Power(BaseModel):
    charge_percent: Annotated[float, Field(ge=0, le=100), AfterValidator(round_dp(2))]
    status: Literal["discharging", "fault"]


class Propulsion(BaseModel):
    power_level_percent: Annotated[float, Field(ge=0, le=100), AfterValidator(round_dp(2))]
    status: Literal["active", "inactive"]


class HullIntegrity(BaseModel):
    hull_pressure_kpa: int
    status: Literal["nominal", "warning", "critical"]


class ManipulatorArm(BaseModel):
    status: Literal["stowed", "deployed", "gripping"]
    sample_collected: bool


class SciencePackage(BaseModel):
    status: Literal["attached", "jettisoned"]


class Environment(BaseModel):
    depth_meters: Annotated[float, AfterValidator(round_dp(1))]
    water_temp_celsius: Annotated[float, AfterValidator(round_dp(1))]


class MissionState(BaseModel):
    status: Literal[
        "standby",
        "en_route",
        "searching",
        "returning",
        "mission_success",
        "emergency_ascent",
        "mission_failure_hull_breach",
        "mission_failure_lost_signal",
    ]


class ActiveAlert(BaseModel):
    active: bool
    severity: Optional[Literal["INFO", "WARNING", "CRITICAL"]] = None
    message: Optional[str] = None


class RovState(BaseModel):
    power: Power
    propulsion: Propulsion
    hull_integrity: HullIntegrity
    manipulator_arm: ManipulatorArm
    science_package: SciencePackage
    environment: Environment


class TelemetryMessage(BaseModel):
    timestamp: str
    rov_state: RovState
    mission_state: MissionState
    alert: ActiveAlert