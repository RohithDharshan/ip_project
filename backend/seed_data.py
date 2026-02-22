"""
Database Seed Script
─────────────────────
Populates the database with:
  • Default users (one for each role)
  • 20 synthetic vendors
  • 8 sample proposals (various states)

All passwords default to: Password@123
Runs automatically on first launch if tables are empty.
"""

import random
import logging
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.workflow import (
    User, Vendor, Proposal, WorkflowStep, AuditLog,
    UserRole, VendorCategory, ProposalStatus, EventType, ApprovalStatus
)

logger      = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PW  = pwd_context.hash("Password@123")


# ─── Default users ────────────────────────────────────────────────────────────

DEFAULT_USERS = [
    {"name": "Dr. Priya Nair",         "email": "faculty@psgai.edu.in",      "role": UserRole.FACULTY,       "department": "Computer Science"},
    {"name": "Dr. Anand Kumar",        "email": "faculty2@psgai.edu.in",     "role": UserRole.FACULTY,       "department": "AI & Data Science"},
    {"name": "Dr. S. Lakshmi",         "email": "coordinator@psgai.edu.in",  "role": UserRole.COORDINATOR,   "department": "Administration"},
    {"name": "Dr. R. Venkatesh",       "email": "hod@psgai.edu.in",          "role": UserRole.HOD,            "department": "Computer Science"},
    {"name": "Dr. P. Krishnamurthy",   "email": "pm@psgai.edu.in",           "role": UserRole.PROGRAMME_MGR, "department": "Academic Affairs"},
    {"name": "Dr. A. Ramasamy",        "email": "principal@psgai.edu.in",    "role": UserRole.PRINCIPAL,     "department": "Management"},
    {"name": "Mr. K. Sundaram",        "email": "bursar@psgai.edu.in",       "role": UserRole.BURSAR,        "department": "Finance"},
    {"name": "Ms. Geetha Subramanian", "email": "admin@psgai.edu.in",        "role": UserRole.ADMIN,         "department": "IT"},
]


# ─── Synthetic vendors ────────────────────────────────────────────────────────

VENDOR_DATA = [
    # name,                         category,            rating, reliability, price_idx, past_orders
    ("Sri Murugan Caterers",        VendorCategory.CATERING,      4.7, 0.95, 0.90, 42),
    ("Annapoorna Food Services",    VendorCategory.CATERING,      4.2, 0.88, 1.05, 28),
    ("Royal Feast Catering",        VendorCategory.CATERING,      3.8, 0.80, 0.95, 15),
    ("AV Masters Tech",             VendorCategory.AV_EQUIPMENT,  4.9, 0.97, 1.10, 55),
    ("Saravana AV Solutions",       VendorCategory.AV_EQUIPMENT,  4.5, 0.90, 0.92, 31),
    ("SoundPro Rentals",            VendorCategory.AV_EQUIPMENT,  3.9, 0.85, 0.85, 20),
    ("PrintWorld Coimbatore",       VendorCategory.PRINTING,      4.6, 0.93, 0.88, 38),
    ("Star Print Solutions",        VendorCategory.PRINTING,      4.1, 0.87, 1.00, 24),
    ("Quick Print Express",         VendorCategory.PRINTING,      3.5, 0.78, 0.80, 12),
    ("Swift Logistics",             VendorCategory.LOGISTICS,     4.4, 0.91, 1.02, 19),
    ("Coimbatore Movers",           VendorCategory.LOGISTICS,     3.7, 0.82, 0.93, 11),
    ("TechServe IT Solutions",      VendorCategory.IT_SERVICES,   4.8, 0.96, 1.15, 47),
    ("DataPath Networks",           VendorCategory.IT_SERVICES,   4.3, 0.89, 1.05, 22),
    ("CloudEdge Technologies",      VendorCategory.IT_SERVICES,   4.0, 0.86, 0.98, 17),
    ("Grand Jubilee Hall",          VendorCategory.VENUE,         4.6, 0.94, 1.20, 33),
    ("PSG Convention Centre",       VendorCategory.VENUE,         4.9, 0.98, 1.35, 61),
    ("City Banquet Halls",          VendorCategory.VENUE,         3.8, 0.80, 0.90, 9),
    ("Ganesh General Suppliers",    VendorCategory.OTHER,         4.0, 0.84, 0.95, 26),
    ("Lakshmi Enterprises",         VendorCategory.OTHER,         3.6, 0.79, 0.88, 14),
    ("Metro Supplies Coimbatore",   VendorCategory.OTHER,         4.2, 0.88, 1.00, 30),
]


# ─── Sample proposals ─────────────────────────────────────────────────────────

PROPOSALS_DATA = [
    {
        "title":         "AI in Healthcare — Guest Lecture",
        "description":   "A guest lecture by Dr. Suresh Babu from IIT Madras on applications of AI in diagnostic imaging.",
        "event_type":    EventType.GUEST_LECTURE,
        "budget":        25000,
        "requirements":  "Projector, microphone, tea for 60 attendees",
        "expected_date": "2026-03-15",
        "expected_attendees": 60,
        "status":        ProposalStatus.APPROVED,
        "ai_budget_cat": "small", "ai_risk_level": "low",
    },
    {
        "title":         "National Conference on Deep Learning",
        "description":   "A two-day national conference featuring paper presentations, keynotes and workshops on deep learning advances.",
        "event_type":    EventType.CONFERENCE,
        "budget":        350000,
        "requirements":  "AV equipment, catering for 200 attendees, conference kits, accommodation for 10 speakers",
        "expected_date": "2026-04-10",
        "expected_attendees": 200,
        "status":        ProposalStatus.IN_REVIEW,
        "ai_budget_cat": "medium", "ai_risk_level": "high",
    },
    {
        "title":         "Python for Data Science Workshop",
        "description":   "A hands-on 3-day workshop covering Python, Pandas, and Scikit-learn for second-year B.Tech students.",
        "event_type":    EventType.WORKSHOP,
        "budget":        45000,
        "requirements":  "30 laptops, projector, printed workbooks, refreshments",
        "expected_date": "2026-03-22",
        "expected_attendees": 30,
        "status":        ProposalStatus.SUBMITTED,
        "ai_budget_cat": "small", "ai_risk_level": "low",
    },
    {
        "title":         "Technovanza 2026 — Annual Technical Fest",
        "description":   "Annual 3-day technical festival with coding contests, robotics, hackathon, and project expo.",
        "event_type":    EventType.TECHNICAL,
        "budget":        750000,
        "requirements":  "Stage, AV, catering, prizes, media coverage, external judges",
        "expected_date": "2026-04-25",
        "expected_attendees": 500,
        "status":        ProposalStatus.SUBMITTED,
        "ai_budget_cat": "large", "ai_risk_level": "high",
    },
    {
        "title":         "Kultura — Cultural Evening",
        "description":   "Annual cultural program featuring music, dance, and drama performances by students.",
        "event_type":    EventType.CULTURAL,
        "budget":        120000,
        "requirements":  "Stage lighting, sound system, costumes, catering",
        "expected_date": "2026-03-30",
        "expected_attendees": 300,
        "status":        ProposalStatus.PROCUREMENT,
        "ai_budget_cat": "medium", "ai_risk_level": "medium",
    },
    {
        "title":         "Research Methodology Seminar",
        "description":   "Half-day seminar for PhD scholars on qualitative and quantitative research methods.",
        "event_type":    EventType.SEMINAR,
        "budget":        18000,
        "requirements":  "Projector, whiteboard, tea for 25 participants",
        "expected_date": "2026-03-10",
        "expected_attendees": 25,
        "status":        ProposalStatus.REJECTED,
        "ai_budget_cat": "small", "ai_risk_level": "low",
    },
    {
        "title":         "Inter-Department Sports Day",
        "description":   "Annual sports competition covering cricket, volleyball, badminton, and athletics.",
        "event_type":    EventType.SPORT,
        "budget":        85000,
        "requirements":  "Sports equipment, trophies, first aid, refreshments for 150 participants",
        "expected_date": "2026-04-05",
        "expected_attendees": 150,
        "status":        ProposalStatus.APPROVED,
        "ai_budget_cat": "medium", "ai_risk_level": "low",
    },
    {
        "title":         "Entrepreneurship Boot Camp",
        "description":   "Two-day boot camp with industry mentors for student startups — pitch competition and workshops.",
        "event_type":    EventType.WORKSHOP,
        "budget":        95000,
        "requirements":  "AV equipment, catering, printed materials, guest speaker honorarium",
        "expected_date": "2026-04-18",
        "expected_attendees": 80,
        "status":        ProposalStatus.IN_REVIEW,
        "ai_budget_cat": "medium", "ai_risk_level": "medium",
    },
]


# ─── Approver directory (mirrors routing_agent.py) ────────────────────────────

APPROVER_EMAILS = {
    "coordinator":       "coordinator@psgai.edu.in",
    "hod":               "hod@psgai.edu.in",
    "programme_manager": "pm@psgai.edu.in",
    "principal":         "principal@psgai.edu.in",
    "bursar":            "bursar@psgai.edu.in",
}
APPROVER_NAMES = {
    "coordinator":       "Dr. S. Lakshmi",
    "hod":               "Dr. R. Venkatesh",
    "programme_manager": "Dr. P. Krishnamurthy",
    "principal":         "Dr. A. Ramasamy",
    "bursar":            "Mr. K. Sundaram",
}

BUDGET_ROUTING = {
    "small":  ["coordinator"],
    "medium": ["coordinator", "hod", "programme_manager"],
    "large":  ["coordinator", "hod", "programme_manager", "principal", "bursar"],
}
HIERARCHY = ["coordinator", "hod", "programme_manager", "principal", "bursar"]


def _compute_steps(budget_cat, risk_level, event_type_str, attendees):
    required = set(BUDGET_ROUTING.get(budget_cat, ["coordinator"]))
    if risk_level == "high":
        required.update(["principal", "bursar"])
    elif risk_level == "medium":
        required.add("programme_manager")
    if event_type_str in ("conference", "cultural_fest", "technical_fest"):
        required.add("principal")
    if attendees > 200:
        required.add("principal")
    return [r for r in HIERARCHY if r in required]


# ─── Main seed function ───────────────────────────────────────────────────────

async def seed_all():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
        if count > 0:
            logger.info("[Seed] Database already seeded — skipping.")
            return

        logger.info("[Seed] Seeding database with default data...")

        # ── Users ──────────────────────────────────────────────────────────
        user_map       = {}   # role -> user (last wins for duplicates)
        user_email_map = {}   # email -> user (always unique)
        for u in DEFAULT_USERS:
            user = User(
                name            = u["name"],
                email           = u["email"],
                hashed_password = DEFAULT_PW,
                role            = u["role"],
                department      = u["department"],
            )
            db.add(user)
            await db.flush()
            user_map[u["role"].value]  = user
            user_email_map[u["email"]] = user

        # ── Vendors ────────────────────────────────────────────────────────
        for name, category, rating, reliability, price_idx, past_orders in VENDOR_DATA:
            vendor = Vendor(
                name            = name,
                category        = category,
                contact_email   = f"{name.lower().replace(' ','.')[:15]}@vendor.in",
                rating          = rating,
                reliability     = reliability,
                avg_price_index = price_idx,
                past_orders     = past_orders,
            )
            db.add(vendor)

        await db.flush()

        # ── Proposals + WorkflowSteps ───────────────────────────────────
        faculty_user  = user_email_map["faculty@psgai.edu.in"]
        faculty2_user = user_email_map["faculty2@psgai.edu.in"]

        for i, pdata in enumerate(PROPOSALS_DATA):
            submitter = faculty_user if i % 2 == 0 else faculty2_user
            event_str = pdata["event_type"].value

            proposal = Proposal(
                title              = pdata["title"],
                description        = pdata["description"],
                event_type         = pdata["event_type"],
                budget             = pdata["budget"],
                requirements       = pdata["requirements"],
                expected_date      = pdata["expected_date"],
                expected_attendees = pdata["expected_attendees"],
                submitted_by       = submitter.id,
                status             = pdata["status"],
                ai_intent          = "Institutional Event",
                ai_budget_cat      = pdata["ai_budget_cat"],
                ai_risk_level      = pdata["ai_risk_level"],
                ai_routing_path    = _compute_steps(
                    pdata["ai_budget_cat"], pdata["ai_risk_level"],
                    event_str, pdata["expected_attendees"]
                ),
                created_at  = datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                updated_at  = datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            )
            db.add(proposal)
            await db.flush()

            # Build workflow steps
            roles = _compute_steps(
                pdata["ai_budget_cat"], pdata["ai_risk_level"],
                event_str, pdata["expected_attendees"]
            )
            final_status = pdata["status"]

            for order, role in enumerate(roles, start=1):
                if final_status == ProposalStatus.APPROVED:
                    step_status = ApprovalStatus.APPROVED
                elif final_status == ProposalStatus.REJECTED and order == 1:
                    step_status = ApprovalStatus.REJECTED
                elif final_status == ProposalStatus.SUBMITTED and order == 1:
                    step_status = ApprovalStatus.PENDING
                elif final_status == ProposalStatus.IN_REVIEW and order <= 1:
                    step_status = ApprovalStatus.APPROVED if order == 1 else ApprovalStatus.PENDING
                elif final_status == ProposalStatus.PROCUREMENT:
                    step_status = ApprovalStatus.APPROVED
                else:
                    step_status = ApprovalStatus.PENDING

                step = WorkflowStep(
                    proposal_id    = proposal.id,
                    step_order     = order,
                    approver_role  = role,
                    approver_name  = APPROVER_NAMES.get(role, ""),
                    approver_email = APPROVER_EMAILS.get(role, ""),
                    status         = step_status,
                    decided_at     = datetime.utcnow() - timedelta(days=random.randint(0,3))
                                     if step_status != ApprovalStatus.PENDING else None,
                )
                db.add(step)

            # Audit log for submission
            db.add(AuditLog(
                action      = "proposal_submitted",
                entity_type = "proposal",
                entity_id   = proposal.id,
                proposal_id = proposal.id,
                user_id     = submitter.id,
                details     = {"ai_budget_cat": pdata["ai_budget_cat"], "ai_risk_level": pdata["ai_risk_level"]},
                timestamp   = proposal.created_at,
            ))

        await db.commit()
        logger.info("[Seed] ✓ Database seeded successfully.")
        logger.info("[Seed]   Default login: faculty@psgai.edu.in / Password@123")
        logger.info("[Seed]   Admin login:   admin@psgai.edu.in / Password@123")
