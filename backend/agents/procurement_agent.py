"""
Procurement Planning Agent
───────────────────────────
After a proposal is fully approved, converts the event requirements
into a structured procurement order with line items.

Also generates an ERP reference number and posts to the ERP stub.
"""

import random
import string
from typing import Dict, Any, List
from datetime import datetime


# ─── Default procurement templates per event type ────────────────────────────

PROCUREMENT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "workshop": [
        {"name": "Projector Rental", "qty": 1, "unit_price": 3000},
        {"name": "Sound System",     "qty": 1, "unit_price": 5000},
        {"name": "Refreshments",     "qty": 1, "unit_price": 8000},
        {"name": "Printed Materials","qty": 50, "unit_price": 50},
    ],
    "seminar": [
        {"name": "Projector Rental", "qty": 1, "unit_price": 3000},
        {"name": "Refreshments",     "qty": 1, "unit_price": 5000},
        {"name": "Printed Materials","qty": 30, "unit_price": 50},
    ],
    "conference": [
        {"name": "AV Equipment Package", "qty": 1, "unit_price": 30000},
        {"name": "Catering (Day 1)",      "qty": 1, "unit_price": 50000},
        {"name": "Catering (Day 2)",      "qty": 1, "unit_price": 50000},
        {"name": "Banners & Flex Boards", "qty": 5, "unit_price": 2000},
        {"name": "Conference Kits",       "qty": 100, "unit_price": 300},
        {"name": "Photography & Video",   "qty": 1, "unit_price": 20000},
    ],
    "guest_lecture": [
        {"name": "Projector Rental",  "qty": 1, "unit_price": 2000},
        {"name": "Refreshments",      "qty": 1, "unit_price": 3000},
        {"name": "Honorarium",        "qty": 1, "unit_price": 5000},
    ],
    "cultural_fest": [
        {"name": "Stage Setup",          "qty": 1, "unit_price": 1_00_000},
        {"name": "Sound & Lighting",     "qty": 1, "unit_price": 80_000},
        {"name": "Catering",             "qty": 1, "unit_price": 1_50_000},
        {"name": "Prizes & Trophies",    "qty": 1, "unit_price": 50_000},
        {"name": "Banners & Decoration", "qty": 1, "unit_price": 30_000},
        {"name": "Photography",          "qty": 1, "unit_price": 25_000},
    ],
    "technical_fest": [
        {"name": "Server/Networking Equipment", "qty": 1, "unit_price": 50_000},
        {"name": "AV Equipment",                "qty": 1, "unit_price": 40_000},
        {"name": "Catering",                    "qty": 1, "unit_price": 80_000},
        {"name": "Prizes & Trophies",           "qty": 1, "unit_price": 30_000},
        {"name": "Printed Materials",           "qty": 200, "unit_price": 100},
    ],
    "sports_event": [
        {"name": "Sports Equipment",  "qty": 1, "unit_price": 20_000},
        {"name": "Refreshments",      "qty": 1, "unit_price": 15_000},
        {"name": "Medals & Trophies", "qty": 1, "unit_price": 10_000},
        {"name": "First Aid Kit",     "qty": 2, "unit_price": 2_000},
    ],
    "other": [
        {"name": "General Supplies",  "qty": 1, "unit_price": 10_000},
        {"name": "Contingency",       "qty": 1, "unit_price": 5_000},
    ],
}


def _generate_erp_ref() -> str:
    """Generate a mock ERP purchase order reference."""
    year  = datetime.utcnow().year
    seq   = "".join(random.choices(string.digits, k=5))
    return f"PO/{year}/{seq}"


class ProcurementAgent:
    """
    Agent 4 — Procurement Planning

    Input : approved proposal dict
    Output: {
        "items":          list of {name, qty, unit_price, total},
        "total_amount":   float,
        "erp_reference":  str,
        "vendor_categories": list[str],   # categories to source vendors for
    }
    """

    def generate_procurement(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        event_type = (proposal_data.get("event_type") or "other").lower().replace(" ", "_")

        # Pick template; fall back to "other"
        template = PROCUREMENT_TEMPLATES.get(event_type, PROCUREMENT_TEMPLATES["other"])

        # Adjust quantities for attendees
        attendees = int(proposal_data.get("expected_attendees") or 50)
        scale     = max(1.0, attendees / 50)

        items = []
        total = 0.0
        categories = set()

        for t_item in template:
            qty        = max(1, round(t_item["qty"] * (scale if "qty" in ["Refreshments", "Catering"] else 1)))
            # only scale catering items
            if any(kw in t_item["name"].lower() for kw in ("catering", "refreshment", "kit", "material")):
                qty = max(1, round(t_item["qty"] * scale))
            else:
                qty = t_item["qty"]

            unit_price = t_item["unit_price"]
            line_total = qty * unit_price
            total     += line_total

            items.append({
                "name":       t_item["name"],
                "qty":        qty,
                "unit_price": unit_price,
                "total":      line_total,
            })

            # Derive vendor category
            cat = self._infer_category(t_item["name"])
            if cat:
                categories.add(cat)

        # Cap to proposal budget
        budget = float(proposal_data.get("budget") or 0)
        if budget > 0 and total > budget:
            # Scale down uniformly
            factor = budget / total
            for item in items:
                item["unit_price"] = round(item["unit_price"] * factor, 2)
                item["total"]      = round(item["qty"] * item["unit_price"], 2)
            total = round(sum(i["total"] for i in items), 2)

        return {
            "items":             items,
            "total_amount":      round(total, 2),
            "erp_reference":     _generate_erp_ref(),
            "vendor_categories": list(categories),
        }

    # ── Helper ────────────────────────────────────────────────────────────────

    def _infer_category(self, item_name: str) -> str:
        name = item_name.lower()
        if any(k in name for k in ("catering", "refreshment", "food", "lunch", "dinner", "breakfast")):
            return "catering"
        if any(k in name for k in ("projector", "av", "sound", "lighting", "microphone", "video", "photo")):
            return "av_equipment"
        if any(k in name for k in ("print", "banner", "brochure", "flex", "material", "kit")):
            return "printing"
        if any(k in name for k in ("transport", "vehicle", "logistics")):
            return "logistics"
        if any(k in name for k in ("server", "network", "laptop", "it", "computer")):
            return "it_services"
        return "other"
