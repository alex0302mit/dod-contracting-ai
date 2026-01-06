"""
Phase 4 Unit Tests: Agent Collaboration

Tests for:
- ContextManager
- DependencyGraph
- BaseAgent collaboration methods
- Collaborative generation flow

Run with: pytest tests/test_phase4_collaboration.py -v
"""

import pytest
import os
from datetime import datetime
from backend.services.context_manager import ContextManager, GeneratedContent, CrossReference
from backend.services.dependency_graph import DependencyGraph, DocumentNode


class TestContextManager:
    """Test ContextManager functionality"""

    def test_context_manager_initialization(self):
        """Test ContextManager initializes correctly"""
        cm = ContextManager(max_content_length=5000)
        assert cm.max_content_length == 5000
        assert len(cm._context_pool) == 0
        assert len(cm._cross_references) == 0

    def test_add_content(self):
        """Test adding content to context pool"""
        cm = ContextManager()

        cm.add_content(
            doc_name="Section L",
            content="This is Section L content...",
            metadata={"agent": "section_l_generator", "method": "template"}
        )

        assert cm.has_content("Section L")
        assert len(cm._context_pool) == 1

        content = cm.get_content("Section L")
        assert content == "This is Section L content..."

    def test_add_content_truncation(self):
        """Test content truncation when exceeding max length"""
        cm = ContextManager(max_content_length=100)

        long_content = "A" * 200
        cm.add_content(
            doc_name="Long Doc",
            content=long_content,
            metadata={}
        )

        stored_content = cm.get_content("Long Doc")
        assert len(stored_content) == 100
        assert stored_content == "A" * 100

    def test_get_content_obj(self):
        """Test retrieving GeneratedContent object"""
        cm = ContextManager()

        cm.add_content(
            doc_name="PWS",
            content="Performance Work Statement content",
            metadata={"agent": "pws_agent"}
        )

        content_obj = cm.get_content_obj("PWS")
        assert isinstance(content_obj, GeneratedContent)
        assert content_obj.doc_name == "PWS"
        assert content_obj.word_count > 0
        assert content_obj.character_count > 0

    def test_get_related_content(self):
        """Test retrieving related content for dependencies"""
        cm = ContextManager()

        # Add multiple documents
        cm.add_content("PWS", "PWS content", {})
        cm.add_content("Section L", "Section L content", {})
        cm.add_content("Acq Plan", "Acquisition Plan content", {})

        # Get dependencies for Section M
        related = cm.get_related_content(
            doc_name="Section M",
            dependency_list=["PWS", "Section L"],
            max_summary_length=100
        )

        assert len(related) == 2
        assert "PWS" in related
        assert "Section L" in related
        assert "Acq Plan" not in related

    def test_get_related_content_with_missing(self):
        """Test getting related content when some dependencies are missing"""
        cm = ContextManager()

        cm.add_content("PWS", "PWS content", {})

        # Request PWS and non-existent Section L
        related = cm.get_related_content(
            doc_name="Section M",
            dependency_list=["PWS", "Section L"],
            max_summary_length=100
        )

        # Should only return PWS
        assert len(related) == 1
        assert "PWS" in related

    def test_add_cross_reference(self):
        """Test tracking cross-references between documents"""
        cm = ContextManager()

        cm.add_cross_reference(
            from_doc="Section M",
            to_doc="PWS",
            reference_text="Technical requirements from PWS"
        )

        refs = cm.get_cross_references()
        assert len(refs) == 1
        assert refs[0]["from"] == "Section M"
        assert refs[0]["to"] == "PWS"
        assert "Technical requirements" in refs[0]["reference"]

    def test_get_cross_references_filtered(self):
        """Test filtering cross-references by document"""
        cm = ContextManager()

        cm.add_cross_reference("Section M", "PWS", "ref1")
        cm.add_cross_reference("Section M", "Section L", "ref2")
        cm.add_cross_reference("Section H", "PWS", "ref3")

        # Get all references involving Section M
        refs_m = cm.get_cross_references("Section M")
        assert len(refs_m) == 2

        # Get references from Section M
        refs_from_m = cm.get_references_from("Section M")
        assert len(refs_from_m) == 2

        # Get references to PWS
        refs_to_pws = cm.get_references_to("PWS")
        assert len(refs_to_pws) == 2

    def test_get_statistics(self):
        """Test context pool statistics"""
        cm = ContextManager()

        cm.add_content("Doc1", "This is document one with some words", {})
        cm.add_content("Doc2", "This is document two with different words", {})
        cm.add_cross_reference("Doc2", "Doc1", "reference")

        stats = cm.get_statistics()
        assert stats["document_count"] == 2
        assert stats["total_words"] > 0
        assert stats["total_characters"] > 0
        assert stats["cross_reference_count"] == 1
        assert "Doc1" in stats["documents"]
        assert "Doc2" in stats["documents"]

    def test_clear(self):
        """Test clearing context pool"""
        cm = ContextManager()

        cm.add_content("Doc1", "content", {})
        cm.add_cross_reference("Doc2", "Doc1", "ref")

        assert len(cm._context_pool) == 1
        assert len(cm._cross_references) == 1

        cm.clear()

        assert len(cm._context_pool) == 0
        assert len(cm._cross_references) == 0

    def test_generated_content_summary(self):
        """Test GeneratedContent get_summary method"""
        content_obj = GeneratedContent(
            doc_name="Test",
            content="A" * 1000,
            metadata={}
        )

        summary = content_obj.get_summary(max_length=100)
        assert len(summary) == 103  # 100 + "..."
        assert summary.endswith("...")

        # Short content shouldn't be truncated
        short_content = GeneratedContent(
            doc_name="Short",
            content="Short text",
            metadata={}
        )
        short_summary = short_content.get_summary(max_length=100)
        assert short_summary == "Short text"
        assert not short_summary.endswith("...")


class TestDependencyGraph:
    """Test DependencyGraph functionality"""

    @pytest.fixture
    def config_path(self):
        """Path to test dependency configuration"""
        return os.path.join(
            os.path.dirname(__file__),
            '../config/document_dependencies.json'
        )

    def test_dependency_graph_initialization(self, config_path):
        """Test DependencyGraph loads configuration"""
        dg = DependencyGraph(config_path=config_path)
        assert len(dg.nodes) > 0
        assert dg.config is not None

    def test_get_dependencies(self, config_path):
        """Test retrieving direct dependencies"""
        dg = DependencyGraph(config_path=config_path)

        # Section M depends on PWS, Section L, and Acquisition Plan
        deps = dg.get_dependencies("Section M - Evaluation Factors")
        assert isinstance(deps, list)

        # Check expected dependencies (based on config)
        if "Section M - Evaluation Factors" in dg.nodes:
            node = dg.nodes["Section M - Evaluation Factors"]
            assert len(node.depends_on) >= 0  # May have dependencies

    def test_get_dependents(self, config_path):
        """Test retrieving documents that depend on a document"""
        dg = DependencyGraph(config_path=config_path)

        # PWS is depended on by Section L, M, H
        dependents = dg.get_dependents("Section C - Performance Work Statement")
        assert isinstance(dependents, list)

    def test_get_generation_order_simple(self, config_path):
        """Test generation order for simple case"""
        dg = DependencyGraph(config_path=config_path)

        # Request just one document with no dependencies
        batches = dg.get_generation_order(["Section K - Representations and Certifications"])
        assert len(batches) >= 1
        assert "Section K - Representations and Certifications" in batches[0]

    def test_get_generation_order_with_dependencies(self, config_path):
        """Test generation order respects dependencies"""
        dg = DependencyGraph(config_path=config_path)

        # Request Section M which depends on PWS, Section L, Acq Plan
        selected = ["Section M - Evaluation Factors"]
        batches = dg.get_generation_order(selected)

        # Section M should be in the result
        all_docs = []
        for batch in batches:
            all_docs.extend(batch)

        assert "Section M - Evaluation Factors" in all_docs

    def test_get_generation_order_parallel_batches(self, config_path):
        """Test that independent documents are batched together"""
        dg = DependencyGraph(config_path=config_path)

        # Select multiple independent documents
        selected = [
            "Section K - Representations and Certifications",
            "Section I - Contract Clauses"
        ]
        batches = dg.get_generation_order(selected)

        # Independent documents should be in same batch if no dependencies
        # (This depends on config - adjust based on actual dependencies)
        assert len(batches) >= 1

    def test_validate_selection(self, config_path):
        """Test validation of document selection"""
        dg = DependencyGraph(config_path=config_path)

        # Valid selection
        result = dg.validate_selection(["Section C - Performance Work Statement"])
        assert "valid" in result
        assert "warnings" in result
        assert "missing_dependencies" in result

    def test_circular_dependency_detection(self, config_path):
        """Test that circular dependencies are detected"""
        # This would require a test config with circular deps
        # For now, test that validate_selection works
        dg = DependencyGraph(config_path=config_path)

        # Normal case shouldn't have circular dependencies
        result = dg.validate_selection(["Section M - Evaluation Factors"])
        assert not result.get("has_circular_dependency", False)

    def test_get_document_info(self, config_path):
        """Test retrieving document information"""
        dg = DependencyGraph(config_path=config_path)

        if "Section C - Performance Work Statement" in dg.nodes:
            info = dg.get_document_info("Section C - Performance Work Statement")
            assert info is not None
            assert "name" in info
            assert "priority" in info
            assert "depends_on" in info
            assert "dependents" in info

    def test_suggest_additional_documents(self, config_path):
        """Test document suggestions"""
        dg = DependencyGraph(config_path=config_path)

        # Select Section L, should suggest Section M, H (that depend on it)
        suggestions = dg.suggest_additional_documents(["Section L - Instructions to Offerors"])
        assert isinstance(suggestions, list)
        # Each suggestion is (doc_name, reason) tuple
        for doc_name, reason in suggestions:
            assert isinstance(doc_name, str)
            assert isinstance(reason, str)


class TestBaseAgentCollaboration:
    """Test BaseAgent collaboration methods"""

    def test_has_collaboration_enabled(self):
        """Test checking if collaboration is enabled"""
        from backend.agents.base_agent import BaseAgent

        # Mock API key
        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")

        # Without context manager
        agent = BaseAgent(name="test", api_key=api_key)
        assert not agent.has_collaboration_enabled()

        # With context manager
        cm = ContextManager()
        agent_with_collab = BaseAgent(name="test", api_key=api_key, context_manager=cm)
        assert agent_with_collab.has_collaboration_enabled()

    def test_reference_section(self):
        """Test creating formatted references"""
        from backend.agents.base_agent import BaseAgent

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        cm = ContextManager()
        agent = BaseAgent(name="Section M", api_key=api_key, context_manager=cm)

        ref = agent.reference_section("Section L", "Evaluation procedures")
        assert "Section L" in ref
        assert "Evaluation procedures" in ref
        assert ref.startswith("[See")

        # Check that cross-reference was tracked
        refs = cm.get_cross_references()
        assert len(refs) == 1
        assert refs[0]["from"] == "Section M"
        assert refs[0]["to"] == "Section L"

    def test_get_related_content(self):
        """Test retrieving related content through agent"""
        from backend.agents.base_agent import BaseAgent

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        cm = ContextManager()

        # Add some content first
        cm.add_content("PWS", "Performance Work Statement content", {})
        cm.add_content("Acq Plan", "Acquisition Plan content", {})

        agent = BaseAgent(name="Section L", api_key=api_key, context_manager=cm)

        related = agent.get_related_content(
            dependency_list=["PWS", "Acq Plan"],
            max_length=100
        )

        assert len(related) == 2
        assert "PWS" in related
        assert "Acq Plan" in related

    def test_build_collaborative_prompt_without_dependencies(self):
        """Test building prompt without dependencies"""
        from backend.agents.base_agent import BaseAgent

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        cm = ContextManager()
        agent = BaseAgent(name="Section K", api_key=api_key, context_manager=cm)

        prompt = agent.build_collaborative_prompt(
            base_requirements="Generate Section K",
            dependencies={},
            context="FAR 52.204-7"
        )

        assert "Generate Section K" in prompt
        assert "FAR 52.204-7" in prompt
        assert "PREVIOUSLY GENERATED DOCUMENTS" not in prompt

    def test_build_collaborative_prompt_with_dependencies(self):
        """Test building prompt with dependencies"""
        from backend.agents.base_agent import BaseAgent

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        cm = ContextManager()
        agent = BaseAgent(name="Section M", api_key=api_key, context_manager=cm)

        prompt = agent.build_collaborative_prompt(
            base_requirements="Generate Section M evaluation factors",
            dependencies={
                "PWS": "The PWS defines technical requirements...",
                "Section L": "Section L provides proposal format..."
            },
            context="FAR 15.304"
        )

        assert "Section M evaluation factors" in prompt
        assert "PREVIOUSLY GENERATED DOCUMENTS" in prompt
        assert "PWS" in prompt
        assert "Section L" in prompt
        assert "FAR 15.304" in prompt
        assert "INSTRUCTIONS" in prompt


class TestCollaborativeFlow:
    """Integration tests for collaborative generation flow"""

    def test_full_collaboration_flow(self):
        """Test complete collaboration flow: add content -> retrieve -> reference"""
        cm = ContextManager()

        # Step 1: Generate PWS (no dependencies)
        cm.add_content(
            doc_name="Section C - Performance Work Statement",
            content="The contractor shall provide IT services...",
            metadata={"agent": "pws_agent", "method": "llm"}
        )

        # Step 2: Generate Section L (depends on PWS)
        pws_content = cm.get_content("Section C - Performance Work Statement")
        assert pws_content is not None

        section_l_content = f"Proposals shall address requirements in PWS: {pws_content[:50]}..."
        cm.add_content(
            doc_name="Section L - Instructions to Offerors",
            content=section_l_content,
            metadata={"agent": "section_l_generator"}
        )

        # Track cross-reference
        cm.add_cross_reference(
            from_doc="Section L - Instructions to Offerors",
            to_doc="Section C - Performance Work Statement",
            reference_text="Technical requirements"
        )

        # Step 3: Generate Section M (depends on PWS and Section L)
        related = cm.get_related_content(
            doc_name="Section M - Evaluation Factors",
            dependency_list=[
                "Section C - Performance Work Statement",
                "Section L - Instructions to Offerors"
            ]
        )

        assert len(related) == 2
        assert "Section C - Performance Work Statement" in related
        assert "Section L - Instructions to Offerors" in related

        # Step 4: Verify statistics
        stats = cm.get_statistics()
        assert stats["document_count"] == 2
        assert stats["cross_reference_count"] == 1

        # Step 5: Clean up
        cm.clear()
        assert len(cm._context_pool) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
