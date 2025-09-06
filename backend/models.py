from pydantic import BaseModel, Field
from datetime import datetime
from typing import Annotated, Literal, Callable, Optional

def round_dp(num_decimals: int) -> Callable[[float], float]:
    """Returns a function that rounds a float to the specified number of decimal places."""
    def _round_float(v: float) -> float:
        return round(v, num_decimals)
    return _round_float
    
class Power(BaseModel):
    charge_percent: Annotated[float, Field(ge=0, le=100), round_dp(2)]
    status: Literal["discharging", "fault"]
    
class Propulsion(BaseModel):
    power_level_percent: Annotated[float, Field(ge=0, le=100), round_dp(2)]
    status: Literal["active", "inactive"]

class HullIntegrity(BaseModel):
    hull_pressure_kpa: int
    status: Literal["nominal", "warning", "critical"]

class ManipulatorArm(BaseModel):
    status: Literal["stowed", "deployed", "gripping"]
    sample_collected: bool

class Environment(BaseModel):
    depth_meters: float
    water_temp_celsius: Annotated[float, round_dp(1)]
    
class MissionState(BaseModel):
    status: Literal["en_route", "searching", "collecting", "returning"]
    
    
class ActiveAlert(BaseModel):
    active: bool
    severity: Optional[Literal["INFO", "WARNING", "CRITICAL"]] = None
    message: Optional[str] = None
    
class RovState(BaseModel):
    power: Power
    propulsion: Propulsion
    hull_integrity: HullIntegrity
    manipulator_arm: ManipulatorArm
    environment: Environment
    
class TelemetryMessage(BaseModel):
    timestamp: datetime
    rov_state: RovState
    mission_state: MissionState
    alert: ActiveAlert
    
    
    
    
    
    