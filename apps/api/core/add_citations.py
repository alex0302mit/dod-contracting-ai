"""
Citation Injector Tool
Automatically adds proper DoD-compliant source citations to acquisition documents

Dependencies:
- anthropic: For LLM-powered intelligent citation placement
- utils.dod_citation_validator: For DoD citation standards validation and formatting
"""

import anthropic
import os
import re
import sys
from typing import Dict, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.dod_citation_validator import DoDCitationValidator, CitationType


class CitationInjector:
    def __init__(self, api_key: str, document_type: str = "Report"):
        """
        Initialize with Anthropic API key and DoD citation validator
        
        Args:
            api_key: Anthropic API key
            document_type: Type of document (e.g., "Report", "RFP", "SOO", "SOW")
            
        Dependencies:
            - anthropic: For LLM-powered citation generation
            - DoDCitationValidator: For DoD citation standards validation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.document_type = document_type
        # Initialize DoD citation validator for standardization and validation
        self.citation_validator = DoDCitationValidator()
        # Load DoD citation guide for prompt context
        self.dod_guide = self._load_dod_citation_guide()

    def _load_dod_citation_guide(self) -> str:
        """
        Load condensed DoD citation guide for reference in prompts
        
        Returns:
            Condensed DoD citation formatting guide for LLM context
            
        Comments:
            Provides essential citation formats without overwhelming the prompt
        """
        return """
═══════════════════════════════════════════════════════════════════
DOD CITATION STANDARDS - REQUIRED FORMATS
═══════════════════════════════════════════════════════════════════

1. FEDERAL ACQUISITION REGULATION (FAR)
   Format: FAR [Part].[Subpart].[Section]
   Examples: 
   - FAR 10.001 (Market Research Policy)
   - FAR 10.002 (Market Research Procedures)
   - FAR 15.203 (Requests for Proposals)
   - FAR 6.302-1 (Only One Responsible Source)
   
   In-text: "per FAR 10.001" or "IAW FAR 15.203"

2. DEFENSE FAR SUPPLEMENT (DFARS)
   Format: DFARS [Part].[Subpart].[Section]
   Examples:
   - DFARS 225.872 (Contracting with qualifying country sources)
   - DFARS 252.225-7001 (Buy American clause)
   
   In-text: "DFARS 252.225-7001 implements..." or "per DFARS 225.872"

3. DOD INSTRUCTIONS (CRITICAL: MUST INCLUDE DATE)
   Format: DoDI [Number], [Title] ([Date])
   Examples:
   - DoDI 5000.85, Major Capability Acquisition (August 6, 2020)
   - DoDI 5000.02, Operation of the Adaptive Acquisition Framework (January 23, 2020)
   
   In-text: "Per DoDI 5000.85, Major Capability Acquisition (August 6, 2020)"

4. UNITED STATES CODE (STATUTORY AUTHORITY)
   Format: [Title] U.S.C. § [Section]
   Examples:
   - 10 U.S.C. § 3201 (Full and Open Competition)
   - 10 U.S.C. § 3451 (Cost or Pricing Data)
   
   In-text: "Per 10 U.S.C. § 3201, full and open competition..."

5. PROGRAM DOCUMENTS (PROJECT-SPECIFIC INFO)
   Format: (Document Name, Date)
   Examples:
   - (Budget Specification, FY2025)
   - (Market Research Report, March 2025)
   - (Technical Requirements Document, October 2025)
   
   In-text: "The budget is $2.5M (Budget Specification, FY2025)"

═══════════════════════════════════════════════════════════════════
CITATION PLACEMENT RULES
═══════════════════════════════════════════════════════════════════

WHEN TO CITE:
✓ Budget/cost figures → Program documents
✓ Vendor counts/names → Market research documents
✓ Technical requirements → Requirements documents
✓ Timeline/schedule → Schedule documents
✓ Acquisition processes → FAR/DFARS regulations
✓ Compliance requirements → Statutory/regulatory sources

HOW TO PLACE:
✓ Immediately after the claim, before punctuation
✓ Use "per", "IAW" (in accordance with), or "pursuant to" for regulations
✓ Use parenthetical format for program documents
✓ One citation per major claim (don't over-cite)

EXAMPLES:
- "Market research was conducted per FAR 10.001 and FAR 10.002."
- "The estimated cost is $2.5 million (Budget Specification, FY2025)."
- "Twelve vendors responded (Market Research Report, March 2025)."
- "This acquisition follows DoDI 5000.85, Major Capability Acquisition (August 6, 2020)."
- "Per 10 U.S.C. § 3201, full and open competition will be used."

═══════════════════════════════════════════════════════════════════
"""

    def inject_citations(self, markdown_file: str = None, project_info: Dict = None, output_file: str = None, content: str = None) -> str:
        """
        Add DoD-compliant citations to document based on project information
        
        Args:
            markdown_file: Path to markdown document (optional if content provided)
            project_info: Dictionary with source data
            output_file: Output path (defaults to adding '_cited' to filename)
            content: Direct content string (alternative to markdown_file)
            
        Returns:
            Path to cited document (if file-based) or cited content string (if content-based)
            
        Comments:
            - Processes document section by section
            - Validates citations against DoD standards after injection
            - Logs validation scores for quality monitoring
        """
        
        # Read content either from file or direct input
        if content is not None:
            report_content = content
            file_based = False
        elif markdown_file is not None:
            with open(markdown_file, 'r') as f:
                report_content = f.read()
            file_based = True
        else:
            raise ValueError("Either markdown_file or content must be provided")
        
        print("="*70)
        print(f"CITATION INJECTION - {self.document_type} (DoD Standards)")
        print("="*70)
        if file_based:
            print(f"\nProcessing: {markdown_file}")
        else:
            print(f"\nProcessing: In-memory {self.document_type} document")
        print(f"Source data fields: {len(project_info) if project_info else 0}")
        
        # Detect sections automatically from the document
        sections_to_cite = self._detect_sections(report_content)
        
        cited_report = report_content
        citation_count = 0
        total_validation_score = 0
        sections_processed = 0
        
        for section in sections_to_cite:
            print(f"\n📝 Processing section: {section}")
            
            # Extract section content
            section_content = self._extract_section(report_content, section)
            
            if not section_content:
                print(f"   ⚠️  Section not found, skipping")
                continue
            
            # Add citations to this section
            cited_section = self._add_citations_to_section(
                section_content,
                section,
                project_info
            )
            
            # Validate citations using DoD validator
            validation_results = self.citation_validator.validate_content(cited_section)
            validation_score = validation_results['score']
            total_validation_score += validation_score
            sections_processed += 1
            
            # Count new citations added
            new_citations = cited_section.count('(') - section_content.count('(')
            citation_count += new_citations
            
            # Display results
            score_emoji = "✓" if validation_score >= 70 else "⚠️"
            print(f"   {score_emoji} Added {new_citations} citations | DoD Compliance: {validation_score}/100")
            
            # Show validation issues if score is low
            if validation_score < 70:
                for issue in validation_results['issues'][:2]:
                    print(f"      ⚠️  {issue}")
            
            # Replace in full report
            cited_report = cited_report.replace(section_content, cited_section)
        
        # Calculate average validation score
        avg_validation = total_validation_score / sections_processed if sections_processed > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"COMPLETE: Added {citation_count} citations")
        print(f"Average DoD Compliance Score: {avg_validation:.1f}/100")
        if avg_validation >= 80:
            print(f"✅ Excellent citation quality")
        elif avg_validation >= 70:
            print(f"✓ Acceptable citation quality")
        else:
            print(f"⚠️  Citation quality needs improvement")
        print(f"{'='*70}\n")
        
        # Return based on mode
        if file_based:
            # Determine output file path
            if output_file is None:
                output_file = markdown_file.replace('.md', '_cited.md')
            
            # Save cited report
            with open(output_file, 'w') as f:
                f.write(cited_report)
            
            print(f"Saved to: {output_file}\n")
            return output_file
        else:
            # Return cited content directly
            return cited_report

    def _detect_sections(self, report: str) -> List[str]:
        """
        Automatically detect sections in the document
        
        Args:
            report: Document content
            
        Returns:
            List of section names found in the document
        """
        # Find all level 2 headers (## Section Name)
        section_pattern = r'^##\s+(.+)$'
        matches = re.findall(section_pattern, report, re.MULTILINE)
        
        # Filter out common non-content sections
        exclude_patterns = [
            r'^Table of Contents',
            r'^Document Information',
            r'^Executive Summary',
            r'^Quality.*Score',
            r'^References',  # Don't cite the references section
        ]
        
        sections = []
        for match in matches:
            # Check if this section should be excluded
            should_exclude = any(re.match(pattern, match, re.IGNORECASE) for pattern in exclude_patterns)
            if not should_exclude:
                sections.append(match.strip())
        
        if not sections:
            # Fallback: use default sections based on document type
            sections = self._get_default_sections()
        
        print(f"Detected {len(sections)} sections to cite")
        return sections

    def _get_default_sections(self) -> List[str]:
        """
        Get default sections based on document type
        
        Returns:
            List of default section names
        """
        defaults = {
            "Report": [
                'Product/Service Description',
                'Background',
                'Performance Requirements',
                'Market Research Conducted',
                'Industry Capabilities',
                'Small Business Opportunities',
                'Commercial Opportunities',
                'Conclusions and Recommendations'
            ],
            "RFP": [
                'Section A',
                'Section B',
                'Section C',
                'Section D',
                'Section E',
                'Section F',
                'Section G',
                'Section H',
                'Section L',
                'Section M'
            ],
            "SOO": [
                'Background',
                'Objectives',
                'Performance Standards',
                'Constraints',
                'Deliverables'
            ],
            "SOW": [
                'Scope',
                'Background',
                'Tasks',
                'Deliverables',
                'Performance Standards',
                'Period of Performance'
            ]
        }
        
        return defaults.get(self.document_type, defaults["Report"])

    def _extract_section(self, report: str, section_name: str) -> str:
        """
        Extract a specific section from the report
        
        Args:
            report: Full document content
            section_name: Name of section to extract
            
        Returns:
            Section content or empty string if not found
        """
        # Find section start
        pattern = f"## {section_name}"
        start = report.find(pattern)
        
        if start == -1:
            return ""
        
        # Find next section (or end of document)
        next_section = report.find('\n## ', start + len(pattern))
        
        if next_section == -1:
            # This is the last section
            section_content = report[start:]
        else:
            section_content = report[start:next_section]
        
        return section_content.strip()

    def _add_citations_to_section(self, section_content: str, section_name: str, project_info: Dict) -> str:
        """
        Use Claude to intelligently add DoD-compliant citations to a section
        
        Args:
            section_content: The section text to add citations to
            section_name: Name of the section
            project_info: Project information for citation sources
            
        Returns:
            Section content with properly formatted DoD citations
            
        Dependencies:
            - Anthropic API for intelligent citation placement
            - DoD citation guide for formatting standards
            
        Comments:
            - Prompts LLM with DoD citation standards
            - Provides available sources for citation
            - Validates output format
        """
        # Build citation reference guide with DoD formatting
        citation_guide = self._build_dod_citation_guide(project_info)
        
        # Updated prompt to use DoD standards
        prompt = f"""You are a government acquisition specialist adding proper DoD-compliant citations to a {self.document_type.lower()} section.

{self.dod_guide}

═══════════════════════════════════════════════════════════════════
SECTION TO CITE:
═══════════════════════════════════════════════════════════════════

{section_content}

═══════════════════════════════════════════════════════════════════
AVAILABLE CITATION SOURCES:
═══════════════════════════════════════════════════════════════════

{citation_guide}

═══════════════════════════════════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════════════════════════════════

Add citations throughout the text following DoD acquisition documentation standards.

CITATION REQUIREMENTS:
1. Use FAR/DFARS citations for acquisition process references
   - Market research → FAR 10.001, FAR 10.002
   - RFP processes → FAR 15.203
   - Competition → FAR 6.302-1 (if applicable)

2. Use program document citations for project-specific information
   - Budget/cost → (Budget Specification, FY2025)
   - Vendor info → (Market Research Report, March 2025)
   - Requirements → (Technical Requirements Document, October 2025)
   - Timeline → (Schedule Requirements, date)

3. Follow exact format from the DoD standards above
4. Place citations immediately after factual claims
5. DO NOT change any content - only add citations
6. Aim for 3-5 key citations per section
7. Focus on: budget, vendors, requirements, timeline, processes

CRITICAL RULES:
✗ DO NOT change, rewrite, or modify the original text
✗ DO NOT add new content or elaborate on existing content
✓ ONLY add citations in the proper format
✓ Keep all markdown formatting intact
✓ Use exact citation formats shown in the standards

Return the COMPLETE section with citations added. Keep all markdown formatting."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        cited_content = response.content[0].text.strip()
        
        # Clean up any markdown code blocks that Claude might add
        cited_content = cited_content.replace('```markdown', '').replace('```', '')
        
        return cited_content.strip()

    def _build_dod_citation_guide(self, project_info: Dict) -> str:
        """
        Build a DoD-compliant citation reference guide
        
        Args:
            project_info: Dictionary with source data
            
        Returns:
            Formatted citation guide with DoD standards and available sources
            
        Comments:
            Maps project information to proper DoD citation formats
            Includes both regulatory and program document citations
        """
        guide = []
        
        guide.append("REGULATORY CITATIONS (use these for process/compliance):")
        guide.append("-" * 70)
        guide.append("- FAR 10.001 - Market Research Policy")
        guide.append("- FAR 10.002 - Market Research Procedures")
        guide.append("- FAR 15.203 - Requests for Proposals")
        guide.append("- FAR 6.302-1 - Only One Responsible Source (if sole source)")
        guide.append("- FAR Part 6 - Competition Requirements")
        guide.append("- DFARS Part 225 - Foreign Acquisition (if applicable)")
        guide.append("")
        
        guide.append("PROGRAM DOCUMENT CITATIONS (use these for project details):")
        guide.append("-" * 70)
        
        # Map project_info fields to proper citation sources
        citation_mapping = {
            'budget': ('Budget Specification, FY2025', 'Budget/cost information'),
            'period_of_performance': ('Schedule Requirements', 'Performance period'),
            'vendor_research': ('Market Research Report, March 2025', 'Vendor research results'),
            'potential_vendors': ('Vendor Capability Assessment', 'Vendor identification'),
            'critical_requirements': ('Technical Requirements Document, October 2025', 'Technical requirements'),
            'schedule_constraints': ('Schedule Requirements', 'Timeline constraints'),
            'small_business_potential': ('Small Business Market Research Report', 'Small business analysis'),
            'background_context': ('Program Background', 'Historical context'),
        }
        
        for key, value in project_info.items():
            if value and key in citation_mapping:
                citation_format, description = citation_mapping[key]
                # Extract date if available
                date = project_info.get('date', '2025')
                # Format with date if not already included
                if 'FY' not in citation_format and 'March' not in citation_format and 'October' not in citation_format:
                    citation_format = f"{citation_format.rstrip(', ')}, {date}"
                
                guide.append(f"- ({citation_format}) - {description}")
                guide.append(f"  Content: {str(value)[:120]}{'...' if len(str(value)) > 120 else ''}")
        
        return '\n'.join(guide)


def main():
    """
    Main execution for testing citation injection
    
    Comments:
        - Demonstrates usage with sample project data
        - Tests DoD-compliant citation injection
    """
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Project info (should match what was used to generate report)
    project_info = {
        "program_name": "Advanced Logistics Management System (ALMS)",
        "author": "John Smith",
        "organization": "DOD/ARMY/LOGISTICS",
        "report_title": "Cloud-Based Inventory Management Services",
        "budget": "$2.5 million",
        "period_of_performance": "36 months (3 years)",
        "date": "10/01/2025",
        "background_context": "Current inventory system is 15 years old and lacks modern cloud capabilities. Previous contract was $1.8M over 5 years.",
        "critical_requirements": "Real-time tracking, 99.9% uptime, integration with existing ERP systems, mobile access",
        "schedule_constraints": "Must be operational by Q2 FY2026",
        "vendor_research": "Conducted RFI in March 2025 with 12 responses, held industry day in April 2025 with 8 vendors",
        "potential_vendors": "TechLogistics Inc., CloudTrack Systems, MilSpec Software Solutions",
        "small_business_potential": "4 of 12 respondents were small businesses with relevant experience",
    }
    
    # Initialize injector with DoD compliance
    injector = CitationInjector(api_key)
    
    # Add citations
    cited_file = injector.inject_citations(
        'filled_market_research_report.md',
        project_info
    )
    
    print(f"\n✅ DoD-compliant citation injection complete!")
    print(f"📄 Original: filled_market_research_report.md")
    print(f"📄 With citations: {cited_file}")
    print(f"\nNext steps:")
    print(f"1. Review the cited report: {cited_file}")
    print(f"2. Verify DoD compliance: python scripts/test_dod_citations.py {cited_file}")
    print(f"3. Run evaluation: python scripts/run_agent_pipeline.py")
    print(f"4. Convert to PDF: python utils/convert_md_to_pdf.py {cited_file}")


if __name__ == "__main__":
    main()
