"""
Audit Service
──────────────
Records every action into the audit_logs table.
Provides query helpers for the audit trail API.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.workflow import AuditLog


class AuditService:

    @staticmethod
    async def log(
        db:          AsyncSession,
        action:      str,
        entity_type: str  = None,
        entity_id:   int  = None,
        proposal_id: int  = None,
        user_id:     int  = None,
        details:     Dict[str, Any] = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            proposal_id=proposal_id,
            user_id=user_id,
            details=details or {},
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def get_for_proposal(
        db: AsyncSession,
        proposal_id: int,
        limit: int = 100,
    ):
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.proposal_id == proposal_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 50):
        result = await db.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()
