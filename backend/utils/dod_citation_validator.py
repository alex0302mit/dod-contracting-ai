"""
DoD Citation Validator
Ensures all citations follow DoD acquisition documentation standards
Based on FAR, DFARS, and service-specific regulations
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CitationType(Enum):
    """Types of DoD citations"""
    FAR = "FAR"  # Federal Acquisition Regulation
    DFARS = "DFARS"  # Defense FAR Supplement
    DOD_INSTRUCTION = "DoDI"  # DoD Instruction
    DOD_DIRECTIVE = "DoDD"  # DoD Directive
    DOD_MANUAL = "DoDM"  # DoD Manual
    USC = "USC"  # United States Code
    MCO = "MCO"  # Marine Corps Order
    DAFI = "DAFI"  # Dept of Air Force Instruction
    AFI = "AFI"  # Air Force Instruction (legacy)
    SPFI = "SPFI"  # Space Force Instruction
    PROGRAM_DOC = "PROG"  # Program-specific documents (e.g., Budget Specification, FY2025)
    MARKET_RESEARCH = "MR"  # Market research artifacts
    INLINE_DOC = "INLINE"  # Inline document citations like (Document Name, Date)


@dataclass
class Citation:
    """Represents a single citation"""
    citation_type: CitationType
    reference: str  # The full citation text
    number: str  # Regulation/document number
    title: Optional[str] = None  # Document title
    date: Optional[str] = None  # Publication/revision date
    section: Optional[str] = None  # Specific section reference
    is_valid: bool = True
    validation_issues: List[str] = None
    
    def __post_init__(self):
        if self.validation_issues is None:
            self.validation_issues = []


class DoDCitationValidator:
    """
    Validates and formats citations according to DoD standards
    
    Dependencies:
    - re (standard library): For regex pattern matching
    - typing (standard library): For type hints
    - dataclasses (standard library): For Citation data structure
    """
    
    # Citation format patterns based on DoD guide
    CITATION_PATTERNS = {
        # FAR format: FAR 15.203 or FAR 15.203-1(a)(2)
        CitationType.FAR: r'\bFAR\s+(\d+\.\d+(?:-\d+)?(?:\([a-z]\))?(?:\(\d+\))?)\b',

        # DFARS format: DFARS 225.872 or DFARS 252.225-7001
        CitationType.DFARS: r'\bDFARS\s+(\d+\.\d+(?:-\d+)?)\b',

        # DoD Instructions: DoDI 5000.02, Operation of... (January 23, 2020)
        CitationType.DOD_INSTRUCTION: r'\bDoDI\s+(\d+\.\d+)',

        # DoD Directives: DoDD 5000.01
        CitationType.DOD_DIRECTIVE: r'\bDoDD\s+(\d+\.\d+)',

        # DoD Manuals: DoDM 5000.04
        CitationType.DOD_MANUAL: r'\bDoDM\s+(\d+\.\d+)',

        # US Code: 10 U.S.C. § 3201
        CitationType.USC: r'\b(\d+)\s+U\.S\.C\.\s+§\s+(\d+)',

        # Marine Corps Orders: MCO 4400.177
        CitationType.MCO: r'\bMCO\s+(\d+\.\d+)',

        # Air Force Instructions: DAFI 63-101/20 or AFI 63-138
        CitationType.DAFI: r'\b(DAFI|AFI|SPFI)\s+([\d-]+(?:/\d+)?)',

        # Inline document citations: (Document Name, Date) or (Document Name, Month Year)
        # Examples: (Program Objectives, 10/05/2025), (Technical Requirements, March 2025)
        # Captures: (Any capitalized words/phrases, followed by comma and date/year)
        CitationType.INLINE_DOC: r'\(([A-Z][A-Za-z\s\/\-]+),\s*([A-Za-z0-9\/\s,]+)\)',

        # Market research citations: (Ref: Source, Date) or (Ref: Source Name, Date)
        # Examples: (Ref: SAM.gov, 2025-10-18), (Ref: GSA Schedule 70, 2024-09)
        # This pattern covers the inline reference format used in market research reports
        CitationType.MARKET_RESEARCH: r'\(Ref:\s*([^,]+),\s*([^)]+)\)',
    }
    
    # Required elements for proper citations
    CITATION_REQUIREMENTS = {
        CitationType.FAR: {'number': True, 'section': False, 'date': False},
        CitationType.DFARS: {'number': True, 'section': False, 'date': False},
        CitationType.DOD_INSTRUCTION: {'number': True, 'title': False, 'date': True},
        CitationType.DOD_DIRECTIVE: {'number': True, 'title': False, 'date': True},
        CitationType.USC: {'number': True, 'section': True, 'date': False},
        CitationType.MCO: {'number': True, 'title': False, 'date': False},
        CitationType.DAFI: {'number': True, 'title': False, 'date': False},
        CitationType.INLINE_DOC: {'title': True, 'date': True},  # Requires document name and date
        CitationType.MARKET_RESEARCH: {'title': True, 'date': True},  # Requires source and date
    }
    
    def __init__(self):
        """Initialize the DoD citation validator"""
        self.detected_citations: List[Citation] = []
        self.citation_registry: Dict[str, int] = {}  # For numbered references
        self.citation_counter = 1
    
    def validate_content(self, content: str) -> Dict:
        """
        Validate all citations in content
        
        Args:
            content: Text content to validate
            
        Returns:
            Dictionary with validation results:
            - valid_citations: List of valid citations found
            - invalid_citations: List of invalid citations
            - missing_citations: Areas that need citations
            - score: Overall citation quality score (0-100)
            - issues: List of specific issues
            - suggestions: List of improvement suggestions
        """
        self.detected_citations = []
        
        # Detect all citations
        self._detect_citations(content)
        
        # Validate each citation
        valid_citations = []
        invalid_citations = []
        
        for citation in self.detected_citations:
            if citation.is_valid and not citation.validation_issues:
                valid_citations.append(citation)
            else:
                invalid_citations.append(citation)
        
        # Check for substantive claims that need citations
        missing_citations = self._detect_uncited_claims(content)
        
        # Calculate score
        score = self._calculate_citation_score(
            valid_citations,
            invalid_citations,
            missing_citations
        )
        
        # Generate issues and suggestions
        issues = self._generate_issues(invalid_citations, missing_citations)
        suggestions = self._generate_suggestions(invalid_citations, missing_citations)
        
        return {
            'score': score,
            'valid_citations': len(valid_citations),
            'invalid_citations': len(invalid_citations),
            'missing_citation_opportunities': len(missing_citations),
            'issues': issues,
            'suggestions': suggestions,
            'citation_details': {
                'valid': [self._citation_to_dict(c) for c in valid_citations],
                'invalid': [self._citation_to_dict(c) for c in invalid_citations],
                'missing_locations': missing_citations
            }
        }
    
    def _detect_citations(self, content: str):
        """Detect all citations in content using regex patterns"""
        for citation_type, pattern in self.CITATION_PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract the full citation context
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                # Create citation object
                citation = self._create_citation_from_match(
                    citation_type,
                    match,
                    context
                )
                
                # Validate the citation
                self._validate_citation(citation, context)
                
                self.detected_citations.append(citation)
    
    def _create_citation_from_match(
        self,
        citation_type: CitationType,
        match: re.Match,
        context: str
    ) -> Citation:
        """Create a Citation object from regex match"""
        full_text = match.group(0)

        if citation_type == CitationType.USC:
            # US Code has special format: 10 U.S.C. § 3201
            title = match.group(1)
            section = match.group(2)
            number = f"{title} U.S.C. § {section}"
            date = None
        elif citation_type == CitationType.INLINE_DOC:
            # Inline document citation: (Document Name, Date)
            title = match.group(1).strip()  # Document name
            date = match.group(2).strip()   # Date
            number = f"{title}, {date}"
        elif citation_type == CitationType.MARKET_RESEARCH:
            # Market research citation: (Ref: Source, Date)
            title = match.group(1).strip()  # Source name
            date = match.group(2).strip()   # Date
            number = f"Ref: {title}, {date}"
        else:
            number = match.group(1) if match.groups() else full_text
            # Try to extract date from context
            date_match = re.search(r'\(([A-Z][a-z]+\s+\d+,\s+\d{4})\)', context)
            date = date_match.group(1) if date_match else None

            # Try to extract title from context (for DoD Instructions)
            title = None
            if citation_type in [CitationType.DOD_INSTRUCTION, CitationType.DOD_DIRECTIVE]:
                title_match = re.search(rf'{citation_type.value}\s+{number},\s+([^,(]+)', context)
                if title_match:
                    title = title_match.group(1).strip()

        return Citation(
            citation_type=citation_type,
            reference=full_text,
            number=number,
            title=title,
            date=date
        )
    
    def _validate_citation(self, citation: Citation, context: str):
        """Validate a citation against DoD standards"""
        requirements = self.CITATION_REQUIREMENTS.get(citation.citation_type, {})
        
        # Check for required date
        if requirements.get('date') and not citation.date:
            citation.is_valid = False
            citation.validation_issues.append(
                f"{citation.citation_type.value} requires publication date"
            )
        
        # Check format based on type
        if citation.citation_type == CitationType.FAR:
            # FAR should have proper part.subpart format
            if not re.match(r'\d+\.\d+', citation.number):
                citation.validation_issues.append("FAR format should be Part.Subpart (e.g., FAR 15.203)")
        
        elif citation.citation_type == CitationType.DOD_INSTRUCTION:
            # DoD Instructions should include title
            if not citation.title:
                citation.validation_issues.append("DoD Instruction should include document title")
    
    def _detect_uncited_claims(self, content: str) -> List[Dict]:
        """
        Detect substantive claims that should have citations
        
        Returns:
            List of dictionaries with claim type and context
        """
        uncited_claims = []
        
        # Patterns for claims that typically need citations
        claim_patterns = {
            'budget': r'\$[\d,\.]+\s+(?:million|billion)',
            'vendors': r'\d+\s+(?:vendors?|contractors?|companies)',
            'requirements': r'(?:must|shall|will|requires?)\s+(?:provide|deliver|meet|achieve)',
            'statistics': r'\d+(?:\.\d+)?%',
            'timeline': r'\d+\s+(?:months?|years?|days?)',
            'capabilities': r'(?:capable of|supports?|provides?)\s+[\w\s]+',
        }
        
        for claim_type, pattern in claim_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Check if this claim is near a citation (within 200 chars)
                start = match.start()
                nearby_content = content[max(0, start-200):min(len(content), start+200)]
                
                # Check if any citation pattern exists nearby
                has_nearby_citation = any(
                    re.search(pattern, nearby_content, re.IGNORECASE)
                    for pattern in self.CITATION_PATTERNS.values()
                )
                
                if not has_nearby_citation:
                    # Extract context
                    context_start = max(0, start - 50)
                    context_end = min(len(content), match.end() + 50)
                    context = content[context_start:context_end].replace('\n', ' ')
                    
                    uncited_claims.append({
                        'type': claim_type,
                        'text': match.group(0),
                        'context': f"...{context}..."
                    })
        
        return uncited_claims
    
    def _calculate_citation_score(
        self,
        valid: List[Citation],
        invalid: List[Citation],
        missing: List[Dict]
    ) -> int:
        """Calculate overall citation quality score"""
        if len(valid) == 0 and len(invalid) == 0:
            # No citations at all
            return 20 if len(missing) == 0 else 10
        
        # Base score on valid citations
        total_citations = len(valid) + len(invalid)
        validity_score = (len(valid) / total_citations) * 60 if total_citations > 0 else 0
        
        # Penalty for missing citations
        if len(missing) > 0:
            penalty = min(30, len(missing) * 3)
        else:
            penalty = 0
        
        # Bonus for having citations
        presence_bonus = min(40, len(valid) * 8)
        
        final_score = int(validity_score + presence_bonus - penalty)
        return max(0, min(100, final_score))
    
    def _generate_issues(
        self,
        invalid_citations: List[Citation],
        missing_claims: List[Dict]
    ) -> List[str]:
        """Generate list of citation issues"""
        issues = []
        
        for citation in invalid_citations:
            for issue in citation.validation_issues:
                issues.append(f"{citation.reference}: {issue}")
        
        if len(missing_claims) > 5:
            issues.append(f"{len(missing_claims)} factual claims lack citations")
        elif len(missing_claims) > 0:
            issues.append(f"{len(missing_claims)} claims need citations: " + 
                         ", ".join([c['type'] for c in missing_claims[:3]]))
        
        if not invalid_citations and not missing_claims:
            issues.append("No citation issues detected")
        
        return issues
    
    def _generate_suggestions(
        self,
        invalid_citations: List[Citation],
        missing_claims: List[Dict]
    ) -> List[str]:
        """Generate suggestions for improvement"""
        suggestions = []
        
        if invalid_citations:
            suggestions.append("Review and correct invalid citation formats per DoD standards")
            suggestions.append("Add publication dates for DoD Instructions and Directives")
        
        if missing_claims:
            suggestions.append("Add citations for budget figures, vendor counts, and requirements")
            suggestions.append("Reference FAR/DFARS regulations for acquisition processes")
            suggestions.append("Cite program documentation for technical requirements")
        
        if not suggestions:
            suggestions.append("Citations meet DoD documentation standards")
        
        return suggestions
    
    def _citation_to_dict(self, citation: Citation) -> Dict:
        """Convert Citation object to dictionary"""
        return {
            'type': citation.citation_type.value,
            'reference': citation.reference,
            'number': citation.number,
            'title': citation.title,
            'date': citation.date,
            'is_valid': citation.is_valid,
            'issues': citation.validation_issues
        }
    
    def format_citation(
        self,
        citation_type: CitationType,
        number: str,
        title: Optional[str] = None,
        date: Optional[str] = None,
        section: Optional[str] = None
    ) -> str:
        """
        Format a citation according to DoD standards
        
        Args:
            citation_type: Type of citation
            number: Regulation/document number
            title: Document title (if applicable)
            date: Publication date (if applicable)
            section: Specific section reference (if applicable)
            
        Returns:
            Properly formatted citation string
        """
        if citation_type == CitationType.FAR:
            citation = f"FAR {number}"
            if section:
                citation += f"({section})"
                
        elif citation_type == CitationType.DFARS:
            citation = f"DFARS {number}"
            if section:
                citation += f"({section})"
                
        elif citation_type == CitationType.DOD_INSTRUCTION:
            citation = f"DoDI {number}"
            if title:
                citation += f", {title}"
            if date:
                citation += f" ({date})"
                
        elif citation_type == CitationType.DOD_DIRECTIVE:
            citation = f"DoDD {number}"
            if title:
                citation += f", {title}"
            if date:
                citation += f" ({date})"
                
        elif citation_type == CitationType.USC:
            citation = f"{number}"  # Should already be formatted as "10 U.S.C. § 3201"
            
        else:
            # Default format
            citation = f"{citation_type.value} {number}"
            if title:
                citation += f", {title}"
            if date:
                citation += f" ({date})"
        
        return citation
    
    def generate_references_section(self, citations: List[Citation]) -> str:
        """
        Generate a properly formatted References section
        
        Args:
            citations: List of Citation objects
            
        Returns:
            Formatted references section text
        """
        if not citations:
            return ""
        
        # Sort citations by type hierarchy
        type_order = {
            CitationType.USC: 1,
            CitationType.FAR: 2,
            CitationType.DFARS: 3,
            CitationType.DOD_DIRECTIVE: 4,
            CitationType.DOD_INSTRUCTION: 5,
            CitationType.DOD_MANUAL: 6,
            CitationType.MCO: 7,
            CitationType.DAFI: 8,
            CitationType.AFI: 9,
            CitationType.SPFI: 10,
            CitationType.PROGRAM_DOC: 11,
            CitationType.MARKET_RESEARCH: 12,
        }
        
        sorted_citations = sorted(
            citations,
            key=lambda c: (type_order.get(c.citation_type, 99), c.number)
        )
        
        references = ["## References\n"]
        
        current_type = None
        for i, citation in enumerate(sorted_citations, 1):
            # Add section header if type changes
            if citation.citation_type != current_type:
                current_type = citation.citation_type
                references.append(f"\n### {self._get_section_name(current_type)}\n")
            
            # Format reference entry
            ref_text = f"{i}. {self.format_citation(**self._citation_to_format_args(citation))}"
            references.append(ref_text)
        
        return '\n'.join(references)
    
    def _get_section_name(self, citation_type: CitationType) -> str:
        """Get section name for reference grouping"""
        section_names = {
            CitationType.USC: "Statutory Authority",
            CitationType.FAR: "Federal Acquisition Regulation",
            CitationType.DFARS: "Defense Federal Acquisition Regulation Supplement",
            CitationType.DOD_INSTRUCTION: "DoD Instructions",
            CitationType.DOD_DIRECTIVE: "DoD Directives",
            CitationType.DOD_MANUAL: "DoD Manuals",
            CitationType.MCO: "Marine Corps Orders",
            CitationType.DAFI: "Air Force/Space Force Instructions",
            CitationType.AFI: "Air Force Instructions (Legacy)",
            CitationType.PROGRAM_DOC: "Program Documentation",
            CitationType.MARKET_RESEARCH: "Market Research Documents",
        }
        return section_names.get(citation_type, "Other References")
    
    def _citation_to_format_args(self, citation: Citation) -> Dict:
        """Convert Citation to format_citation arguments"""
        return {
            'citation_type': citation.citation_type,
            'number': citation.number,
            'title': citation.title,
            'date': citation.date,
            'section': citation.section
        }


# Example usage and testing
if __name__ == "__main__":
    validator = DoDCitationValidator()
    
    # Test content
    test_content = """
    This acquisition will follow FAR 15.203 procedures for competitive negotiation.
    The market research was conducted per FAR 10.001 and FAR 10.002.
    
    Per DoDI 5000.85, Major Capability Acquisition (August 6, 2020), this program
    requires milestone approval. The budget of $2.5 million must meet requirements
    specified in the technical specifications.
    
    In accordance with 10 U.S.C. § 3201, full and open competition will be used.
    DFARS 225.872 implements contracting with qualifying country sources.
    """
    
    results = validator.validate_content(test_content)
    
    print("="*70)
    print("DoD CITATION VALIDATION RESULTS")
    print("="*70)
    print(f"Score: {results['score']}/100")
    print(f"Valid Citations: {results['valid_citations']}")
    print(f"Invalid Citations: {results['invalid_citations']}")
    print(f"Missing Citation Opportunities: {results['missing_citation_opportunities']}")
    print("\nIssues:")
    for issue in results['issues']:
        print(f"  - {issue}")
    print("\nSuggestions:")
    for suggestion in results['suggestions']:
        print(f"  - {suggestion}")
