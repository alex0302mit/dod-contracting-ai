"""
Document Processor: Post-processes generated documents with enhancements

Enhances agent outputs with:
- PDF generation from markdown
- Quality evaluation reports
- Citations to source documents

Uses existing utilities without modifying agent code (least intrusive approach).

Dependencies:
- utils/convert_md_to_pdf.py: PDF generation
- agents/quality_agent.py: Quality evaluation
- utils/evaluation_report_generator.py: Evaluation report formatting
- utils/document_metadata_store.py: Citation tracking
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import existing utilities
from backend.utils.convert_md_to_pdf import convert_markdown_to_pdf
from backend.utils.convert_md_to_docx import convert_markdown_to_docx  # Word document generation
from backend.agents.quality_agent import QualityAgent
from backend.utils.evaluation_report_generator import EvaluationReportGenerator
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.progressive_refinement_orchestrator import ProgressiveRefinementOrchestrator


class DocumentProcessor:
    """
    Post-processes agent-generated documents with enhancements

    Features:
    1. PDF generation from markdown
    2. Quality evaluation with scoring
    3. Citation injection for source documents
    4. Metadata tracking

    Design: Wrapper pattern - doesn't modify agent code
    """

    def __init__(
        self,
        api_key: str,
        enable_progressive_refinement: bool = True,
        quality_threshold: int = 85,
        max_refinement_iterations: int = 2
    ):
        """
        Initialize document processor

        Args:
            api_key: Anthropic API key for quality agent
            enable_progressive_refinement: Enable automatic refinement loop (default: True)
            quality_threshold: Target quality score for refinement (default: 85)
            max_refinement_iterations: Max refinement iterations (default: 2)
        """
        self.api_key = api_key
        self.quality_agent = QualityAgent(api_key=api_key)
        self.metadata_store = DocumentMetadataStore()

        # Progressive refinement configuration
        self.enable_progressive_refinement = enable_progressive_refinement
        self.quality_threshold = quality_threshold
        self.max_refinement_iterations = max_refinement_iterations

        # Initialize refinement orchestrator if enabled
        if self.enable_progressive_refinement:
            self.refinement_orchestrator = ProgressiveRefinementOrchestrator(
                api_key=api_key,
                quality_threshold=quality_threshold,
                max_iterations=max_refinement_iterations
            )

    def process_document(
        self,
        content: str,
        output_path: str,
        doc_type: str,
        program_name: str,
        source_docs: Optional[List[str]] = None,
        project_info: Optional[Dict] = None,
        generate_pdf: bool = True,
        generate_docx: bool = False,  # NEW: Generate Word document (default: False, configurable)
        generate_evaluation: bool = True,
        add_citations: bool = True,
        apply_progressive_refinement: bool = None
    ) -> Dict:
        """
        Process a generated document with enhancements

        Args:
            content: Generated markdown content
            output_path: Path to save markdown file
            doc_type: Document type (e.g., 'igce', 'pws', 'rfi')
            program_name: Program name for metadata
            source_docs: List of source document filenames (for citations)
            project_info: Project information dict (for evaluation)
            generate_pdf: Generate PDF version (default: True)
            generate_docx: Generate Word document version (default: False, configurable)
            generate_evaluation: Generate quality evaluation report (default: True)
            add_citations: Add source document citations (default: True)
            apply_progressive_refinement: Apply progressive refinement loop (default: uses global setting)

        Returns:
            Dictionary with:
                - markdown_path: Path to saved markdown file
                - pdf_path: Path to PDF (if generated)
                - docx_path: Path to Word document (if generated)
                - evaluation_path: Path to evaluation markdown (if generated)
                - evaluation_pdf_path: Path to evaluation PDF (if generated)
                - citations_added: Number of citations added
                - quality_score: Quality score (if evaluation generated)
                - refinement_applied: Whether progressive refinement was applied
                - refinement_improvement: Score improvement from refinement (if applied)
                - refinement_iterations: Number of refinement iterations (if applied)
        """
        # Determine if progressive refinement should be applied
        if apply_progressive_refinement is None:
            apply_progressive_refinement = self.enable_progressive_refinement

        results = {
            'markdown_path': str(output_path),
            'pdf_path': None,
            'docx_path': None,  # NEW: Word document path
            'evaluation_path': None,
            'evaluation_pdf_path': None,
            'citations_added': 0,
            'quality_score': None,
            'refinement_applied': False,
            'refinement_improvement': 0,
            'refinement_iterations': 0
        }

        # Step 1: Progressive Refinement (if enabled)
        if apply_progressive_refinement and hasattr(self, 'refinement_orchestrator'):
            try:
                print(f"\n🔄 Progressive Refinement enabled for {doc_type}")

                refinement_result = self.refinement_orchestrator.refine_until_quality_met(
                    content=content,
                    section_name=doc_type.upper(),
                    doc_type=doc_type,
                    project_info=project_info or {},
                    research_findings={}
                )

                # Use refined content
                content = refinement_result['final_content']
                results['quality_score'] = refinement_result['final_score']
                results['refinement_applied'] = refinement_result['refinement_applied']
                results['refinement_improvement'] = refinement_result['improvement']
                results['refinement_iterations'] = refinement_result['iterations_used']

                # Generate refinement report
                output_path_obj = Path(output_path)
                refinement_report_path = output_path_obj.parent / f"{output_path_obj.stem}_refinement_report.md"
                self.refinement_orchestrator.generate_refinement_report(
                    refinement_result,
                    str(refinement_report_path)
                )
                print(f"   📄 Refinement report: {refinement_report_path.name}")

            except Exception as e:
                print(f"  ⚠️  Progressive refinement failed: {e}")
                print(f"  Continuing with original content...")

        # Step 2: Add citations to content (if enabled)
        if add_citations and source_docs:
            content, citations_count = self._add_citations(content, source_docs, program_name)
            results['citations_added'] = citations_count

        # Step 3: Save updated markdown content
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Step 4: Generate PDF (if enabled)
        if generate_pdf:
            try:
                pdf_path = self._generate_pdf(content, output_path)
                results['pdf_path'] = str(pdf_path)
            except Exception as e:
                print(f"  ⚠️  PDF generation failed: {e}")
        
        # Step 4.5: Generate Word document (if enabled)
        # Dependencies: python-docx>=1.1.0
        if generate_docx:
            try:
                docx_path = self._generate_docx(content, output_path, program_name)
                results['docx_path'] = str(docx_path)
            except Exception as e:
                print(f"  ⚠️  Word document generation failed: {e}")

        # Step 5: Generate quality evaluation (if enabled and not already done by refinement)
        if generate_evaluation and not results['refinement_applied']:
            try:
                eval_path, eval_pdf_path, quality_score = self._generate_evaluation(
                    content=content,
                    output_path=output_path,
                    doc_type=doc_type,
                    program_name=program_name,
                    project_info=project_info or {}
                )
                results['evaluation_path'] = str(eval_path)
                results['evaluation_pdf_path'] = str(eval_pdf_path) if eval_pdf_path else None
                results['quality_score'] = quality_score
            except Exception as e:
                print(f"  ⚠️  Evaluation generation failed: {e}")

        return results

    def _add_citations(
        self,
        content: str,
        source_docs: List[str],
        program_name: str
    ) -> tuple[str, int]:
        """
        Add citations section to document footer

        Args:
            content: Document content
            source_docs: List of source document filenames
            program_name: Program name

        Returns:
            Tuple of (updated_content, citations_count)
        """
        # Build citations section
        citation_lines = [
            "",
            "---",
            "",
            "## References and Source Documents",
            "",
            "This document was generated using the following source materials:",
            ""
        ]

        for i, doc_name in enumerate(source_docs, 1):
            # Extract readable name from filename
            display_name = self._format_doc_name(doc_name)
            citation_lines.append(f"{i}. **{display_name}**")
            citation_lines.append(f"   - Document: `{doc_name}`")
            citation_lines.append(f"   - Used for: Program requirements, specifications, and source data")
            citation_lines.append("")

        # Add generation metadata
        citation_lines.extend([
            "---",
            "",
            f"*Generated by DoD Acquisition Automation System*  ",
            f"*Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  ",
            f"*Program: {program_name}*",
            ""
        ])

        citations_text = '\n'.join(citation_lines)
        updated_content = content + '\n' + citations_text

        return updated_content, len(source_docs)

    def _format_doc_name(self, filename: str) -> str:
        """
        Format document filename to readable name

        Args:
            filename: Document filename

        Returns:
            Formatted readable name
        """
        # Remove path and extension
        name = Path(filename).stem

        # Common acronyms and names
        replacements = {
            'alms': 'ALMS',
            'kpp': 'KPP',
            'ksa': 'KSA',
            'cdd': 'Capability Development Document',
            'rfp': 'RFP',
            'rfi': 'RFI',
            'pws': 'PWS',
            'sow': 'SOW',
            'igce': 'IGCE',
            'far': 'FAR',
            'dfars': 'DFARS'
        }

        # Replace underscores and dashes with spaces
        name = name.replace('_', ' ').replace('-', ' ')

        # Apply replacements
        for old, new in replacements.items():
            name = name.replace(old, new)

        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def _generate_pdf(self, content: str, markdown_path: str) -> Path:
        """
        Generate PDF from markdown content

        Args:
            content: Markdown content
            markdown_path: Path to markdown file

        Returns:
            Path to generated PDF
        """
        # Determine PDF path (same name, .pdf extension)
        md_path = Path(markdown_path)
        pdf_path = md_path.parent / f"{md_path.stem}.pdf"

        # Use existing PDF converter
        convert_markdown_to_pdf(str(md_path), str(pdf_path))

        return pdf_path
    
    def _generate_docx(self, content: str, markdown_path: str, program_name: str) -> Path:
        """
        Generate Word document from markdown content
        
        Args:
            content: Markdown content
            markdown_path: Path to markdown file
            program_name: Program name for metadata
        
        Returns:
            Path to generated Word document
        
        Dependencies:
            - python-docx>=1.1.0: Word document creation and manipulation
        
        Features:
            - AI-generated section markers
            - Track changes enabled
            - Document metadata (author, title, subject)
            - Professional formatting
        """
        # Determine Word document path (same name, .docx extension)
        md_path = Path(markdown_path)
        docx_path = md_path.parent / f"{md_path.stem}.docx"
        
        # Use Word converter utility
        convert_markdown_to_docx(str(md_path), str(docx_path), program_name=program_name)
        
        return docx_path

    def _generate_evaluation(
        self,
        content: str,
        output_path: str,
        doc_type: str,
        program_name: str,
        project_info: Dict
    ) -> tuple[Path, Optional[Path], int]:
        """
        Generate quality evaluation report

        Args:
            content: Document content
            output_path: Original document path
            doc_type: Document type
            program_name: Program name
            project_info: Project information

        Returns:
            Tuple of (eval_markdown_path, eval_pdf_path, quality_score)
        """
        # Run quality evaluation
        evaluation_task = {
            'content': content,
            'section_name': doc_type.upper(),
            'project_info': {
                'program_name': program_name,
                **project_info
            },
            'research_findings': {},
            'evaluation_type': 'full'
        }

        evaluation_result = self.quality_agent.execute(evaluation_task)

        # Generate evaluation report
        output_path_obj = Path(output_path)
        eval_path = output_path_obj.parent / f"{output_path_obj.stem}_evaluation.md"

        # Build evaluation report content
        report_generator = EvaluationReportGenerator(document_type=doc_type.upper())

        # Format evaluation results for report generator
        formatted_results = {
            doc_type.upper(): evaluation_result
        }

        report_generator.generate_full_report(
            evaluation_results=formatted_results,
            project_info={'program_name': program_name, **project_info},
            output_path=str(eval_path)
        )

        # Generate PDF of evaluation report
        eval_pdf_path = None
        try:
            eval_pdf_path = output_path_obj.parent / f"{output_path_obj.stem}_evaluation.pdf"
            convert_markdown_to_pdf(str(eval_path), str(eval_pdf_path))
        except Exception as e:
            print(f"  ⚠️  Evaluation PDF generation failed: {e}")

        quality_score = evaluation_result.get('score', 0)

        return eval_path, eval_pdf_path, quality_score

    def process_batch(
        self,
        documents: List[Dict],
        generate_pdf: bool = True,
        generate_docx: bool = False,  # NEW: Generate Word documents (configurable)
        generate_evaluation: bool = True,
        add_citations: bool = True
    ) -> List[Dict]:
        """
        Process multiple documents in batch

        Args:
            documents: List of document dicts with keys:
                - content: Document content
                - output_path: Save path
                - doc_type: Document type
                - program_name: Program name
                - source_docs: Source documents (optional)
                - project_info: Project info (optional)
            generate_pdf: Generate PDFs
            generate_docx: Generate Word documents (default: False, configurable)
            generate_evaluation: Generate evaluations
            add_citations: Add citations

        Returns:
            List of processing results
        """
        results = []

        for i, doc in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] Processing {doc['doc_type']}...")

            result = self.process_document(
                content=doc['content'],
                output_path=doc['output_path'],
                doc_type=doc['doc_type'],
                program_name=doc['program_name'],
                source_docs=doc.get('source_docs'),
                project_info=doc.get('project_info'),
                generate_pdf=generate_pdf,
                generate_docx=generate_docx,  # NEW: Pass Word generation flag
                generate_evaluation=generate_evaluation,
                add_citations=add_citations
            )

            results.append({
                'doc_type': doc['doc_type'],
                'output_path': doc['output_path'],
                **result
            })

            # Print summary
            print(f"  ✅ Markdown: {result['markdown_path']}")
            if result['pdf_path']:
                print(f"  ✅ PDF: {result['pdf_path']}")
            if result['docx_path']:
                print(f"  ✅ DOCX: {result['docx_path']}")
            if result['evaluation_path']:
                print(f"  📊 Evaluation: {result['evaluation_path']} (Score: {result['quality_score']}/100)")
            if result['citations_added'] > 0:
                print(f"  📚 Citations: {result['citations_added']} source documents")

        return results

    def generate_summary_report(
        self,
        batch_results: List[Dict],
        output_path: str
    ) -> str:
        """
        Generate summary report for batch processing

        Args:
            batch_results: Results from process_batch
            output_path: Path to save summary report

        Returns:
            Path to summary report
        """
        lines = [
            "# Document Processing Summary Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Documents Processed:** {len(batch_results)}",
            "",
            "---",
            "",
            "## Processing Results",
            "",
            "| Document Type | Quality Score | PDF | Evaluation | Citations |",
            "|---------------|---------------|-----|------------|-----------|"
        ]

        total_score = 0
        pdf_count = 0
        eval_count = 0
        citation_count = 0

        for result in batch_results:
            doc_type = result['doc_type'].upper()
            score = result.get('quality_score', 'N/A')
            pdf_status = "✅" if result.get('pdf_path') else "❌"
            eval_status = "✅" if result.get('evaluation_path') else "❌"
            citations = result.get('citations_added', 0)

            lines.append(f"| {doc_type} | {score}/100 | {pdf_status} | {eval_status} | {citations} |")

            if isinstance(score, (int, float)):
                total_score += score
            if result.get('pdf_path'):
                pdf_count += 1
            if result.get('evaluation_path'):
                eval_count += 1
            if citations > 0:
                citation_count += 1

        avg_score = total_score / len(batch_results) if batch_results else 0

        lines.extend([
            "",
            "---",
            "",
            "## Summary Statistics",
            "",
            f"- **Average Quality Score:** {avg_score:.1f}/100",
            f"- **PDFs Generated:** {pdf_count}/{len(batch_results)}",
            f"- **Evaluations Generated:** {eval_count}/{len(batch_results)}",
            f"- **Documents with Citations:** {citation_count}/{len(batch_results)}",
            "",
            "---",
            "",
            "## Quality Analysis",
            ""
        ])

        # Categorize by quality
        excellent = [r for r in batch_results if r.get('quality_score', 0) >= 90]
        good = [r for r in batch_results if 80 <= r.get('quality_score', 0) < 90]
        acceptable = [r for r in batch_results if 70 <= r.get('quality_score', 0) < 80]
        needs_improvement = [r for r in batch_results if r.get('quality_score', 0) < 70]

        lines.extend([
            f"- **Excellent (90-100):** {len(excellent)} documents",
            f"- **Good (80-89):** {len(good)} documents",
            f"- **Acceptable (70-79):** {len(acceptable)} documents",
            f"- **Needs Improvement (<70):** {len(needs_improvement)} documents",
            ""
        ])

        if needs_improvement:
            lines.extend([
                "### Documents Needing Improvement:",
                ""
            ])
            for result in needs_improvement:
                lines.append(f"- {result['doc_type'].upper()} (Score: {result.get('quality_score', 'N/A')}/100)")
            lines.append("")

        lines.extend([
            "---",
            "",
            "*This summary was generated automatically by the Document Processor.*",
            ""
        ])

        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return output_path


if __name__ == "__main__":
    import sys

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        DOCUMENT PROCESSOR UTILITY                          ║
║                                                                            ║
║  Post-processes generated documents with:                                 ║
║    - PDF generation                                                       ║
║    - Quality evaluation reports                                           ║
║    - Source document citations                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    print("Usage:")
    print("  from utils.document_processor import DocumentProcessor")
    print("  processor = DocumentProcessor(api_key='your-key')")
    print("  result = processor.process_document(...)")
    print("\nSee ENHANCEMENT_PLAN.md for integration examples.")
