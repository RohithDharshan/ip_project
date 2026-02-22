"""
Vendor Intelligence Agent
──────────────────────────
Scores and recommends vendors for a procurement order based on:
  • Rating         (30%)
  • Reliability    (25%)
  • Price index    (25% — lower is better)
  • Past orders    (20% — experience)

Returns a ranked list of vendors with composite scores.
"""

from typing import List, Dict, Any


# ─── Scoring weights ──────────────────────────────────────────────────────────
W_RATING      = 0.30
W_RELIABILITY = 0.25
W_PRICE       = 0.25   # inverted: lower price → higher score
W_EXPERIENCE  = 0.20


class VendorAgent:
    """
    Agent 5 — Vendor Intelligence

    Input : list of vendor dicts (from DB) + procurement order dict
    Output: same list with "ai_score" and "recommendation_rank" added,
            sorted best-first.
            Also returns "top_vendor_id" and "recommendation_reason".
    """

    def score_vendors(
        self,
        vendors: List[Dict[str, Any]],
        procurement: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Score and rank all vendors.
        """
        if not vendors:
            return {
                "ranked_vendors":        [],
                "top_vendor_id":         None,
                "recommendation_reason": "No vendors available.",
            }

        scored = []
        for v in vendors:
            score = self._compute_score(v)
            entry = dict(v)
            entry["ai_score"] = round(score, 4)
            scored.append(entry)

        # Sort best first
        scored.sort(key=lambda x: x["ai_score"], reverse=True)
        for rank, v in enumerate(scored, start=1):
            v["recommendation_rank"] = rank

        top = scored[0]
        reason = self._build_reason(top, scored)

        return {
            "ranked_vendors":        scored,
            "top_vendor_id":         top.get("id"),
            "recommendation_reason": reason,
        }

    # ── Scoring logic ─────────────────────────────────────────────────────────

    def _compute_score(self, vendor: Dict[str, Any]) -> float:
        rating      = float(vendor.get("rating", 3.0))       # 1-5
        reliability = float(vendor.get("reliability", 0.8))  # 0-1
        price_index = float(vendor.get("avg_price_index", 1.0))  # lower=better
        past_orders = int(vendor.get("past_orders", 0))

        # Normalize
        rating_n      = (rating - 1) / 4          # 0-1
        reliability_n = reliability                 # already 0-1
        price_n       = max(0.0, 1 - (price_index - 0.5))   # invert; clamp
        experience_n  = min(1.0, past_orders / 50)

        score = (
            W_RATING      * rating_n
          + W_RELIABILITY * reliability_n
          + W_PRICE       * price_n
          + W_EXPERIENCE  * experience_n
        )
        return score

    # ── Explanation ───────────────────────────────────────────────────────────

    def _build_reason(self, top: Dict, all_vendors: List[Dict]) -> str:
        strengths = []
        if top.get("rating", 0) >= 4.5:
            strengths.append(f"high rating ({top['rating']}/5)")
        if top.get("reliability", 0) >= 0.9:
            strengths.append(f"excellent reliability ({top['reliability']*100:.0f}%)")
        if top.get("avg_price_index", 1.0) < 0.9:
            strengths.append("competitive pricing")
        if top.get("past_orders", 0) >= 20:
            strengths.append(f"{top['past_orders']} successful orders")

        if not strengths:
            strengths.append("best overall composite score")

        return (
            f"Recommended vendor: {top.get('name', 'N/A')} — "
            + ", ".join(strengths)
            + f". AI score: {top.get('ai_score', 0):.2f}/1.00."
        )

    # ── Compare quotations ────────────────────────────────────────────────────

    def select_best_quotation(
        self, quotations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Given a list of quotation dicts (each with vendor info embedded),
        selects the best one using a combined price + vendor score.
        """
        if not quotations:
            return {}

        budget_amt = max(q.get("amount", 0) for q in quotations)

        scored = []
        for q in quotations:
            vendor_score = self._compute_score(q.get("vendor", {}))
            # Price score: lower price relative to max budget → better
            price_score = 1 - (q.get("amount", budget_amt) / (budget_amt or 1))
            combined = 0.5 * vendor_score + 0.5 * price_score
            entry = dict(q)
            entry["ai_score"] = round(combined, 4)
            scored.append(entry)

        scored.sort(key=lambda x: x["ai_score"], reverse=True)
        for rank, q in enumerate(scored, start=1):
            q["recommendation_rank"] = rank

        return scored[0] if scored else {}
