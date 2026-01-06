"""
AI Agents for DoD Procurement Document Generation

This package contains specialized AI agents for generating various DoD procurement documents:
- Base agent framework
- Document-specific generator agents
- Orchestrators for multi-phase workflows
- Quality assurance and refinement agents
"""

# Main orchestrators
from backend.agents.orchestrator import Orchestrator
from backend.agents.pre_solicitation_orchestrator import PreSolicitationOrchestrator
from backend.agents.solicitation_package_orchestrator import SolicitationPackageOrchestrator
from backend.agents.post_solicitation_orchestrator import PostSolicitationOrchestrator
from backend.agents.pws_orchestrator import PWSOrchestrator
from backend.agents.soo_orchestrator import SOOOrchestrator
from backend.agents.sow_orchestrator import SOWOrchestrator
from backend.agents.rfp_orchestrator import RFPOrchestrator

# Quality and management agents
from backend.agents.quality_agent import QualityAgent
from backend.agents.qa_manager_agent import QAManagerAgent
from backend.agents.refinement_agent import RefinementAgent

# Base agent
from backend.agents.base_agent import BaseAgent

__all__ = [
    'Orchestrator',
    'PreSolicitationOrchestrator',
    'SolicitationPackageOrchestrator',
    'PostSolicitationOrchestrator',
    'PWSOrchestrator',
    'SOOOrchestrator',
    'SOWOrchestrator',
    'RFPOrchestrator',
    'QualityAgent',
    'QAManagerAgent',
    'RefinementAgent',
    'BaseAgent',
]
