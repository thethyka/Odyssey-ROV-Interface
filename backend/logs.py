from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OPERATOR = "OPERATOR"


class LogEntry(BaseModel):
    timestamp: datetime
    level: LogLevel
    message: str
