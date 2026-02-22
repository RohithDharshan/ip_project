"""
Analytics Router
──────────────────
GET /analytics/overview       — top-level KPIs
GET /analytics/proposals      — proposals by status / event type / month
GET /analytics/approvals      — avg approval time, bottlenecks
GET /analytics/vendors        — top vendors, spending
GET /analytics/audit          — recent audit trail
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from database import get_db
from models.workflow import (
    Proposal, WorkflowStep, Vendor, ProcurementOrder,
    AuditLog, ProposalStatus, ApprovalStatus
)
from routers.auth import get_current_user
from models.workflow import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    total_proposals = (await db.execute(select(func.count()).select_from(Proposal))).scalar() or 0
    approved        = (await db.execute(
        select(func.count()).select_from(Proposal)
        .where(Proposal.status.in_([ProposalStatus.APPROVED, ProposalStatus.PROCUREMENT, ProposalStatus.COMPLETED]))
    )).scalar() or 0
    rejected        = (await db.execute(
        select(func.count()).select_from(Proposal).where(Proposal.status == ProposalStatus.REJECTED)
    )).scalar() or 0
    pending         = (await db.execute(
        select(func.count()).select_from(Proposal)
        .where(Proposal.status.in_([ProposalStatus.SUBMITTED, ProposalStatus.IN_REVIEW]))
    )).scalar() or 0

    total_budget_result = await db.execute(select(func.sum(Proposal.budget)))
    total_budget = total_budget_result.scalar() or 0

    total_spend_result = await db.execute(select(func.sum(ProcurementOrder.total_amount)))
    total_spend = total_spend_result.scalar() or 0

    vendor_count = (await db.execute(select(func.count()).select_from(Vendor).where(Vendor.is_active == True))).scalar() or 0

    return {
        "total_proposals":   total_proposals,
        "approved_proposals":approved,
        "rejected_proposals":rejected,
        "pending_proposals": pending,
        "approval_rate":     round(approved / total_proposals * 100, 1) if total_proposals else 0,
        "total_budget_requested": total_budget,
        "total_procurement_spend": total_spend,
        "active_vendors":    vendor_count,
    }


@router.get("/proposals")
async def proposals_breakdown(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    # By status
    result = await db.execute(
        select(Proposal.status, func.count()).group_by(Proposal.status)
    )
    by_status = [{"status": r[0].value if hasattr(r[0],"value") else r[0], "count": r[1]} for r in result.all()]

    # By event type
    result2 = await db.execute(
        select(Proposal.event_type, func.count()).group_by(Proposal.event_type)
    )
    by_event = [{"event_type": r[0].value if hasattr(r[0],"value") else r[0], "count": r[1]} for r in result2.all()]

    # By risk level
    result3 = await db.execute(
        select(Proposal.ai_risk_level, func.count()).group_by(Proposal.ai_risk_level)
    )
    by_risk = [{"risk": r[0], "count": r[1]} for r in result3.all()]

    # Budget distribution
    result4 = await db.execute(select(Proposal.ai_budget_cat, func.count(), func.sum(Proposal.budget)).group_by(Proposal.ai_budget_cat))
    by_budget = [{"category": r[0], "count": r[1], "total_budget": r[2] or 0} for r in result4.all()]

    return {
        "by_status":      by_status,
        "by_event_type":  by_event,
        "by_risk_level":  by_risk,
        "by_budget_cat":  by_budget,
    }


@router.get("/approvals")
async def approvals_analysis(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    # Pending steps by role
    result = await db.execute(
        select(WorkflowStep.approver_role, func.count())
        .where(WorkflowStep.status == ApprovalStatus.PENDING)
        .group_by(WorkflowStep.approver_role)
    )
    pending_by_role = [{"role": r[0], "pending": r[1]} for r in result.all()]

    # Approval rate by role
    result2 = await db.execute(
        select(WorkflowStep.approver_role, WorkflowStep.status, func.count())
        .where(WorkflowStep.status.in_([ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]))
        .group_by(WorkflowStep.approver_role, WorkflowStep.status)
    )
    rate_data: dict = {}
    for role, status, cnt in result2.all():
        if role not in rate_data:
            rate_data[role] = {"approved": 0, "rejected": 0}
        key = status.value if hasattr(status, "value") else status
        if "approved" in key:
            rate_data[role]["approved"] += cnt
        else:
            rate_data[role]["rejected"] += cnt

    approval_rates = [
        {
            "role":          role,
            "approved":      d["approved"],
            "rejected":      d["rejected"],
            "approval_rate": round(d["approved"] / (d["approved"] + d["rejected"]) * 100, 1)
                             if (d["approved"] + d["rejected"]) else 0,
        }
        for role, d in rate_data.items()
    ]

    return {
        "pending_by_role": pending_by_role,
        "approval_rates":  approval_rates,
    }


@router.get("/vendors")
async def vendor_analytics(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Vendor).where(Vendor.is_active == True).order_by(desc(Vendor.rating)).limit(10)
    )
    top_vendors = result.scalars().all()

    # Vendor category distribution
    result2 = await db.execute(
        select(Vendor.category, func.count()).group_by(Vendor.category)
    )
    by_category = [
        {"category": r[0].value if hasattr(r[0], "value") else r[0], "count": r[1]}
        for r in result2.all()
    ]

    return {
        "top_vendors": [
            {"id": v.id, "name": v.name, "category": v.category.value if hasattr(v.category,"value") else str(v.category),
             "rating": v.rating, "past_orders": v.past_orders}
            for v in top_vendors
        ],
        "by_category": by_category,
    }


@router.get("/audit")
async def recent_audit(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id":          l.id,
            "action":      l.action,
            "entity_type": l.entity_type,
            "entity_id":   l.entity_id,
            "proposal_id": l.proposal_id,
            "user_id":     l.user_id,
            "details":     l.details,
            "timestamp":   l.timestamp.isoformat(),
        }
        for l in logs
    ]
