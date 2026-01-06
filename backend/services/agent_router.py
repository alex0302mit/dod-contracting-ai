"""
Agent Router Service

Routes document generation requests to specialized agents based on document type.
Provides intelligent mapping of 41+ specialized agents to document names.
"""

from typing import Optional, Dict, Type, List
import os
from pathlib import Path

# Import all specialized agents
from backend.agents.base_agent import BaseAgent
from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
from backend.agents.section_m_generator_agent import SectionMGeneratorAgent
from backend.agents.section_b_generator_agent import SectionBGeneratorAgent
from backend.agents.section_h_generator_agent import SectionHGeneratorAgent
from backend.agents.section_i_generator_agent import SectionIGeneratorAgent
from backend.agents.section_k_generator_agent import SectionKGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.agents.sow_writer_agent import SOWWriterAgent
from backend.agents.soo_writer_agent import SOOWriterAgent
from backend.agents.qasp_generator_agent import QASPGeneratorAgent
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent
from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
from backend.agents.rfi_generator_agent import RFIGeneratorAgent
from backend.agents.rfp_writer_agent import RFPWriterAgent
from backend.agents.sf33_generator_agent import SF33GeneratorAgent
from backend.agents.sf26_generator_agent import SF26GeneratorAgent
from backend.agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
from backend.agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
from backend.agents.ppq_generator_agent import PPQGeneratorAgent
from backend.agents.ssdd_generator_agent import SSDDGeneratorAgent
from backend.agents.amendment_generator_agent import AmendmentGeneratorAgent
from backend.agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
from backend.agents.debriefing_generator_agent import DebriefingGeneratorAgent

# Import orchestrators
from backend.agents.solicitation_package_orchestrator import SolicitationPackageOrchestrator


class AgentRouter:
    """
    Routes document generation requests to specialized agents

    Provides intelligent mapping between document names and specialized
    agents, with support for:
    - Exact name matching
    - Pattern matching (e.g., "Section L" variations)
    - Category-based routing
    - Phase-based fallbacks
    """

    def __init__(self, api_key: Optional[str] = None, retriever=None):
        """
        Initialize agent router

        Args:
            api_key: Anthropic API key (defaults to env var)
            retriever: RAG retriever instance (optional, will be created if not provided)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        # Store retriever (lazy load if not provided)
        self._retriever = retriever

        # Agent instance cache (reuse agents for performance)
        self._agent_cache: Dict[str, BaseAgent] = {}

        # Build agent registry
        self._agent_registry = self._build_agent_registry()

    def _build_agent_registry(self) -> Dict[str, Type[BaseAgent]]:
        """
        Build comprehensive agent registry mapping document names to agent classes

        Returns:
            Dictionary mapping document names/patterns to agent classes
        """
        return {
            # RFP/Solicitation Sections (A-M)
            "Section A": SF33GeneratorAgent,
            "SF33": SF33GeneratorAgent,
            "Standard Form 33": SF33GeneratorAgent,
            "SF33 - Solicitation, Offer and Award": SF33GeneratorAgent,

            "Section B": SectionBGeneratorAgent,
            "Section B - Supplies or Services and Prices": SectionBGeneratorAgent,
            "Section B - Supplies/Services and Prices": SectionBGeneratorAgent,
            "Supplies or Services": SectionBGeneratorAgent,
            "CLIN Structure": SectionBGeneratorAgent,

            "Section C": PWSWriterAgent,  # Default to PWS
            "Section C - Description/Specs/Work Statement": PWSWriterAgent,
            "Section C - Performance Work Statement": PWSWriterAgent,
            "Work Statement": PWSWriterAgent,

            "Section H": SectionHGeneratorAgent,
            "Section H - Special Contract Requirements": SectionHGeneratorAgent,
            "Special Contract Requirements": SectionHGeneratorAgent,

            "Section I": SectionIGeneratorAgent,
            "Section I - Contract Clauses": SectionIGeneratorAgent,
            "Contract Clauses": SectionIGeneratorAgent,

            "Section K": SectionKGeneratorAgent,
            "Section K - Representations and Certifications": SectionKGeneratorAgent,
            "Section K - Representations, Certifications, and Other Statements": SectionKGeneratorAgent,
            "Representations and Certifications": SectionKGeneratorAgent,

            "Section L": SectionLGeneratorAgent,
            "Section L - Instructions to Offerors": SectionLGeneratorAgent,
            "Section L - Instructions, Conditions, and Notices to Offerors": SectionLGeneratorAgent,
            "Instructions to Offerors": SectionLGeneratorAgent,

            "Section M": SectionMGeneratorAgent,
            "Section M - Evaluation Factors": SectionMGeneratorAgent,
            "Section M - Evaluation Factors for Award": SectionMGeneratorAgent,
            "Evaluation Factors": SectionMGeneratorAgent,

            # Work Statements (different types)
            "PWS": PWSWriterAgent,
            "Performance Work Statement": PWSWriterAgent,
            "Performance Work Statement (PWS)": PWSWriterAgent,

            "SOW": SOWWriterAgent,
            "Statement of Work": SOWWriterAgent,
            "Statement of Work (SOW)": SOWWriterAgent,

            "SOO": SOOWriterAgent,
            "Statement of Objectives": SOOWriterAgent,
            "Statement of Objectives (SOO)": SOOWriterAgent,

            # Supporting Documents
            "QASP": QASPGeneratorAgent,
            "Quality Assurance Surveillance Plan": QASPGeneratorAgent,
            "Quality Assurance Surveillance Plan (QASP)": QASPGeneratorAgent,

            "IGCE": IGCEGeneratorAgent,
            "Independent Government Cost Estimate": IGCEGeneratorAgent,
            "Independent Government Cost Estimate (IGCE)": IGCEGeneratorAgent,
            "Cost Estimate": IGCEGeneratorAgent,

            # Pre-Solicitation Documents
            "Market Research": MarketResearchReportGeneratorAgent,
            "Market Research Report": MarketResearchReportGeneratorAgent,

            "Acquisition Plan": AcquisitionPlanGeneratorAgent,
            "Acquisition Strategy": AcquisitionPlanGeneratorAgent,

            "Sources Sought": SourcesSoughtGeneratorAgent,
            "Sources Sought Notice": SourcesSoughtGeneratorAgent,

            "Presolicitation Notice": PreSolicitationNoticeGeneratorAgent,
            "Pre-Solicitation Notice": PreSolicitationNoticeGeneratorAgent,
            "Pre-solicitation Notice": PreSolicitationNoticeGeneratorAgent,

            "Industry Day": IndustryDayGeneratorAgent,
            "Industry Day Materials": IndustryDayGeneratorAgent,

            "RFI": RFIGeneratorAgent,
            "Request for Information": RFIGeneratorAgent,
            "Request for Information (RFI)": RFIGeneratorAgent,

            # Complete Documents
            "RFP": RFPWriterAgent,
            "Request for Proposal": RFPWriterAgent,
            "Request for Proposal (RFP)": RFPWriterAgent,

            # Evaluation Documents
            "Source Selection Plan": SourceSelectionPlanGeneratorAgent,
            "SSP": SourceSelectionPlanGeneratorAgent,

            "Evaluation Scorecard": EvaluationScorecardGeneratorAgent,
            "Scorecard": EvaluationScorecardGeneratorAgent,

            "PPQ": PPQGeneratorAgent,
            "Past Performance Questionnaire": PPQGeneratorAgent,
            "Past Performance Questionnaire (PPQ)": PPQGeneratorAgent,

            "SSDD": SSDDGeneratorAgent,
            "Source Selection Decision Document": SSDDGeneratorAgent,

            # Forms
            "SF26": SF26GeneratorAgent,
            "Standard Form 26": SF26GeneratorAgent,
            "SF26 - Award/Contract": SF26GeneratorAgent,

            # Post-Award Documents
            "Amendment": AmendmentGeneratorAgent,
            "Contract Amendment": AmendmentGeneratorAgent,

            "Award Notification": AwardNotificationGeneratorAgent,
            "Award Notice": AwardNotificationGeneratorAgent,

            "Debriefing": DebriefingGeneratorAgent,
            "Debriefing Letter": DebriefingGeneratorAgent,
        }

    def get_agent_for_document(
        self,
        document_name: str,
        use_cache: bool = True
    ) -> Optional[BaseAgent]:
        """
        Get specialized agent for a document

        Args:
            document_name: Name of document to generate
            use_cache: Whether to use cached agent instance

        Returns:
            Agent instance or None if no matching agent found
        """
        # Check cache first
        if use_cache and document_name in self._agent_cache:
            return self._agent_cache[document_name]

        # Try exact match
        agent_class = self._agent_registry.get(document_name)

        # Try case-insensitive match
        if not agent_class:
            document_name_lower = document_name.lower()
            for key, value in self._agent_registry.items():
                if key.lower() == document_name_lower:
                    agent_class = value
                    break

        # Try partial match (contains)
        if not agent_class:
            document_name_lower = document_name.lower()
            for key, value in self._agent_registry.items():
                if key.lower() in document_name_lower or document_name_lower in key.lower():
                    agent_class = value
                    break

        # If no agent found, return None (will fall back to generic generation)
        if not agent_class:
            return None

        # Instantiate agent
        try:
            # Get or create retriever (lazy loading)
            # The retriever requires a VectorStore for RAG-based document search
            if self._retriever is None:
                try:
                    from backend.rag.retriever import Retriever
                    from backend.rag.vector_store import VectorStore
                    
                    # Initialize VectorStore with default settings
                    # Uses sentence-transformers for embeddings (no API key needed)
                    vector_db_path = "backend/data/vector_db/faiss_index"
                    vector_store = VectorStore(
                        api_key=None,  # Not needed for local sentence-transformers
                        embedding_dimension=384,  # all-MiniLM-L6-v2 dimension
                        index_path=vector_db_path
                    )
                    
                    # Try to load existing index (may be empty if no docs uploaded)
                    vector_store.load()
                    
                    # Create retriever with the vector store
                    self._retriever = Retriever(vector_store=vector_store, top_k=5)
                    print("✓ RAG retriever initialized successfully")
                    
                except ImportError as import_error:
                    # Missing RAG dependencies (faiss, sentence-transformers, etc.)
                    print(f"Info: RAG dependencies not available: {import_error}")
                    print("  Document generation will proceed without RAG search.")
                    self._retriever = None
                except Exception as retriever_error:
                    # Other errors (file not found, etc.) - non-critical
                    print(f"Info: Could not initialize RAG retriever: {retriever_error}")
                    print("  Document generation will proceed without RAG search.")
                    self._retriever = None

            # Try to instantiate with retriever first
            if self._retriever is not None:
                try:
                    agent = agent_class(api_key=self.api_key, retriever=self._retriever)
                except TypeError:
                    # Agent doesn't accept retriever, try without it
                    try:
                        agent = agent_class(api_key=self.api_key)
                    except TypeError:
                        # Agent has different constructor signature, skip it
                        print(f"Agent '{agent_class.__name__}' has incompatible constructor")
                        return None
            else:
                # No retriever available, try without it
                try:
                    agent = agent_class(api_key=self.api_key)
                except TypeError:
                    # Agent requires retriever but we don't have one
                    print(f"Agent '{agent_class.__name__}' requires retriever but none available")
                    return None

            # Cache for future use
            if use_cache:
                self._agent_cache[document_name] = agent

            return agent

        except Exception as e:
            print(f"Error instantiating agent for '{document_name}': {e}")
            return None

    def get_agent_info(self, document_name: str) -> Dict:
        """
        Get information about the agent that would handle a document

        Args:
            document_name: Name of document

        Returns:
            Dictionary with agent information
        """
        agent = self.get_agent_for_document(document_name, use_cache=False)

        if not agent:
            return {
                "document_name": document_name,
                "has_specialized_agent": False,
                "agent_name": None,
                "agent_class": None,
                "fallback": "generic_generation"
            }

        return {
            "document_name": document_name,
            "has_specialized_agent": True,
            "agent_name": agent.name if hasattr(agent, 'name') else agent.__class__.__name__,
            "agent_class": agent.__class__.__name__,
            "fallback": None
        }

    def list_supported_documents(self) -> List[str]:
        """
        List all document types with specialized agents

        Returns:
            List of supported document names
        """
        # Return unique document names (primary names only)
        primary_names = [
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors",
            "Section B - Supplies/Services and Prices",
            "Section H - Special Contract Requirements",
            "Section I - Contract Clauses",
            "Section K - Representations and Certifications",
            "Performance Work Statement (PWS)",
            "Statement of Work (SOW)",
            "Statement of Objectives (SOO)",
            "Quality Assurance Surveillance Plan (QASP)",
            "Independent Government Cost Estimate (IGCE)",
            "Market Research Report",
            "Acquisition Plan",
            "Sources Sought Notice",
            "Pre-Solicitation Notice",
            "Industry Day Materials",
            "Request for Information (RFI)",
            "Request for Proposal (RFP)",
            "SF33 - Solicitation, Offer and Award",
            "SF26 - Award/Contract",
            "Source Selection Plan",
            "Evaluation Scorecard",
            "Past Performance Questionnaire (PPQ)",
            "Source Selection Decision Document (SSDD)",
            "Amendment",
            "Award Notification",
            "Debriefing"
        ]

        return sorted(primary_names)

    def get_coverage_stats(self) -> Dict:
        """
        Get statistics about agent coverage

        Returns:
            Dictionary with coverage statistics
        """
        total_mappings = len(self._agent_registry)
        unique_agents = len(set(self._agent_registry.values()))
        primary_documents = len(self.list_supported_documents())

        return {
            "total_mappings": total_mappings,
            "unique_agents": unique_agents,
            "primary_documents": primary_documents,
            "coverage_ratio": unique_agents / primary_documents if primary_documents > 0 else 0
        }

    def clear_cache(self):
        """Clear the agent instance cache"""
        self._agent_cache.clear()


# Singleton instance for global use
_router_instance: Optional[AgentRouter] = None


def get_agent_router(api_key: Optional[str] = None, retriever=None) -> AgentRouter:
    """
    Get singleton instance of agent router

    Args:
        api_key: Anthropic API key (optional, uses env var if not provided)
        retriever: RAG retriever instance (optional)

    Returns:
        AgentRouter instance
    """
    global _router_instance

    if _router_instance is None:
        _router_instance = AgentRouter(api_key=api_key, retriever=retriever)

    return _router_instance
