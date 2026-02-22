"""
Agent Orchestrator
───────────────────
Coordinates the entire agent pipeline in the correct sequence:

  1. ProposalAgent   — understand the proposal
  2. ComplianceAgent — validate against policies
  3. RoutingAgent    — compute approval chain
  4. (Human approvals happen via the API)
  5. ProcurementAgent — generate procurement order (post-approval)
  6. VendorAgent      — score / recommend vendors

The orchestrator is called by API routers and maintains
a full trace of every agent's output for audit purposes.
"""

import logging
from typing import Dict, Any, List, Optional

from agents.proposal_agent    import ProposalAgent
from agents.routing_agent     import RoutingAgent
from agents.compliance_agent  import ComplianceAgent
from agents.procurement_agent import ProcurementAgent
from agents.vendor_agent      import VendorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(self):
        self.proposal_agent    = ProposalAgent()
        self.routing_agent     = RoutingAgent()
        self.compliance_agent  = ComplianceAgent()
        self.procurement_agent = ProcurementAgent()
        self.vendor_agent      = VendorAgent()

    # ─────────────────────────────────────────────────────────────────────────
    # Stage 1: Process new proposal submission
    # ─────────────────────────────────────────────────────────────────────────

    def process_new_proposal(
        self,
        proposal_data: Dict[str, Any],
        existing_proposals: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run on proposal submission.
        Returns enriched proposal data + workflow steps + compliance result.
        """
        trace = {}

        # Step 1 — Understand proposal
        logger.info("[Orchestrator] Running ProposalAgent...")
        enriched = self.proposal_agent.process(proposal_data)
        trace["proposal_agent"] = {
            "intent":     enriched.get("ai_intent"),
            "budget_cat": enriched.get("ai_budget_cat"),
            "risk_level": enriched.get("ai_risk_level"),
            "summary":    enriched.get("ai_summary"),
        }

        # Step 2 — Compliance check
        logger.info("[Orchestrator] Running ComplianceAgent...")
        compliance = self.compliance_agent.validate(enriched, existing_proposals or [])
        trace["compliance_agent"] = compliance

        # Step 3 — Routing (even if non-compliant — for visibility)
        logger.info("[Orchestrator] Running RoutingAgent...")
        steps = self.routing_agent.compute_routing(enriched)
        routing_explanation = self.routing_agent.explain_routing(enriched, steps)
        trace["routing_agent"] = {
            "steps":       steps,
            "explanation": routing_explanation,
        }

        logger.info(f"[Orchestrator] Routing computed: {[s['approver_role'] for s in steps]}")

        return {
            "enriched_proposal":  enriched,
            "compliance":         compliance,
            "workflow_steps":     steps,
            "routing_explanation":routing_explanation,
            "agent_trace":        trace,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Stage 2: Generate procurement after full approval
    # ─────────────────────────────────────────────────────────────────────────

    def process_approved_proposal(
        self,
        proposal_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run after all approvers have approved.
        Returns procurement order details.
        """
        logger.info("[Orchestrator] Running ProcurementAgent...")
        procurement = self.procurement_agent.generate_procurement(proposal_data)
        return procurement

    # ─────────────────────────────────────────────────────────────────────────
    # Stage 3: Vendor recommendation for a procurement order
    # ─────────────────────────────────────────────────────────────────────────

    def recommend_vendors(
        self,
        vendors: List[Dict[str, Any]],
        procurement: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Score and rank vendors for a given procurement order.
        """
        logger.info(f"[Orchestrator] Running VendorAgent on {len(vendors)} vendors...")
        return self.vendor_agent.score_vendors(vendors, procurement)

    # ─────────────────────────────────────────────────────────────────────────
    # Utility: select best quotation
    # ─────────────────────────────────────────────────────────────────────────

    def select_best_quotation(self, quotations: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.vendor_agent.select_best_quotation(quotations)
