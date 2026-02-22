"""
Approvals Router
──────────────────
GET  /approvals/pending          — steps pending for current user's role
POST /approvals/{step_id}/decide — approve / reject / request clarification
GET  /approvals/dashboard        — summary stats for approval dashboard
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.workflow import (
    WorkflowStep, Proposal, User, ApprovalStatus,
    ProposalStatus, ProcurementOrder
)
from agents.orchestrator import AgentOrchestrator
from services.audit_service import AuditService
from services.email_service import EmailService
from routers.auth import get_current_user

router       = APIRouter(prefix="/approvals", tags=["approvals"])
orchestrator = AgentOrchestrator()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class DecisionIn(BaseModel):
    decision: str        # "approved" | "rejected" | "clarification_requested"
    comments: Optional[str] = None


class PendingStepOut(BaseModel):
    id:             int
    proposal_id:    int
    step_order:     int
    approver_role:  str
    approver_name:  str
    status:         str
    proposal_title: str
    proposal_budget:float
    submitted_by:   str
    created_at:     str

    class Config:
        from_attributes = True


# ── Helper: advance to next step ─────────────────────────────────────────────

async def _try_advance_workflow(
    db:       AsyncSession,
    proposal: Proposal,
    step:     WorkflowStep,
    actor:    User,
) -> None:
    """
    After an approval, check if all steps are approved.
    If so, mark proposal as approved and trigger procurement.
    If not, notify the next approver.
    """
    # Load all steps for this proposal
    result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.proposal_id == proposal.id)
        .order_by(WorkflowStep.step_order)
    )
    all_steps = result.scalars().all()

    approved_ids = {s.id for s in all_steps if s.status == ApprovalStatus.APPROVED}

    if len(approved_ids) == len(all_steps):
        # All approved → move to procurement
        proposal.status = ProposalStatus.PROCUREMENT
        proposal.updated_at = datetime.utcnow()

        await AuditService.log(
            db,
            action      = "proposal_fully_approved",
            entity_type = "proposal",
            entity_id   = proposal.id,
            proposal_id = proposal.id,
            user_id     = actor.id,
            details     = {"message": "All approvers have approved. Moving to procurement."},
        )

        # Generate procurement order via ProcurementAgent
        proposal_dict = {
            "title":    proposal.title,
            "event_type": proposal.event_type.value if hasattr(proposal.event_type, "value") else str(proposal.event_type),
            "budget":   proposal.budget,
            "expected_attendees": proposal.expected_attendees,
            "requirements": proposal.requirements,
        }
        proc_data = orchestrator.process_approved_proposal(proposal_dict)

        p_order = ProcurementOrder(
            proposal_id   = proposal.id,
            items         = proc_data["items"],
            total_amount  = proc_data["total_amount"],
            erp_reference = proc_data["erp_reference"],
        )
        db.add(p_order)

        # Notify submitter
        u_result = await db.execute(select(User).where(User.id == proposal.submitted_by))
        submitter = u_result.scalar_one_or_none()
        if submitter:
            EmailService.send_status_update(
                submitter.email, submitter.name,
                proposal.title, "approved"
            )
    else:
        # Find next pending step
        pending = [
            s for s in all_steps
            if s.status == ApprovalStatus.PENDING and s.id != step.id
        ]
        if pending:
            proposal.status = ProposalStatus.IN_REVIEW
            proposal.updated_at = datetime.utcnow()
            next_step = min(pending, key=lambda s: s.step_order)
            EmailService.send_approval_request(
                next_step.approver_email or "",
                next_step.approver_name  or "Approver",
                proposal.title,
                proposal.id,
            )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/pending", response_model=List[dict])
async def pending_approvals(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    """Returns workflow steps pending for the current user's role."""
    role = current_user.role.value

    result = await db.execute(
        select(WorkflowStep, Proposal, User)
        .join(Proposal, WorkflowStep.proposal_id == Proposal.id)
        .join(User,     Proposal.submitted_by    == User.id)
        .where(WorkflowStep.approver_role == role)
        .where(WorkflowStep.status == ApprovalStatus.PENDING)
        .where(Proposal.status.in_([
            ProposalStatus.SUBMITTED, ProposalStatus.IN_REVIEW
        ]))
    )
    rows = result.all()

    return [
        {
            "id":              step.id,
            "proposal_id":     step.proposal_id,
            "step_order":      step.step_order,
            "approver_role":   step.approver_role,
            "approver_name":   step.approver_name,
            "status":          step.status.value,
            "proposal_title":  proposal.title,
            "proposal_budget": proposal.budget,
            "proposal_event_type": proposal.event_type.value if hasattr(proposal.event_type,"value") else str(proposal.event_type),
            "ai_risk_level":   proposal.ai_risk_level,
            "submitted_by":    submitter.name,
            "created_at":      step.created_at.isoformat(),
        }
        for step, proposal, submitter in rows
    ]


@router.post("/{step_id}/decide", response_model=dict)
async def decide(
    step_id:      int,
    data:         DecisionIn,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    # Load step
    s_result = await db.execute(select(WorkflowStep).where(WorkflowStep.id == step_id))
    step     = s_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="Workflow step not found.")

    # Verify role
    if step.approver_role != current_user.role.value:
        raise HTTPException(
            status_code=403,
            detail=f"Your role '{current_user.role.value}' is not authorized for this step (requires '{step.approver_role}')."
        )

    # Map decision
    decision_map = {
        "approved":                  ApprovalStatus.APPROVED,
        "rejected":                  ApprovalStatus.REJECTED,
        "clarification_requested":   ApprovalStatus.CLARIFY,
    }
    new_status = decision_map.get(data.decision)
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Invalid decision: {data.decision}")

    step.status     = new_status
    step.comments   = data.comments
    step.decided_at = datetime.utcnow()

    # Load proposal
    p_result = await db.execute(select(Proposal).where(Proposal.id == step.proposal_id))
    proposal = p_result.scalar_one_or_none()

    if data.decision == "rejected":
        proposal.status     = ProposalStatus.REJECTED
        proposal.updated_at = datetime.utcnow()
        # Notify submitter
        u_result  = await db.execute(select(User).where(User.id == proposal.submitted_by))
        submitter = u_result.scalar_one_or_none()
        if submitter:
            EmailService.send_status_update(
                submitter.email, submitter.name, proposal.title, "rejected"
            )
    elif data.decision == "clarification_requested":
        proposal.status     = ProposalStatus.REVISION
        proposal.updated_at = datetime.utcnow()
    elif data.decision == "approved":
        await _try_advance_workflow(db, proposal, step, current_user)

    # Audit
    await AuditService.log(
        db,
        action      = f"step_{data.decision}",
        entity_type = "workflow_step",
        entity_id   = step.id,
        proposal_id = step.proposal_id,
        user_id     = current_user.id,
        details     = {"comments": data.comments, "role": current_user.role.value},
    )

    await db.commit()
    return {"success": True, "step_id": step_id, "decision": data.decision}


@router.get("/dashboard", response_model=dict)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Summary stats for the approval dashboard."""
    async def _count(status_val):
        r = await db.execute(
            select(func.count()).select_from(Proposal).where(Proposal.status == status_val)
        )
        return r.scalar() or 0

    total     = (await db.execute(select(func.count()).select_from(Proposal))).scalar() or 0
    pending   = await _count(ProposalStatus.SUBMITTED)
    in_review = await _count(ProposalStatus.IN_REVIEW)
    approved  = await _count(ProposalStatus.APPROVED)
    rejected  = await _count(ProposalStatus.REJECTED)
    procure   = await _count(ProposalStatus.PROCUREMENT)

    return {
        "total":       total,
        "pending":     pending + in_review,
        "approved":    approved + procure,
        "rejected":    rejected,
        "in_review":   in_review,
        "procurement": procure,
    }
