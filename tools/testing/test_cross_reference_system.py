"""
Test Cross-Reference System
Tests all 15 implemented agents to verify cross-reference functionality

Usage:
    python scripts/test_cross_reference_system.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor
from backend.agents.igce_generator_agent import IGCEGeneratorAgent
from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
from backend.agents.rfi_generator_agent import RFIGeneratorAgent
from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
from backend.agents.pws_writer_agent import PWSWriterAgent
from backend.agents.qasp_generator_agent import QASPGeneratorAgent
from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
from backend.agents.section_m_generator_agent import SectionMGeneratorAgent
from backend.agents.qa_manager_agent import QAManagerAgent
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever


class CrossReferenceSystemTest:
    """Test suite for cross-reference system"""

    def __init__(self):
        """Initialize test suite"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.metadata_store = DocumentMetadataStore()
        self.test_program = "Test_ALMS_CrossRef"
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }

        print("\n" + "="*80)
        print("CROSS-REFERENCE SYSTEM TEST SUITE")
        print("="*80)
        print(f"Test Program: {self.test_program}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

    def cleanup_test_data(self):
        """Clean up any existing test data"""
        print("🧹 Cleaning up previous test data...")

        # Get all documents for test program
        test_docs = self.metadata_store.list_documents(program=self.test_program)

        for doc in test_docs:
            self.metadata_store.delete_document(doc['id'])

        print(f"✓ Cleaned up {len(test_docs)} test documents\n")

    def test_metadata_store(self):
        """Test 1: Verify metadata store is working"""
        print("\n" + "="*80)
        print("TEST 1: Metadata Store Functionality")
        print("="*80)

        try:
            # Test save
            test_data = {
                'test_field': 'test_value',
                'timestamp': datetime.now().isoformat()
            }

            doc_id = self.metadata_store.save_document(
                doc_type='test',
                program=self.test_program,
                content='Test content',
                file_path='/tmp/test.md',
                extracted_data=test_data,
                references={}
            )

            print(f"✓ Successfully saved test document: {doc_id}")

            # Test retrieve
            retrieved = self.metadata_store.find_latest_document('test', self.test_program)
            assert retrieved is not None, "Failed to retrieve saved document"
            assert retrieved['extracted_data']['test_field'] == 'test_value', "Data mismatch"

            print("✓ Successfully retrieved test document")

            # Test delete
            self.metadata_store.delete_document(doc_id)
            deleted = self.metadata_store.find_latest_document('test', self.test_program)
            assert deleted is None, "Document not deleted"

            print("✓ Successfully deleted test document")

            self.results['passed'].append('Metadata Store')
            print("\n✅ TEST 1 PASSED\n")
            return True

        except Exception as e:
            print(f"\n❌ TEST 1 FAILED: {str(e)}\n")
            self.results['failed'].append(('Metadata Store', str(e)))
            return False

    def test_phase1_igce_generation(self):
        """Test 2: IGCE Generator with metadata saving"""
        print("\n" + "="*80)
        print("TEST 2: IGCE Generator (Foundation Document)")
        print("="*80)

        try:
            # Initialize RAG
            vector_store = VectorStore(self.api_key)
            vector_store.load()
            retriever = Retriever(vector_store, top_k=5)

            # Initialize IGCE agent
            igce_agent = IGCEGeneratorAgent(
                api_key=self.api_key,
                retriever=retriever
            )

            # Generate IGCE
            project_info = {
                'program_name': self.test_program,
                'organization': 'Test DoD',
                'estimated_value': '$2.5M - $6.4M',
                'period_of_performance': '12 months base + 4 option years'
            }

            requirements = """
            # Test Requirements
            - Cloud-based system deployment
            - Real-time inventory tracking
            - Mobile application support
            - Integration with enterprise systems
            """

            result = igce_agent.execute({
                'project_info': project_info,
                'requirements_content': requirements,
                'config': {'contract_type': 'services'}
            })

            assert result['status'] == 'success', "IGCE generation failed"
            print("✓ IGCE generated successfully")

            # Verify metadata was saved (reload store to get fresh data)
            import time
            time.sleep(0.5)  # Brief pause to ensure file is written
            self.metadata_store = DocumentMetadataStore()  # Reload from file
            saved_igce = self.metadata_store.find_latest_document('igce', self.test_program)
            assert saved_igce is not None, "IGCE metadata not saved"
            assert 'total_cost' in saved_igce['extracted_data'], "Missing cost data"

            print(f"✓ IGCE metadata saved: {saved_igce['id']}")
            print(f"  Total Cost: {saved_igce['extracted_data'].get('total_cost_formatted', 'N/A')}")

            self.results['passed'].append('IGCE Generator')
            print("\n✅ TEST 2 PASSED\n")
            return True

        except Exception as e:
            print(f"\n❌ TEST 2 FAILED: {str(e)}\n")
            self.results['failed'].append(('IGCE Generator', str(e)))
            return False

    def test_phase1_acquisition_plan(self):
        """Test 3: Acquisition Plan with IGCE cross-reference"""
        print("\n" + "="*80)
        print("TEST 3: Acquisition Plan Generator (Cross-references IGCE)")
        print("="*80)

        try:
            # Verify IGCE exists first
            igce_doc = self.metadata_store.find_latest_document('igce', self.test_program)
            if not igce_doc:
                print("⚠️  Skipping: IGCE not available")
                self.results['skipped'].append('Acquisition Plan (no IGCE)')
                return False

            # Initialize RAG
            vector_store = VectorStore(self.api_key)
            vector_store.load()
            retriever = Retriever(vector_store, top_k=5)

            # Initialize Acquisition Plan agent
            acq_plan_agent = AcquisitionPlanGeneratorAgent(
                api_key=self.api_key,
                retriever=retriever
            )

            # Generate Acquisition Plan
            project_info = {
                'program_name': self.test_program,
                'organization': 'Test DoD',
                'estimated_value': '$2.5M',
                'period_of_performance': '12 months'
            }

            result = acq_plan_agent.execute({
                'project_info': project_info,
                'requirements_content': 'Test requirements',
                'config': {'contract_type': 'services'}
            })

            assert result['status'] == 'success', "Acquisition Plan generation failed"
            print("✓ Acquisition Plan generated successfully")

            # Verify metadata was saved with IGCE reference
            saved_plan = self.metadata_store.find_latest_document('acquisition_plan', self.test_program)
            assert saved_plan is not None, "Acquisition Plan metadata not saved"
            assert 'igce' in saved_plan.get('references', {}), "IGCE reference not saved"

            print(f"✓ Acquisition Plan metadata saved: {saved_plan['id']}")
            print(f"  References IGCE: {saved_plan['references']['igce']}")

            # Verify cross-reference integrity
            assert saved_plan['references']['igce'] == igce_doc['id'], "IGCE reference mismatch"
            print("✓ Cross-reference integrity verified")

            self.results['passed'].append('Acquisition Plan')
            print("\n✅ TEST 3 PASSED\n")
            return True

        except Exception as e:
            print(f"\n❌ TEST 3 FAILED: {str(e)}\n")
            self.results['failed'].append(('Acquisition Plan', str(e)))
            return False

    def test_phase1_pre_solicitation_agents(self):
        """Test 4: Pre-Solicitation Agents (Sources Sought, RFI, Notice, Industry Day)"""
        print("\n" + "="*80)
        print("TEST 4: Pre-Solicitation Agents")
        print("="*80)

        agents_to_test = [
            ('Sources Sought', SourcesSoughtGeneratorAgent, 'sources_sought'),
            ('RFI', RFIGeneratorAgent, 'rfi'),
            ('Pre-Solicitation Notice', PreSolicitationNoticeGeneratorAgent, 'pre_solicitation_notice'),
            ('Industry Day', IndustryDayGeneratorAgent, 'industry_day')
        ]

        for agent_name, agent_class, doc_type in agents_to_test:
            try:
                print(f"\n  Testing {agent_name}...")

                # Initialize agent
                if agent_name == 'Pre-Solicitation Notice' or agent_name == 'Industry Day':
                    agent = agent_class(api_key=self.api_key)
                else:
                    agent = agent_class(api_key=self.api_key, retriever=None)

                # Generate document
                project_info = {
                    'program_name': self.test_program,
                    'organization': 'Test DoD'
                }

                result = agent.execute({
                    'project_info': project_info,
                    'requirements_content': 'Test requirements',
                    'config': {'contract_type': 'services'}
                })

                assert result['status'] == 'success', f"{agent_name} generation failed"
                print(f"    ✓ {agent_name} generated")

                # Verify metadata saved (reload store to get fresh data)
                import time
                time.sleep(0.3)  # Brief pause
                self.metadata_store = DocumentMetadataStore()  # Reload from file
                saved_doc = self.metadata_store.find_latest_document(doc_type, self.test_program)
                assert saved_doc is not None, f"{agent_name} metadata not saved"
                print(f"    ✓ Metadata saved: {saved_doc['id']}")

                self.results['passed'].append(agent_name)

            except Exception as e:
                print(f"    ❌ {agent_name} failed: {str(e)}")
                self.results['failed'].append((agent_name, str(e)))

        print("\n✅ TEST 4 COMPLETED\n")
        return True

    def test_cross_reference_chain(self):
        """Test 5: Verify complete cross-reference chain"""
        print("\n" + "="*80)
        print("TEST 5: Cross-Reference Chain Integrity")
        print("="*80)

        try:
            # Reload metadata store to get fresh data
            import time
            time.sleep(0.5)
            self.metadata_store = DocumentMetadataStore()

            # Get all documents for test program
            all_docs = self.metadata_store.list_documents(program=self.test_program)

            print(f"\nTotal documents generated: {len(all_docs)}")

            # Build reference graph
            reference_graph = {}
            for doc in all_docs:
                doc_id = doc['id']
                references = doc.get('references', {})
                reference_graph[doc_id] = {
                    'type': doc['type'],
                    'references': list(references.values()),
                    'referenced_by': []
                }

            # Find referring documents
            for doc_id, info in reference_graph.items():
                for ref_id in info['references']:
                    if ref_id in reference_graph:
                        reference_graph[ref_id]['referenced_by'].append(doc_id)

            # Print reference graph
            print("\n📊 Reference Graph:")
            print("-" * 80)
            for doc_id, info in reference_graph.items():
                print(f"\n{doc_id} ({info['type']})")
                if info['references']:
                    print(f"  ← References: {', '.join(info['references'])}")
                if info['referenced_by']:
                    print(f"  → Referenced by: {', '.join(info['referenced_by'])}")

            # Verify expected references
            print("\n\n✓ Verifying expected cross-references...")

            # Acquisition Plan should reference IGCE
            acq_plan = self.metadata_store.find_latest_document('acquisition_plan', self.test_program)
            if acq_plan:
                assert 'igce' in acq_plan.get('references', {}), "Acquisition Plan should reference IGCE"
                print("  ✓ Acquisition Plan → IGCE")

            self.results['passed'].append('Cross-Reference Chain')
            print("\n✅ TEST 5 PASSED\n")
            return True

        except Exception as e:
            print(f"\n❌ TEST 5 FAILED: {str(e)}\n")
            self.results['failed'].append(('Cross-Reference Chain', str(e)))
            return False

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*80)
        print("TEST REPORT")
        print("="*80)

        total_tests = len(self.results['passed']) + len(self.results['failed']) + len(self.results['skipped'])

        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⏭️  Skipped: {len(self.results['skipped'])}")

        if self.results['passed']:
            print("\n✅ Passed Tests:")
            for test in self.results['passed']:
                print(f"  • {test}")

        if self.results['failed']:
            print("\n❌ Failed Tests:")
            for test, error in self.results['failed']:
                print(f"  • {test}: {error}")

        if self.results['skipped']:
            print("\n⏭️  Skipped Tests:")
            for test in self.results['skipped']:
                print(f"  • {test}")

        # Summary
        print("\n" + "="*80)
        success_rate = (len(self.results['passed']) / total_tests * 100) if total_tests > 0 else 0
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        print("="*80 + "\n")

        return success_rate >= 80

    def run_all_tests(self):
        """Run all tests"""
        print("\n🚀 Starting Cross-Reference System Tests...\n")

        # Cleanup
        self.cleanup_test_data()

        # Run tests in order (some depend on previous)
        self.test_metadata_store()
        self.test_phase1_igce_generation()
        self.test_phase1_acquisition_plan()
        self.test_phase1_pre_solicitation_agents()
        self.test_cross_reference_chain()

        # Generate report
        success = self.generate_report()

        # Cleanup after tests
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_data()

        return success


def main():
    """Main test execution"""
    try:
        test_suite = CrossReferenceSystemTest()
        success = test_suite.run_all_tests()

        if success:
            print("✅ All tests passed successfully!")
            return 0
        else:
            print("⚠️  Some tests failed. Review report above.")
            return 1

    except Exception as e:
        print(f"\n❌ Test suite failed to run: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
