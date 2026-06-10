# backend/repository.py
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db_models import EventLog


@dataclass
class MissionSummary:
    mission_id: uuid.UUID
    event_count: int
    first_event_at: datetime
    last_event_at: datetime


class EventLogRepository:
    """Persistence for `event_log` rows (WARNING/CRITICAL+ mission events)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert(
        self, *, timestamp: datetime, severity: str, message: str, mission_id: uuid.UUID
    ) -> EventLog:
        event = EventLog(
            timestamp=timestamp, severity=severity, message=message, mission_id=mission_id
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_by_severity(self, severity: str) -> list[EventLog]:
        result = await self.session.execute(
            select(EventLog)
            .where(EventLog.severity == severity)
            .order_by(EventLog.timestamp)
        )
        return list(result.scalars().all())

    async def get_by_mission(self, mission_id: uuid.UUID) -> list[EventLog]:
        result = await self.session.execute(
            select(EventLog)
            .where(EventLog.mission_id == mission_id)
            .order_by(EventLog.timestamp)
        )
        return list(result.scalars().all())

    async def list_events(
        self, *, severity: str | None = None, mission_id: uuid.UUID | None = None
    ) -> list[EventLog]:
        query = select(EventLog).order_by(EventLog.timestamp)
        if severity is not None:
            query = query.where(EventLog.severity == severity)
        if mission_id is not None:
            query = query.where(EventLog.mission_id == mission_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_missions(self) -> list[MissionSummary]:
        """Summarize past missions by grouping persisted events by mission_id."""
        result = await self.session.execute(
            select(
                EventLog.mission_id,
                func.count(EventLog.id),
                func.min(EventLog.timestamp),
                func.max(EventLog.timestamp),
            )
            .group_by(EventLog.mission_id)
            .order_by(func.max(EventLog.timestamp).desc())
        )
        return [
            MissionSummary(
                mission_id=mission_id,
                event_count=event_count,
                first_event_at=first_event_at,
                last_event_at=last_event_at,
            )
            for mission_id, event_count, first_event_at, last_event_at in result.all()
        ]
