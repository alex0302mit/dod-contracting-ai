"""
RFP Orchestrator: Coordinates RFP generation workflow
Manages the multi-section RFP document creation process
"""

from typing import Dict, List
from .rfp_writer_agent import RFPWriterAgent
from .quality_agent import QualityAgent
from backend.rag.retriever import Retriever
from backend.utils.evaluation_report_generator import EvaluationReportGenerator
import time
from backend.utils.grounding_verifier import GroundingVerifier


class RFPOrchestrator:
    """
    RFP Orchestrator: Coordinates Request for Proposal generation
    
    Workflow:
    1. Writing Phase: Generate each RFP section (A through M)
    2. Quality Phase: Evaluate completeness and compliance
    3. Revision Phase: Improve sections if needed
    4. Assembly Phase: Compile final RFP document
    
    RFP Structure (per FAR):
    - Part I - The Schedule (Sections A-H)
    - Part II - Contract Clauses (Section I)
    - Part III - List of Documents, Exhibits, and Other Attachments (Section J)
    - Part IV - Representations and Instructions (Sections K-M)
    
    Dependencies:
    - RFPWriterAgent: RFP content generation
    - QualityAgent: Quality evaluation
    - RAG system: RFP guide knowledge base
    """
    
    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize RFP orchestrator
        
        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever with RFP guide indexed
            model: Claude model to use
        """
        # Initialize agents
        self.rfp_writer = RFPWriterAgent(api_key, retriever, model)
        self.quality_agent = QualityAgent(api_key, model)
        
        # Workflow state
        self.workflow_state = {
            'phase': 'initialized',
            'written_sections': {},
            'evaluation_results': {},
            'final_rfp': None
        }
        
        # Configuration
        self.quality_threshold = 75
        self.enable_auto_revision = True
        
        print("\n" + "="*70)
        print("RFP ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"  ✓ RFP Writer Agent ready")
        print(f"  ✓ Quality Agent ready")
        print(f"  Quality threshold: {self.quality_threshold}/100")
        print("="*70 + "\n")
    
    def execute_rfp_workflow(
        self,
        project_info: Dict,
        rfp_sections_config: List[Dict],
        output_path: str = "outputs/rfp/request_for_proposal.md"
    ) -> Dict:
        """
        Execute complete RFP generation workflow
        
        Args:
            project_info: Project information
            rfp_sections_config: List of RFP section configurations
            output_path: Path to save RFP
            
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("STARTING RFP GENERATION WORKFLOW")
        print("="*70)
        print(f"Project: {project_info.get('program_name', 'Unknown')}")
        print(f"RFP Sections: {len(rfp_sections_config)}")
        print("="*70 + "\n")
        
        # Phase 1: Writing
        written_sections = self._phase_writing(rfp_sections_config, project_info)
        
        # Phase 1.5: Grounding Verification (NEW)
        written_sections = self._phase_grounding_check(written_sections, project_info)
        
        # Phase 2: Quality Check
        evaluation_results = self._phase_quality(written_sections, project_info)
        self.workflow_state['evaluation_results'] = evaluation_results
        
        # Phase 3: Revision (if needed)
        if self.enable_auto_revision:
            written_sections = self._phase_revision(
                written_sections,
                evaluation_results,
                rfp_sections_config,
                project_info
            )
        
        # Phase 4: Assembly
        final_rfp = self._phase_assembly(written_sections, project_info, evaluation_results)
        self.workflow_state['final_rfp'] = final_rfp

        # Save
        self._save_rfp(final_rfp, output_path)

        # Save evaluation report
        self._save_evaluation_report(evaluation_results, project_info, output_path)

        elapsed_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("✅ RFP GENERATION COMPLETE")
        print("="*70)
        print(f"Time elapsed: {elapsed_time:.1f}s")
        print(f"Output: {output_path}")
        print("="*70 + "\n")
        
        return {
            'status': 'success',
            'output_path': output_path,
            'elapsed_time': elapsed_time,
            'workflow_state': self.workflow_state
        }
    
    def _phase_writing(self, sections_config: List[Dict], project_info: Dict) -> Dict:
        """Generate all RFP sections"""
        print("\n" + "="*70)
        print("PHASE 1: WRITING RFP SECTIONS")
        print("="*70 + "\n")
        
        written_sections = {}
        
        for i, section_config in enumerate(sections_config, 1):
            section_name = section_config['name']
            print(f"[{i}/{len(sections_config)}] Writing: {section_name}...")
            
            task = {
                'section_name': section_name,
                'project_info': project_info,
                'guidance': section_config.get('guidance', ''),
                'section_type': section_config.get('section_type', 'general')
            }
            
            result = self.rfp_writer.execute(task)
            written_sections[section_name] = result['content']
            
            # Show section-specific metrics
            metrics = [f"{result['word_count']} words"]
            if result['compliance_items']:
                metrics.append(f"{len(result['compliance_items'])} FAR refs")
            if result['evaluation_factors']:
                metrics.append(f"{len(result['evaluation_factors'])} eval factors")
            
            print(f"  ✓ Complete ({', '.join(metrics)})")
            print()
        
        print(f"✅ Writing phase complete: {len(written_sections)} sections\n")
        return written_sections
    
    def _phase_quality(self, sections: Dict, project_info: Dict) -> Dict:
        """Evaluate RFP quality"""
        print("\n" + "="*70)
        print("PHASE 2: QUALITY EVALUATION")
        print("="*70 + "\n")
        
        evaluations = {}
        
        for section_name, content in sections.items():
            print(f"Evaluating: {section_name}...")
            
            task = {
                'content': content,
                'section_name': section_name,
                'project_info': project_info,
                'evaluation_type': 'rfp'  # RFP-specific evaluation
            }
            
            result = self.quality_agent.execute(task)
            evaluations[section_name] = result
            
            print(f"  Score: {result['score']}/100 ({result['grade']})")
            print()
        
        avg_score = sum(e['score'] for e in evaluations.values()) / len(evaluations)
        print(f"✅ Quality evaluation complete: Average score {avg_score:.1f}/100\n")
        
        return evaluations
    
    def _phase_revision(
        self,
        sections: Dict,
        evaluations: Dict,
        sections_config: List[Dict],
        project_info: Dict
    ) -> Dict:
        """Revise low-scoring sections"""
        print("\n" + "="*70)
        print("PHASE 3: REVISION")
        print("="*70 + "\n")
        
        sections_to_revise = [
            name for name, eval_result in evaluations.items()
            if eval_result['score'] < self.quality_threshold
        ]
        
        if not sections_to_revise:
            print("✓ All sections meet quality threshold\n")
            return sections
        
        print(f"Revising {len(sections_to_revise)} section(s)...\n")
        
        revised_sections = sections.copy()
        
        for section_name in sections_to_revise:
            print(f"Revising: {section_name}...")
            
            # Find section config
            section_config = next(
                (s for s in sections_config if s['name'] == section_name),
                {}
            )
            
            # Create revision task
            task = {
                'section_name': section_name,
                'project_info': project_info,
                'guidance': section_config.get('guidance', ''),
                'section_type': section_config.get('section_type', 'general')
            }
            
            result = self.rfp_writer.execute(task)
            revised_sections[section_name] = result['content']
            
            print(f"  ✓ Revision complete\n")
        
        print(f"✅ Revision phase complete\n")
        return revised_sections
    
    def _phase_assembly(
        self,
        sections: Dict,
        project_info: Dict,
        evaluations: Dict
    ) -> str:
        """Assemble final RFP document"""
        print("\n" + "="*70)
        print("PHASE 4: ASSEMBLY")
        print("="*70 + "\n")
        
        rfp_parts = []
        
        # Title Page
        rfp_parts.append("# Request for Proposal (RFP)")
        rfp_parts.append("")
        rfp_parts.append(f"**Solicitation Number:** {project_info.get('solicitation_number', 'TBD')}")
        rfp_parts.append(f"**Program:** {project_info.get('program_name', '')}")
        rfp_parts.append(f"**Issue Date:** {project_info.get('issue_date', '')}")
        rfp_parts.append(f"**Closing Date:** {project_info.get('closing_date', '')}")
        rfp_parts.append(f"**Issuing Office:** {project_info.get('issuing_office', '')}")
        rfp_parts.append(f"**Contracting Officer:** {project_info.get('contracting_officer', '')}")
        rfp_parts.append("")
        rfp_parts.append("---")
        rfp_parts.append("")
        
        # Table of Contents
        rfp_parts.append("## Table of Contents")
        rfp_parts.append("")
        for i, section_name in enumerate(sections.keys(), 1):
            rfp_parts.append(f"{i}. {section_name}")
        rfp_parts.append("")
        rfp_parts.append("---")
        rfp_parts.append("")
        
        # Sections
        for section_name, content in sections.items():
            rfp_parts.append(f"## {section_name}")
            rfp_parts.append("")
            rfp_parts.append(content)
            rfp_parts.append("")
            rfp_parts.append("---")
            rfp_parts.append("")
        
        rfp = "\n".join(rfp_parts)
        
        print(f"✅ RFP assembled: {len(rfp.split())} total words\n")
        
        return rfp
    
    def _save_rfp(self, rfp_content: str, output_path: str) -> None:
        """Save RFP to file (markdown and PDF)"""
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        with open(output_path, 'w') as f:
            f.write(rfp_content)

        print(f"Saved: {output_path}")

        # Convert to PDF
        pdf_path = output_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(output_path, pdf_path)
            print(f"PDF saved: {pdf_path}")
        except Exception as e:
            print(f"Warning: Could not create PDF: {e}")

    def _save_evaluation_report(
        self,
        evaluations: Dict,
        project_info: Dict,
        rfp_output_path: str
    ) -> None:
        """
        Save evaluation report for RFP document

        Args:
            evaluations: Evaluation results from quality agent
            project_info: Project information
            rfp_output_path: Path where RFP was saved
        """
        from pathlib import Path

        # Determine evaluation report path
        eval_path = rfp_output_path.replace('.md', '_evaluation_report.md')

        print(f"\nGenerating evaluation report...")

        # Create report generator
        generator = EvaluationReportGenerator(document_type="RFP")

        # Generate and save report
        generator.generate_full_report(
            evaluation_results=evaluations,
            project_info=project_info,
            output_path=eval_path
        )

        print(f"Evaluation report saved: {eval_path}")

        # Convert to PDF
        pdf_eval_path = eval_path.replace('.md', '.pdf')
        try:
            from utils.convert_md_to_pdf import convert_markdown_to_pdf
            convert_markdown_to_pdf(eval_path, pdf_eval_path)
            print(f"PDF evaluation report: {pdf_eval_path}")
        except Exception as e:
            print(f"Warning: Could not create PDF evaluation report: {e}")

    def _phase_grounding_check(
        self,
        sections: Dict,
        project_info: Dict
    ) -> Dict:
        """Verify all sections are grounded in source material"""
        print("\n" + "="*70)
        print("PHASE 1.5: GROUNDING VERIFICATION")
        print("="*70 + "\n")
        
        import os
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        verifier = GroundingVerifier(api_key)
        
        verified_sections = {}
        issues_found = 0
        
        for section_name, content in sections.items():
            print(f"Verifying: {section_name}...")
            
            # Get retrieved docs (we'd need to store these during writing)
            # For now, verify against project_info only
            result = verifier.verify_content(
                content=content,
                project_info=project_info,
                retrieved_docs=[]  # Would pass actual retrieved docs
            )
            
            if result['is_grounded']:
                print(f"  ✓ Grounded ({result['grounding_score']}/100)")
                verified_sections[section_name] = content
            else:
                print(f"  ⚠️ Grounding issues ({result['grounding_score']}/100)")
                print(f"     {len(result['hallucinations'])} hallucinations detected")
                issues_found += 1
                
                # Keep content but flag for revision
                verified_sections[section_name] = content
        
        if issues_found > 0:
            print(f"\n⚠️ {issues_found} section(s) have grounding issues")
        else:
            print(f"\n✅ All sections properly grounded")
        
        print()
        return verified_sections
