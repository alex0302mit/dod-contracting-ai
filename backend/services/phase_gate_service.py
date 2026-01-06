"""
Phase Gate Service

Handles validation logic for phase transitions in procurement projects.
Reads requirements from phase_definitions.yaml and validates document
approval status before allowing phase transitions.

Dependencies:
- phase_definitions.yaml: Configuration file with phase requirements and transition rules
- backend/models/procurement.py: PhaseName, PhaseTransitionRequest models
- backend/models/document.py: ProjectDocument, DocumentStatus models
"""
import os
import yaml
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.procurement import PhaseName, PhaseTransitionRequest, TransitionStatus
from backend.models.document import ProjectDocument, DocumentStatus
from backend.models.user import User, UserRole


class PhaseGateService:
    """
    Service for validating and managing phase transitions.
    Implements phase gate enforcement by checking document approvals
    against requirements defined in phase_definitions.yaml.
    """
    
    def __init__(self):
        """Initialize service and load phase definitions from YAML config"""
        self._phase_definitions = None
        self._load_phase_definitions()
    
    def _load_phase_definitions(self):
        """Load phase definitions from YAML configuration file"""
        # Get the path to the config file relative to this service
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config',
            'phase_definitions.yaml'
        )
        
        try:
            with open(config_path, 'r') as f:
                self._phase_definitions = yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to empty definitions if file not found
            self._phase_definitions = {
                'phases': {},
                'phase_transitions': {}
            }
    
    def get_phase_config(self, phase_name: str) -> Dict:
        """
        Get configuration for a specific phase.
        
        Args:
            phase_name: The phase name (e.g., 'pre_solicitation')
            
        Returns:
            Dict containing phase configuration including required documents
        """
        return self._phase_definitions.get('phases', {}).get(phase_name, {})
    
    def get_transition_config(self, from_phase: str, to_phase: str) -> Dict:
        """
        Get configuration for a specific phase transition.
        
        Args:
            from_phase: Source phase name
            to_phase: Target phase name
            
        Returns:
            Dict containing transition requirements and gatekeeper info
        """
        # Build the transition key (e.g., 'pre_solicitation_to_solicitation')
        transition_key = f"{from_phase}_to_{to_phase}"
        return self._phase_definitions.get('phase_transitions', {}).get(transition_key, {})
    
    def get_required_documents(self, phase_name: str) -> List[str]:
        """
        Get list of required documents for a phase.
        
        Args:
            phase_name: The phase name
            
        Returns:
            List of required document names
        """
        phase_config = self.get_phase_config(phase_name)
        return phase_config.get('required_documents', [])
    
    def get_gatekeeper_role(self, from_phase: str, to_phase: str) -> Optional[str]:
        """
        Get the required gatekeeper role for a transition.
        
        Args:
            from_phase: Source phase name
            to_phase: Target phase name
            
        Returns:
            Role name (e.g., 'Contracting Officer', 'Source Selection Authority')
            or None if no gatekeeper required
        """
        transition_config = self.get_transition_config(from_phase, to_phase)
        return transition_config.get('gatekeeper')
    
    def map_gatekeeper_to_user_role(self, gatekeeper: str) -> Optional[UserRole]:
        """
        Map gatekeeper description to UserRole enum.
        
        Args:
            gatekeeper: Gatekeeper description from config
            
        Returns:
            UserRole enum value or None
        """
        # Map configuration gatekeeper names to UserRole enum values
        mapping = {
            'Contracting Officer': UserRole.CONTRACTING_OFFICER,
            'Source Selection Authority': UserRole.CONTRACTING_OFFICER,  # Often same as CO
            'Program Manager': UserRole.PROGRAM_MANAGER,
        }
        return mapping.get(gatekeeper)
    
    def check_document_approvals(
        self,
        db: Session,
        project_id: str,
        phase_name: str
    ) -> Dict[str, Dict]:
        """
        Check approval status of required documents for a phase.
        
        Args:
            db: Database session
            project_id: UUID of the project
            phase_name: Name of the phase to check
            
        Returns:
            Dict mapping document names to their status info:
            {
                "Document Name": {
                    "exists": bool,
                    "status": str or None,
                    "approved": bool,
                    "document_id": str or None
                }
            }
        """
        required_docs = self.get_required_documents(phase_name)
        results = {}
        
        for doc_name in required_docs:
            # Query for the document in this project
            # Use ILIKE for case-insensitive partial matching
            document = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.document_name.ilike(f"%{doc_name}%")
            ).first()
            
            if document:
                results[doc_name] = {
                    "exists": True,
                    "status": document.status.value if document.status else None,
                    "approved": document.status == DocumentStatus.APPROVED,
                    "document_id": str(document.id)
                }
            else:
                results[doc_name] = {
                    "exists": False,
                    "status": None,
                    "approved": False,
                    "document_id": None
                }
        
        return results
    
    def validate_transition(
        self,
        db: Session,
        project_id: str,
        from_phase: str,
        to_phase: str,
        user: User
    ) -> Dict:
        """
        Validate if a phase transition is allowed.
        
        Args:
            db: Database session
            project_id: UUID of the project
            from_phase: Source phase name
            to_phase: Target phase name
            user: Current user requesting validation
            
        Returns:
            Dict containing validation results:
            {
                "can_transition": bool,
                "blocking_issues": List[str],
                "warnings": List[str],
                "document_status": Dict[str, Dict],
                "required_gatekeeper": str or None,
                "user_can_request": bool
            }
        """
        results = {
            "can_transition": True,
            "blocking_issues": [],
            "warnings": [],
            "document_status": {},
            "required_gatekeeper": None,
            "user_can_request": True
        }
        
        # 1. Check valid phase transition order
        valid_transitions = [
            ('pre_solicitation', 'solicitation'),
            ('solicitation', 'post_solicitation'),
            ('post_solicitation', 'award'),
        ]
        
        if (from_phase, to_phase) not in valid_transitions:
            results["can_transition"] = False
            results["blocking_issues"].append(
                f"Invalid phase transition: {from_phase} → {to_phase}"
            )
            return results
        
        # 2. Check document approvals for current phase
        doc_status = self.check_document_approvals(db, project_id, from_phase)
        results["document_status"] = doc_status
        
        # Check for missing or unapproved documents
        for doc_name, status in doc_status.items():
            if not status["exists"]:
                results["blocking_issues"].append(
                    f"Required document missing: {doc_name}"
                )
                results["can_transition"] = False
            elif not status["approved"]:
                # Document exists but not approved - this is a warning, not blocker
                # Some workflows may allow transition with pending approvals
                results["warnings"].append(
                    f"Document not yet approved: {doc_name} (status: {status['status']})"
                )
        
        # 3. Check gatekeeper requirement
        gatekeeper = self.get_gatekeeper_role(from_phase, to_phase)
        results["required_gatekeeper"] = gatekeeper
        
        # 4. Check if user can request transition
        # CO, PM, and Admins can request transitions
        if user.role not in [UserRole.CONTRACTING_OFFICER, UserRole.PROGRAM_MANAGER, UserRole.ADMIN]:
            results["user_can_request"] = False
            results["warnings"].append(
                "Only Contracting Officers, Program Managers, or Admins can request phase transitions"
            )
        
        # 5. Get transition-specific validation checks
        transition_config = self.get_transition_config(from_phase, to_phase)
        validation_checks = transition_config.get('validation_checks', [])
        if validation_checks:
            results["validation_checks"] = validation_checks
        
        return results
    
    def get_next_phase(self, current_phase: str) -> Optional[str]:
        """
        Get the next phase in the procurement lifecycle.
        
        Args:
            current_phase: Current phase name
            
        Returns:
            Next phase name or None if at final phase
        """
        phase_order = ['pre_solicitation', 'solicitation', 'post_solicitation', 'award']
        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass
        return None
    
    def get_eligible_gatekeepers(
        self,
        db: Session,
        project_id: str,
        from_phase: str,
        to_phase: str
    ) -> List[Dict]:
        """
        Get list of users who can act as gatekeepers for this transition.
        
        Args:
            db: Database session
            project_id: UUID of the project
            from_phase: Source phase name
            to_phase: Target phase name
            
        Returns:
            List of user dicts with id and name
        """
        gatekeeper = self.get_gatekeeper_role(from_phase, to_phase)
        target_role = self.map_gatekeeper_to_user_role(gatekeeper)
        
        if not target_role:
            return []
        
        # Get the project to find assigned CO/PM
        from backend.models.procurement import ProcurementProject
        project = db.query(ProcurementProject).filter(
            ProcurementProject.id == project_id
        ).first()
        
        eligible_users = []
        
        # Add the assigned CO if role matches
        if target_role == UserRole.CONTRACTING_OFFICER and project.contracting_officer:
            eligible_users.append({
                "id": str(project.contracting_officer.id),
                "name": project.contracting_officer.name,
                "role": "Assigned Contracting Officer"
            })
        
        # Also include other users with the required role
        other_users = db.query(User).filter(
            User.role == target_role,
            User.is_active == True
        ).all()
        
        for user in other_users:
            # Skip if already added as assigned CO
            if any(u["id"] == str(user.id) for u in eligible_users):
                continue
            eligible_users.append({
                "id": str(user.id),
                "name": user.name,
                "role": target_role.value
            })
        
        return eligible_users
    
    def create_transition_request(
        self,
        db: Session,
        project_id: str,
        from_phase: str,
        to_phase: str,
        requested_by: str,
        gatekeeper_id: Optional[str],
        validation_results: Dict
    ) -> PhaseTransitionRequest:
        """
        Create a new phase transition request.
        
        Args:
            db: Database session
            project_id: UUID of the project
            from_phase: Source phase name
            to_phase: Target phase name
            requested_by: UUID of the requesting user
            gatekeeper_id: UUID of the assigned gatekeeper (optional)
            validation_results: Results from validate_transition
            
        Returns:
            Created PhaseTransitionRequest object
        """
        request = PhaseTransitionRequest(
            project_id=project_id,
            from_phase=PhaseName(from_phase),
            to_phase=PhaseName(to_phase),
            requested_by=requested_by,
            gatekeeper_id=gatekeeper_id,
            status=TransitionStatus.PENDING,
            validation_results=validation_results
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)
        
        return request
    
    def approve_transition(
        self,
        db: Session,
        transition_request: PhaseTransitionRequest,
        gatekeeper: User,
        comments: Optional[str] = None
    ) -> Tuple[PhaseTransitionRequest, bool]:
        """
        Approve a phase transition request and update project phase.
        
        Args:
            db: Database session
            transition_request: The transition request to approve
            gatekeeper: User approving the transition
            comments: Optional approval comments
            
        Returns:
            Tuple of (updated request, success boolean)
        """
        from datetime import datetime
        from backend.models.procurement import ProcurementProject, ProcurementPhase, PhaseStatus
        
        # Update the transition request
        transition_request.status = TransitionStatus.APPROVED
        transition_request.gatekeeper_comments = comments
        transition_request.resolved_at = datetime.now()
        
        # Update project's current phase
        project = db.query(ProcurementProject).filter(
            ProcurementProject.id == transition_request.project_id
        ).first()
        
        if project:
            project.current_phase = transition_request.to_phase
            
            # Update phase statuses
            # Mark the old phase as completed
            old_phase = db.query(ProcurementPhase).filter(
                ProcurementPhase.project_id == project.id,
                ProcurementPhase.phase_name == transition_request.from_phase
            ).first()
            
            if old_phase:
                old_phase.status = PhaseStatus.COMPLETED
                old_phase.end_date = datetime.now().date()
            
            # Mark the new phase as in_progress
            new_phase = db.query(ProcurementPhase).filter(
                ProcurementPhase.project_id == project.id,
                ProcurementPhase.phase_name == transition_request.to_phase
            ).first()
            
            if new_phase:
                new_phase.status = PhaseStatus.IN_PROGRESS
                new_phase.start_date = datetime.now().date()
        
        db.commit()
        db.refresh(transition_request)
        
        return transition_request, True
    
    def reject_transition(
        self,
        db: Session,
        transition_request: PhaseTransitionRequest,
        gatekeeper: User,
        comments: str
    ) -> PhaseTransitionRequest:
        """
        Reject a phase transition request.
        
        Args:
            db: Database session
            transition_request: The transition request to reject
            gatekeeper: User rejecting the transition
            comments: Required rejection reason
            
        Returns:
            Updated PhaseTransitionRequest
        """
        from datetime import datetime
        
        transition_request.status = TransitionStatus.REJECTED
        transition_request.gatekeeper_comments = comments
        transition_request.resolved_at = datetime.now()
        
        db.commit()
        db.refresh(transition_request)
        
        return transition_request


# Singleton instance for use across the application
phase_gate_service = PhaseGateService()

