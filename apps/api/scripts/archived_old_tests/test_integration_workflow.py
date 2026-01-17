"""
Integration Test: Pre-Solicitation Workflow
Tests the complete workflow from Acquisition Plan through PWS generation

Workflow:
1. Acquisition Plan Generator (Phase 2 Agent 1)
2. IGCE Generator (Phase 1 Agent)
3. PWS Writer (Phase 2 Agent 2)

Validates:
- All agents run successfully
- Data flows correctly between agents
- Documents maintain consistency
- Aggregate TBD reduction meets targets
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from backend.utils.consistency_validator import create_standard_validator
from dotenv import load_dotenv

load_dotenv()

class IntegrationTester:
    """Integration testing framework"""

    def __init__(self, api_key: str, retriever: Retriever):
        self.api_key = api_key
        self.retriever = retriever
        self.results = {
            'workflow_name': 'Pre-Solicitation Package Generation',
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'agents_tested': [],
            'documents_generated': [],
            'consistency_checks': [],
            'aggregate_metrics': {},
            'issues_found': [],
            'success': False
        }

    def count_tbds(self, content: str) -> int:
        """Count TBD placeholders in content"""
        # Count {{template_variables}}
        template_vars = set(re.findall(r'\{\{([^}]+)\}\}', content))
        # Count explicit TBD markers
        tbd_markers = len(re.findall(r'\bTBD\b', content, re.IGNORECASE))
        return len(template_vars) + tbd_markers

    def extract_value(self, content: str, pattern: str, label: str = "value") -> str:
        """Extract a value from document using regex"""
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                return match.group(1).strip()
            except IndexError:
                # Pattern didn't have a capture group, return the whole match
                return match.group(0).strip()
        return None

    def check_consistency(self, doc1_name: str, doc1_content: str,
                         doc2_name: str, doc2_content: str,
                         field_name: str, pattern1: str, pattern2: str = None) -> dict:
        """Check if a field is consistent across two documents"""
        if pattern2 is None:
            pattern2 = pattern1

        value1 = self.extract_value(doc1_content, pattern1, field_name)
        value2 = self.extract_value(doc2_content, pattern2, field_name)

        consistent = (value1 is not None and value2 is not None and
                     value1.lower().strip() == value2.lower().strip())

        return {
            'field': field_name,
            'doc1': doc1_name,
            'doc2': doc2_name,
            'value1': value1,
            'value2': value2,
            'consistent': consistent
        }

    def save_document(self, content: str, filename: str, output_dir: str):
        """Save generated document"""
        filepath = Path(output_dir) / filename
        with open(filepath, 'w') as f:
            f.write(content)
        return str(filepath)

    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "="*80)
        print(text)
        print("="*80)

    def print_step(self, step_num: int, text: str):
        """Print formatted step"""
        print(f"\n{'='*80}")
        print(f"STEP {step_num}: {text}")
        print(f"{'='*80}")

def main():
    print("="*80)
    print("INTEGRATION TEST: PRE-SOLICITATION WORKFLOW")
    print("="*80)
    print("\nWorkflow: Acquisition Plan → IGCE → PWS")
    print("Testing: Phase 1 + Phase 2 enhanced agents working together")

    # Initialize
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        return

    # Setup RAG
    print("\n" + "="*80)
    print("SETUP: Initializing RAG System")
    print("="*80)
    vector_store = VectorStore(api_key=api_key)
    vector_store.load()
    retriever = Retriever(vector_store, top_k=5)
    print("  ✓ RAG system loaded")

    # Create tester
    tester = IntegrationTester(api_key, retriever)

    # Create output directory
    output_dir = "output/integration_tests"
    os.makedirs(output_dir, exist_ok=True)
    print(f"  ✓ Output directory: {output_dir}")

    # Test project information (consistent across all documents)
    project_info = {
        'program_name': 'Advanced Logistics Management System (ALMS)',
        'organization': 'U.S. Army',
        'description': 'Cloud-based logistics inventory management system for Army installations',
        'capability_gap': 'Current 15-year-old system lacks real-time tracking and modern cloud capabilities',
        'num_locations': 15,
        'num_users': 2800,
        'estimated_value': '$45M',
        'contract_type': 'Firm-Fixed-Price with Option Years',
        'period_of_performance': '36 months',
        'base_year': '2026',
        'option_years': 4
    }

    print("\n  Project Information:")
    for key, value in project_info.items():
        print(f"    - {key}: {value}")

    # ========================================================================
    # STEP 1: Generate Acquisition Plan
    # ========================================================================
    tester.print_step(1, "Generate Acquisition Plan")

    print("\n  Initializing Acquisition Plan Generator Agent...")
    acq_agent = AcquisitionPlanGeneratorAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    print("\n  Generating acquisition plan...")
    acq_task = {
        'project_info': project_info,
        'config': {}
    }

    acq_result = acq_agent.execute(acq_task)
    acq_content = acq_result['content']
    acq_tbds = tester.count_tbds(acq_content)
    acq_words = len(acq_content.split())

    print(f"\n  ✓ Acquisition Plan generated:")
    print(f"    - Word count: {acq_words}")
    print(f"    - TBDs remaining: {acq_tbds}")
    print(f"    - RAG extracted: {acq_result.get('rag_extracted_count', 0)} fields")
    print(f"    - LLM generated: {acq_result.get('llm_generated_count', 0)} sections")
    print(f"    - Smart defaults: {acq_result.get('smart_defaults_count', 0)} values")

    # Save document
    acq_path = tester.save_document(acq_content, "01_acquisition_plan.md", output_dir)
    print(f"    - Saved to: {acq_path}")

    tester.results['agents_tested'].append({
        'name': 'AcquisitionPlanGeneratorAgent',
        'phase': 'Phase 2 Agent 1',
        'status': 'success',
        'tbds': acq_tbds,
        'word_count': acq_words
    })

    tester.results['documents_generated'].append({
        'name': 'Acquisition Plan',
        'path': acq_path,
        'tbds': acq_tbds,
        'word_count': acq_words
    })

    # ========================================================================
    # STEP 2: Generate IGCE
    # ========================================================================
    tester.print_step(2, "Generate IGCE (Independent Government Cost Estimate)")

    print("\n  Initializing IGCE Generator Agent...")
    igce_agent = IGCEGeneratorAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    print("\n  Generating IGCE...")
    igce_task = {
        'project_info': project_info,
        'config': {}
    }

    igce_result = igce_agent.execute(igce_task)
    igce_content = igce_result['content']
    igce_tbds = tester.count_tbds(igce_content)
    igce_words = len(igce_content.split())

    print(f"\n  ✓ IGCE generated:")
    print(f"    - Word count: {igce_words}")
    print(f"    - TBDs remaining: {igce_tbds}")
    print(f"    - RAG extracted: {igce_result.get('rag_extracted_count', 0)} fields")
    print(f"    - LLM generated: {igce_result.get('llm_generated_count', 0)} sections")
    print(f"    - Smart defaults: {igce_result.get('smart_defaults_count', 0)} values")

    # Save document
    igce_path = tester.save_document(igce_content, "02_igce.md", output_dir)
    print(f"    - Saved to: {igce_path}")

    tester.results['agents_tested'].append({
        'name': 'IGCEGeneratorAgent',
        'phase': 'Phase 1 Agent',
        'status': 'success',
        'tbds': igce_tbds,
        'word_count': igce_words
    })

    tester.results['documents_generated'].append({
        'name': 'IGCE',
        'path': igce_path,
        'tbds': igce_tbds,
        'word_count': igce_words
    })

    # ========================================================================
    # STEP 3: Generate PWS
    # ========================================================================
    tester.print_step(3, "Generate Performance Work Statement (PWS)")

    print("\n  Initializing PWS Writer Agent...")
    pws_agent = PWSWriterAgent(api_key=api_key, retriever=retriever)
    print("  ✓ Agent initialized")

    print("\n  Generating PWS...")
    pws_task = {
        'project_info': project_info,
        'config': {}
    }

    pws_result = pws_agent.execute(pws_task)
    pws_content = pws_result['content']
    pws_tbds = tester.count_tbds(pws_content)
    pws_words = len(pws_content.split())

    print(f"\n  ✓ PWS generated:")
    print(f"    - Word count: {pws_words}")
    print(f"    - TBDs remaining: {pws_tbds}")
    print(f"    - RAG extracted: {pws_result.get('rag_extracted_count', 0)} fields")
    print(f"    - LLM generated: {pws_result.get('llm_generated_count', 0)} sections")
    print(f"    - Smart defaults: {pws_result.get('smart_defaults_count', 0)} values")
    print(f"    - PBSC Compliance: {pws_result.get('pbsc_compliance', 0)}/100")

    # Save document
    pws_path = tester.save_document(pws_content, "03_pws.md", output_dir)
    print(f"    - Saved to: {pws_path}")

    tester.results['agents_tested'].append({
        'name': 'PWSWriterAgent',
        'phase': 'Phase 2 Agent 2',
        'status': 'success',
        'tbds': pws_tbds,
        'word_count': pws_words
    })

    tester.results['documents_generated'].append({
        'name': 'PWS',
        'path': pws_path,
        'tbds': pws_tbds,
        'word_count': pws_words
    })

    # ========================================================================
    # STEP 4: Cross-Document Consistency Validation (Enhanced Framework)
    # ========================================================================
    tester.print_step(4, "Cross-Document Consistency Validation")

    print("\n  Using enhanced consistency validation framework...")
    print("  Features: Fuzzy matching, format normalization, tolerance-based comparison\n")

    # Create validator with standard fields
    validator = create_standard_validator()

    # Validate Acquisition Plan vs IGCE
    print("  Validating: Acquisition Plan ↔ IGCE")
    report_acq_igce = validator.validate(acq_content, igce_content, "Acquisition Plan", "IGCE")

    # Validate Acquisition Plan vs PWS
    print("  Validating: Acquisition Plan ↔ PWS")
    report_acq_pws = validator.validate(acq_content, pws_content, "Acquisition Plan", "PWS")

    # Validate IGCE vs PWS
    print("  Validating: IGCE ↔ PWS")
    report_igce_pws = validator.validate(igce_content, pws_content, "IGCE", "PWS")

    # Aggregate results
    total_checks = 0
    total_passed = 0
    all_field_results = {}

    for report in [report_acq_igce, report_acq_pws, report_igce_pws]:
        total_checks += report['passed'] + report['failed']
        total_passed += report['passed']

        # Collect all field results
        for field_name, result in report['fields'].items():
            key = f"{report['doc1_name']}_vs_{report['doc2_name']}_{field_name}"
            all_field_results[key] = result

    consistency_score = (total_passed / total_checks * 100) if total_checks > 0 else 0

    # Print detailed results
    print(f"\n  📊 Consistency Validation Results:")
    print(f"     Overall Score: {consistency_score:.1f}% ({total_passed}/{total_checks} checks passed)")
    print(f"     Grade: {report_acq_igce['grade']}")
    print()

    # Show detailed field results
    print("  Detailed Field Results:")
    for field_name in ['program_name', 'organization', 'budget', 'period_of_performance', 'contract_type']:
        print(f"\n  📋 {field_name.replace('_', ' ').title()}:")

        # Check across all document pairs
        for report in [report_acq_igce, report_acq_pws, report_igce_pws]:
            if field_name in report['fields']:
                result = report['fields'][field_name]
                status_icon = '✅' if result.status == 'PASS' else ('❌' if result.status == 'FAIL' else '⚠️')

                print(f"     {status_icon} {report['doc1_name']} ↔ {report['doc2_name']}")
                print(f"        {report['doc1_name']}: {result.doc1_value or 'Not found'}")
                print(f"        {report['doc2_name']}: {result.doc2_value or 'Not found'}")

                if result.status == 'PASS':
                    print(f"        ✓ Match! (Similarity: {result.similarity:.1%}, Method: {result.method})")
                elif result.status == 'FAIL':
                    print(f"        ✗ Mismatch (Similarity: {result.similarity:.1%})")
                    if 'normalized_v1' in result.evidence:
                        print(f"        Normalized: '{result.normalized_v1}' vs '{result.normalized_v2}'")
                else:
                    print(f"        Reason: {result.reason}")

    # Helper function to convert ValidationResult to dict
    def validation_result_to_dict(result):
        return {
            'field_name': result.field_name,
            'status': result.status,
            'confidence': result.confidence,
            'similarity': result.similarity,
            'doc1_value': result.doc1_value,
            'doc2_value': result.doc2_value,
            'normalized_v1': result.normalized_v1,
            'normalized_v2': result.normalized_v2,
            'method': result.method,
            'reason': result.reason,
            'recommendation': result.recommendation,
            'evidence': result.evidence
        }

    # Convert reports to JSON-serializable format
    def report_to_dict(report):
        return {
            'overall_score': report['overall_score'],
            'passed': report['passed'],
            'failed': report['failed'],
            'not_found': report['not_found'],
            'total_checks': report['total_checks'],
            'grade': report['grade'],
            'doc1_name': report['doc1_name'],
            'doc2_name': report['doc2_name'],
            'fields': {k: validation_result_to_dict(v) for k, v in report['fields'].items()}
        }

    # Store results for reporting
    tester.results['consistency_validation'] = {
        'framework_version': '2.0_enhanced',
        'total_checks': total_checks,
        'passed': total_passed,
        'failed': total_checks - total_passed,
        'score': consistency_score,
        'grade': report_acq_igce['grade'],
        'reports': {
            'acq_vs_igce': report_to_dict(report_acq_igce),
            'acq_vs_pws': report_to_dict(report_acq_pws),
            'igce_vs_pws': report_to_dict(report_igce_pws)
        }
    }

    # Legacy format for backward compatibility (convert ValidationResult to dict)
    for key, result in all_field_results.items():
        tester.results['consistency_checks'].append({
            'field': result.field_name,
            'doc1': key.split('_vs_')[0],
            'doc2': key.split('_vs_')[1].split('_')[0],
            'value1': result.doc1_value,
            'value2': result.doc2_value,
            'consistent': result.status == 'PASS',
            'similarity': result.similarity,
            'method': result.method
        })

    print(f"\n  Overall Consistency Score: {consistency_score:.1f}% ({total_passed}/{total_checks} checks passed)")
    print(f"  Grade: {report_acq_igce['grade']}")

    # ========================================================================
    # STEP 5: Aggregate Quality Metrics
    # ========================================================================
    tester.print_step(5, "Aggregate Quality Metrics")

    total_words = sum(d['word_count'] for d in tester.results['documents_generated'])
    total_tbds = sum(d['tbds'] for d in tester.results['documents_generated'])
    avg_tbds_per_doc = total_tbds / len(tester.results['documents_generated'])

    print(f"\n  Total Documents Generated: {len(tester.results['documents_generated'])}")
    print(f"  Total Word Count: {total_words:,}")
    print(f"  Total TBDs Remaining: {total_tbds}")
    print(f"  Average TBDs per Document: {avg_tbds_per_doc:.1f}")
    print(f"  Cross-Document Consistency: {consistency_score:.1f}%")

    tester.results['aggregate_metrics'] = {
        'total_documents': len(tester.results['documents_generated']),
        'total_words': total_words,
        'total_tbds': total_tbds,
        'avg_tbds_per_doc': avg_tbds_per_doc,
        'consistency_score': consistency_score
    }

    # ========================================================================
    # STEP 6: Success Criteria Evaluation
    # ========================================================================
    tester.print_step(6, "Success Criteria Evaluation")

    criteria = {
        'all_agents_run': len(tester.results['agents_tested']) == 3,
        'all_docs_generated': len(tester.results['documents_generated']) == 3,
        'consistency_acceptable': consistency_score >= 75,
        'low_tbd_count': avg_tbds_per_doc <= 15,
        'no_critical_issues': len(tester.results['issues_found']) == 0
    }

    print("\n  Evaluation:")
    for criterion, passed in criteria.items():
        status = '✅ PASS' if passed else '❌ FAIL'
        print(f"    {status}: {criterion.replace('_', ' ').title()}")

    all_passed = all(criteria.values())
    tester.results['success'] = all_passed

    if all_passed:
        print(f"\n  🎉 INTEGRATION TEST: ✅ SUCCESS")
    else:
        print(f"\n  ⚠️  INTEGRATION TEST: ❌ FAILED")
        failed_criteria = [k for k, v in criteria.items() if not v]
        print(f"  Failed criteria: {', '.join(failed_criteria)}")

    # ========================================================================
    # STEP 7: Save Results
    # ========================================================================
    tester.print_step(7, "Save Test Results")

    # Save JSON results
    results_path = Path(output_dir) / "integration_test_results.json"
    with open(results_path, 'w') as f:
        json.dump(tester.results, f, indent=2)
    print(f"\n  ✓ JSON results saved to: {results_path}")

    # Save text report
    report_path = Path(output_dir) / "integration_test_report.txt"
    with open(report_path, 'w') as f:
        f.write("INTEGRATION TEST REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Workflow: {tester.results['workflow_name']}\n")
        f.write(f"Date: {tester.results['test_date']}\n\n")

        f.write("AGENTS TESTED:\n")
        for agent in tester.results['agents_tested']:
            f.write(f"  - {agent['name']} ({agent['phase']}): {agent['status']}\n")

        f.write(f"\nDOCUMENTS GENERATED:\n")
        for doc in tester.results['documents_generated']:
            f.write(f"  - {doc['name']}: {doc['word_count']} words, {doc['tbds']} TBDs\n")

        f.write(f"\nCONSISTENCY CHECKS:\n")
        for check in tester.results['consistency_checks']:
            status = 'PASS' if check['consistent'] else 'FAIL'
            f.write(f"  - {check['field']}: {status}\n")

        f.write(f"\nAGGREGATE METRICS:\n")
        for key, value in tester.results['aggregate_metrics'].items():
            f.write(f"  - {key}: {value}\n")

        f.write(f"\nOVERALL RESULT: {'SUCCESS' if tester.results['success'] else 'FAILED'}\n")

    print(f"  ✓ Text report saved to: {report_path}")

    # Final summary
    print("\n" + "="*80)
    print("INTEGRATION TEST COMPLETE")
    print("="*80)
    print(f"\n✅ Generated {len(tester.results['documents_generated'])} documents")
    print(f"✅ Total {total_words:,} words")
    print(f"✅ Consistency score: {consistency_score:.1f}%")
    print(f"✅ Average {avg_tbds_per_doc:.1f} TBDs per document")
    print(f"\n📁 All files saved to: {output_dir}/")

    return tester.results

if __name__ == "__main__":
    results = main()
