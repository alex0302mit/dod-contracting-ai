"""
SF33 Generator Agent: Orchestrates SF33 form generation from PWS/SOO/SOW documents
"""

from typing import Dict, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.sf33_field_extractor import SF33FieldExtractor
from backend.utils.pdf_form_filler import PDFFormFiller
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class SF33GeneratorAgent:
    """
    SF33 Generator Agent

    Orchestrates the extraction of data from PWS/SOO/SOW documents
    and population of SF33 Solicitation, Offer, and Award form

    Workflow:
    1. Extract metadata from work statement document
    2. Generate solicitation-specific data (numbers, dates)
    3. Map extracted data to SF33 form fields
    4. Fill PDF form template
    5. Save filled SF33
    """

    def __init__(
        self,
        sf33_template_path: str = "data/documents/SF33.pdf"
    ):
        """
        Initialize SF33 Generator Agent

        Args:
            sf33_template_path: Path to blank SF33 PDF template
        """
        self.sf33_template_path = sf33_template_path
        self.extractor = SF33FieldExtractor()

        # Validate template exists
        if not Path(sf33_template_path).exists():
            raise FileNotFoundError(f"SF33 template not found: {sf33_template_path}")

        print("\n" + "="*70)
        print("SF33 GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ SF33 Template: {sf33_template_path}")
        print(f"  ✓ Field Extractor ready")
        print("="*70 + "\n")

    def execute(
        self,
        work_statement_path: str,
        output_path: str,
        solicitation_config: Optional[Dict] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Execute SF33 generation workflow

        Args:
            work_statement_path: Path to PWS/SOO/SOW markdown file
            output_path: Path to save filled SF33 PDF
            solicitation_config: Optional configuration overrides
            verbose: Print detailed progress

        Returns:
            Dictionary with generation results
        """
        if verbose:
            print("\n" + "="*70)
            print("GENERATING SF33 SOLICITATION FORM")
            print("="*70)
            print(f"Source: {work_statement_path}")
            print(f"Output: {output_path}")
            print("="*70 + "\n")

        # NEW: Cross-reference lookup - Find Acquisition Plan and IGCE
        program_name = solicitation_config.get('program_name', 'Unknown') if solicitation_config else 'Unknown'

        if program_name != 'Unknown':
            try:
                if verbose:
                    print("🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for Acquisition Plan (contract details)
                latest_acq_plan = metadata_store.find_latest_document('acquisition_plan', program_name)
                # Look for IGCE (estimated value)
                latest_igce = metadata_store.find_latest_document('igce', program_name)
                # Look for PWS/SOW/SOO
                latest_pws = metadata_store.find_latest_document('pws', program_name)

                if latest_acq_plan:
                    if verbose:
                        print(f"✅ Found Acquisition Plan: {latest_acq_plan['id']}")
                    if not solicitation_config:
                        solicitation_config = {}
                    solicitation_config['acq_plan_data'] = latest_acq_plan['extracted_data']
                    self._acq_plan_reference = latest_acq_plan['id']
                else:
                    self._acq_plan_reference = None

                if latest_igce:
                    if verbose:
                        print(f"✅ Found IGCE: {latest_igce['id']}")
                        print(f"   Estimated Value: {latest_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")
                    if not solicitation_config:
                        solicitation_config = {}
                    solicitation_config['estimated_value'] = latest_igce['extracted_data'].get('total_cost_formatted', 'TBD')
                    self._igce_reference = latest_igce['id']
                else:
                    self._igce_reference = None

                if latest_pws:
                    if verbose:
                        print(f"✅ Found PWS: {latest_pws['id']}")
                    self._pws_reference = latest_pws['id']
                else:
                    self._pws_reference = None

            except Exception as e:
                if verbose:
                    print(f"⚠️  Cross-reference lookup failed: {str(e)}")
                self._acq_plan_reference = None
                self._igce_reference = None
                self._pws_reference = None
        else:
            self._acq_plan_reference = None
            self._igce_reference = None
            self._pws_reference = None

        # Step 1: Extract metadata
        if verbose:
            print("\nSTEP 1: Extracting metadata from work statement...")

        metadata = self.extractor.extract_from_markdown(work_statement_path)

        if verbose:
            print(f"\n  Extracted Metadata:")
            print(f"    Document Type: {metadata['document_type']}")
            print(f"    Program: {metadata['program_name']}")
            print(f"    Organization: {metadata['organization']}")
            print(f"    Date: {metadata['date']}")
            print(f"    Author: {metadata['author']}")
            if metadata['budget']:
                print(f"    Budget: {metadata['budget']}")
            if metadata['period_of_performance']:
                print(f"    Period: {metadata['period_of_performance']}")

        # Step 2: Validate required fields
        if verbose:
            print(f"\nSTEP 2: Validating required fields...")

        validation_result = self.validate_required_fields(metadata)

        if not validation_result['valid']:
            print(f"\n  ✗ Validation failed!")
            print(f"    Missing fields: {', '.join(validation_result['missing'])}")
            return {
                'success': False,
                'error': 'Missing required fields',
                'missing_fields': validation_result['missing']
            }

        if verbose:
            print(f"  ✓ All required fields present")

        # Step 3: Map to SF33 fields
        if verbose:
            print(f"\nSTEP 3: Mapping data to SF33 form fields...")

        sf33_fields = self.extractor.map_to_sf33_fields(
            metadata,
            solicitation_config
        )

        if verbose:
            print(f"  ✓ Mapped {len(sf33_fields)} fields")

        # Step 4: Fill PDF form
        if verbose:
            print(f"\nSTEP 4: Filling SF33 PDF form...")

        filler = PDFFormFiller(self.sf33_template_path)

        # Validate fields against PDF template
        field_validation = filler.validate_fields(sf33_fields)

        if verbose:
            print(f"  Valid fields: {len(field_validation['valid'])}")
            if field_validation['invalid']:
                print(f"  ⚠ Invalid fields: {len(field_validation['invalid'])}")
                for field in field_validation['invalid'][:5]:
                    print(f"    - {field}")

        # Fill and save
        filler.fill_and_save(
            field_values=sf33_fields,
            output_path=output_path,
            verbose=verbose
        )

        # Success
        if verbose:
            print("\n" + "="*70)
            print("✅ SF33 GENERATION COMPLETE")
            print("="*70)
            print(f"Output: {output_path}")
            print("="*70 + "\n")

        # NEW: Save document metadata for cross-referencing
        if program_name != 'Unknown':
            try:
                if verbose:
                    print("💾 Saving document metadata for cross-referencing...")
                metadata_store = DocumentMetadataStore()

                # Extract structured data from generated SF33
                extracted_data = {
                    'solicitation_number': sf33_fields.get(self.extractor.field_mapping['solicitation_number'], 'TBD'),
                    'program_name': metadata['program_name'],
                    'organization': metadata['organization'],
                    'estimated_value': solicitation_config.get('estimated_value', 'TBD') if solicitation_config else 'TBD',
                    'fields_filled': len(field_validation['valid']),
                    'form_metadata': metadata
                }

                # Build references dict
                references = {}
                if self._acq_plan_reference:
                    references['acquisition_plan'] = self._acq_plan_reference
                if self._igce_reference:
                    references['igce'] = self._igce_reference
                if self._pws_reference:
                    references['pws'] = self._pws_reference

                # Save to metadata store
                doc_id = metadata_store.save_document(
                    doc_type='sf33',
                    program=program_name,
                    content='',  # SF33 is a PDF form, no markdown content
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
            'metadata': metadata,
            'fields_filled': len(field_validation['valid']),
            'solicitation_number': sf33_fields.get(
                self.extractor.field_mapping['solicitation_number'],
                'N/A'
            )
        }

    def validate_required_fields(self, metadata: Dict) -> Dict:
        """
        Validate that required metadata fields are present

        Args:
            metadata: Extracted metadata

        Returns:
            Dictionary with validation results
        """
        required_fields = [
            'program_name',
            'organization',
            'date'
        ]

        missing = []
        for field in required_fields:
            if not metadata.get(field):
                missing.append(field)

        return {
            'valid': len(missing) == 0,
            'missing': missing,
            'present': [f for f in required_fields if metadata.get(f)]
        }

    def generate_from_multiple_documents(
        self,
        pws_path: Optional[str] = None,
        soo_path: Optional[str] = None,
        sow_path: Optional[str] = None,
        output_dir: str = "outputs/solicitation",
        verbose: bool = True
    ) -> Dict:
        """
        Generate SF33 forms for multiple document types

        Args:
            pws_path: Path to PWS document
            soo_path: Path to SOO document
            sow_path: Path to SOW document
            output_dir: Directory to save generated SF33s
            verbose: Print progress

        Returns:
            Dictionary with results for each document type
        """
        results = {}

        documents = {
            'PWS': pws_path,
            'SOO': soo_path,
            'SOW': sow_path
        }

        for doc_type, doc_path in documents.items():
            if doc_path and Path(doc_path).exists():
                output_path = f"{output_dir}/SF33_{doc_type}.pdf"

                print(f"\nGenerating SF33 for {doc_type}...")

                result = self.execute(
                    work_statement_path=doc_path,
                    output_path=output_path,
                    verbose=verbose
                )

                results[doc_type] = result

        return results


# Example usage
def main():
    """Test SF33 Generator Agent"""
    import os

    # Paths
    pws_path = "outputs/pws/performance_work_statement.md"
    soo_path = "outputs/soo/statement_of_objectives.md"
    sow_path = "outputs/sow/statement_of_work.md"

    output_dir = "outputs/solicitation"
    os.makedirs(output_dir, exist_ok=True)

    # Initialize agent
    agent = SF33GeneratorAgent()

    # Generate SF33 for PWS
    if Path(pws_path).exists():
        print("Testing with PWS document...")
        result = agent.execute(
            work_statement_path=pws_path,
            output_path=f"{output_dir}/SF33_PWS.pdf",
            verbose=True
        )

        if result['success']:
            print(f"\n✅ SF33 generated successfully!")
            print(f"   Solicitation #: {result['solicitation_number']}")
            print(f"   Fields filled: {result['fields_filled']}")
        else:
            print(f"\n✗ Generation failed: {result.get('error')}")
    else:
        print(f"PWS file not found: {pws_path}")

    # Optional: Generate for all document types
    print("\n\nGenerating SF33 for all document types...")
    results = agent.generate_from_multiple_documents(
        pws_path=pws_path if Path(pws_path).exists() else None,
        soo_path=soo_path if Path(soo_path).exists() else None,
        sow_path=sow_path if Path(sow_path).exists() else None,
        output_dir=output_dir,
        verbose=False
    )

    print(f"\n\nGeneration Summary:")
    print("="*70)
    for doc_type, result in results.items():
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {doc_type}: {result.get('output_path', 'Failed')}")
    print("="*70)


if __name__ == "__main__":
    main()
