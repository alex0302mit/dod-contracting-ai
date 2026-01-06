"""
Unit tests for PhaseDetector

Tests phase detection, validation, and recommendation logic.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.services.phase_detector import PhaseDetector, get_phase_detector


class TestPhaseDetector:
    """Test suite for PhaseDetector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance for testing"""
        return PhaseDetector()

    def test_detector_initialization(self, detector):
        """Test that detector initializes correctly"""
        assert detector.phase_config is not None
        assert "phases" in detector.phase_config
        assert len(detector.phase_config["phases"]) >= 4  # At least 4 phases

    def test_detect_pre_solicitation_phase(self, detector):
        """Test detection of pre-solicitation phase"""
        documents = [
            "Market Research Report",
            "Acquisition Plan",
            "Performance Work Statement (PWS)",
            "Independent Government Cost Estimate (IGCE)"
        ]

        result = detector.detect_phase(documents)

        assert result["primary_phase"] == "pre_solicitation"
        assert result["confidence"] >= 0.75  # High confidence
        assert result["mixed_phases"] is False

    def test_detect_solicitation_phase(self, detector):
        """Test detection of solicitation phase"""
        documents = [
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors",
            "Section B - Supplies/Services and Prices",
            "Section H - Special Contract Requirements",
            "Section I - Contract Clauses",
            "Section K - Representations and Certifications"
        ]

        result = detector.detect_phase(documents)

        assert result["primary_phase"] == "solicitation"
        assert result["confidence"] >= 0.8
        assert result["mixed_phases"] is False

    def test_detect_post_solicitation_phase(self, detector):
        """Test detection of post-solicitation phase"""
        documents = [
            "Source Selection Plan",
            "Evaluation Scorecard",
            "Source Selection Decision Document (SSDD)"
        ]

        result = detector.detect_phase(documents)

        assert result["primary_phase"] == "post_solicitation"
        assert result["confidence"] == 1.0  # All docs from same phase
        assert result["mixed_phases"] is False

    def test_detect_award_phase(self, detector):
        """Test detection of award phase"""
        documents = [
            "SF26 - Award/Contract",
            "Award Notification",
            "Debriefing Letter"
        ]

        result = detector.detect_phase(documents)

        assert result["primary_phase"] == "award"
        assert result["confidence"] >= 0.66
        assert result["mixed_phases"] is False

    def test_detect_mixed_phases(self, detector):
        """Test detection when documents from multiple phases selected"""
        documents = [
            "Market Research Report",  # pre-solicitation
            "Section L - Instructions to Offerors",  # solicitation
            "Section M - Evaluation Factors",  # solicitation
            "Evaluation Scorecard"  # post-solicitation
        ]

        result = detector.detect_phase(documents)

        assert result["mixed_phases"] is True
        assert len(result["warnings"]) > 0
        assert "Mixed phases" in result["warnings"][0]
        # Should still determine primary phase (solicitation - 2 docs)
        assert result["primary_phase"] == "solicitation"

    def test_empty_document_list(self, detector):
        """Test handling of empty document list"""
        result = detector.detect_phase([])

        assert result["primary_phase"] is None
        assert result["confidence"] == 0.0
        assert len(result["warnings"]) > 0
        assert "No documents selected" in result["warnings"][0]

    def test_phase_breakdown(self, detector):
        """Test phase breakdown counting"""
        documents = [
            "Market Research Report",  # pre-sol
            "Section L - Instructions to Offerors",  # sol
            "Section M - Evaluation Factors",  # sol
            "Section B - Supplies/Services and Prices"  # sol
        ]

        result = detector.detect_phase(documents)

        assert result["phase_breakdown"]["pre_solicitation"] == 1
        assert result["phase_breakdown"]["solicitation"] == 3
        assert result["phase_breakdown"]["post_solicitation"] == 0
        assert result["phase_breakdown"]["award"] == 0

    def test_document_phase_mapping(self, detector):
        """Test individual document to phase mapping"""
        documents = [
            "Market Research Report",
            "Section L - Instructions to Offerors",
            "Evaluation Scorecard"
        ]

        result = detector.detect_phase(documents)

        assert "document_phase_map" in result
        assert result["document_phase_map"]["Market Research Report"] == "pre_solicitation"
        assert result["document_phase_map"]["Section L - Instructions to Offerors"] == "solicitation"
        assert result["document_phase_map"]["Evaluation Scorecard"] == "post_solicitation"

    def test_recommendations_for_solicitation(self, detector):
        """Test that recommendations are generated for incomplete solicitation"""
        # Missing Section L and Section M
        documents = [
            "Section B - Supplies/Services and Prices",
            "Section H - Special Contract Requirements"
        ]

        result = detector.detect_phase(documents)

        assert len(result["recommendations"]) > 0
        # Should recommend adding Section L and M
        recommendations_text = " ".join(result["recommendations"])
        assert "Section L" in recommendations_text or "Section M" in recommendations_text

    def test_recommendations_for_pre_solicitation(self, detector):
        """Test recommendations for incomplete pre-solicitation"""
        # Only has one pre-sol document
        documents = ["Performance Work Statement (PWS)"]

        result = detector.detect_phase(documents)

        assert len(result["recommendations"]) > 0

    def test_classify_document_phase_pre_solicitation(self, detector):
        """Test document classification for pre-solicitation docs"""
        test_cases = [
            "Market Research Report",
            "Acquisition Plan",
            "Sources Sought Notice",
            "Pre-Solicitation Notice",
            "Industry Day Materials",
            "Request for Information (RFI)"
        ]

        for doc in test_cases:
            phase = detector._classify_document_phase(doc)
            assert phase == "pre_solicitation", f"Failed for: {doc}"

    def test_classify_document_phase_solicitation(self, detector):
        """Test document classification for solicitation docs"""
        test_cases = [
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors",
            "Section B - Supplies/Services and Prices",
            "Section H - Special Contract Requirements",
            "Section I - Contract Clauses",
            "Section K - Representations and Certifications",
            "Quality Assurance Surveillance Plan (QASP)",
            "SF33 - Solicitation, Offer and Award"
        ]

        for doc in test_cases:
            phase = detector._classify_document_phase(doc)
            assert phase == "solicitation", f"Failed for: {doc}"

    def test_classify_document_phase_post_solicitation(self, detector):
        """Test document classification for post-solicitation docs"""
        test_cases = [
            "Source Selection Plan",
            "Evaluation Scorecard",
            "Source Selection Decision Document (SSDD)",
            "Past Performance Questionnaire (PPQ)"
        ]

        for doc in test_cases:
            phase = detector._classify_document_phase(doc)
            assert phase == "post_solicitation", f"Failed for: {doc}"

    def test_classify_document_phase_award(self, detector):
        """Test document classification for award docs"""
        test_cases = [
            "SF26 - Award/Contract",
            "Award Notification",
            "Debriefing Letter"
        ]

        for doc in test_cases:
            phase = detector._classify_document_phase(doc)
            assert phase == "award", f"Failed for: {doc}"

    def test_get_phase_info(self, detector):
        """Test retrieving phase information"""
        info = detector.get_phase_info("solicitation")

        assert info["name"] is not None
        assert info["description"] is not None
        assert len(info["required_documents"]) > 0
        assert "orchestrator" in info

    def test_get_all_phases(self, detector):
        """Test retrieving all phase information"""
        phases = detector.get_all_phases()

        assert len(phases) >= 4  # At least 4 phases
        assert all("phase_id" in phase for phase in phases)
        assert all("name" in phase for phase in phases)

    def test_validate_phase_completeness_complete(self, detector):
        """Test validation of complete phase"""
        # Complete solicitation package
        documents = [
            "SF33 - Solicitation, Offer and Award",
            "Section B - Supplies/Services and Prices",
            "Section C - Performance Work Statement",
            "Section H - Special Contract Requirements",
            "Section I - Contract Clauses",
            "Section K - Representations and Certifications",
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors"
        ]

        validation = detector.validate_phase_completeness("solicitation", documents)

        assert validation["is_complete"] is True
        assert len(validation["missing_required"]) == 0
        assert validation["completeness_percentage"] == 100.0

    def test_validate_phase_completeness_incomplete(self, detector):
        """Test validation of incomplete phase"""
        # Missing several required docs
        documents = [
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors"
        ]

        validation = detector.validate_phase_completeness("solicitation", documents)

        assert validation["is_complete"] is False
        assert len(validation["missing_required"]) > 0
        assert validation["completeness_percentage"] < 100.0

    def test_case_insensitive_detection(self, detector):
        """Test that detection works with different cases"""
        documents_lower = [
            "section l - instructions to offerors",
            "section m - evaluation factors"
        ]

        documents_upper = [
            "SECTION L - INSTRUCTIONS TO OFFERORS",
            "SECTION M - EVALUATION FACTORS"
        ]

        result_lower = detector.detect_phase(documents_lower)
        result_upper = detector.detect_phase(documents_upper)

        assert result_lower["primary_phase"] == result_upper["primary_phase"]
        assert result_lower["primary_phase"] == "solicitation"

    def test_singleton_get_phase_detector(self):
        """Test singleton pattern for get_phase_detector"""
        # Clear singleton
        import backend.services.phase_detector as detector_module
        detector_module._detector_instance = None

        # Get first instance
        detector1 = get_phase_detector()

        # Get second instance (should be same)
        detector2 = get_phase_detector()

        assert detector1 is detector2  # Same instance


class TestPhaseDetectorEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return PhaseDetector()

    def test_unknown_document_classification(self, detector):
        """Test classification of completely unknown document"""
        phase = detector._classify_document_phase("Completely Unknown Document Type 12345")
        assert phase is None

    def test_ambiguous_document(self, detector):
        """Test handling of ambiguous document name"""
        # Document name doesn't clearly indicate phase
        documents = ["Generic Document"]

        result = detector.detect_phase(documents)

        # Should still provide a result (may be low confidence)
        assert "primary_phase" in result

    def test_confidence_with_single_document(self, detector):
        """Test confidence calculation with single document"""
        documents = ["Section L - Instructions to Offerors"]

        result = detector.detect_phase(documents)

        assert result["confidence"] == 1.0  # 100% when all docs from same phase

    def test_very_low_confidence_warning(self, detector):
        """Test that low confidence generates warnings in strict mode"""
        # Mix of unknown and known docs
        documents = [
            "Unknown Doc 1",
            "Unknown Doc 2",
            "Section L - Instructions to Offerors"
        ]

        result = detector.detect_phase(documents, strict=True)

        # May have warnings about low confidence or unknown docs
        # (Depends on implementation details)
        assert "warnings" in result

    def test_special_characters_in_document_names(self, detector):
        """Test handling of special characters"""
        documents = [
            "Section L - Instructions (2024) [v2.0]",
            "Section M - Evaluation @ Draft Stage"
        ]

        result = detector.detect_phase(documents)

        assert result["primary_phase"] == "solicitation"

    def test_detect_phase_with_duplicates(self, detector):
        """Test handling of duplicate document names"""
        documents = [
            "Section L - Instructions to Offerors",
            "Section L - Instructions to Offerors",  # Duplicate
            "Section M - Evaluation Factors"
        ]

        result = detector.detect_phase(documents)

        # Should still work correctly
        assert result["primary_phase"] == "solicitation"


class TestPhaseDetectorPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return PhaseDetector()

    def test_large_document_list_performance(self, detector):
        """Test detection with large document list"""
        import time

        # Create large list of documents
        documents = []
        for i in range(100):
            documents.append(f"Section L - Instructions to Offerors {i}")

        start_time = time.time()
        result = detector.detect_phase(documents)
        elapsed_time = time.time() - start_time

        assert elapsed_time < 1.0  # Should complete in under 1 second
        assert result["primary_phase"] == "solicitation"

    def test_repeated_detection_performance(self, detector):
        """Test performance of repeated detections"""
        import time

        documents = [
            "Section L - Instructions to Offerors",
            "Section M - Evaluation Factors"
        ]

        start_time = time.time()
        for _ in range(100):
            detector.detect_phase(documents)
        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0  # 100 detections in under 2 seconds


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
