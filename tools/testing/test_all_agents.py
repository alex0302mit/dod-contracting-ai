#!/usr/bin/env python3
"""
Agent Tests
===========

Comprehensive tests for all 40+ document generation agents organized by acquisition phase.

Phases:
- Pre-Solicitation (6 agents)
- Solicitation (15 agents)
- Post-Solicitation (3 agents)
- Award (3 agents)
- Supporting (4 agents)

Dependencies:
- test_config: TestConfig, TestResult, TestSuiteResults
- backend.agents.*: All agent classes
- dotenv: Environment variable loading

Usage:
    python test_all_agents.py [--phase PHASE] [--agent AGENT]
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from tools.testing.test_config import (
    TestConfig, TestResult, TestSuiteResults,
    TestStatus, TEST_PROJECT_INFO
)


class AgentTests:
    """
    Agent test suite
    
    Tests all 40+ document generation agents with proper
    initialization, execution, and output validation.
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.api_key = TestConfig.ANTHROPIC_API_KEY
        self.results = TestSuiteResults(suite_name="Agent Tests")
        self.program_name = f"AGENT_TEST_{int(time.time())}"
        
        # Standard project info for all agents
        self.project_info = {
            **TEST_PROJECT_INFO,
            'program_name': self.program_name
        }
        
        # Standard solicitation info
        self.solicitation_info = {
            'program_name': self.program_name,
            'solicitation_number': f'TEST-SOL-{int(time.time())}',
            'response_date': '2025-03-01',
            'contracting_office': 'U.S. Army Contracting Command'
        }
    
    def _test_agent(
        self,
        name: str,
        agent_class: type,
        task: Dict[str, Any],
        phase: str,
        validate_fn: Optional[callable] = None
    ) -> TestResult:
        """
        Test a single agent
        
        Args:
            name: Agent name for reporting
            agent_class: Agent class to instantiate
            task: Task dictionary to pass to execute()
            phase: Acquisition phase (pre_solicitation, solicitation, etc.)
            validate_fn: Optional validation function for output
            
        Returns:
            TestResult object
        """
        if not self.api_key:
            return TestResult(
                name=name,
                category=phase,
                status=TestStatus.SKIPPED,
                message="ANTHROPIC_API_KEY not set"
            )
        
        start_time = time.time()
        try:
            # Initialize agent
            agent = agent_class(api_key=self.api_key)
            
            # Execute task
            result = agent.execute(task)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Validate result
            if result is None:
                return TestResult(
                    name=name,
                    category=phase,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    message="Agent returned None"
                )
            
            # Check for required fields
            if isinstance(result, dict):
                has_content = 'content' in result or 'sections' in result or 'document' in result
                if not has_content:
                    return TestResult(
                        name=name,
                        category=phase,
                        status=TestStatus.FAILED,
                        duration_ms=duration_ms,
                        message=f"Missing content in result: {list(result.keys())}"
                    )
            
            # Run custom validation if provided
            if validate_fn and not validate_fn(result):
                return TestResult(
                    name=name,
                    category=phase,
                    status=TestStatus.FAILED,
                    duration_ms=duration_ms,
                    message="Custom validation failed"
                )
            
            return TestResult(
                name=name,
                category=phase,
                status=TestStatus.PASSED,
                duration_ms=duration_ms,
                message="Agent executed successfully",
                details={'result_keys': list(result.keys()) if isinstance(result, dict) else str(type(result))}
            )
            
        except ImportError as e:
            return TestResult(
                name=name,
                category=phase,
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Import error: {str(e)}"
            )
        except Exception as e:
            return TestResult(
                name=name,
                category=phase,
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Execution error: {str(e)}"
            )
    
    # =========================================================================
    # PRE-SOLICITATION AGENTS (6)
    # =========================================================================
    
    def test_sources_sought_agent(self) -> TestResult:
        """Test Sources Sought Generator Agent"""
        from backend.agents.sources_sought_generator_agent import SourcesSoughtGeneratorAgent
        return self._test_agent(
            name="Sources Sought Generator",
            agent_class=SourcesSoughtGeneratorAgent,
            task={
                'solicitation_info': self.solicitation_info,
                'project_info': self.project_info
            },
            phase="pre_solicitation"
        )
    
    def test_rfi_agent(self) -> TestResult:
        """Test RFI Generator Agent"""
        from backend.agents.rfi_generator_agent import RFIGeneratorAgent
        return self._test_agent(
            name="RFI Generator",
            agent_class=RFIGeneratorAgent,
            task={
                'solicitation_info': self.solicitation_info,
                'project_info': self.project_info
            },
            phase="pre_solicitation"
        )
    
    def test_industry_day_agent(self) -> TestResult:
        """Test Industry Day Generator Agent"""
        from backend.agents.industry_day_generator_agent import IndustryDayGeneratorAgent
        return self._test_agent(
            name="Industry Day Generator",
            agent_class=IndustryDayGeneratorAgent,
            task={
                'solicitation_info': self.solicitation_info,
                'project_info': self.project_info,
                'event_date': '2025-02-15',
                'event_location': 'Pentagon Conference Room B'
            },
            phase="pre_solicitation"
        )
    
    def test_market_research_agent(self) -> TestResult:
        """Test Market Research Report Generator Agent"""
        from backend.agents.market_research_report_generator_agent import MarketResearchReportGeneratorAgent
        return self._test_agent(
            name="Market Research Report Generator",
            agent_class=MarketResearchReportGeneratorAgent,
            task={
                'project_info': self.project_info,
                'research_scope': 'Full market analysis'
            },
            phase="pre_solicitation"
        )
    
    def test_acquisition_plan_agent(self) -> TestResult:
        """Test Acquisition Plan Generator Agent"""
        from backend.agents.acquisition_plan_generator_agent import AcquisitionPlanGeneratorAgent
        return self._test_agent(
            name="Acquisition Plan Generator",
            agent_class=AcquisitionPlanGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="pre_solicitation"
        )
    
    def test_igce_agent(self) -> TestResult:
        """Test IGCE Generator Agent"""
        from backend.agents.igce_generator_agent import IGCEGeneratorAgent
        return self._test_agent(
            name="IGCE Generator",
            agent_class=IGCEGeneratorAgent,
            task={
                'project_info': self.project_info,
                'cost_elements': [
                    {'name': 'Labor', 'estimate': 1500000},
                    {'name': 'Materials', 'estimate': 500000},
                    {'name': 'Travel', 'estimate': 100000},
                    {'name': 'ODCs', 'estimate': 400000}
                ]
            },
            phase="pre_solicitation"
        )
    
    # =========================================================================
    # SOLICITATION AGENTS (15)
    # =========================================================================
    
    def test_pws_writer_agent(self) -> TestResult:
        """Test PWS Writer Agent"""
        from backend.agents.pws_writer_agent import PWSWriterAgent
        return self._test_agent(
            name="PWS Writer",
            agent_class=PWSWriterAgent,
            task={
                'project_info': self.project_info,
                'section_name': 'Scope of Work',
                'research_findings': {}
            },
            phase="solicitation"
        )
    
    def test_soo_writer_agent(self) -> TestResult:
        """Test SOO Writer Agent"""
        from backend.agents.soo_writer_agent import SOOWriterAgent
        return self._test_agent(
            name="SOO Writer",
            agent_class=SOOWriterAgent,
            task={
                'project_info': self.project_info,
                'section_name': 'Objectives',
                'research_findings': {}
            },
            phase="solicitation"
        )
    
    def test_sow_writer_agent(self) -> TestResult:
        """Test SOW Writer Agent"""
        from backend.agents.sow_writer_agent import SOWWriterAgent
        return self._test_agent(
            name="SOW Writer",
            agent_class=SOWWriterAgent,
            task={
                'project_info': self.project_info,
                'section_name': 'Work Requirements',
                'research_findings': {}
            },
            phase="solicitation"
        )
    
    def test_rfp_writer_agent(self) -> TestResult:
        """Test RFP Writer Agent"""
        from backend.agents.rfp_writer_agent import RFPWriterAgent
        return self._test_agent(
            name="RFP Writer",
            agent_class=RFPWriterAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'section_name': 'Instructions'
            },
            phase="solicitation"
        )
    
    def test_section_b_agent(self) -> TestResult:
        """Test Section B Generator Agent"""
        from backend.agents.section_b_generator_agent import SectionBGeneratorAgent
        return self._test_agent(
            name="Section B Generator",
            agent_class=SectionBGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_section_h_agent(self) -> TestResult:
        """Test Section H Generator Agent"""
        from backend.agents.section_h_generator_agent import SectionHGeneratorAgent
        return self._test_agent(
            name="Section H Generator",
            agent_class=SectionHGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_section_i_agent(self) -> TestResult:
        """Test Section I Generator Agent"""
        from backend.agents.section_i_generator_agent import SectionIGeneratorAgent
        return self._test_agent(
            name="Section I Generator",
            agent_class=SectionIGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_section_k_agent(self) -> TestResult:
        """Test Section K Generator Agent"""
        from backend.agents.section_k_generator_agent import SectionKGeneratorAgent
        return self._test_agent(
            name="Section K Generator",
            agent_class=SectionKGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_section_l_agent(self) -> TestResult:
        """Test Section L Generator Agent"""
        from backend.agents.section_l_generator_agent import SectionLGeneratorAgent
        return self._test_agent(
            name="Section L Generator",
            agent_class=SectionLGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_section_m_agent(self) -> TestResult:
        """Test Section M Generator Agent"""
        from backend.agents.section_m_generator_agent import SectionMGeneratorAgent
        return self._test_agent(
            name="Section M Generator",
            agent_class=SectionMGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_qasp_agent(self) -> TestResult:
        """Test QASP Generator Agent"""
        from backend.agents.qasp_generator_agent import QASPGeneratorAgent
        return self._test_agent(
            name="QASP Generator",
            agent_class=QASPGeneratorAgent,
            task={
                'project_info': self.project_info,
                'pws_content': 'Sample PWS content for QASP generation'
            },
            phase="solicitation"
        )
    
    def test_source_selection_plan_agent(self) -> TestResult:
        """Test Source Selection Plan Generator Agent"""
        from backend.agents.source_selection_plan_generator_agent import SourceSelectionPlanGeneratorAgent
        return self._test_agent(
            name="Source Selection Plan Generator",
            agent_class=SourceSelectionPlanGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'evaluation_factors': ['Technical', 'Past Performance', 'Price']
            },
            phase="solicitation"
        )
    
    def test_ssdd_agent(self) -> TestResult:
        """Test SSDD Generator Agent"""
        from backend.agents.ssdd_generator_agent import SSDDGeneratorAgent
        return self._test_agent(
            name="SSDD Generator",
            agent_class=SSDDGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    def test_sf26_agent(self) -> TestResult:
        """Test SF26 Generator Agent"""
        from backend.agents.sf26_generator_agent import SF26GeneratorAgent
        return self._test_agent(
            name="SF26 Generator",
            agent_class=SF26GeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'contract_info': {
                    'contract_number': 'TEST-CONTRACT-001',
                    'award_date': '2025-04-01'
                }
            },
            phase="solicitation"
        )
    
    def test_sf33_agent(self) -> TestResult:
        """Test SF33 Generator Agent"""
        from backend.agents.sf33_generator_agent import SF33GeneratorAgent
        return self._test_agent(
            name="SF33 Generator",
            agent_class=SF33GeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="solicitation"
        )
    
    # =========================================================================
    # POST-SOLICITATION AGENTS (3)
    # =========================================================================
    
    def test_evaluation_scorecard_agent(self) -> TestResult:
        """Test Evaluation Scorecard Generator Agent"""
        from backend.agents.evaluation_scorecard_generator_agent import EvaluationScorecardGeneratorAgent
        return self._test_agent(
            name="Evaluation Scorecard Generator",
            agent_class=EvaluationScorecardGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'offerors': [
                    {'name': 'Vendor A', 'proposal_date': '2025-03-01'},
                    {'name': 'Vendor B', 'proposal_date': '2025-03-01'}
                ]
            },
            phase="post_solicitation"
        )
    
    def test_ppq_agent(self) -> TestResult:
        """Test PPQ Generator Agent"""
        from backend.agents.ppq_generator_agent import PPQGeneratorAgent
        return self._test_agent(
            name="PPQ Generator",
            agent_class=PPQGeneratorAgent,
            task={
                'project_info': self.project_info,
                'vendor_info': {
                    'name': 'Test Vendor Corp',
                    'cage_code': '12345',
                    'duns': '123456789'
                }
            },
            phase="post_solicitation"
        )
    
    def test_debriefing_agent(self) -> TestResult:
        """Test Debriefing Generator Agent"""
        from backend.agents.debriefing_generator_agent import DebriefingGeneratorAgent
        return self._test_agent(
            name="Debriefing Generator",
            agent_class=DebriefingGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'offeror_info': {
                    'name': 'Unsuccessful Vendor Inc',
                    'proposal_score': 75
                },
                'award_info': {
                    'winner': 'Winning Vendor Corp',
                    'award_date': '2025-04-01'
                }
            },
            phase="post_solicitation"
        )
    
    # =========================================================================
    # AWARD AGENTS (3)
    # =========================================================================
    
    def test_award_notification_agent(self) -> TestResult:
        """Test Award Notification Generator Agent"""
        from backend.agents.award_notification_generator_agent import AwardNotificationGeneratorAgent
        return self._test_agent(
            name="Award Notification Generator",
            agent_class=AwardNotificationGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'award_info': {
                    'winner': 'Winning Vendor Corp',
                    'contract_value': '$2,500,000',
                    'award_date': '2025-04-01'
                }
            },
            phase="award"
        )
    
    def test_amendment_agent(self) -> TestResult:
        """Test Amendment Generator Agent"""
        from backend.agents.amendment_generator_agent import AmendmentGeneratorAgent
        return self._test_agent(
            name="Amendment Generator",
            agent_class=AmendmentGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info,
                'amendment_info': {
                    'amendment_number': '0001',
                    'reason': 'Extended response deadline',
                    'changes': ['Response date changed from 2025-03-01 to 2025-03-15']
                }
            },
            phase="award"
        )
    
    def test_pre_solicitation_notice_agent(self) -> TestResult:
        """Test Pre-Solicitation Notice Generator Agent"""
        from backend.agents.pre_solicitation_notice_generator_agent import PreSolicitationNoticeGeneratorAgent
        return self._test_agent(
            name="Pre-Solicitation Notice Generator",
            agent_class=PreSolicitationNoticeGeneratorAgent,
            task={
                'project_info': self.project_info,
                'solicitation_info': self.solicitation_info
            },
            phase="award"
        )
    
    # =========================================================================
    # SUPPORTING AGENTS (4)
    # =========================================================================
    
    def test_quality_agent(self) -> TestResult:
        """Test Quality Agent"""
        from backend.agents.quality_agent import QualityAgent
        
        if not self.api_key:
            return TestResult(
                name="Quality Agent",
                category="supporting",
                status=TestStatus.SKIPPED,
                message="ANTHROPIC_API_KEY not set"
            )
        
        start_time = time.time()
        try:
            agent = QualityAgent(api_key=self.api_key)
            result = agent.execute({
                'content': '''
                The Advanced Logistics Management System (ALMS) shall provide cloud-based 
                inventory tracking capabilities. Per FAR 10.001, market research has been 
                conducted to identify potential sources. (Ref: Market Research Report, 2025)
                
                The system shall integrate with existing DoD logistics systems IAW 
                DFARS 252.204-7012 cybersecurity requirements.
                ''',
                'section_name': 'Test Section',
                'project_info': self.project_info,
                'research_findings': {},
                'evaluation_type': 'section'
            })
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result and 'score' in result:
                return TestResult(
                    name="Quality Agent",
                    category="supporting",
                    status=TestStatus.PASSED,
                    duration_ms=duration_ms,
                    message=f"Score: {result['score']}, Grade: {result.get('grade', 'N/A')}",
                    details={'score': result['score'], 'grade': result.get('grade')}
                )
            return TestResult(
                name="Quality Agent",
                category="supporting",
                status=TestStatus.FAILED,
                duration_ms=duration_ms,
                message="Missing score in result"
            )
            
        except Exception as e:
            return TestResult(
                name="Quality Agent",
                category="supporting",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=str(e)
            )
    
    def test_research_agent(self) -> TestResult:
        """Test Research Agent"""
        from backend.agents.research_agent import ResearchAgent
        return self._test_agent(
            name="Research Agent",
            agent_class=ResearchAgent,
            task={
                'project_info': self.project_info,
                'research_topic': 'Cloud-based logistics management systems',
                'research_scope': 'Market analysis'
            },
            phase="supporting"
        )
    
    def test_refinement_agent(self) -> TestResult:
        """Test Refinement Agent"""
        from backend.agents.refinement_agent import RefinementAgent
        return self._test_agent(
            name="Refinement Agent",
            agent_class=RefinementAgent,
            task={
                'content': 'This is some sample content that needs refinement.',
                'feedback': 'Please improve clarity and add more specifics.',
                'project_info': self.project_info
            },
            phase="supporting"
        )
    
    def test_qa_manager_agent(self) -> TestResult:
        """Test QA Manager Agent"""
        from backend.agents.qa_manager_agent import QAManagerAgent
        return self._test_agent(
            name="QA Manager Agent",
            agent_class=QAManagerAgent,
            task={
                'documents': {
                    'PWS': 'Sample PWS content',
                    'SOW': 'Sample SOW content'
                },
                'project_info': self.project_info
            },
            phase="supporting"
        )
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all(self, phase: str = None, parallel: bool = False) -> TestSuiteResults:
        """
        Run all agent tests
        
        Args:
            phase: Optional phase filter (pre_solicitation, solicitation, etc.)
            parallel: Run tests in parallel (faster but may hit rate limits)
            
        Returns:
            TestSuiteResults with all test results
        """
        print("\n🤖 Running Agent Tests...")
        print(f"Program: {self.program_name}")
        
        if not self.api_key:
            print("⚠️  ANTHROPIC_API_KEY not set - all tests will be skipped")
        
        # Define all tests by phase
        tests = {
            'pre_solicitation': [
                self.test_sources_sought_agent,
                self.test_rfi_agent,
                self.test_industry_day_agent,
                self.test_market_research_agent,
                self.test_acquisition_plan_agent,
                self.test_igce_agent,
            ],
            'solicitation': [
                self.test_pws_writer_agent,
                self.test_soo_writer_agent,
                self.test_sow_writer_agent,
                self.test_rfp_writer_agent,
                self.test_section_b_agent,
                self.test_section_h_agent,
                self.test_section_i_agent,
                self.test_section_k_agent,
                self.test_section_l_agent,
                self.test_section_m_agent,
                self.test_qasp_agent,
                self.test_source_selection_plan_agent,
                self.test_ssdd_agent,
                self.test_sf26_agent,
                self.test_sf33_agent,
            ],
            'post_solicitation': [
                self.test_evaluation_scorecard_agent,
                self.test_ppq_agent,
                self.test_debriefing_agent,
            ],
            'award': [
                self.test_award_notification_agent,
                self.test_amendment_agent,
                self.test_pre_solicitation_notice_agent,
            ],
            'supporting': [
                self.test_quality_agent,
                self.test_research_agent,
                self.test_refinement_agent,
                self.test_qa_manager_agent,
            ],
        }
        
        # Filter by phase if specified
        if phase:
            tests = {k: v for k, v in tests.items() if k == phase}
        
        # Run tests
        if parallel and self.api_key:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=TestConfig.MAX_PARALLEL_TESTS) as executor:
                for phase_name, phase_tests in tests.items():
                    print(f"\n📋 Running {phase_name.upper()} agents (parallel)...")
                    futures = {executor.submit(test_fn): test_fn.__name__ for test_fn in phase_tests}
                    for future in as_completed(futures):
                        result = future.result()
                        self.results.add_result(result)
                        status_icon = "✅" if result.status == TestStatus.PASSED else \
                                      "❌" if result.status == TestStatus.FAILED else \
                                      "⏭️" if result.status == TestStatus.SKIPPED else "💥"
                        print(f"  {status_icon} {result.name} ({result.duration_ms:.0f}ms)")
        else:
            # Sequential execution
            for phase_name, phase_tests in tests.items():
                print(f"\n📋 Running {phase_name.upper()} agents...")
                for test_fn in phase_tests:
                    result = test_fn()
                    self.results.add_result(result)
                    status_icon = "✅" if result.status == TestStatus.PASSED else \
                                  "❌" if result.status == TestStatus.FAILED else \
                                  "⏭️" if result.status == TestStatus.SKIPPED else "💥"
                    print(f"  {status_icon} {result.name} ({result.duration_ms:.0f}ms)")
        
        self.results.end_time = TestConfig.get_report_path("agents").stem
        return self.results


def main():
    """Main entry point for agent tests"""
    parser = argparse.ArgumentParser(description='Run agent tests')
    parser.add_argument('--phase', '-p', type=str, 
                        choices=['pre_solicitation', 'solicitation', 'post_solicitation', 'award', 'supporting'],
                        help='Acquisition phase to test')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output', '-o', type=str, help='Output file for results')
    args = parser.parse_args()
    
    # Run tests
    suite = AgentTests()
    results = suite.run_all(phase=args.phase, parallel=args.parallel)
    
    # Print summary
    results.print_summary()
    
    # Save results
    output_path = Path(args.output) if args.output else TestConfig.get_report_path('agents')
    results.save_json(output_path)
    print(f"\n📄 Results saved to: {output_path}")
    
    # Return exit code based on results
    sys.exit(0 if results.failed == 0 and results.errors == 0 else 1)


if __name__ == '__main__':
    main()
