"""
Proposal Understanding Agent
─────────────────────────────
Parses a raw proposal and extracts:
  • intent / purpose
  • budget category  (small / medium / large)
  • risk level       (low / medium / high)
  • key entities     (venue, date, attendees, items needed)
  • formatted summary for downstream agents

Works in rule-based mode by default.
Set OPENAI_API_KEY to enable LLM-enhanced extraction.
"""

import re
import json
from typing import Dict, Any, Optional
from config import settings


# ─── Budget thresholds (INR) ─────────────────────────────────────────────────
BUDGET_SMALL  = 50_000
BUDGET_MEDIUM = 2_00_000


# ─── High-risk keywords ───────────────────────────────────────────────────────
HIGH_RISK_KEYWORDS  = ["international", "external sponsor", "off-campus", "overnight"]
MED_RISK_KEYWORDS   = ["large scale", "cultural fest", "technical fest", "conference", "500+"]

# ─── Item extraction patterns ─────────────────────────────────────────────────
ITEM_PATTERNS = [
    r"\d+\s*(chairs?|tables?|projectors?|microphones?|banners?|tents?|laptops?|cameras?)",
    r"(catering|food|snacks?|lunch|dinner|breakfast)\s+for\s+\d+",
    r"(printing|brochures?|certificates?|badges?)",
    r"(av\s+equipment|sound\s+system|lighting)",
    r"(transport|logistics|vehicles?)",
]


class ProposalAgent:
    """
    Agent 1 — Proposal Understanding

    Input : raw proposal dict (title, description, event_type, budget, requirements)
    Output: enriched dict with ai_* fields populated
    """

    def __init__(self):
        self.use_llm = bool(settings.OPENAI_API_KEY)

    # ── Public ────────────────────────────────────────────────────────────────

    def process(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point.
        Returns the proposal_data dict enriched with AI-extracted fields.
        """
        if self.use_llm:
            return self._llm_process(proposal_data)
        return self._rule_based_process(proposal_data)

    # ── Rule-based processing ─────────────────────────────────────────────────

    def _rule_based_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        title       = (data.get("title") or "").lower()
        description = (data.get("description") or "").lower()
        requirements= (data.get("requirements") or "").lower()
        full_text   = f"{title} {description} {requirements}"
        budget      = float(data.get("budget") or 0)
        event_type  = (data.get("event_type") or "").lower()

        # Intent extraction
        intent = self._extract_intent(title, event_type, description)

        # Budget category
        if budget <= BUDGET_SMALL:
            budget_cat = "small"
        elif budget <= BUDGET_MEDIUM:
            budget_cat = "medium"
        else:
            budget_cat = "large"

        # Risk level
        risk = "low"
        for kw in HIGH_RISK_KEYWORDS:
            if kw in full_text:
                risk = "high"
                break
        if risk != "high":
            for kw in MED_RISK_KEYWORDS:
                if kw in full_text:
                    risk = "medium"
                    break
        if budget_cat == "large" and risk == "low":
            risk = "medium"

        # Required items
        items_needed = self._extract_items(full_text)

        result = dict(data)
        result["ai_intent"]     = intent
        result["ai_budget_cat"] = budget_cat
        result["ai_risk_level"] = risk
        result["ai_items"]      = items_needed
        result["ai_summary"]    = (
            f"Event: {intent}. Budget category: {budget_cat} "
            f"(INR {budget:,.0f}). Risk: {risk}. "
            f"Items identified: {', '.join(items_needed) if items_needed else 'none'}."
        )
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_intent(self, title: str, event_type: str, description: str) -> str:
        intent_map = {
            "workshop"     : "Workshop / Training",
            "seminar"      : "Academic Seminar",
            "conference"   : "Conference",
            "guest_lecture": "Guest Lecture",
            "cultural_fest": "Cultural Festival",
            "technical_fest": "Technical Festival",
            "sports_event" : "Sports Event",
        }
        if event_type in intent_map:
            return intent_map[event_type]
        # fall back to title keywords
        for key, label in intent_map.items():
            if key.replace("_", " ") in title or key.replace("_", " ") in description[:100]:
                return label
        return "Institutional Event"

    def _extract_items(self, text: str) -> list:
        items = []
        for pattern in ITEM_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                item = m if isinstance(m, str) else " ".join(m).strip()
                if item and item not in items:
                    items.append(item.strip())
        return items[:10]

    # ── Full Risk Analysis ────────────────────────────────────────────────────

    def analyze_risks(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a detailed risk breakdown with individual risk factors,
        severity ratings, descriptions, and mitigation recommendations.
        """
        title        = (proposal_data.get("title") or "").lower()
        description  = (proposal_data.get("description") or "").lower()
        requirements = (proposal_data.get("requirements") or "").lower()
        full_text    = f"{title} {description} {requirements}"
        budget       = float(proposal_data.get("budget") or 0)
        event_type   = (proposal_data.get("event_type") or "").lower()
        attendees    = int(proposal_data.get("expected_attendees") or 0)
        risk_level   = proposal_data.get("ai_risk_level") or "low"
        budget_cat   = proposal_data.get("ai_budget_cat") or "small"

        factors = []

        # ── Budget risk ───────────────────────────────────────────────────────
        from agents.compliance_agent import BUDGET_LIMITS
        policy_limit = BUDGET_LIMITS.get(event_type, BUDGET_LIMITS.get("other", 200000))
        utilisation  = round((budget / policy_limit) * 100, 1) if policy_limit else 0

        if budget > policy_limit:
            factors.append({
                "factor":      "Budget Exceeds Policy Limit",
                "severity":    "critical",
                "icon":        "💸",
                "description": f"Requested budget ₹{budget:,.0f} exceeds the "
                               f"institutional cap of ₹{policy_limit:,.0f} for "
                               f"'{event_type.replace('_', ' ')}' events "
                               f"({utilisation:.0f}% of limit).",
                "mitigation":  "Reduce scope or split into multiple smaller proposals. "
                               "Alternatively, seek special dispensation from the Principal "
                               "with a detailed justification letter.",
            })
        elif budget_cat == "large":
            factors.append({
                "factor":      "Large Budget Event",
                "severity":    "high",
                "icon":        "💰",
                "description": f"Budget of ₹{budget:,.0f} falls in the 'large' category "
                               f"({utilisation:.0f}% of policy limit). Requires multi-level "
                               "financial scrutiny.",
                "mitigation":  "Obtain a minimum of 3 competitive vendor quotations. "
                               "Submit a detailed line-item budget breakdown with justification "
                               "for each expense. Ensure Finance Office pre-approval.",
            })
        elif budget_cat == "medium":
            factors.append({
                "factor":      "Moderate Budget",
                "severity":    "medium",
                "icon":        "💳",
                "description": f"Budget of ₹{budget:,.0f} is mid-range "
                               f"({utilisation:.0f}% of policy limit). Subject to HoD and "
                               "Programme Manager review.",
                "mitigation":  "Prepare itemised budget with at least 2 vendor quotes. "
                               "Maintain all receipts for post-event audit.",
            })

        # ── Attendee scale risk ───────────────────────────────────────────────
        if attendees > 500:
            factors.append({
                "factor":      "Very Large Event Scale",
                "severity":    "high",
                "icon":        "👥",
                "description": f"{attendees:,} expected attendees — requires enhanced "
                               "safety, logistics, and crowd management planning.",
                "mitigation":  "Prepare a formal crowd-management plan. Coordinate with "
                               "campus security for additional personnel. Ensure first-aid "
                               "stations and emergency exits are clearly marked. Obtain "
                               "venue capacity certificate.",
            })
        elif attendees > 200:
            factors.append({
                "factor":      "Large Attendance",
                "severity":    "medium",
                "icon":        "👥",
                "description": f"{attendees:,} attendees exceeds the standard 200-person "
                               "threshold, requiring additional safety and logistical consideration.",
                "mitigation":  "Confirm venue capacity. Arrange adequate seating, emergency "
                               "exits, and basic first-aid. Inform campus security in advance.",
            })

        # ── High-risk keywords ────────────────────────────────────────────────
        kw_checks = [
            ("international",       "International Involvement",
             "high", "🌐",
             "Presence of international participants or content requires coordination "
             "with the International Relations Office and may need Ministry of Education "
             "notification.",
             "Notify the International Relations Cell at least 4 weeks prior. "
             "Obtain visa/invitation letters promptly. Verify FCRA/visa compliance "
             "if foreign funding is involved."),
            ("external sponsor",    "External Sponsorship",
             "high", "🤝",
             "External sponsorship introduces financial, legal, and brand-alignment "
             "risks. Sponsor terms may conflict with institutional policies.",
             "Draft a formal sponsorship MoU reviewed by the Legal/Admin office. "
             "Ensure sponsor branding complies with institutional guidelines. "
             "Disclose all in-kind and monetary contributions."),
            ("off-campus",          "Off-Campus Venue",
             "high", "📍",
             "Off-campus events require additional travel, insurance, and liability "
             "coverage outside institutional premises.",
             "Book venue with written agreement. Arrange institutional transport and "
             "personal accident insurance for all participants. Obtain Principal approval "
             "and inform parents/guardians for student participants."),
            ("overnight",           "Overnight Stay",
             "high", "🌙",
             "Overnight stays significantly increase duty-of-care obligations, "
             "accommodation logistics, and insurance requirements.",
             "Obtain signed consent forms from students/parents. Arrange accommodation "
             "with verified facilities. Assign staff supervisors for each floor/block. "
             "Create a detailed roster shared with the admin office."),
            ("media coverage",      "Media / Press Involvement",
             "medium", "📸",
             "Media presence requires institutional communication approval to prevent "
             "unauthorised statements or reputational exposure.",
             "Route all media communications through the PRO/Communications Officer. "
             "Brief all speakers to avoid off-the-record statements. "
             "Prepare an approved press release in advance."),
            ("foreign national",    "Foreign National Participation",
             "high", "🛂",
             "Participation of foreign nationals triggers immigration compliance, "
             "FCRA, and Ministry reporting requirements.",
             "Collect passport/visa copies well in advance. File required government "
             "reports. Coordinate with the institution's compliance officer."),
        ]

        for keyword, factor_name, severity, icon, desc, mitigation in kw_checks:
            if keyword in full_text:
                factors.append({
                    "factor":      factor_name,
                    "severity":    severity,
                    "icon":        icon,
                    "description": desc,
                    "mitigation":  mitigation,
                })

        # ── Event-type specific risks ─────────────────────────────────────────
        event_risks = {
            "cultural_fest": (
                "Cultural Event Complexity",
                "medium", "🎭",
                "Cultural festivals involve multiple simultaneous sub-events, "
                "external performers, and public-facing activities, increasing "
                "coordination complexity and liability exposure.",
                "Create a master event schedule with sub-event coordinators assigned. "
                "Verify all external performers have contracts and relevant permits (IPRS, etc.). "
                "Set up a dedicated help desk and clear signage.",
            ),
            "technical_fest": (
                "Technical Event Infrastructure",
                "medium", "💻",
                "Technical fests require specialised equipment, networking infrastructure, "
                "and participation from multiple external institutions, raising "
                "data-security and IP-related considerations.",
                "Ensure all software used is licensed. Set up isolated network access "
                "for external participants. Define problem statements and IP ownership "
                "clauses in participation forms.",
            ),
            "conference": (
                "Academic Conference Requirements",
                "medium", "🎓",
                "Conferences demand publication handling, peer review, and coordination "
                "with external academics, increasing compliance and scheduling complexity.",
                "Set up a programme committee with clear deadlines. Use a DOI-registered "
                "proceedings publisher. Register with ISSN/ISBN if applicable.",
            ),
            "sports_event": (
                "Sports Event Safety",
                "medium", "⚽",
                "Sports events carry inherent physical injury risks and require "
                "medical coverage and certified facilities.",
                "Ensure a trained first-aider/paramedic is on standby. Verify "
                "sports equipment meets safety standards. Obtain signed participant "
                "indemnity forms.",
            ),
        }

        if event_type in event_risks:
            name, sev, icon, desc, mit = event_risks[event_type]
            # Only add if not already captured by keyword
            if not any(f["factor"] == name for f in factors):
                factors.append({
                    "factor": name, "severity": sev, "icon": icon,
                    "description": desc, "mitigation": mit,
                })

        # ── All clear ─────────────────────────────────────────────────────────
        if not factors:
            factors.append({
                "factor":      "Standard Institutional Event",
                "severity":    "low",
                "icon":        "✅",
                "description": "No elevated risk factors detected. This is a routine "
                               "internal event well within policy guidelines.",
                "mitigation":  "Proceed through the standard approval workflow. "
                               "Ensure all facilities are booked and in-house resources "
                               "are confirmed at least 2 weeks before the event date.",
            })

        # ── Overall mitigation summary ────────────────────────────────────────
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        top_factors    = sorted(factors, key=lambda f: severity_order.get(f["severity"], 0), reverse=True)

        if risk_level == "high" or any(f["severity"] == "critical" for f in factors):
            overall = (
                "This proposal carries HIGH risk and requires escalated review. "
                "Address all critical and high-severity items before submission or "
                "request a pre-submission meeting with the Principal's office. "
                "Ensure all mitigations are documented in the proposal package."
            )
        elif risk_level == "medium":
            overall = (
                "This proposal carries MODERATE risk. Standard multi-level approval "
                "is sufficient, but ensure all medium-severity mitigations are in place. "
                "Prepare supporting documents (quotations, venue confirmations, consent forms) "
                "before the HoD review stage."
            )
        else:
            overall = (
                "This proposal is LOW risk. The standard departmental approval workflow "
                "applies. Keep records of all approvals and expenditures for the annual "
                "audit. No special escalation is required."
            )

        return {
            "risk_level":          risk_level,
            "risk_factors":        top_factors,
            "overall_mitigation":  overall,
            "budget_analysis": {
                "amount":          budget,
                "category":        budget_cat,
                "policy_limit":    policy_limit,
                "utilisation_pct": utilisation,
            },
        }

    # ── LLM-enhanced processing (requires OPENAI_API_KEY) ────────────────────

    def _llm_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses OpenAI GPT to extract structured information from the proposal.
        Falls back to rule-based if API call fails.
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = f"""
You are an institutional workflow assistant. Analyze this event proposal and return a JSON object with fields:
- intent (string): brief description of the event purpose
- budget_cat (string): "small" (<50000), "medium" (50000-200000), or "large" (>200000)
- risk_level (string): "low", "medium", or "high" based on scale, external involvement, budget
- items_needed (list of strings): physical items or services required
- summary (string): 1-sentence summary

Proposal:
Title: {data.get('title')}
Event Type: {data.get('event_type')}
Description: {data.get('description')}
Budget (INR): {data.get('budget')}
Requirements: {data.get('requirements')}

Respond only with valid JSON.
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                response_format={"type":"json_object"}
            )
            parsed = json.loads(response.choices[0].message.content)
            result = dict(data)
            result["ai_intent"]     = parsed.get("intent", "Institutional Event")
            result["ai_budget_cat"] = parsed.get("budget_cat", "small")
            result["ai_risk_level"] = parsed.get("risk_level", "low")
            result["ai_items"]      = parsed.get("items_needed", [])
            result["ai_summary"]    = parsed.get("summary", "")
            return result
        except Exception:
            return self._rule_based_process(data)
