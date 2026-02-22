"""
Vendors Router
───────────────
GET  /vendors               — list all vendors (with category filter)
POST /vendors               — add vendor (admin only)
GET  /vendors/{id}          — get single vendor
GET  /vendors/recommend     — AI vendor recommendation for a category
POST /vendors/quotations    — submit quotation for a procurement order
GET  /procurement/{id}      — get procurement order details
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.workflow import Vendor, VendorCategory, VendorQuotation, ProcurementOrder
from agents.orchestrator import AgentOrchestrator
from services.audit_service import AuditService
from routers.auth import get_current_user
from models.workflow import User

router       = APIRouter(prefix="/vendors", tags=["vendors"])
orchestrator = AgentOrchestrator()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class VendorIn(BaseModel):
    name:             str
    category:         str
    contact_email:    Optional[str] = None
    contact_phone:    Optional[str] = None
    address:          Optional[str] = None
    rating:           float = 3.0
    reliability:      float = 0.8
    avg_price_index:  float = 1.0


class VendorOut(BaseModel):
    id:               int
    name:             str
    category:         str
    contact_email:    Optional[str]
    contact_phone:    Optional[str]
    rating:           float
    reliability:      float
    avg_price_index:  float
    past_orders:      int
    is_active:        bool

    class Config:
        from_attributes = True


class QuotationIn(BaseModel):
    procurement_id: int
    vendor_id:      int
    amount:         float
    notes:          Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[VendorOut])
async def list_vendors(
    category:     Optional[str] = Query(None),
    db:           AsyncSession  = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    q = select(Vendor).where(Vendor.is_active == True)
    if category:
        q = q.where(Vendor.category == category)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=VendorOut, status_code=201)
async def create_vendor(
    data:         VendorIn,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    if current_user.role.value not in ("admin", "bursar"):
        raise HTTPException(status_code=403, detail="Only admin/bursar can add vendors.")
    vendor = Vendor(**data.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


@router.get("/recommend", response_model=dict)
async def recommend_vendors(
    category:     Optional[str] = Query(None),
    db:           AsyncSession  = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    q = select(Vendor).where(Vendor.is_active == True)
    if category:
        q = q.where(Vendor.category == category)
    result   = await db.execute(q)
    vendors  = result.scalars().all()
    if not vendors:
        return {"ranked_vendors": [], "top_vendor_id": None, "recommendation_reason": "No vendors found."}

    vendor_dicts = [
        {
            "id":              v.id,
            "name":            v.name,
            "category":        v.category.value if hasattr(v.category, "value") else str(v.category),
            "rating":          v.rating,
            "reliability":     v.reliability,
            "avg_price_index": v.avg_price_index,
            "past_orders":     v.past_orders,
        }
        for v in vendors
    ]
    return orchestrator.recommend_vendors(vendor_dicts)


@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(
    vendor_id:    int,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor


@router.post("/quotations", response_model=dict, status_code=201)
async def submit_quotation(
    data:         QuotationIn,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    quotation = VendorQuotation(
        procurement_id = data.procurement_id,
        vendor_id      = data.vendor_id,
        amount         = data.amount,
        notes          = data.notes,
    )
    db.add(quotation)
    await db.commit()
    await db.refresh(quotation)

    # Score all quotations for this procurement order
    q_result = await db.execute(
        select(VendorQuotation, Vendor)
        .join(Vendor, VendorQuotation.vendor_id == Vendor.id)
        .where(VendorQuotation.procurement_id == data.procurement_id)
    )
    rows = q_result.all()
    quotation_dicts = [
        {
            "id":     qo.id,
            "amount": qo.amount,
            "notes":  qo.notes,
            "vendor": {
                "id":              v.id,
                "name":            v.name,
                "rating":          v.rating,
                "reliability":     v.reliability,
                "avg_price_index": v.avg_price_index,
                "past_orders":     v.past_orders,
            }
        }
        for qo, v in rows
    ]
    best = orchestrator.select_best_quotation(quotation_dicts)

    return {
        "quotation_id": quotation.id,
        "best_quotation_id": best.get("id"),
        "recommendation_reason": None,
    }


@router.get("/procurement/{procurement_id}", response_model=dict)
async def get_procurement(
    procurement_id: int,
    db:             AsyncSession = Depends(get_db),
    current_user:   User         = Depends(get_current_user),
):
    result = await db.execute(
        select(ProcurementOrder).where(ProcurementOrder.id == procurement_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Procurement order not found.")
    return {
        "id":            order.id,
        "proposal_id":   order.proposal_id,
        "items":         order.items,
        "total_amount":  order.total_amount,
        "erp_reference": order.erp_reference,
        "status":        order.status.value,
        "created_at":    order.created_at.isoformat(),
    }
