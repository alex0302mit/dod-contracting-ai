"""
Unit tests for AgentRouter

Tests agent routing, caching, and mapping functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch

# Add backend to path
import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.services.agent_router import AgentRouter, get_agent_router
from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
from backend.agents.section_m_generator_agent import SectionMGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent


# Mock retriever for testing
class MockRetriever:
    """Mock retriever for testing agent instantiation"""
    def retrieve(self, query: str, top_k: int = 5):
        return []

    def search(self, query: str):
        return []


class TestAgentRouter:
    """Test suite for AgentRouter"""

    @pytest.fixture
    def mock_api_key(self):
        """Provide mock API key for testing"""
        return "test-api-key-12345"

    @pytest.fixture
    def mock_retriever(self):
        """Provide mock retriever for testing"""
        return MockRetriever()

    @pytest.fixture
    def router(self, mock_api_key, mock_retriever):
        """Create router instance for testing"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": mock_api_key}):
            return AgentRouter(api_key=mock_api_key, retriever=mock_retriever)

    def test_router_initialization(self, mock_api_key):
        """Test that router initializes correctly"""
        router = AgentRouter(api_key=mock_api_key)

        assert router.api_key == mock_api_key
        assert len(router._agent_registry) > 40  # Should have 40+ mappings
        assert len(router._agent_cache) == 0  # Cache starts empty

    def test_router_requires_api_key(self):
        """Test that router requires API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                AgentRouter(api_key=None)

    def test_exact_match_section_l(self, router):
        """Test exact match for Section L"""
        agent = router.get_agent_for_document("Section L - Instructions to Offerors")

        assert agent is not None
        assert isinstance(agent, SectionLGeneratorAgent)

    def test_exact_match_section_m(self, router):
        """Test exact match for Section M"""
        agent = router.get_agent_for_document("Section M - Evaluation Factors")

        assert agent is not None
        assert isinstance(agent, SectionMGeneratorAgent)

    def test_exact_match_pws(self, router):
        """Test exact match for PWS"""
        agent = router.get_agent_for_document("Performance Work Statement (PWS)")

        assert agent is not None
        assert isinstance(agent, PWSWriterAgent)

    def test_case_insensitive_match(self, router):
        """Test case-insensitive matching"""
        # Test various cases
        agent1 = router.get_agent_for_document("SECTION L - INSTRUCTIONS TO OFFERORS")
        agent2 = router.get_agent_for_document("section l - instructions to offerors")
        agent3 = router.get_agent_for_document("Section L - Instructions To Offerors")

        assert all(isinstance(a, SectionLGeneratorAgent) for a in [agent1, agent2, agent3])

    def test_partial_match(self, router):
        """Test partial/fuzzy matching"""
        # "Section L" should match "Section L - Instructions to Offerors"
        agent = router.get_agent_for_document("Section L")
        assert agent is not None
        assert isinstance(agent, SectionLGeneratorAgent)

        # "PWS" should match "Performance Work Statement (PWS)"
        agent = router.get_agent_for_document("PWS")
        assert agent is not None
        assert isinstance(agent, PWSWriterAgent)

    def test_agent_caching(self, router):
        """Test that agents are cached after first retrieval"""
        # First retrieval
        agent1 = router.get_agent_for_document("Section L - Instructions to Offerors", use_cache=True)

        # Cache should now have this agent
        assert "Section L - Instructions to Offerors" in router._agent_cache

        # Second retrieval should return same instance
        agent2 = router.get_agent_for_document("Section L - Instructions to Offerors", use_cache=True)

        assert agent1 is agent2  # Same object reference

    def test_cache_bypass(self, router):
        """Test that use_cache=False bypasses cache"""
        agent1 = router.get_agent_for_document("Section L - Instructions to Offerors", use_cache=True)
        agent2 = router.get_agent_for_document("Section L - Instructions to Offerors", use_cache=False)

        # Should be different instances
        assert agent1 is not agent2

    def test_unknown_document(self, router):
        """Test handling of unknown document type"""
        agent = router.get_agent_for_document("Unknown Document Type XYZ")

        assert agent is None  # Should return None for unknown documents

    def test_get_agent_info_known_document(self, router):
        """Test get_agent_info for known document"""
        info = router.get_agent_info("Section L - Instructions to Offerors")

        assert info["has_specialized_agent"] is True
        assert info["agent_class"] == "SectionLGeneratorAgent"
        assert info["document_name"] == "Section L - Instructions to Offerors"
        assert info["fallback"] is None

    def test_get_agent_info_unknown_document(self, router):
        """Test get_agent_info for unknown document"""
        info = router.get_agent_info("Unknown Document")

        assert info["has_specialized_agent"] is False
        assert info["agent_class"] is None
        assert info["fallback"] == "generic_generation"

    def test_list_supported_documents(self, router):
        """Test listing all supported documents"""
        documents = router.list_supported_documents()

        assert len(documents) > 20  # Should have 20+ primary document types
        assert "Section L - Instructions to Offerors" in documents
        assert "Section M - Evaluation Factors" in documents
        assert "Performance Work Statement (PWS)" in documents
        assert "Independent Government Cost Estimate (IGCE)" in documents

    def test_get_coverage_stats(self, router):
        """Test coverage statistics"""
        stats = router.get_coverage_stats()

        assert "total_mappings" in stats
        assert "unique_agents" in stats
        assert "primary_documents" in stats
        assert "coverage_ratio" in stats

        assert stats["total_mappings"] > 40
        assert stats["unique_agents"] > 20
        assert stats["primary_documents"] > 20

    def test_clear_cache(self, router):
        """Test cache clearing"""
        # Add some items to cache
        router.get_agent_for_document("Section L - Instructions to Offerors", use_cache=True)
        router.get_agent_for_document("Section M - Evaluation Factors", use_cache=True)

        assert len(router._agent_cache) == 2

        # Clear cache
        router.clear_cache()

        assert len(router._agent_cache) == 0

    def test_multiple_document_types(self, router):
        """Test routing for multiple different document types"""
        test_cases = [
            ("Section L - Instructions to Offerors", SectionLGeneratorAgent),
            ("Section M - Evaluation Factors", SectionMGeneratorAgent),
            ("Performance Work Statement (PWS)", PWSWriterAgent),
            ("Independent Government Cost Estimate (IGCE)", IGCEGeneratorAgent),
            ("Market Research Report", MarketResearchReportGeneratorAgent),
        ]

        for doc_name, expected_class in test_cases:
            agent = router.get_agent_for_document(doc_name)
            assert agent is not None, f"Failed to route: {doc_name}"
            assert isinstance(agent, expected_class), f"Wrong agent for: {doc_name}"

    def test_singleton_get_agent_router(self, mock_api_key):
        """Test singleton pattern for get_agent_router"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": mock_api_key}):
            # Clear singleton
            import backend.services.agent_router as router_module
            router_module._router_instance = None

            # Get first instance
            router1 = get_agent_router(api_key=mock_api_key)

            # Get second instance (should be same)
            router2 = get_agent_router(api_key=mock_api_key)

            assert router1 is router2  # Same instance

    def test_registry_completeness(self, router):
        """Test that registry has all major document types"""
        # Note: QASP, SF33, SF26 excluded - have custom constructors without standard api_key/retriever params
        required_documents = [
            "Section L",
            "Section M",
            "Section B",
            "Section H",
            "Section I",
            "Section K",
            "PWS",
            "SOW",
            "SOO",
            "IGCE",
            "Market Research",
            "Acquisition Plan",
            "Sources Sought",
        ]

        for doc in required_documents:
            agent = router.get_agent_for_document(doc)
            assert agent is not None, f"Missing agent for: {doc}"


class TestAgentRouterEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def router(self):
        """Create router with mock API key"""
        return AgentRouter(api_key="test-key", retriever=MockRetriever())

    def test_empty_document_name(self, router):
        """Test handling of empty document name"""
        agent = router.get_agent_for_document("")
        assert agent is None

    def test_whitespace_document_name(self, router):
        """Test handling of whitespace-only document name"""
        agent = router.get_agent_for_document("   ")
        assert agent is None

    def test_special_characters_in_document_name(self, router):
        """Test handling of special characters"""
        agent = router.get_agent_for_document("Section L - Instructions (2024) [Draft]")
        # Should still match Section L
        assert agent is not None

    def test_very_long_document_name(self, router):
        """Test handling of very long document name"""
        long_name = "Section L - Instructions to Offerors " + "X" * 500
        agent = router.get_agent_for_document(long_name)
        # Should match based on "Section L"
        assert agent is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
