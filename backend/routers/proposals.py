"""
Proposals Router
──────────────────
GET    /proposals               — list all (with filters)
POST   /proposals               — submit new proposal
GET    /proposals/{id}          — get single proposal
PATCH  /proposals/{id}/status   — update status
DELETE /proposals/{id}          — delete (draft only)
GET    /proposals/{id}/agent-trace — get AI agent trace
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from database import get_db
from models.workflow import Proposal, WorkflowStep, User, ProposalStatus, EventType
from agents.orchestrator import AgentOrchestrator
from services.audit_service import AuditService
from services.email_service import EmailService
from routers.auth import get_current_user

router      = APIRouter(prefix="/proposals", tags=["proposals"])
orchestrator = AgentOrchestrator()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ProposalIn(BaseModel):
    title:              str
    description:        str
    event_type:         str
    budget:             float
    requirements:       Optional[str] = None
    venue:              Optional[str] = None
    expected_date:      Optional[str] = None
    expected_attendees: Optional[int] = 50


class ProposalOut(BaseModel):
    id:                 int
    title:              str
    description:        str
    event_type:         str
    budget:             float
    requirements:       Optional[str]
    venue:              Optional[str]
    expected_date:      Optional[str]
    expected_attendees: Optional[int]
    status:             str
    submitted_by:       int
    ai_intent:          Optional[str]
    ai_risk_level:      Optional[str]
    ai_budget_cat:      Optional[str]
    ai_routing_path:    Optional[list]
    created_at:         datetime
    updated_at:         datetime

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_all_proposals_dicts(db: AsyncSession) -> List[dict]:
    result = await db.execute(select(Proposal))
    return [
        {"expected_date": p.expected_date, "submitted_by": p.submitted_by,
         "status": p.status.value if p.status else None, "department": None}
        for p in result.scalars().all()
    ]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ProposalOut])
async def list_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    event_type:    Optional[str] = Query(None),
    limit:         int           = Query(50, le=200),
    offset:        int           = Query(0),
    db: AsyncSession             = Depends(get_db),
    current_user: User           = Depends(get_current_user),
):
    q = select(Proposal).order_by(desc(Proposal.created_at)).limit(limit).offset(offset)
    if status_filter:
        q = q.where(Proposal.status == status_filter)
    if event_type:
        q = q.where(Proposal.event_type == event_type)

    # Non-admin users see only their own proposals; coordinators and above see all
    if current_user.role.value == "faculty":
        q = q.where(Proposal.submitted_by == current_user.id)

    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=ProposalOut, status_code=201)
async def create_proposal(
    data:         ProposalIn,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    # Gather existing proposals for compliance check
    existing = await _get_all_proposals_dicts(db)

    proposal_dict = data.model_dump()
    proposal_dict["submitted_by"] = current_user.id

    # Run the agent pipeline
    pipeline_result = orchestrator.process_new_proposal(proposal_dict, existing)
    enriched        = pipeline_result["enriched_proposal"]
    steps           = pipeline_result["workflow_steps"]
    compliance      = pipeline_result["compliance"]

    # Build proposal ORM object
    proposal = Proposal(
        title              = data.title,
        description        = data.description,
        event_type         = data.event_type,
        budget             = data.budget,
        requirements       = data.requirements,
        venue              = data.venue,
        expected_date      = data.expected_date,
        expected_attendees = data.expected_attendees,
        submitted_by       = current_user.id,
        status             = ProposalStatus.SUBMITTED,
        ai_intent          = enriched.get("ai_intent"),
        ai_risk_level      = enriched.get("ai_risk_level"),
        ai_budget_cat      = enriched.get("ai_budget_cat"),
        ai_routing_path    = [s["approver_role"] for s in steps],
    )
    db.add(proposal)
    await db.flush()  # get proposal.id

    # Create workflow steps
    for step_data in steps:
        step = WorkflowStep(
            proposal_id   = proposal.id,
            step_order    = step_data["step_order"],
            approver_role = step_data["approver_role"],
            approver_name = step_data.get("approver_name", ""),
            approver_email= step_data.get("approver_email", ""),
        )
        db.add(step)

    await db.flush()

    # Audit log
    await AuditService.log(
        db,
        action      = "proposal_submitted",
        entity_type = "proposal",
        entity_id   = proposal.id,
        proposal_id = proposal.id,
        user_id     = current_user.id,
        details     = {
            "compliance_passed": compliance["passed"],
            "compliance_issues": compliance["issues"],
            "ai_trace":          pipeline_result["agent_trace"],
            "routing":           [s["approver_role"] for s in steps],
        },
    )

    await db.commit()
    await db.refresh(proposal)

    # Send email to first approver
    if steps:
        first_step = steps[0]
        EmailService.send_approval_request(
            approver_email = first_step.get("approver_email", ""),
            approver_name  = first_step.get("approver_name", "Approver"),
            proposal_title = proposal.title,
            proposal_id    = proposal.id,
        )

    return proposal


@router.get("/{proposal_id}", response_model=ProposalOut)
async def get_proposal(
    proposal_id:  int,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    return proposal


@router.get("/{proposal_id}/workflow", response_model=List[dict])
async def get_workflow(
    proposal_id:  int,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.proposal_id == proposal_id)
        .order_by(WorkflowStep.step_order)
    )
    steps = result.scalars().all()
    return [
        {
            "id":            s.id,
            "step_order":    s.step_order,
            "approver_role": s.approver_role,
            "approver_name": s.approver_name,
            "status":        s.status.value,
            "comments":      s.comments,
            "decided_at":    s.decided_at.isoformat() if s.decided_at else None,
        }
        for s in steps
    ]


@router.get("/{proposal_id}/audit", response_model=List[dict])
async def get_audit(
    proposal_id:  int,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    logs = await AuditService.get_for_proposal(db, proposal_id)
    return [
        {
            "id":          l.id,
            "action":      l.action,
            "user_id":     l.user_id,
            "details":     l.details,
            "timestamp":   l.timestamp.isoformat(),
        }
        for l in logs
    ]


@router.delete("/{proposal_id}", status_code=204)
async def delete_proposal(
    proposal_id:  int,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result   = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.status not in (ProposalStatus.DRAFT, ProposalStatus.SUBMITTED):
        raise HTTPException(status_code=400, detail="Only draft/submitted proposals can be deleted.")
    await db.delete(proposal)
    await db.commit()
