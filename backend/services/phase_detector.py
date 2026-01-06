"""
Phase Detector Service

Analyzes selected documents to determine the appropriate procurement phase
and orchestration strategy.
"""

from typing import List, Dict, Optional, Set
from pathlib import Path
import yaml


class PhaseDetector:
    """
    Detects procurement phase based on selected documents

    Analyzes document selection to determine whether the user is in:
    - Pre-Solicitation (planning and requirements)
    - Solicitation (RFP package development)
    - Post-Solicitation (evaluation and source selection)
    - Award (contract award and notifications)
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize phase detector

        Args:
            config_path: Path to phase_definitions.yaml (optional)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "phase_definitions.yaml"

        self.config_path = config_path
        self.phase_config = self._load_phase_config()

    def _load_phase_config(self) -> Dict:
        """Load phase definitions from YAML config"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load phase config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Fallback default configuration if YAML not available"""
        return {
            "phases": {
                "pre_solicitation": {
                    "required_documents": [
                        "Market Research Report",
                        "Acquisition Plan",
                        "Performance Work Statement (PWS)",
                        "Independent Government Cost Estimate (IGCE)"
                    ]
                },
                "solicitation": {
                    "required_documents": [
                        "SF33",
                        "Section B",
                        "Section C",
                        "Section H",
                        "Section I",
                        "Section K",
                        "Section L",
                        "Section M"
                    ]
                },
                "post_solicitation": {
                    "required_documents": [
                        "Source Selection Plan",
                        "Evaluation Scorecard",
                        "Source Selection Decision Document"
                    ]
                },
                "award": {
                    "required_documents": [
                        "SF26",
                        "Award Notification"
                    ]
                }
            }
        }

    def detect_phase(
        self,
        document_names: List[str],
        strict: bool = False
    ) -> Dict:
        """
        Detect procurement phase from document selection

        Args:
            document_names: List of selected document names
            strict: If True, require exact phase match. If False, use best guess.

        Returns:
            Dictionary with phase detection results:
            {
                "primary_phase": "solicitation",
                "confidence": 0.9,
                "mixed_phases": False,
                "phase_breakdown": {"solicitation": 8, "pre_solicitation": 2},
                "recommendations": ["Consider adding Section L"],
                "warnings": []
            }
        """
        if not document_names:
            return {
                "primary_phase": None,
                "confidence": 0.0,
                "mixed_phases": False,
                "phase_breakdown": {},
                "recommendations": [],
                "warnings": ["No documents selected"]
            }

        # Analyze each document's phase
        phase_counts = {
            "pre_solicitation": 0,
            "solicitation": 0,
            "post_solicitation": 0,
            "award": 0
        }

        document_phase_map = {}

        for doc_name in document_names:
            phase = self._classify_document_phase(doc_name)
            if phase:
                phase_counts[phase] += 1
                document_phase_map[doc_name] = phase

        # Determine primary phase (most documents)
        primary_phase = max(phase_counts, key=phase_counts.get)

        # Check if mixed phases
        active_phases = [p for p, count in phase_counts.items() if count > 0]
        mixed_phases = len(active_phases) > 1

        # Calculate confidence
        total_docs = len(document_names)
        primary_count = phase_counts[primary_phase]
        confidence = primary_count / total_docs if total_docs > 0 else 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(
            primary_phase,
            document_names,
            phase_counts
        )

        # Generate warnings
        warnings = []
        if mixed_phases:
            warnings.append(
                f"Mixed phases detected: Documents from {', '.join(active_phases)}. "
                f"Consider generating documents in phase-appropriate batches."
            )

        if confidence < 0.5 and strict:
            warnings.append(
                f"Low phase confidence ({confidence:.0%}). "
                f"Document selection is ambiguous."
            )

        return {
            "primary_phase": primary_phase if phase_counts[primary_phase] > 0 else None,
            "confidence": confidence,
            "mixed_phases": mixed_phases,
            "phase_breakdown": phase_counts,
            "document_phase_map": document_phase_map,
            "recommendations": recommendations,
            "warnings": warnings
        }

    def _classify_document_phase(self, document_name: str) -> Optional[str]:
        """
        Classify a single document into a phase

        Args:
            document_name: Name of document

        Returns:
            Phase name or None if cannot classify
        """
        doc_lower = document_name.lower()

        # Pre-Solicitation indicators
        if any(keyword in doc_lower for keyword in [
            "market research",
            "acquisition plan",
            "sources sought",
            "pre-solicitation",
            "industry day",
            "rfi",
            "request for information",
            "pws", "performance work statement",
            "sow", "statement of work",
            "soo", "statement of objectives",
            "igce", "cost estimate", "government cost estimate"
        ]):
            return "pre_solicitation"

        # Solicitation indicators (RFP sections)
        if any(keyword in doc_lower for keyword in [
            "section a", "section b", "section c", "section h",
            "section i", "section k", "section l", "section m",
            "sf33", "solicitation",
            "instructions to offerors",
            "evaluation factors",
            "qasp", "quality assurance"  # QASP typically included with solicitation
        ]):
            return "solicitation"

        # Post-Solicitation indicators
        if any(keyword in doc_lower for keyword in [
            "source selection",
            "evaluation scorecard",
            "ssdd", "selection decision",
            "ppq", "past performance"
        ]):
            return "post_solicitation"

        # Award indicators
        if any(keyword in doc_lower for keyword in [
            "sf26", "award notification",
            "debriefing", "award contract"
        ]):
            return "award"

        return None

    def _generate_recommendations(
        self,
        primary_phase: str,
        selected_documents: List[str],
        phase_counts: Dict[str, int]
    ) -> List[str]:
        """
        Generate recommendations based on phase detection

        Args:
            primary_phase: Detected primary phase
            selected_documents: List of selected document names
            phase_counts: Count of documents per phase

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if primary_phase == "solicitation":
            # Check for required RFP sections
            required_sections = [
                "Section L", "Section M", "Section C",
                "Section B", "Section H", "Section I", "Section K"
            ]

            selected_lower = [doc.lower() for doc in selected_documents]

            for required in required_sections:
                if not any(required.lower() in doc for doc in selected_lower):
                    recommendations.append(
                        f"Consider adding {required} (required for complete solicitation)"
                    )

        elif primary_phase == "pre_solicitation":
            # Check for key planning documents
            if not any("market research" in doc.lower() for doc in selected_documents):
                recommendations.append(
                    "Consider adding Market Research Report (required for acquisition planning)"
                )

            if not any("acquisition plan" in doc.lower() for doc in selected_documents):
                recommendations.append(
                    "Consider adding Acquisition Plan (required before solicitation)"
                )

        elif primary_phase == "post_solicitation":
            # Check for evaluation documents
            if not any("scorecard" in doc.lower() for doc in selected_documents):
                recommendations.append(
                    "Consider adding Evaluation Scorecard (required for evaluation)"
                )

        return recommendations

    def get_phase_info(self, phase_name: str) -> Dict:
        """
        Get detailed information about a specific phase

        Args:
            phase_name: Name of phase (pre_solicitation, solicitation, etc.)

        Returns:
            Dictionary with phase information
        """
        phases = self.phase_config.get("phases", {})
        phase_data = phases.get(phase_name, {})

        return {
            "name": phase_data.get("name", phase_name),
            "description": phase_data.get("description", ""),
            "required_documents": phase_data.get("required_documents", []),
            "recommended_documents": phase_data.get("recommended_documents", []),
            "optional_documents": phase_data.get("optional_documents", []),
            "orchestrator": phase_data.get("orchestrator"),
            "estimated_duration_days": phase_data.get("estimated_duration_days"),
            "compliance_requirements": phase_data.get("compliance_requirements", [])
        }

    def get_all_phases(self) -> List[Dict]:
        """
        Get information about all phases

        Returns:
            List of phase information dictionaries
        """
        phases = self.phase_config.get("phases", {})

        return [
            {
                "phase_id": phase_id,
                **self.get_phase_info(phase_id)
            }
            for phase_id in phases.keys()
        ]

    def validate_phase_completeness(
        self,
        phase_name: str,
        selected_documents: List[str]
    ) -> Dict:
        """
        Validate if document selection is complete for a phase

        Args:
            phase_name: Name of phase to validate
            selected_documents: List of selected document names

        Returns:
            Validation results
        """
        phase_info = self.get_phase_info(phase_name)
        required = phase_info.get("required_documents", [])

        selected_lower = [doc.lower() for doc in selected_documents]
        missing_required = []

        for req_doc in required:
            # Flexible matching (contains)
            if not any(req_doc.lower() in selected or selected in req_doc.lower()
                      for selected in selected_lower):
                missing_required.append(req_doc)

        is_complete = len(missing_required) == 0

        return {
            "phase": phase_name,
            "is_complete": is_complete,
            "missing_required": missing_required,
            "completeness_percentage": ((len(required) - len(missing_required)) / len(required) * 100)
                                       if len(required) > 0 else 100.0
        }


# Singleton instance
_detector_instance: Optional[PhaseDetector] = None


def get_phase_detector() -> PhaseDetector:
    """
    Get singleton instance of phase detector

    Returns:
        PhaseDetector instance
    """
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = PhaseDetector()

    return _detector_instance
