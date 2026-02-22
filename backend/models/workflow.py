import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from database import Base


# ─────────────────────────────────────────
#  Enumerations
# ─────────────────────────────────────────

class UserRole(str, enum.Enum):
    FACULTY       = "faculty"
    COORDINATOR   = "coordinator"
    HOD           = "hod"
    PROGRAMME_MGR = "programme_manager"
    PRINCIPAL     = "principal"
    BURSAR        = "bursar"
    ADMIN         = "admin"


class ProposalStatus(str, enum.Enum):
    DRAFT      = "draft"
    SUBMITTED  = "submitted"
    IN_REVIEW  = "in_review"
    APPROVED   = "approved"
    REJECTED   = "rejected"
    REVISION   = "revision_requested"
    PROCUREMENT= "procurement"
    COMPLETED  = "completed"


class EventType(str, enum.Enum):
    WORKSHOP     = "workshop"
    SEMINAR      = "seminar"
    CONFERENCE   = "conference"
    GUEST_LECTURE= "guest_lecture"
    CULTURAL     = "cultural_fest"
    TECHNICAL    = "technical_fest"
    SPORT        = "sports_event"
    OTHER        = "other"


class ApprovalStatus(str, enum.Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    REJECTED  = "rejected"
    CLARIFY   = "clarification_requested"
    SKIPPED   = "skipped"


class VendorCategory(str, enum.Enum):
    CATERING      = "catering"
    AV_EQUIPMENT  = "av_equipment"
    PRINTING      = "printing"
    LOGISTICS     = "logistics"
    IT_SERVICES   = "it_services"
    VENUE         = "venue"
    OTHER         = "other"


class ProcurementStatus(str, enum.Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    ORDERED   = "ordered"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ─────────────────────────────────────────
#  User
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.FACULTY, nullable=False)
    department    = Column(String(100))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    proposals     = relationship("Proposal", back_populates="submitted_by_user", foreign_keys="Proposal.submitted_by")
    audit_logs    = relationship("AuditLog", back_populates="user")


# ─────────────────────────────────────────
#  Proposal
# ─────────────────────────────────────────

class Proposal(Base):
    __tablename__ = "proposals"

    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(255), nullable=False)
    description   = Column(Text, nullable=False)
    event_type    = Column(SAEnum(EventType), nullable=False)
    budget        = Column(Float, nullable=False)
    requirements  = Column(Text)
    venue         = Column(String(255))
    expected_date = Column(String(50))
    expected_attendees = Column(Integer, default=50)

    submitted_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    status        = Column(SAEnum(ProposalStatus), default=ProposalStatus.DRAFT)

    # AI-extracted fields
    ai_intent       = Column(String(255))
    ai_risk_level   = Column(String(20), default="low")   # low / medium / high
    ai_budget_cat   = Column(String(20), default="small") # small / medium / large
    ai_routing_path = Column(JSON)                         # list of roles

    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submitted_by_user  = relationship("User", back_populates="proposals", foreign_keys=[submitted_by])
    workflow_steps     = relationship("WorkflowStep", back_populates="proposal", cascade="all, delete-orphan")
    procurement_orders = relationship("ProcurementOrder", back_populates="proposal", cascade="all, delete-orphan")
    audit_logs         = relationship("AuditLog", back_populates="proposal")


# ─────────────────────────────────────────
#  WorkflowStep  (approval chain)
# ─────────────────────────────────────────

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id            = Column(Integer, primary_key=True, index=True)
    proposal_id   = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    step_order    = Column(Integer, nullable=False)
    approver_role = Column(String(50), nullable=False)
    approver_name = Column(String(100))
    approver_email= Column(String(150))
    status        = Column(SAEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments      = Column(Text)
    decided_at    = Column(DateTime)
    created_at    = Column(DateTime, default=datetime.utcnow)

    proposal      = relationship("Proposal", back_populates="workflow_steps")


# ─────────────────────────────────────────
#  Vendor
# ─────────────────────────────────────────

class Vendor(Base):
    __tablename__ = "vendors"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(150), nullable=False)
    category      = Column(SAEnum(VendorCategory), nullable=False)
    contact_email = Column(String(150))
    contact_phone = Column(String(20))
    address       = Column(Text)
    rating        = Column(Float, default=3.0)          # 1-5
    reliability   = Column(Float, default=0.8)          # 0-1
    avg_price_index = Column(Float, default=1.0)        # relative price (1=average)
    is_active     = Column(Boolean, default=True)
    past_orders   = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)

    quotations        = relationship("VendorQuotation", back_populates="vendor")
    procurement_orders = relationship("ProcurementOrder", back_populates="vendor")


# ─────────────────────────────────────────
#  VendorQuotation
# ─────────────────────────────────────────

class VendorQuotation(Base):
    __tablename__ = "vendor_quotations"

    id              = Column(Integer, primary_key=True, index=True)
    procurement_id  = Column(Integer, ForeignKey("procurement_orders.id"))
    vendor_id       = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    amount          = Column(Float, nullable=False)
    notes           = Column(Text)
    ai_score        = Column(Float)   # composite AI score
    is_selected     = Column(Boolean, default=False)
    submitted_at    = Column(DateTime, default=datetime.utcnow)

    vendor              = relationship("Vendor", back_populates="quotations")
    procurement_order   = relationship("ProcurementOrder", back_populates="quotations")


# ─────────────────────────────────────────
#  ProcurementOrder
# ─────────────────────────────────────────

class ProcurementOrder(Base):
    __tablename__ = "procurement_orders"

    id            = Column(Integer, primary_key=True, index=True)
    proposal_id   = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    vendor_id     = Column(Integer, ForeignKey("vendors.id"))
    items         = Column(JSON)           # list of {name, qty, unit_price}
    total_amount  = Column(Float)
    status        = Column(SAEnum(ProcurementStatus), default=ProcurementStatus.PENDING)
    erp_reference = Column(String(100))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    proposal      = relationship("Proposal", back_populates="procurement_orders")
    vendor        = relationship("Vendor", back_populates="procurement_orders")
    quotations    = relationship("VendorQuotation", back_populates="procurement_order")


# ─────────────────────────────────────────
#  AuditLog
# ─────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id   = Column(Integer)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    user_id     = Column(Integer, ForeignKey("users.id"))
    details     = Column(JSON)
    timestamp   = Column(DateTime, default=datetime.utcnow)

    proposal    = relationship("Proposal", back_populates="audit_logs")
    user        = relationship("User", back_populates="audit_logs")


# ─────────────────────────────────────────
#  Notification
# ─────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title       = Column(String(255), nullable=False)
    message     = Column(Text)
    is_read     = Column(Boolean, default=False)
    link        = Column(String(255))
    created_at  = Column(DateTime, default=datetime.utcnow)
