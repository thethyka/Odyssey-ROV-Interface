from enum import Enum
from datetime import datetime
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
