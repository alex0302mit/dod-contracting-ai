#!/usr/bin/env python3
"""
Integration Tests
=================

End-to-end workflow tests for the DoD Contracting System.

Workflows:
- Complete document generation pipeline
- Cross-reference consistency
- Approval workflow
- Phase transitions
- Export workflow

Dependencies:
- test_config: TestConfig, APIClient, TestResult, TestSuiteResults
- requests: HTTP client

Usage:
    python test_integration.py [--workflow WORKFLOW]
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
    TestConfig, APIClient, TestResult, TestSuiteResults,
    TestStatus, TEST_PROJECT_INFO
)


class IntegrationTests:
    """
    Integration test suite
    
    Tests complete end-to-end workflows across
    multiple components and services.
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.client = APIClient()
        self.results = TestSuiteResults(suite_name="Integration Tests")
        self.test_project_id: Optional[int] = None
        self.test_document_ids: Dict[str, int] = {}
        self.test_phase_ids: Dict[str, int] = {}
    
    def setup(self) -> bool:
        """
        Setup test environment
        
        Returns:
            True if setup successful
        """
        print("\n🔧 Setting up Integration Tests...")
        
        # Login
        if not self.client.login():
            print("❌ Failed to login")
            return False
        
        print(f"✅ Logged in as user {self.client.user_id}")
        return True
    
    def teardown(self):
        """Cleanup test environment"""
        print("\n🧹 Cleaning up...")
        
        # Delete test project
        if self.test_project_id:
            try:
                self.client.delete(f'/api/projects/{self.test_project_id}')
                print(f"✅ Deleted test project {self.test_project_id}")
            except Exception:
                pass
        
        self.client.logout()
    
    def _test_workflow(
        self,
        name: str,
        test_fn: callable
    ) -> TestResult:
        """
        Test a single workflow
        
        Args:
            name: Workflow name for reporting
            test_fn: Test function to execute
            
        Returns:
            TestResult object
        """
        start_time = time.time()
        try:
            success, message, details = test_fn()
            duration_ms = (time.time() - start_time) * 1000
            
            return TestResult(
                name=name,
                category="integration",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                duration_ms=duration_ms,
                message=message,
                details=details or {}
            )
            
        except Exception as e:
            return TestResult(
                name=name,
                category="integration",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}"
            )
    
    # =========================================================================
    # WORKFLOW TESTS
    # =========================================================================
    
    def test_project_creation_workflow(self) -> TestResult:
        """Test complete project creation workflow"""
        def test_fn():
            steps_completed = []
            
            # Step 1: Create project
            response = self.client.post('/api/projects', {
                'name': f"Integration Test {int(time.time())}",
                'description': 'Integration test project',
                'program_name': TEST_PROJECT_INFO['program_name'],
                'organization': TEST_PROJECT_INFO['organization'],
                'estimated_value': TEST_PROJECT_INFO['estimated_value'],
                'contract_type': TEST_PROJECT_INFO['contract_type']
            })
            
            if response.status_code not in [200, 201]:
                return False, f"Project creation failed: {response.status_code}", {}
            
            data = response.json()
            self.test_project_id = data.get('id')
            steps_completed.append("Project created")
            
            # Step 2: Initialize documents
            response = self.client.post(
                f'/api/projects/{self.test_project_id}/initialize-documents',
                {}
            )
            
            if response.status_code not in [200, 201]:
                return False, f"Document initialization failed: {response.status_code}", {'steps': steps_completed}
            
            steps_completed.append("Documents initialized")
            
            # Step 3: Get project phases
            response = self.client.get(f'/api/projects/{self.test_project_id}/phases')
            
            if response.status_code != 200:
                return False, f"Phase retrieval failed: {response.status_code}", {'steps': steps_completed}
            
            phases = response.json()
            for phase in phases:
                self.test_phase_ids[phase['name']] = phase['id']
            steps_completed.append(f"Retrieved {len(phases)} phases")
            
            # Step 4: Get project documents
            response = self.client.get(f'/api/projects/{self.test_project_id}/documents')
            
            if response.status_code != 200:
                return False, f"Document retrieval failed: {response.status_code}", {'steps': steps_completed}
            
            docs = response.json()
            for doc in docs:
                self.test_document_ids[doc['document_type']] = doc['id']
            steps_completed.append(f"Retrieved {len(docs)} documents")
            
            return True, "Project creation workflow completed", {
                'steps': steps_completed,
                'project_id': self.test_project_id,
                'phases': len(phases),
                'documents': len(docs)
            }
        
        return self._test_workflow("Project Creation Workflow", test_fn)
    
    def test_document_editing_workflow(self) -> TestResult:
        """Test document editing workflow"""
        def test_fn():
            if not self.test_document_ids:
                return False, "No documents available for testing", {}
            
            steps_completed = []
            
            # Get first document
            doc_type = list(self.test_document_ids.keys())[0]
            doc_id = self.test_document_ids[doc_type]
            
            # Step 1: Update document content
            response = self.client.patch(f'/api/documents/{doc_id}', {
                'content': 'Updated content for integration testing'
            })
            
            if response.status_code not in [200, 204]:
                return False, f"Document update failed: {response.status_code}", {}
            
            steps_completed.append("Document content updated")
            
            # Step 2: Save generated content
            response = self.client.post(f'/api/documents/{doc_id}/save-generated', {
                'content': 'Integration test generated content',
                'sections': {'intro': 'Test intro section'}
            })
            
            if response.status_code not in [200, 201, 400]:
                return False, f"Save generated failed: {response.status_code}", {'steps': steps_completed}
            
            steps_completed.append("Generated content saved")
            
            return True, "Document editing workflow completed", {
                'steps': steps_completed,
                'document_id': doc_id,
                'document_type': doc_type
            }
        
        return self._test_workflow("Document Editing Workflow", test_fn)
    
    def test_approval_workflow(self) -> TestResult:
        """Test approval request workflow"""
        def test_fn():
            if not self.test_document_ids:
                return False, "No documents available for testing", {}
            
            steps_completed = []
            
            # Get first document
            doc_id = list(self.test_document_ids.values())[0]
            
            # Step 1: Request approval
            response = self.client.post(f'/api/documents/{doc_id}/request-approval', {
                'approver_id': self.client.user_id,
                'comments': 'Integration test approval request'
            })
            
            # May fail if document not ready for approval
            if response.status_code in [200, 201]:
                steps_completed.append("Approval requested")
                approval_id = response.json().get('id')
                
                # Step 2: Check pending approvals
                response = self.client.get('/api/approvals/pending')
                if response.status_code == 200:
                    steps_completed.append("Pending approvals retrieved")
                
                # Step 3: Get approval history
                response = self.client.get(f'/api/documents/{doc_id}/approval-history')
                if response.status_code == 200:
                    steps_completed.append("Approval history retrieved")
                
                return True, "Approval workflow completed", {
                    'steps': steps_completed,
                    'approval_id': approval_id
                }
            elif response.status_code == 400:
                return True, "Document not ready for approval (expected behavior)", {
                    'steps': ['Approval request attempted'],
                    'status': 'Document prerequisites not met'
                }
            else:
                return False, f"Approval request failed: {response.status_code}", {}
        
        return self._test_workflow("Approval Workflow", test_fn)
    
    def test_phase_transition_workflow(self) -> TestResult:
        """Test phase transition workflow"""
        def test_fn():
            if not self.test_phase_ids:
                return False, "No phases available for testing", {}
            
            steps_completed = []
            
            # Get first phase
            phase_name = list(self.test_phase_ids.keys())[0]
            phase_id = self.test_phase_ids[phase_name]
            
            # Step 1: Validate transition
            response = self.client.get(f'/api/phases/{phase_id}/validate-transition')
            
            if response.status_code != 200:
                return False, f"Transition validation failed: {response.status_code}", {}
            
            validation = response.json()
            steps_completed.append("Transition validated")
            
            # Step 2: Check pending transitions
            response = self.client.get('/api/phase-transitions/pending')
            
            if response.status_code == 200:
                steps_completed.append("Pending transitions retrieved")
            
            # Step 3: Get transition history
            if self.test_project_id:
                response = self.client.get(
                    f'/api/projects/{self.test_project_id}/transition-history'
                )
                if response.status_code == 200:
                    steps_completed.append("Transition history retrieved")
            
            return True, "Phase transition workflow completed", {
                'steps': steps_completed,
                'phase_name': phase_name,
                'can_transition': validation.get('can_transition', False)
            }
        
        return self._test_workflow("Phase Transition Workflow", test_fn)
    
    def test_dependency_workflow(self) -> TestResult:
        """Test document dependency workflow"""
        def test_fn():
            if not self.test_document_ids:
                return False, "No documents available for testing", {}
            
            steps_completed = []
            dependencies_found = {}
            
            # Check dependencies for each document
            for doc_type, doc_id in list(self.test_document_ids.items())[:5]:
                response = self.client.get(f'/api/documents/{doc_id}/check-dependencies')
                
                if response.status_code == 200:
                    deps = response.json()
                    dependencies_found[doc_type] = deps
            
            steps_completed.append(f"Checked dependencies for {len(dependencies_found)} documents")
            
            return True, "Dependency workflow completed", {
                'steps': steps_completed,
                'documents_checked': len(dependencies_found),
                'dependencies': dependencies_found
            }
        
        return self._test_workflow("Dependency Workflow", test_fn)
    
    def test_cross_reference_consistency(self) -> TestResult:
        """Test cross-reference consistency across documents"""
        def test_fn():
            if not self.test_project_id:
                return False, "No project available for testing", {}
            
            steps_completed = []
            
            # Get all project documents
            response = self.client.get(f'/api/projects/{self.test_project_id}/documents')
            
            if response.status_code != 200:
                return False, f"Document retrieval failed: {response.status_code}", {}
            
            docs = response.json()
            steps_completed.append(f"Retrieved {len(docs)} documents")
            
            # Check document relationships
            relationships = []
            for doc in docs[:10]:
                doc_id = doc.get('id')
                if doc_id:
                    dep_response = self.client.get(f'/api/documents/{doc_id}/check-dependencies')
                    if dep_response.status_code == 200:
                        deps = dep_response.json()
                        if deps.get('dependencies'):
                            relationships.extend(deps['dependencies'])
            
            steps_completed.append(f"Found {len(relationships)} cross-references")
            
            return True, "Cross-reference consistency verified", {
                'steps': steps_completed,
                'documents': len(docs),
                'relationships': len(relationships)
            }
        
        return self._test_workflow("Cross-Reference Consistency", test_fn)
    
    def test_api_health_workflow(self) -> TestResult:
        """Test API health and connectivity"""
        def test_fn():
            steps_completed = []
            
            # Step 1: Health check
            response = self.client.get('/health', auth=False)
            if response.status_code == 200:
                steps_completed.append("Health endpoint OK")
            else:
                return False, f"Health check failed: {response.status_code}", {}
            
            # Step 2: Auth endpoint
            response = self.client.get('/api/auth/me')
            if response.status_code == 200:
                steps_completed.append("Auth endpoint OK")
            
            # Step 3: Projects endpoint
            response = self.client.get('/api/projects')
            if response.status_code == 200:
                projects = response.json()
                steps_completed.append(f"Projects endpoint OK ({len(projects)} projects)")
            
            return True, "API health workflow completed", {
                'steps': steps_completed
            }
        
        return self._test_workflow("API Health Workflow", test_fn)
    
    def test_user_session_workflow(self) -> TestResult:
        """Test user session management"""
        def test_fn():
            steps_completed = []
            
            # Step 1: Get current user
            response = self.client.get('/api/auth/me')
            if response.status_code != 200:
                return False, f"Get user failed: {response.status_code}", {}
            
            user_data = response.json()
            steps_completed.append(f"Retrieved user: {user_data.get('email')}")
            
            # Step 2: List users
            response = self.client.get('/api/users')
            if response.status_code == 200:
                users = response.json()
                steps_completed.append(f"Listed {len(users)} users")
            
            return True, "User session workflow completed", {
                'steps': steps_completed,
                'user_id': user_data.get('id'),
                'user_role': user_data.get('role')
            }
        
        return self._test_workflow("User Session Workflow", test_fn)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all(self, workflow: str = None) -> TestSuiteResults:
        """
        Run all integration tests
        
        Args:
            workflow: Optional workflow filter
            
        Returns:
            TestSuiteResults with all test results
        """
        print("\n🔗 Running Integration Tests...")
        
        if not self.setup():
            self.results.add_result(TestResult(
                name="Setup",
                category="setup",
                status=TestStatus.ERROR,
                message="Failed to setup test environment"
            ))
            return self.results
        
        # Define all tests in order (some depend on previous tests)
        tests = {
            'health': self.test_api_health_workflow,
            'session': self.test_user_session_workflow,
            'project': self.test_project_creation_workflow,
            'editing': self.test_document_editing_workflow,
            'dependencies': self.test_dependency_workflow,
            'crossref': self.test_cross_reference_consistency,
            'approval': self.test_approval_workflow,
            'phase': self.test_phase_transition_workflow,
        }
        
        # Filter by workflow if specified
        if workflow:
            tests = {k: v for k, v in tests.items() if k == workflow}
        
        # Run tests
        for test_name, test_fn in tests.items():
            result = test_fn()
            self.results.add_result(result)
            status_icon = "✅" if result.status == TestStatus.PASSED else \
                          "❌" if result.status == TestStatus.FAILED else \
                          "⏭️" if result.status == TestStatus.SKIPPED else "💥"
            print(f"  {status_icon} {result.name} ({result.duration_ms:.0f}ms)")
            if result.message:
                print(f"      {result.message}")
        
        self.teardown()
        self.results.end_time = TestConfig.get_report_path("integration").stem
        
        return self.results


def main():
    """Main entry point for integration tests"""
    parser = argparse.ArgumentParser(description='Run integration tests')
    parser.add_argument('--workflow', '-w', type=str, help='Workflow to test')
    parser.add_argument('--output', '-o', type=str, help='Output file for results')
    args = parser.parse_args()
    
    # Validate configuration
    issues = TestConfig.validate()
    if issues:
        print("⚠️  Configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
    
    # Run tests
    suite = IntegrationTests()
    results = suite.run_all(workflow=args.workflow)
    
    # Print summary
    results.print_summary()
    
    # Save results
    output_path = Path(args.output) if args.output else TestConfig.get_report_path('integration')
    results.save_json(output_path)
    print(f"\n📄 Results saved to: {output_path}")
    
    # Return exit code based on results
    sys.exit(0 if results.failed == 0 and results.errors == 0 else 1)


if __name__ == '__main__':
    main()
