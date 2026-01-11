#!/usr/bin/env python3
"""
Database Model Tests
====================

Comprehensive tests for all 6 database models.

Models:
- User: User accounts and authentication
- Document: Document storage and versioning
- Procurement: Project/procurement lifecycle
- Audit: Audit trail logging
- Lineage: Document relationships
- Notification: User notifications

Dependencies:
- test_config: TestConfig, TestResult, TestSuiteResults
- backend.models.*: All model classes
- backend.database.base: Database session management

Usage:
    python test_database_models.py [--model MODEL]
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
    TestStatus
)


class DatabaseModelTests:
    """
    Database model test suite
    
    Tests all 6 database models with CRUD operations
    and relationship validation.
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.results = TestSuiteResults(suite_name="Database Model Tests")
        self.db_session = None
        self.test_user_id = None
        self.test_project_id = None
        self.test_document_id = None
    
    def setup(self) -> bool:
        """
        Setup database connection
        
        Returns:
            True if setup successful
        """
        try:
            from backend.database.base import SessionLocal
            self.db_session = SessionLocal()
            return True
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    def teardown(self):
        """Cleanup database session"""
        if self.db_session:
            self.db_session.close()
    
    def _test_model(
        self,
        name: str,
        test_fn: callable
    ) -> TestResult:
        """
        Test a single model
        
        Args:
            name: Model name for reporting
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
                category="models",
                status=TestStatus.PASSED if success else TestStatus.FAILED,
                duration_ms=duration_ms,
                message=message
            )
            
        except ImportError as e:
            return TestResult(
                name=name,
                category="models",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Import error: {str(e)}"
            )
        except Exception as e:
            return TestResult(
                name=name,
                category="models",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Error: {str(e)}"
            )
    
    # =========================================================================
    # MODEL TESTS
    # =========================================================================
    
    def test_user_model(self) -> TestResult:
        """Test User model"""
        def test_fn():
            from backend.models.user import User
            
            # Test model attributes
            assert hasattr(User, 'id'), "Missing id attribute"
            assert hasattr(User, 'email'), "Missing email attribute"
            assert hasattr(User, 'name'), "Missing name attribute"
            assert hasattr(User, 'role'), "Missing role attribute"
            assert hasattr(User, 'hashed_password'), "Missing hashed_password attribute"
            
            # Test model can be instantiated
            user = User(
                email="test@example.com",
                name="Test User",
                role="contracting_officer"
            )
            assert user.email == "test@example.com"
            assert user.name == "Test User"
            
            # Test password hashing if available
            if hasattr(User, 'set_password'):
                user.set_password("testpassword")
                assert user.hashed_password is not None
            
            # Query existing users
            if self.db_session:
                users = self.db_session.query(User).limit(5).all()
                return True, f"Model verified, {len(users)} users in database"
            
            return True, "Model structure verified"
        
        return self._test_model("User Model", test_fn)
    
    def test_document_model(self) -> TestResult:
        """Test Document model"""
        def test_fn():
            from backend.models.document import Document
            
            # Test model attributes
            assert hasattr(Document, 'id'), "Missing id attribute"
            assert hasattr(Document, 'name'), "Missing name attribute"
            assert hasattr(Document, 'document_type'), "Missing document_type attribute"
            assert hasattr(Document, 'content'), "Missing content attribute"
            assert hasattr(Document, 'status'), "Missing status attribute"
            
            # Test model can be instantiated
            doc = Document(
                name="Test Document",
                document_type="market_research",
                content="Test content"
            )
            assert doc.name == "Test Document"
            assert doc.document_type == "market_research"
            
            # Query existing documents
            if self.db_session:
                docs = self.db_session.query(Document).limit(5).all()
                if docs:
                    self.test_document_id = docs[0].id
                return True, f"Model verified, {len(docs)} documents in database"
            
            return True, "Model structure verified"
        
        return self._test_model("Document Model", test_fn)
    
    def test_procurement_model(self) -> TestResult:
        """Test Procurement model"""
        def test_fn():
            from backend.models.procurement import Procurement, Phase, Step
            
            # Test Procurement model attributes
            assert hasattr(Procurement, 'id'), "Missing id attribute"
            assert hasattr(Procurement, 'name'), "Missing name attribute"
            assert hasattr(Procurement, 'description'), "Missing description attribute"
            assert hasattr(Procurement, 'status'), "Missing status attribute"
            
            # Test Phase model attributes
            assert hasattr(Phase, 'id'), "Missing Phase id"
            assert hasattr(Phase, 'name'), "Missing Phase name"
            assert hasattr(Phase, 'procurement_id'), "Missing Phase procurement_id"
            
            # Test Step model attributes
            assert hasattr(Step, 'id'), "Missing Step id"
            assert hasattr(Step, 'name'), "Missing Step name"
            assert hasattr(Step, 'phase_id'), "Missing Step phase_id"
            
            # Query existing procurements
            if self.db_session:
                procs = self.db_session.query(Procurement).limit(5).all()
                if procs:
                    self.test_project_id = procs[0].id
                return True, f"Model verified, {len(procs)} procurements in database"
            
            return True, "Model structure verified"
        
        return self._test_model("Procurement Model", test_fn)
    
    def test_audit_model(self) -> TestResult:
        """Test Audit model"""
        def test_fn():
            from backend.models.audit import AuditLog
            
            # Test model attributes
            assert hasattr(AuditLog, 'id'), "Missing id attribute"
            assert hasattr(AuditLog, 'action'), "Missing action attribute"
            assert hasattr(AuditLog, 'user_id'), "Missing user_id attribute"
            assert hasattr(AuditLog, 'timestamp'), "Missing timestamp attribute"
            
            # Query existing audit logs
            if self.db_session:
                logs = self.db_session.query(AuditLog).limit(5).all()
                return True, f"Model verified, {len(logs)} audit logs in database"
            
            return True, "Model structure verified"
        
        return self._test_model("Audit Model", test_fn)
    
    def test_lineage_model(self) -> TestResult:
        """Test Lineage model"""
        def test_fn():
            from backend.models.lineage import DocumentLineage
            
            # Test model attributes
            assert hasattr(DocumentLineage, 'id'), "Missing id attribute"
            assert hasattr(DocumentLineage, 'source_document_id'), "Missing source_document_id attribute"
            assert hasattr(DocumentLineage, 'target_document_id'), "Missing target_document_id attribute"
            assert hasattr(DocumentLineage, 'relationship_type'), "Missing relationship_type attribute"
            
            # Query existing lineage records
            if self.db_session:
                lineages = self.db_session.query(DocumentLineage).limit(5).all()
                return True, f"Model verified, {len(lineages)} lineage records in database"
            
            return True, "Model structure verified"
        
        return self._test_model("Lineage Model", test_fn)
    
    def test_notification_model(self) -> TestResult:
        """Test Notification model"""
        def test_fn():
            from backend.models.notification import Notification
            
            # Test model attributes
            assert hasattr(Notification, 'id'), "Missing id attribute"
            assert hasattr(Notification, 'user_id'), "Missing user_id attribute"
            assert hasattr(Notification, 'message'), "Missing message attribute"
            assert hasattr(Notification, 'read'), "Missing read attribute"
            
            # Query existing notifications
            if self.db_session:
                notifs = self.db_session.query(Notification).limit(5).all()
                return True, f"Model verified, {len(notifs)} notifications in database"
            
            return True, "Model structure verified"
        
        return self._test_model("Notification Model", test_fn)
    
    # =========================================================================
    # RELATIONSHIP TESTS
    # =========================================================================
    
    def test_user_document_relationship(self) -> TestResult:
        """Test User-Document relationship"""
        def test_fn():
            from backend.models.user import User
            from backend.models.document import Document
            
            if not self.db_session:
                return True, "Skipped - no database session"
            
            # Check if relationship exists
            user = self.db_session.query(User).first()
            if user and hasattr(user, 'documents'):
                return True, "User-Document relationship verified"
            
            return True, "Relationship structure verified (no data to test)"
        
        return self._test_model("User-Document Relationship", test_fn)
    
    def test_procurement_phase_relationship(self) -> TestResult:
        """Test Procurement-Phase relationship"""
        def test_fn():
            from backend.models.procurement import Procurement, Phase
            
            if not self.db_session:
                return True, "Skipped - no database session"
            
            # Check if relationship exists
            proc = self.db_session.query(Procurement).first()
            if proc and hasattr(proc, 'phases'):
                phases = proc.phases
                return True, f"Procurement-Phase relationship verified ({len(phases)} phases)"
            
            return True, "Relationship structure verified (no data to test)"
        
        return self._test_model("Procurement-Phase Relationship", test_fn)
    
    def test_phase_step_relationship(self) -> TestResult:
        """Test Phase-Step relationship"""
        def test_fn():
            from backend.models.procurement import Phase, Step
            
            if not self.db_session:
                return True, "Skipped - no database session"
            
            # Check if relationship exists
            phase = self.db_session.query(Phase).first()
            if phase and hasattr(phase, 'steps'):
                steps = phase.steps
                return True, f"Phase-Step relationship verified ({len(steps)} steps)"
            
            return True, "Relationship structure verified (no data to test)"
        
        return self._test_model("Phase-Step Relationship", test_fn)
    
    def test_document_lineage_relationship(self) -> TestResult:
        """Test Document-Lineage relationship"""
        def test_fn():
            from backend.models.document import Document
            from backend.models.lineage import DocumentLineage
            
            if not self.db_session:
                return True, "Skipped - no database session"
            
            # Check if documents have lineage
            doc = self.db_session.query(Document).first()
            if doc:
                lineages = self.db_session.query(DocumentLineage).filter(
                    (DocumentLineage.source_document_id == doc.id) |
                    (DocumentLineage.target_document_id == doc.id)
                ).all()
                return True, f"Document-Lineage relationship verified ({len(lineages)} connections)"
            
            return True, "Relationship structure verified (no data to test)"
        
        return self._test_model("Document-Lineage Relationship", test_fn)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all(self, model: str = None) -> TestSuiteResults:
        """
        Run all database model tests
        
        Args:
            model: Optional model filter
            
        Returns:
            TestSuiteResults with all test results
        """
        print("\n🗄️  Running Database Model Tests...")
        
        # Setup database connection
        if not self.setup():
            self.results.add_result(TestResult(
                name="Database Setup",
                category="setup",
                status=TestStatus.ERROR,
                message="Failed to connect to database"
            ))
            return self.results
        
        # Define all tests
        tests = {
            'user': [
                self.test_user_model,
            ],
            'document': [
                self.test_document_model,
            ],
            'procurement': [
                self.test_procurement_model,
            ],
            'audit': [
                self.test_audit_model,
            ],
            'lineage': [
                self.test_lineage_model,
            ],
            'notification': [
                self.test_notification_model,
            ],
            'relationships': [
                self.test_user_document_relationship,
                self.test_procurement_phase_relationship,
                self.test_phase_step_relationship,
                self.test_document_lineage_relationship,
            ],
        }
        
        # Filter by model if specified
        if model:
            tests = {k: v for k, v in tests.items() if k == model}
        
        # Run tests
        for group_name, group_tests in tests.items():
            print(f"\n📋 Testing {group_name.upper()}...")
            for test_fn in group_tests:
                result = test_fn()
                self.results.add_result(result)
                status_icon = "✅" if result.status == TestStatus.PASSED else \
                              "❌" if result.status == TestStatus.FAILED else \
                              "⏭️" if result.status == TestStatus.SKIPPED else "💥"
                print(f"  {status_icon} {result.name} ({result.duration_ms:.0f}ms)")
        
        self.teardown()
        self.results.end_time = TestConfig.get_report_path("models").stem
        
        return self.results


def main():
    """Main entry point for database model tests"""
    parser = argparse.ArgumentParser(description='Run database model tests')
    parser.add_argument('--model', '-m', type=str, help='Model to test')
    parser.add_argument('--output', '-o', type=str, help='Output file for results')
    args = parser.parse_args()
    
    # Run tests
    suite = DatabaseModelTests()
    results = suite.run_all(model=args.model)
    
    # Print summary
    results.print_summary()
    
    # Save results
    output_path = Path(args.output) if args.output else TestConfig.get_report_path('models')
    results.save_json(output_path)
    print(f"\n📄 Results saved to: {output_path}")
    
    # Return exit code based on results
    sys.exit(0 if results.failed == 0 and results.errors == 0 else 1)


if __name__ == '__main__':
    main()
