#!/usr/bin/env python3
"""
Test Configuration Module
========================

Shared configuration, credentials, and utilities for the comprehensive test suite.

Dependencies:
- requests: HTTP client for API testing
- dotenv: Environment variable loading
- pathlib: Path manipulation

Usage:
    from test_config import TestConfig, TestResult, api_request
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')


class TestStatus(Enum):
    """Test execution status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """
    Individual test result container
    
    Attributes:
        name: Test name/identifier
        category: Test category (api, agent, service, model, integration)
        status: Pass/fail/skip/error status
        duration_ms: Execution time in milliseconds
        message: Success/error message
        details: Additional test details (request/response, etc.)
    """
    name: str
    category: str
    status: TestStatus
    duration_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'status': self.status.value
        }


@dataclass
class TestSuiteResults:
    """
    Aggregated test suite results
    
    Attributes:
        suite_name: Name of the test suite
        start_time: Suite start timestamp
        end_time: Suite end timestamp
        results: List of individual test results
    """
    suite_name: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    results: List[TestResult] = field(default_factory=list)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)
    
    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
    
    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.ERROR)
    
    @property
    def total(self) -> int:
        return len(self.results)
    
    @property
    def total_duration_ms(self) -> float:
        return sum(r.duration_ms for r in self.results)
    
    def add_result(self, result: TestResult):
        """Add a test result to the suite"""
        self.results.append(result)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'suite_name': self.suite_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'summary': {
                'total': self.total,
                'passed': self.passed,
                'failed': self.failed,
                'skipped': self.skipped,
                'errors': self.errors,
                'pass_rate': f"{(self.passed / self.total * 100):.1f}%" if self.total > 0 else "0%",
                'total_duration_ms': self.total_duration_ms
            },
            'results': [r.to_dict() for r in self.results]
        }
    
    def save_json(self, filepath: Path):
        """Save results to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 70)
        print(f"TEST SUITE: {self.suite_name}")
        print("=" * 70)
        print(f"Total Tests: {self.total}")
        print(f"  ✅ Passed:  {self.passed}")
        print(f"  ❌ Failed:  {self.failed}")
        print(f"  ⏭️  Skipped: {self.skipped}")
        print(f"  💥 Errors:  {self.errors}")
        print(f"Pass Rate: {(self.passed / self.total * 100):.1f}%" if self.total > 0 else "N/A")
        print(f"Duration: {self.total_duration_ms / 1000:.2f}s")
        print("=" * 70)
        
        # Print failed tests
        failed_tests = [r for r in self.results if r.status in (TestStatus.FAILED, TestStatus.ERROR)]
        if failed_tests:
            print("\nFailed Tests:")
            for r in failed_tests:
                print(f"  ❌ {r.name}: {r.message}")


class TestConfig:
    """
    Central test configuration
    
    Provides:
    - API base URL and endpoints
    - Test user credentials
    - Timeout settings
    - Report output paths
    - Database configuration
    """
    
    # API Configuration
    API_BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')
    API_TIMEOUT = int(os.getenv('TEST_API_TIMEOUT', '30'))
    
    # Test User Credentials
    TEST_USER_EMAIL = os.getenv('TEST_USER_EMAIL', 'john.contracting@navy.mil')
    TEST_USER_PASSWORD = os.getenv('TEST_USER_PASSWORD', 'password123')
    
    # Admin User Credentials
    ADMIN_USER_EMAIL = os.getenv('ADMIN_USER_EMAIL', 'admin@dod.mil')
    ADMIN_USER_PASSWORD = os.getenv('ADMIN_USER_PASSWORD', 'admin123')
    
    # Anthropic API Key (for agent tests)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Report Output Paths
    REPORTS_DIR = PROJECT_ROOT / 'tools' / 'testing' / 'reports'
    LOGS_DIR = PROJECT_ROOT / 'tools' / 'testing' / 'logs'
    
    # Test Data
    TEST_PROJECT_NAME = f"TEST_PROJECT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    TEST_PROGRAM_NAME = "Advanced Logistics Management System (ALMS)"
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY_MS = 1000
    
    # Parallel Execution
    MAX_PARALLEL_TESTS = 4
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist"""
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_report_path(cls, name: str, extension: str = 'json') -> Path:
        """Get path for a report file"""
        cls.ensure_directories()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return cls.REPORTS_DIR / f"{name}_{timestamp}.{extension}"
    
    @classmethod
    def get_log_path(cls, name: str) -> Path:
        """Get path for a log file"""
        cls.ensure_directories()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return cls.LOGS_DIR / f"{name}_{timestamp}.log"
    
    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate configuration and return list of issues
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        # Check API key
        if not cls.ANTHROPIC_API_KEY:
            issues.append("ANTHROPIC_API_KEY not set - agent tests will be skipped")
        
        # Check API connectivity
        try:
            response = requests.get(f"{cls.API_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                issues.append(f"API health check failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            issues.append(f"Cannot connect to API at {cls.API_BASE_URL}: {str(e)}")
        
        return issues


class APIClient:
    """
    HTTP client for API testing
    
    Features:
    - Automatic authentication
    - Request/response logging
    - Timeout handling
    - Session management
    """
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialize API client
        
        Args:
            base_url: API base URL (defaults to TestConfig.API_BASE_URL)
            timeout: Request timeout in seconds (defaults to TestConfig.API_TIMEOUT)
        """
        self.base_url = base_url or TestConfig.API_BASE_URL
        self.timeout = timeout or TestConfig.API_TIMEOUT
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
    
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Authenticate and store token
        
        Args:
            email: User email (defaults to TestConfig.TEST_USER_EMAIL)
            password: User password (defaults to TestConfig.TEST_USER_PASSWORD)
            
        Returns:
            True if login successful, False otherwise
            
        Note:
            API expects query parameters, not JSON body
        """
        email = email or TestConfig.TEST_USER_EMAIL
        password = password or TestConfig.TEST_USER_PASSWORD
        
        try:
            # Send credentials as query parameters (API expects query params, not JSON)
            url = f"{self.base_url}/api/auth/login"
            response = self.session.post(
                url,
                params={'email': email, 'password': password},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_id = data.get('user', {}).get('id')
                return True
            return False
        except Exception:
            return False
    
    def logout(self):
        """Clear authentication"""
        self.token = None
        self.user_id = None
    
    def _get_headers(self, auth: bool = True) -> Dict[str, str]:
        """Get request headers"""
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def get(self, endpoint: str, params: Dict = None, auth: bool = True) -> requests.Response:
        """
        Make GET request
        
        Args:
            endpoint: API endpoint (e.g., '/api/projects')
            params: Query parameters
            auth: Include auth header
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.get(
            url,
            params=params,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def post(self, endpoint: str, data: Dict = None, auth: bool = True) -> requests.Response:
        """
        Make POST request
        
        Args:
            endpoint: API endpoint
            data: Request body
            auth: Include auth header
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.post(
            url,
            json=data,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def put(self, endpoint: str, data: Dict = None, auth: bool = True) -> requests.Response:
        """Make PUT request with JSON body"""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(
            url,
            json=data,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def post_params(self, endpoint: str, params: Dict = None, auth: bool = True) -> requests.Response:
        """
        Make POST request with query parameters (not JSON body)
        
        Use this for FastAPI endpoints that expect query parameters.
        
        Args:
            endpoint: API endpoint
            params: Query parameters to send
            auth: Include auth header
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.post(
            url,
            params=params,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def put_params(self, endpoint: str, params: Dict = None, auth: bool = True) -> requests.Response:
        """
        Make PUT request with query parameters (not JSON body)
        
        Use this for FastAPI endpoints that expect query parameters.
        
        Args:
            endpoint: API endpoint
            params: Query parameters to send
            auth: Include auth header
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        return self.session.put(
            url,
            params=params,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def patch(self, endpoint: str, data: Dict = None, auth: bool = True) -> requests.Response:
        """Make PATCH request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.patch(
            url,
            json=data,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )
    
    def delete(self, endpoint: str, auth: bool = True) -> requests.Response:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(
            url,
            headers=self._get_headers(auth),
            timeout=self.timeout
        )


def run_test(
    name: str,
    category: str,
    test_fn: Callable[[], bool],
    skip_condition: bool = False,
    skip_reason: str = ""
) -> TestResult:
    """
    Run a single test with timing and error handling
    
    Args:
        name: Test name
        category: Test category
        test_fn: Test function that returns True on success
        skip_condition: If True, skip the test
        skip_reason: Reason for skipping
        
    Returns:
        TestResult object
    """
    if skip_condition:
        return TestResult(
            name=name,
            category=category,
            status=TestStatus.SKIPPED,
            message=skip_reason
        )
    
    start_time = time.time()
    try:
        success = test_fn()
        duration_ms = (time.time() - start_time) * 1000
        
        return TestResult(
            name=name,
            category=category,
            status=TestStatus.PASSED if success else TestStatus.FAILED,
            duration_ms=duration_ms,
            message="Test passed" if success else "Test assertion failed"
        )
    except AssertionError as e:
        duration_ms = (time.time() - start_time) * 1000
        return TestResult(
            name=name,
            category=category,
            status=TestStatus.FAILED,
            duration_ms=duration_ms,
            message=str(e)
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return TestResult(
            name=name,
            category=category,
            status=TestStatus.ERROR,
            duration_ms=duration_ms,
            message=f"Unexpected error: {str(e)}"
        )


def retry_test(max_retries: int = 3, delay_ms: int = 1000):
    """
    Decorator to retry flaky tests
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_ms: Delay between retries in milliseconds
    """
    def decorator(test_fn: Callable) -> Callable:
        @wraps(test_fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return test_fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay_ms / 1000)
            raise last_exception
        return wrapper
    return decorator


# Test project info template for agent tests
TEST_PROJECT_INFO = {
    'program_name': 'Advanced Logistics Management System (ALMS)',
    'organization': 'U.S. Army',
    'description': 'Cloud-based logistics tracking and inventory management system',
    'estimated_value': '$2.5M',
    'budget': '$2.5M',
    'timeline': '36 months',
    'contract_type': 'Firm Fixed Price (FFP)',
    'period_of_performance': '36 months (Base: 12 months + 2 Option Years)',
    'naics_code': '541512',
    'psc_code': 'D310',
    'set_aside': 'Small Business Set-Aside',
    'competition_type': 'Full and Open Competition',
    'technical_requirements': [
        'Cloud-native architecture (AWS/Azure)',
        'Real-time inventory tracking',
        'Mobile-first design',
        'Integration with existing DoD systems',
        'FedRAMP High authorization'
    ],
    'key_personnel': [
        {'role': 'Program Manager', 'level': 'Senior'},
        {'role': 'Technical Lead', 'level': 'Senior'},
        {'role': 'Cloud Architect', 'level': 'Mid-Senior'}
    ]
}


if __name__ == '__main__':
    # Validate configuration when run directly
    print("Validating Test Configuration...")
    print(f"API Base URL: {TestConfig.API_BASE_URL}")
    print(f"Reports Directory: {TestConfig.REPORTS_DIR}")
    print(f"Logs Directory: {TestConfig.LOGS_DIR}")
    
    issues = TestConfig.validate()
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Configuration is valid!")
    
    # Test API client
    print("\nTesting API Client...")
    client = APIClient()
    if client.login():
        print(f"✅ Login successful (user_id: {client.user_id})")
    else:
        print("❌ Login failed")
