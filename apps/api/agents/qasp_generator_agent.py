"""
QASP Generator Agent: Generates Quality Assurance Surveillance Plans from PWS documents
"""

from typing import Dict, Optional
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.qasp_field_extractor import QASPFieldExtractor
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class QASPGeneratorAgent:
    """
    QASP Generator Agent

    Generates Quality Assurance Surveillance Plans (QASP) from Performance Work Statements (PWS)

    Workflow:
    1. Extract performance requirements from PWS
    2. Map requirements to surveillance methods
    3. Generate performance requirements matrix
    4. Populate QASP template
    5. Save as markdown and PDF
    """

    def __init__(self):
        """Initialize QASP Generator Agent"""
        self.extractor = QASPFieldExtractor()

        print("\n" + "="*70)
        print("QASP GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ Field Extractor ready")
        print(f"  ✓ Template ready")
        print("="*70 + "\n")

    def execute(
        self,
        pws_path: str,
        output_path: str,
        config: Optional[Dict] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Execute QASP generation workflow

        Args:
            pws_path: Path to PWS markdown file
            output_path: Path to save QASP
            config: Optional configuration (COR info, contact details)
            verbose: Print progress

        Returns:
            Dictionary with generation results
        """
        if verbose:
            print("\n" + "="*70)
            print("GENERATING QUALITY ASSURANCE SURVEILLANCE PLAN (QASP)")
            print("="*70)
            print(f"Source PWS: {pws_path}")
            print(f"Output: {output_path}")
            print("="*70 + "\n")

        # NEW: Cross-reference lookup - Find PWS document in metadata store
        program_name = config.get('program_name', 'Unknown') if config else 'Unknown'
        pws_reference = None

        if program_name != 'Unknown':
            try:
                if verbose:
                    print("🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for PWS document (most critical - we need its performance metrics)
                latest_pws = metadata_store.find_latest_document('pws', program_name)

                if latest_pws:
                    if verbose:
                        print(f"✅ Found PWS: {latest_pws['id']}")
                        print(f"   Performance Metrics: {len(latest_pws['extracted_data'].get('performance_metrics', []))}")
                    pws_reference = latest_pws['id']
                    # Inject PWS performance data into config for use in QASP
                    if not config:
                        config = {}
                    config['pws_metrics'] = latest_pws['extracted_data'].get('performance_metrics', [])
                    config['pws_qasp_elements'] = latest_pws['extracted_data'].get('qasp_elements', [])
                else:
                    if verbose:
                        print(f"⚠️  No PWS found for {program_name} - extracting from file")

            except Exception as e:
                if verbose:
                    print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                pws_reference = None

        # Step 1: Extract data from PWS
        if verbose:
            print("\nSTEP 1: Extracting performance requirements from PWS...")

        qasp_data = self.extractor.extract_from_pws(pws_path)

        if verbose:
            print(f"  ✓ Extracted {len(qasp_data['performance_requirements'])} performance requirements")
            print(f"  ✓ Extracted {len(qasp_data['deliverables'])} deliverables")
            print(f"  ✓ Extracted {len(qasp_data['performance_standards'])} performance standards")

        # Step 2: Build performance requirements matrix
        if verbose:
            print(f"\nSTEP 2: Building performance requirements matrix...")

        perf_matrix = self._build_performance_matrix(
            qasp_data['performance_requirements'],
            qasp_data['deliverables']
        )

        if verbose:
            print(f"  ✓ Generated {len(perf_matrix)} surveillance requirements")

        # Step 3: Populate QASP template
        if verbose:
            print(f"\nSTEP 3: Populating QASP template...")

        qasp_content = self._populate_template(
            qasp_data,
            perf_matrix,
            config or {}
        )

        if verbose:
            print(f"  ✓ Template populated")

        # Step 4: Save QASP
        if verbose:
            print(f"\nSTEP 4: Saving QASP...")

        self._save_qasp(qasp_content, output_path)

        if verbose:
            print(f"  ✓ QASP saved: {output_path}")

        # Step 5: Convert to PDF
        pdf_path = output_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(output_path, pdf_path)
            if verbose:
                print(f"  ✓ PDF saved: {pdf_path}")
        except Exception as e:
            if verbose:
                print(f"  ⚠ PDF generation skipped: {e}")

        # Success
        if verbose:
            print("\n" + "="*70)
            print("✅ QASP GENERATION COMPLETE")
            print("="*70)
            print(f"QASP: {output_path}")
            print(f"Performance Requirements: {len(perf_matrix)}")
            print("="*70 + "\n")

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                if verbose:
                    print("💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()
                extractor = DocumentDataExtractor()

                # Extract structured data from generated QASP
                extracted_data = {
                    'performance_requirements': qasp_data['performance_requirements'],
                    'requirements_count': len(perf_matrix),
                    'deliverables': qasp_data['deliverables'],
                    'deliverables_count': len(qasp_data['deliverables']),
                    'performance_standards': qasp_data['performance_standards'],
                    'surveillance_methods': [req.get('surveillance_method', '') for req in perf_matrix],
                    'contract_info': qasp_data['contract_info'],
                    'performance_matrix': perf_matrix
                }

                # Build references dict
                references = {}
                if pws_reference:
                    references['pws'] = pws_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='qasp',
                    program=program_name,
                    content=qasp_content,
                    file_path=output_path,
                    extracted_data=extracted_data,
                    references=references
                )

                if verbose:
                    print(f"✅ Document metadata saved: {doc_id}")

            except Exception as e:
                if verbose:
                    print(f"⚠️  Failed to save document metadata: {str(e)}")

        return {
            'success': True,
            'output_path': output_path,
            'pdf_path': pdf_path if Path(pdf_path).exists() else None,
            'requirements_count': len(perf_matrix),
            'deliverables_count': len(qasp_data['deliverables']),
            'contract_info': qasp_data['contract_info']
        }

    def _build_performance_matrix(
        self,
        requirements: list,
        deliverables: list
    ) -> list:
        """
        Build performance requirements matrix table

        Args:
            requirements: List of performance requirements
            deliverables: List of deliverables

        Returns:
            List of formatted matrix rows
        """
        matrix = []

        # Add performance requirements
        for i, req in enumerate(requirements, 1):
            # Generate AQL
            aql, aql_desc = self.extractor.generate_aql_recommendation(req)

            # Generate frequency
            frequency = self.extractor.generate_surveillance_frequency(req)

            # Determine surveillance method
            method = self._determine_surveillance_method(req)

            # Determine responsible party
            responsible = "COR" if "critical" in str(req).lower() else "QAE"

            matrix_row = {
                'pws_para': req.get('pws_paragraph', f"PWS {i}"),
                'objective': req.get('performance_objective', '')[:80],
                'standard': req.get('performance_standard', '')[:100],
                'aql': aql,
                'method': method,
                'frequency': frequency,
                'responsible': responsible
            }

            matrix.append(matrix_row)

        # Add deliverables as separate requirements
        for i, deliv in enumerate(deliverables, 1):
            matrix_row = {
                'pws_para': f"PWS Deliverable {i}",
                'objective': deliv['title'][:80],
                'standard': "Delivered on time, complete, and accurate",
                'aql': "0% (No late/incomplete deliveries tolerated)",
                'method': deliv['surveillance_method'],
                'frequency': "Per delivery schedule",
                'responsible': "COR"
            }

            matrix.append(matrix_row)

        return matrix[:20]  # Limit to top 20 for readability

    def _determine_surveillance_method(self, requirement: Dict) -> str:
        """Determine appropriate surveillance method"""
        text = str(requirement).lower()

        if 'report' in text or 'document' in text:
            return "Desk Review"
        elif 'system' in text or 'availability' in text:
            return "Automated Monitoring"
        elif 'satisfaction' in text or 'feedback' in text:
            return "Customer Feedback"
        elif 'response' in text or 'incident' in text:
            return "Random Sampling"
        elif 'inspection' in text:
            return "100% Inspection"
        else:
            return "Periodic Surveillance"

    def _populate_template(
        self,
        qasp_data: Dict,
        perf_matrix: list,
        config: Dict
    ) -> str:
        """
        Populate QASP template with extracted data

        Args:
            qasp_data: Extracted QASP data
            perf_matrix: Performance requirements matrix
            config: Configuration (COR info, etc.)

        Returns:
            Populated QASP markdown content
        """
        # Load template
        template_path = Path(__file__).parent.parent / "templates" / "qasp_template.md"
        with open(template_path, 'r') as f:
            template = f.read()

        # Build performance requirements table
        perf_table = self._format_performance_table(perf_matrix)

        # Prepare template variables
        contract_info = qasp_data['contract_info']

        variables = {
            'contract_number': config.get('contract_number', 'TBD-XXXX-XX-X-XXXX'),
            'program_name': contract_info.get('program_name', 'Program Name'),
            'period_of_performance': contract_info.get('period_of_performance', '36 months'),
            'pws_reference': config.get('pws_reference', f"PWS dated {contract_info.get('date', 'TBD')}"),
            'pws_date': contract_info.get('date', datetime.now().strftime('%m/%d/%Y')),
            'qasp_date': datetime.now().strftime('%m/%d/%Y'),
            'organization': contract_info.get('organization', 'DOD/ARMY'),
            'contracting_officer': config.get('contracting_officer', 'John Smith'),
            'ko_phone': config.get('ko_phone', '(XXX) XXX-XXXX'),
            'ko_email': config.get('ko_email', 'contracting.officer@mil'),
            'cor_name': config.get('cor_name', contract_info.get('author', 'Jane Doe')),
            'cor_organization': contract_info.get('organization', 'Program Office'),
            'cor_phone': config.get('cor_phone', '(XXX) XXX-XXXX'),
            'cor_email': config.get('cor_email', 'cor@mil'),
            'cor_level': config.get('cor_level', 'II'),
            'qae_name': config.get('qae_name', 'Bob Johnson'),
            'qae_organization': contract_info.get('organization', 'Operations Division'),
            'qae_phone': config.get('qae_phone', '(XXX) XXX-XXXX'),
            'qae_email': config.get('qae_email', 'qae@mil'),
            'qcp_reference': config.get('qcp_reference', 'X.X'),
            'performance_requirements_table': perf_table
        }

        # Replace all variables
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

        return template

    def _format_performance_table(self, perf_matrix: list) -> str:
        """Format performance requirements as markdown table"""
        if not perf_matrix:
            return "_No performance requirements extracted_"

        # Table header
        table = "| PWS Para | Performance Objective | Performance Standard | AQL | Surveillance Method | Frequency | Responsible |\n"
        table += "|----------|----------------------|---------------------|-----|---------------------|-----------|-------------|\n"

        # Table rows
        for row in perf_matrix:
            table += f"| {row['pws_para']} | {row['objective']} | {row['standard']} | {row['aql']} | {row['method']} | {row['frequency']} | {row['responsible']} |\n"

        return table

    def _save_qasp(self, content: str, output_path: str):
        """Save QASP markdown file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(content)


# Example usage
def main():
    """Test QASP Generator Agent"""
    import os

    # Paths
    pws_path = "outputs/pws/performance_work_statement.md"
    output_dir = "outputs/qasp"
    os.makedirs(output_dir, exist_ok=True)

    output_path = f"{output_dir}/quality_assurance_surveillance_plan.md"

    # Configuration (optional - provide COR/KO details)
    config = {
        'contracting_officer': 'John Smith',
        'ko_phone': '(410) 555-1234',
        'ko_email': 'john.smith@army.mil',
        'cor_name': 'Jane Doe',
        'cor_phone': '(410) 555-5678',
        'cor_email': 'jane.doe@army.mil',
        'cor_level': 'II'
    }

    # Initialize agent
    agent = QASPGeneratorAgent()

    # Generate QASP
    if Path(pws_path).exists():
        print("Generating QASP from PWS...")

        result = agent.execute(
            pws_path=pws_path,
            output_path=output_path,
            config=config,
            verbose=True
        )

        if result['success']:
            print(f"\n✅ QASP generated successfully!")
            print(f"   QASP: {result['output_path']}")
            print(f"   Requirements: {result['requirements_count']}")
            print(f"   Deliverables: {result['deliverables_count']}")
        else:
            print(f"\n✗ QASP generation failed")

    else:
        print(f"PWS file not found: {pws_path}")


if __name__ == "__main__":
    main()
