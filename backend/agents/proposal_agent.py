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
