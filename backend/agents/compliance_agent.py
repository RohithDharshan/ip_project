"""
Compliance Agent
────────────────
Validates a proposal against institutional policies:
  • Budget limits by event type
  • Scheduling conflicts
  • Department quota (max events per semester)
  • Policy keyword flags

Returns:
  { "passed": bool, "issues": [...], "warnings": [...] }
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime


# ─── Policy table ─────────────────────────────────────────────────────────────

BUDGET_LIMITS: Dict[str, float] = {
    "workshop"      : 1_00_000,
    "seminar"       : 50_000,
    "conference"    : 5_00_000,
    "guest_lecture" : 30_000,
    "cultural_fest" : 10_00_000,
    "technical_fest": 8_00_000,
    "sports_event"  : 3_00_000,
    "other"         : 2_00_000,
}

MAX_EVENTS_PER_DEPT_PER_SEMESTER = 8

BANNED_KEYWORDS = [
    "political", "election", "alcohol", "gambling", "protest"
]

WARNING_KEYWORDS = [
    "external venue", "overnight stay", "foreign national", "media coverage"
]


class ComplianceAgent:
    """
    Agent 3 — Compliance & Policy Validation

    Input : proposal dict + list of existing approved proposals (for conflict check)
    Output: {"passed": bool, "issues": list[str], "warnings": list[str]}
    """

    def validate(
        self,
        proposal_data: Dict[str, Any],
        existing_proposals: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        existing_proposals = existing_proposals or []
        issues:   List[str] = []
        warnings: List[str] = []

        self._check_budget_limit(proposal_data, issues)
        self._check_banned_content(proposal_data, issues, warnings)
        self._check_date_conflict(proposal_data, existing_proposals, warnings)
        self._check_dept_quota(proposal_data, existing_proposals, issues)
        self._check_required_fields(proposal_data, issues)

        return {
            "passed":   len(issues) == 0,
            "issues":   issues,
            "warnings": warnings,
            "summary":  self._build_summary(issues, warnings),
        }

    # ── Checks ────────────────────────────────────────────────────────────────

    def _check_budget_limit(self, data: Dict, issues: List[str]) -> None:
        event_type = (data.get("event_type") or "other").lower().replace(" ", "_")
        budget     = float(data.get("budget") or 0)
        limit      = BUDGET_LIMITS.get(event_type, BUDGET_LIMITS["other"])
        if budget > limit:
            issues.append(
                f"Budget INR {budget:,.0f} exceeds the policy limit of "
                f"INR {limit:,.0f} for '{event_type}' events."
            )

    def _check_banned_content(
        self, data: Dict, issues: List[str], warnings: List[str]
    ) -> None:
        text = " ".join([
            str(data.get("title", "")),
            str(data.get("description", "")),
            str(data.get("requirements", "")),
        ]).lower()

        for kw in BANNED_KEYWORDS:
            if kw in text:
                issues.append(f"Proposal contains banned keyword: '{kw}'.")

        for kw in WARNING_KEYWORDS:
            if kw in text:
                warnings.append(f"Proposal mentions '{kw}' — additional scrutiny may apply.")

    def _check_date_conflict(
        self, data: Dict, existing: List[Dict], warnings: List[str]
    ) -> None:
        proposed_date = data.get("expected_date", "")
        if not proposed_date:
            return
        for existing_p in existing:
            if (
                existing_p.get("expected_date") == proposed_date
                and existing_p.get("submitted_by") == data.get("submitted_by")
            ):
                warnings.append(
                    f"Another event by the same faculty is already scheduled for {proposed_date}."
                )
                break

    def _check_dept_quota(
        self, data: Dict, existing: List[Dict], issues: List[str]
    ) -> None:
        dept = data.get("department", "")
        if not dept:
            return
        # Count approved proposals from same dept this academic year
        current_year = datetime.utcnow().year
        count = sum(
            1 for p in existing
            if p.get("department") == dept
            and str(current_year) in str(p.get("expected_date", ""))
            and p.get("status") in ("approved", "in_review", "submitted")
        )
        if count >= MAX_EVENTS_PER_DEPT_PER_SEMESTER:
            issues.append(
                f"Department '{dept}' has reached the maximum of "
                f"{MAX_EVENTS_PER_DEPT_PER_SEMESTER} events for this year."
            )

    def _check_required_fields(self, data: Dict, issues: List[str]) -> None:
        required = ["title", "description", "event_type", "budget"]
        for field in required:
            if not data.get(field):
                issues.append(f"Required field '{field}' is missing.")

    # ── Summary ───────────────────────────────────────────────────────────────

    def _build_summary(self, issues: List[str], warnings: List[str]) -> str:
        if not issues and not warnings:
            return "Proposal passed all compliance checks."
        parts = []
        if issues:
            parts.append(f"{len(issues)} issue(s) found: " + "; ".join(issues))
        if warnings:
            parts.append(f"{len(warnings)} warning(s): " + "; ".join(warnings))
        return " | ".join(parts)
