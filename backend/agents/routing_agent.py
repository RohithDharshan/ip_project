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
  FACULTY (submitter) → COORDINATOR → HOD → PROGRAMME_MANAGER
  → PRINCIPAL (if needed) → BURSAR (if budget > 50k)

This is the core innovation of the system.
"""

from typing import List, Dict, Any


# ─── Hierarchy definition ─────────────────────────────────────────────────────
HIERARCHY_ORDER = [
    "coordinator",
    "hod",
    "programme_manager",
    "principal",
    "bursar",
]

# ─── Routing rules ────────────────────────────────────────────────────────────
# Each rule is evaluated; the one with the highest matching score wins.
# Rules define the minimum role required.

BUDGET_ROUTING = {
    "small":  ["coordinator"],               # <= 50k
    "medium": ["coordinator", "hod", "programme_manager"],
    "large":  ["coordinator", "hod", "programme_manager", "principal", "bursar"],
}

EVENT_TYPE_EXTRAS = {
    "conference":    ["principal"],
    "cultural_fest": ["principal"],
    "technical_fest":["principal"],
    "sports_event":  ["programme_manager"],
}

RISK_EXTRAS = {
    "high":  ["principal", "bursar"],
    "medium": ["programme_manager"],
    "low":   [],
}

ATTENDEE_THRESHOLD = 200  # above this → add principal if not already present


# ─── Approver directory (mock — in production pulled from DB / LDAP) ──────────
APPROVER_DIRECTORY: Dict[str, Dict[str, str]] = {
    "coordinator":      {"name": "Dr. S. Lakshmi",      "email": "coordinator@psgai.edu.in"},
    "hod":              {"name": "Dr. R. Venkatesh",     "email": "hod@psgai.edu.in"},
    "programme_manager":{"name": "Dr. P. Krishnamurthy", "email": "pm@psgai.edu.in"},
    "principal":        {"name": "Dr. A. Ramasamy",      "email": "principal@psgai.edu.in"},
    "bursar":           {"name": "Mr. K. Sundaram",      "email": "bursar@psgai.edu.in"},
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
        budget_cat  = proposal_data.get("ai_budget_cat", "small")
        risk_level  = proposal_data.get("ai_risk_level", "low")
        event_type  = (proposal_data.get("event_type") or "").lower()
        attendees   = int(proposal_data.get("expected_attendees") or 0)

        # Start with base set from budget
        required_roles = set(BUDGET_ROUTING.get(budget_cat, ["coordinator"]))

        # Add event-type extras
        for role in EVENT_TYPE_EXTRAS.get(event_type, []):
            required_roles.add(role)

        # Add risk extras
        for role in RISK_EXTRAS.get(risk_level, []):
            required_roles.add(role)

        # Attendee rule
        if attendees > ATTENDEE_THRESHOLD:
            required_roles.add("principal")

        # Sort by hierarchy order
        ordered = [r for r in HIERARCHY_ORDER if r in required_roles]

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
