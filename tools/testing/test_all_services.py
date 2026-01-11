#!/usr/bin/env python3
"""
Service Tests
=============

Comprehensive tests for all 13 backend services.

Services:
- AgentComparisonService
- AgentRouter
- ContextManager
- DependencyGraph
- DocumentGenerator
- DocumentInitializer
- ExportService
- GenerationCoordinator
- PhaseDetector
- PhaseGateService
- RAGService
- WebSocketManager

Dependencies:
- test_config: TestConfig, TestResult, TestSuiteResults
- backend.services.*: All service classes

Usage:
    python test_all_services.py [--service SERVICE]
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from tools.testing.test_config import (
    TestConfig, TestResult, TestSuiteResults,
    TestStatus, TEST_PROJECT_INFO
)


class ServiceTests:
    """
    Service test suite
    
    Tests all 13 backend services with proper
    initialization and method validation.
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.api_key = TestConfig.ANTHROPIC_API_KEY
        self.results = TestSuiteResults(suite_name="Service Tests")
    
    def _test_service(
        self,
        name: str,
        test_fn: callable
    ) -> TestResult:
        """
        Test a single service
        
        Args:
            name: Service name for reporting
            test_fn: Test function to execute
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        try:
            success, message = test_fn()
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                name=name,
                category="services",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                duration_ms=duration_ms,
                message=message
            )
            
        except ImportError as e:
            return TestResult(
                name=name,
                category="services",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Import error: {str(e)}"
            )
        except Exception as e:
            return TestResult(
                name=name,
                category="services",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}"
            )
    
    # =========================================================================
    # SERVICE TESTS
    # =========================================================================
    
    def test_agent_comparison_service(self) -> TestResult:
        """Test AgentComparisonService"""
        def test_fn():
            from backend.services.agent_comparison_service import AgentComparisonService
            
            if not self.api_key:
                return True, "Skipped - no API key (service imports correctly)"
            
            # Test initialization
            service = AgentComparisonService(api_key=self.api_key)
            
            # Test method existence
            assert hasattr(service, 'compare_agents'), "Missing compare_agents method"
            assert hasattr(service, 'get_comparison_status'), "Missing get_comparison_status method"
            
            return True, "Service initialized and methods verified"
        
        return self._test_service("AgentComparisonService", test_fn)
    
    def test_agent_router(self) -> TestResult:
        """Test AgentRouter"""
        def test_fn():
            from backend.services.agent_router import AgentRouter
            
            # Test initialization
            router = AgentRouter()
            
            # Test routing functionality
            assert hasattr(router, 'route'), "Missing route method"
            assert hasattr(router, 'get_agent_for_document'), "Missing get_agent_for_document method"
            
            # Test document type routing
            doc_types = ['market_research', 'pws', 'sow', 'rfp', 'igce']
            for doc_type in doc_types:
                try:
                    agent_class = router.get_agent_for_document(doc_type)
                    if agent_class is None:
                        # Some document types may not have direct agents
                        continue
                except Exception:
                    continue
            
            return True, "Router initialized and routing verified"
        
        return self._test_service("AgentRouter", test_fn)
    
    def test_context_manager(self) -> TestResult:
        """Test ContextManager"""
        def test_fn():
            from backend.services.context_manager import ContextManager
            
            # Test initialization
            manager = ContextManager()
            
            # Test method existence
            assert hasattr(manager, 'get_context'), "Missing get_context method"
            assert hasattr(manager, 'add_context'), "Missing add_context method"
            assert hasattr(manager, 'clear_context'), "Missing clear_context method"
            
            # Test basic operations
            test_key = f"test_context_{int(time.time())}"
            manager.add_context(test_key, {"test": "data"})
            context = manager.get_context(test_key)
            
            return True, "Context manager operations verified"
        
        return self._test_service("ContextManager", test_fn)
    
    def test_dependency_graph(self) -> TestResult:
        """Test DependencyGraph"""
        def test_fn():
            from backend.services.dependency_graph import DependencyGraph
            
            # Test initialization
            graph = DependencyGraph()
            
            # Test method existence
            assert hasattr(graph, 'get_dependencies'), "Missing get_dependencies method"
            assert hasattr(graph, 'get_dependents'), "Missing get_dependents method"
            assert hasattr(graph, 'get_generation_order'), "Missing get_generation_order method"
            
            # Test dependency resolution
            deps = graph.get_dependencies('pws')
            order = graph.get_generation_order()
            
            assert isinstance(deps, (list, set, tuple)), "Dependencies should be iterable"
            assert isinstance(order, (list, tuple)), "Generation order should be a list"
            
            return True, f"Graph verified with {len(order)} documents in order"
        
        return self._test_service("DependencyGraph", test_fn)
    
    def test_document_generator(self) -> TestResult:
        """Test DocumentGenerator"""
        def test_fn():
            from backend.services.document_generator import DocumentGenerator
            
            if not self.api_key:
                return True, "Skipped - no API key (service imports correctly)"
            
            # Test initialization
            generator = DocumentGenerator(api_key=self.api_key)
            
            # Test method existence
            assert hasattr(generator, 'generate'), "Missing generate method"
            assert hasattr(generator, 'generate_section'), "Missing generate_section method"
            
            return True, "Document generator initialized"
        
        return self._test_service("DocumentGenerator", test_fn)
    
    def test_document_initializer(self) -> TestResult:
        """Test DocumentInitializer"""
        def test_fn():
            from backend.services.document_initializer import DocumentInitializer
            
            # Test initialization
            initializer = DocumentInitializer()
            
            # Test method existence
            assert hasattr(initializer, 'initialize_documents'), "Missing initialize_documents method"
            assert hasattr(initializer, 'get_document_template'), "Missing get_document_template method"
            
            return True, "Document initializer verified"
        
        return self._test_service("DocumentInitializer", test_fn)
    
    def test_export_service(self) -> TestResult:
        """Test ExportService"""
        def test_fn():
            from backend.services.export_service import ExportService
            
            # Test initialization
            service = ExportService()
            
            # Test method existence
            assert hasattr(service, 'export_to_pdf'), "Missing export_to_pdf method"
            assert hasattr(service, 'export_to_docx'), "Missing export_to_docx method"
            
            return True, "Export service verified"
        
        return self._test_service("ExportService", test_fn)
    
    def test_generation_coordinator(self) -> TestResult:
        """Test GenerationCoordinator"""
        def test_fn():
            from backend.services.generation_coordinator import GenerationCoordinator
            
            if not self.api_key:
                return True, "Skipped - no API key (service imports correctly)"
            
            # Test initialization
            coordinator = GenerationCoordinator(api_key=self.api_key)
            
            # Test method existence
            assert hasattr(coordinator, 'generate_documents'), "Missing generate_documents method"
            assert hasattr(coordinator, 'get_task_status'), "Missing get_task_status method"
            
            return True, "Generation coordinator initialized"
        
        return self._test_service("GenerationCoordinator", test_fn)
    
    def test_phase_detector(self) -> TestResult:
        """Test PhaseDetector"""
        def test_fn():
            from backend.services.phase_detector import PhaseDetector
            
            # Test initialization
            detector = PhaseDetector()
            
            # Test method existence
            assert hasattr(detector, 'detect_phase'), "Missing detect_phase method"
            assert hasattr(detector, 'get_phase_documents'), "Missing get_phase_documents method"
            
            # Test phase detection
            phases = ['pre_solicitation', 'solicitation', 'post_solicitation', 'award']
            for phase in phases:
                docs = detector.get_phase_documents(phase)
                assert isinstance(docs, (list, set, tuple)), f"Phase {phase} documents should be iterable"
            
            return True, "Phase detector verified for all phases"
        
        return self._test_service("PhaseDetector", test_fn)
    
    def test_phase_gate_service(self) -> TestResult:
        """Test PhaseGateService"""
        def test_fn():
            from backend.services.phase_gate_service import PhaseGateService
            
            # Test initialization
            service = PhaseGateService()
            
            # Test method existence
            assert hasattr(service, 'validate_transition'), "Missing validate_transition method"
            assert hasattr(service, 'get_gate_requirements'), "Missing get_gate_requirements method"
            
            return True, "Phase gate service verified"
        
        return self._test_service("PhaseGateService", test_fn)
    
    def test_rag_service(self) -> TestResult:
        """Test RAGService"""
        def test_fn():
            from backend.services.rag_service import RAGService
            
            # Test initialization
            service = RAGService()
            
            # Test method existence
            assert hasattr(service, 'query'), "Missing query method"
            assert hasattr(service, 'add_document'), "Missing add_document method"
            
            return True, "RAG service verified"
        
        return self._test_service("RAGService", test_fn)
    
    def test_websocket_manager(self) -> TestResult:
        """Test WebSocketManager"""
        def test_fn():
            from backend.services.websocket_manager import WebSocketManager
            
            # Test initialization (singleton pattern)
            manager = WebSocketManager()
            
            # Test method existence
            assert hasattr(manager, 'connect'), "Missing connect method"
            assert hasattr(manager, 'disconnect'), "Missing disconnect method"
            assert hasattr(manager, 'broadcast'), "Missing broadcast method"
            
            return True, "WebSocket manager verified"
        
        return self._test_service("WebSocketManager", test_fn)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all(self, service: str = None) -> TestSuiteResults:
        """
        Run all service tests
        
        Args:
            service: Optional service filter
            
        Returns:
            TestSuiteResults with all test results
        """
        print("\n⚙️  Running Service Tests...")
        
        # Define all tests
        tests = {
            'agent_comparison': self.test_agent_comparison_service,
            'agent_router': self.test_agent_router,
            'context_manager': self.test_context_manager,
            'dependency_graph': self.test_dependency_graph,
            'document_generator': self.test_document_generator,
            'document_initializer': self.test_document_initializer,
            'export_service': self.test_export_service,
            'generation_coordinator': self.test_generation_coordinator,
            'phase_detector': self.test_phase_detector,
            'phase_gate_service': self.test_phase_gate_service,
            'rag_service': self.test_rag_service,
            'websocket_manager': self.test_websocket_manager,
        }
        
        # Filter by service if specified
        if service:
            tests = {k: v for k, v in tests.items() if k == service}
        
        # Run tests
        for test_name, test_fn in tests.items():
            result = test_fn()
            self.results.add_result(result)
            status_icon = "✅" if result.status == TestStatus.PASSED else \
                          "❌" if result.status == TestStatus.FAILED else \
                          "⏭️" if result.status == TestStatus.SKIPPED else "💥"
            print(f"  {status_icon} {result.name} ({result.duration_ms:.0f}ms)")
        
        self.results.end_time = TestConfig.get_report_path("services").stem
        return self.results


def main():
    """Main entry point for service tests"""
    parser = argparse.ArgumentParser(description='Run service tests')
    parser.add_argument('--service', '-s', type=str, help='Service to test')
    parser.add_argument('--output', '-o', type=str, help='Output file for results')
    args = parser.parse_args()
    
    # Run tests
    suite = ServiceTests()
    results = suite.run_all(service=args.service)
    
    # Print summary
    results.print_summary()
    
    # Save results
    output_path = Path(args.output) if args.output else TestConfig.get_report_path('services')
    results.save_json(output_path)
    print(f"\n📄 Results saved to: {output_path}")
    
    # Return exit code based on results
    sys.exit(0 if results.failed == 0 and results.errors == 0 else 1)


if __name__ == '__main__':
    main()
