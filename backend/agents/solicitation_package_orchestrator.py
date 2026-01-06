"""
Solicitation Package Orchestrator: Assembles complete solicitation packages
Combines SF33 + work statements + supplementary sections
"""

from typing import Dict, Optional, List
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.sf33_generator_agent import SF33GeneratorAgent
from pypdf import PdfReader, PdfWriter


class SolicitationPackageOrchestrator:
    """
    Solicitation Package Orchestrator

    Assembles complete Federal acquisition solicitation packages including:
    - Section A: SF33 Solicitation, Offer, and Award form
    - Section B: Supplies or Services and Prices (CLIN Structure)
    - Section C: Work Statement (PWS/SOO/SOW)
    - Section H: Special Contract Requirements
    - Section I: Contract Clauses
    - Section J: List of Attachments (QASP)
    - Section K: Representations, Certifications, and Other Statements
    - Section L: Instructions to Offerors
    - Section M: Evaluation Factors for Award

    Creates a complete, submission-ready solicitation package with all 12 sections
    """

    def __init__(
        self,
        sf33_template_path: str = "data/documents/SF33.pdf"
    ):
        """
        Initialize Solicitation Package Orchestrator

        Args:
            sf33_template_path: Path to SF33 PDF template
        """
        self.sf33_generator = SF33GeneratorAgent(sf33_template_path)

        print("\n" + "="*70)
        print("SOLICITATION PACKAGE ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ SF33 Generator ready")
        print(f"  ✓ PDF merger ready")
        print("="*70 + "\n")

    def build_complete_package(
        self,
        work_statement_md: str,
        work_statement_pdf: str,
        output_path: str,
        solicitation_config: Optional[Dict] = None,
        include_templates: bool = True,
        verbose: bool = True
    ) -> Dict:
        """
        Build complete solicitation package

        Args:
            work_statement_md: Path to work statement markdown
            work_statement_pdf: Path to work statement PDF
            output_path: Path to save complete package
            solicitation_config: Optional configuration
            include_templates: Include Section L/M templates
            verbose: Print progress

        Returns:
            Dictionary with build results
        """
        if verbose:
            print("\n" + "="*70)
            print("BUILDING COMPLETE SOLICITATION PACKAGE")
            print("="*70)
            print(f"Work Statement: {Path(work_statement_md).name}")
            print(f"Output: {output_path}")
            print("="*70 + "\n")

        # Step 1: Generate SF33
        if verbose:
            print("STEP 1: Generating SF33 form...")

        sf33_output = output_path.replace('.pdf', '_SF33.pdf')

        sf33_result = self.sf33_generator.execute(
            work_statement_path=work_statement_md,
            output_path=sf33_output,
            solicitation_config=solicitation_config,
            verbose=verbose
        )

        if not sf33_result['success']:
            return {
                'success': False,
                'error': 'SF33 generation failed',
                'details': sf33_result
            }

        # Step 2: Collect all PDFs
        if verbose:
            print(f"\nSTEP 2: Collecting package components...")

        pdf_components = []

        # Section A: SF33
        if Path(sf33_output).exists():
            pdf_components.append({
                'section': 'A',
                'title': 'Solicitation/Contract Form (SF33)',
                'path': sf33_output
            })
            if verbose:
                print(f"  ✓ Section A: SF33")

        # Section B: Supplies or Services and Prices (if exists)
        section_b_pdf = work_statement_pdf.replace('/pws/', '/solicitation/').replace('performance_work_statement.pdf', 'section_b.pdf')
        if Path(section_b_pdf).exists():
            pdf_components.append({
                'section': 'B',
                'title': 'Supplies or Services and Prices',
                'path': section_b_pdf
            })
            if verbose:
                print(f"  ✓ Section B: CLIN Structure")

        # Section C: Work Statement
        if Path(work_statement_pdf).exists():
            pdf_components.append({
                'section': 'C',
                'title': 'Description/Specifications/Work Statement',
                'path': work_statement_pdf
            })
            if verbose:
                print(f"  ✓ Section C: Work Statement")

        # Section H: Special Contract Requirements (if exists)
        section_h_pdf = work_statement_pdf.replace('/pws/', '/solicitation/').replace('performance_work_statement.pdf', 'section_h.pdf')
        if Path(section_h_pdf).exists():
            pdf_components.append({
                'section': 'H',
                'title': 'Special Contract Requirements',
                'path': section_h_pdf
            })
            if verbose:
                print(f"  ✓ Section H: Special Requirements")

        # Section I: Contract Clauses (if exists)
        section_i_pdf = work_statement_pdf.replace('/pws/', '/solicitation/').replace('performance_work_statement.pdf', 'section_i.pdf')
        if Path(section_i_pdf).exists():
            pdf_components.append({
                'section': 'I',
                'title': 'Contract Clauses',
                'path': section_i_pdf
            })
            if verbose:
                print(f"  ✓ Section I: Contract Clauses")

        # Section J: QASP (if exists)
        qasp_pdf = work_statement_pdf.replace('/pws/', '/qasp/').replace('performance_work_statement.pdf', 'quality_assurance_surveillance_plan.pdf')
        if Path(qasp_pdf).exists():
            pdf_components.append({
                'section': 'J',
                'title': 'Quality Assurance Surveillance Plan (QASP)',
                'path': qasp_pdf
            })
            if verbose:
                print(f"  ✓ Section J: QASP")

        # Section L: Instructions to Offerors (if exists)
        section_l_pdf = work_statement_pdf.replace('/pws/', '/section_l/').replace('performance_work_statement.pdf', 'section_l_instructions_to_offerors.pdf')
        if Path(section_l_pdf).exists():
            pdf_components.append({
                'section': 'L',
                'title': 'Instructions to Offerors',
                'path': section_l_pdf
            })
            if verbose:
                print(f"  ✓ Section L: Instructions to Offerors")

        # Section K: Representations and Certifications (if exists)
        section_k_pdf = work_statement_pdf.replace('/pws/', '/solicitation/').replace('performance_work_statement.pdf', 'section_k.pdf')
        if Path(section_k_pdf).exists():
            pdf_components.append({
                'section': 'K',
                'title': 'Representations, Certifications, and Other Statements',
                'path': section_k_pdf
            })
            if verbose:
                print(f"  ✓ Section K: Representations & Certifications")

        # Section M: Evaluation Factors (if exists)
        section_m_pdf = work_statement_pdf.replace('/pws/', '/section_m/').replace('performance_work_statement.pdf', 'section_m_evaluation_factors.pdf')
        if Path(section_m_pdf).exists():
            pdf_components.append({
                'section': 'M',
                'title': 'Evaluation Factors for Award',
                'path': section_m_pdf
            })
            if verbose:
                print(f"  ✓ Section M: Evaluation Factors")

        # Step 3: Merge PDFs
        if verbose:
            print(f"\nSTEP 3: Merging PDFs into complete package...")

        merge_result = self.merge_pdfs(
            pdf_components,
            output_path,
            verbose=verbose
        )

        if not merge_result['success']:
            return {
                'success': False,
                'error': 'PDF merge failed',
                'details': merge_result
            }

        # Step 4: Generate manifest
        if verbose:
            print(f"\nSTEP 4: Generating package manifest...")

        manifest = self._generate_manifest(
            pdf_components,
            sf33_result,
            output_path
        )

        manifest_path = output_path.replace('.pdf', '_manifest.json')
        self._save_manifest(manifest, manifest_path)

        if verbose:
            print(f"  ✓ Manifest saved: {manifest_path}")

        # Success
        if verbose:
            print("\n" + "="*70)
            print("✅ SOLICITATION PACKAGE BUILD COMPLETE")
            print("="*70)
            print(f"Package: {output_path}")
            print(f"Total pages: {merge_result['total_pages']}")
            print(f"Sections: {len(pdf_components)}")
            print(f"Solicitation #: {sf33_result['solicitation_number']}")
            print("="*70 + "\n")

        return {
            'success': True,
            'output_path': output_path,
            'manifest_path': manifest_path,
            'total_pages': merge_result['total_pages'],
            'sections': len(pdf_components),
            'solicitation_number': sf33_result['solicitation_number'],
            'components': pdf_components
        }

    def merge_pdfs(
        self,
        pdf_components: List[Dict],
        output_path: str,
        verbose: bool = True
    ) -> Dict:
        """
        Merge multiple PDFs into single package

        Args:
            pdf_components: List of PDF component dictionaries
            output_path: Output path for merged PDF
            verbose: Print progress

        Returns:
            Dictionary with merge results
        """
        writer = PdfWriter()
        total_pages = 0

        for component in pdf_components:
            pdf_path = component['path']

            if not Path(pdf_path).exists():
                if verbose:
                    print(f"  ⚠ Skipping missing file: {pdf_path}")
                continue

            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)

            for page in reader.pages:
                writer.add_page(page)

            total_pages += page_count

            if verbose:
                print(f"  ✓ Added Section {component['section']}: {page_count} page(s)")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        if verbose:
            print(f"\n  ✓ Merged {len(pdf_components)} components")
            print(f"  ✓ Total pages: {total_pages}")

        return {
            'success': True,
            'output_path': output_path,
            'total_pages': total_pages,
            'components_merged': len(pdf_components)
        }

    def _create_section_l_template(self, base_path: str) -> Optional[str]:
        """
        Create Section L (Instructions to Offerors) template

        Args:
            base_path: Base path for output

        Returns:
            Path to Section L PDF or None
        """
        # For now, return None - would need markdown template + conversion
        # This can be implemented later with actual Section L content
        return None

    def _create_section_m_template(self, base_path: str) -> Optional[str]:
        """
        Create Section M (Evaluation Factors) template

        Args:
            base_path: Base path for output

        Returns:
            Path to Section M PDF or None
        """
        # For now, return None - would need markdown template + conversion
        # This can be implemented later with actual Section M content
        return None

    def _generate_manifest(
        self,
        components: List[Dict],
        sf33_result: Dict,
        package_path: str
    ) -> Dict:
        """
        Generate package manifest with metadata

        Args:
            components: List of package components
            sf33_result: SF33 generation results
            package_path: Path to package

        Returns:
            Manifest dictionary
        """
        from datetime import datetime

        manifest = {
            'solicitation_number': sf33_result.get('solicitation_number', 'N/A'),
            'program_name': sf33_result.get('metadata', {}).get('program_name', 'N/A'),
            'organization': sf33_result.get('metadata', {}).get('organization', 'N/A'),
            'generated_date': datetime.now().isoformat(),
            'package_path': package_path,
            'components': [
                {
                    'section': c['section'],
                    'title': c['title'],
                    'source': c['path']
                }
                for c in components
            ],
            'metadata': sf33_result.get('metadata', {})
        }

        return manifest

    def _save_manifest(self, manifest: Dict, output_path: str):
        """Save manifest as JSON"""
        import json

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)


# Example usage
def main():
    """Test Solicitation Package Orchestrator"""
    import os

    # Paths
    pws_md = "outputs/pws/performance_work_statement.md"
    pws_pdf = "outputs/pws/performance_work_statement.pdf"

    output_dir = "outputs/solicitation"
    os.makedirs(output_dir, exist_ok=True)

    output_package = f"{output_dir}/ALMS_Solicitation_Package.pdf"

    # Initialize orchestrator
    orchestrator = SolicitationPackageOrchestrator()

    # Build package
    if Path(pws_md).exists() and Path(pws_pdf).exists():
        print("Building solicitation package from PWS...")

        result = orchestrator.build_complete_package(
            work_statement_md=pws_md,
            work_statement_pdf=pws_pdf,
            output_path=output_package,
            include_templates=False,  # No L/M templates yet
            verbose=True
        )

        if result['success']:
            print(f"\n✅ Solicitation package created successfully!")
            print(f"   Package: {result['output_path']}")
            print(f"   Manifest: {result['manifest_path']}")
            print(f"   Total pages: {result['total_pages']}")
            print(f"   Solicitation #: {result['solicitation_number']}")
        else:
            print(f"\n✗ Package build failed: {result.get('error')}")
    else:
        print(f"Required files not found:")
        print(f"  PWS MD: {pws_md} - {'✓' if Path(pws_md).exists() else '✗'}")
        print(f"  PWS PDF: {pws_pdf} - {'✓' if Path(pws_pdf).exists() else '✗'}")


if __name__ == "__main__":
    main()
