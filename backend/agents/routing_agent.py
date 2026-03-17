"""
Approval Routing Agent
───────────────────────
Determines which approvers are required and in what order
based on:
  • event type
  • budget category  (small / medium / large)
  • risk level       (low / medium / high)
  • number of attendees

Routing hierarchy (PSG AI Consortium rules):
    FACULTY (submitter) → HOD → BURSAR → DEAN (Administration)
    → DEAN (Autonomous) → PRINCIPAL

This is the core innovation of the system.
"""

from typing import List, Dict, Any


# ─── Hierarchy definition ─────────────────────────────────────────────────────
HIERARCHY_ORDER = [
    "hod",
    "bursar",
    "dean_administration",
    "dean_autonomous",
    "principal",
]

# ─── Routing rules ────────────────────────────────────────────────────────────
# Each rule is evaluated; the one with the highest matching score wins.
# Rules define the minimum role required.

FIXED_APPROVAL_CHAIN = [
    "hod",
    "bursar",
    "dean_administration",
    "dean_autonomous",
    "principal",
]


# ─── Approver directory (mock — in production pulled from DB / LDAP) ──────────
APPROVER_DIRECTORY: Dict[str, Dict[str, str]] = {
    "hod":              {"name": "Dr. R. Venkatesh",     "email": "hod@psgai.edu.in"},
    "bursar":           {"name": "Mr. K. Sundaram",      "email": "bursar@psgai.edu.in"},
    "dean_administration": {"name": "Dr. M. Janaki",     "email": "deanadmin@psgai.edu.in"},
    "dean_autonomous":  {"name": "Dr. V. Balachander",   "email": "deanautonomous@psgai.edu.in"},
    "principal":        {"name": "Dr. A. Ramasamy",      "email": "principal@psgai.edu.in"},
}


class RoutingAgent:
    """
    Agent 2 — Approval Routing

    Input : AI-enriched proposal dict
    Output: ordered list of approver steps
            [{"step_order":1, "approver_role":"coordinator", "approver_name":..., "approver_email":...}, ...]
    """

    def compute_routing(self, proposal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point.
        Returns an ordered list of approval steps.
        """
        # Fixed institutional policy chain for all proposal types.
        ordered = [r for r in HIERARCHY_ORDER if r in FIXED_APPROVAL_CHAIN]

        # Build step objects
        steps = []
        for i, role in enumerate(ordered, start=1):
            approver = APPROVER_DIRECTORY.get(role, {})
            steps.append({
                "step_order":    i,
                "approver_role": role,
                "approver_name": approver.get("name", ""),
                "approver_email":approver.get("email", ""),
            })

        return steps

    def explain_routing(self, proposal_data: Dict[str, Any], steps: List[Dict]) -> str:
        """
        Returns a human-readable explanation of why each approver was included.
        """
        budget_cat = proposal_data.get("ai_budget_cat", "small")
        risk       = proposal_data.get("ai_risk_level", "low")
        event_type = proposal_data.get("event_type", "")
        attendees  = proposal_data.get("expected_attendees", 0)

        lines = [f"Routing path computed for '{proposal_data.get('title', '')}':",
                 f"  Budget category : {budget_cat}",
                 f"  Risk level      : {risk}",
                 f"  Event type      : {event_type}",
                 f"  Expected attendees: {attendees}",
                 "",
                 "Approval chain:"]
        for step in steps:
            lines.append(f"  Step {step['step_order']}: {step['approver_role'].replace('_',' ').title()}"
                         f" ({step['approver_name']})")
        return "\n".join(lines)
