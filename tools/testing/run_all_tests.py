#!/usr/bin/env python3
"""
Comprehensive Test Runner
=========================

Main test runner that executes all test suites and generates comprehensive reports.

Features:
- Runs all test categories (API, Agents, Services, Models, Integration)
- Generates HTML and JSON reports
- Supports selective category execution
- Parallel execution option
- Dry run mode
- CI/CD friendly exit codes

Usage:
    python run_all_tests.py                    # Run all tests
    python run_all_tests.py --category api     # Run only API tests
    python run_all_tests.py --dry-run          # Validate setup without executing
    python run_all_tests.py --parallel         # Run tests in parallel
    python run_all_tests.py --help             # Show help

Dependencies:
- test_config: Configuration and utilities
- test_api_endpoints: API endpoint tests
- test_all_agents: Agent tests
- test_all_services: Service tests
- test_database_models: Database model tests
- test_integration: Integration tests
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from tools.testing.test_config import (
    TestConfig, TestSuiteResults, TestStatus
)


class TestRunner:
    """
    Main test runner that orchestrates all test suites
    
    Features:
    - Runs multiple test suites
    - Aggregates results
    - Generates reports
    - CLI interface
    """
    
    def __init__(self, parallel: bool = False, verbose: bool = True):
        """
        Initialize test runner
        
        Args:
            parallel: Run test suites in parallel
            verbose: Print detailed output
        """
        self.parallel = parallel
        self.verbose = verbose
        self.start_time = datetime.now()
        self.suite_results: Dict[str, TestSuiteResults] = {}
        
        # Ensure output directories exist
        TestConfig.ensure_directories()
    
    def validate_environment(self) -> List[str]:
        """
        Validate test environment
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = TestConfig.validate()
        
        if self.verbose:
            if issues:
                print("\n⚠️  Environment Issues:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("\n✅ Environment validated")
        
        return issues
    
    def run_api_tests(self, category: str = None) -> TestSuiteResults:
        """Run API endpoint tests"""
        from tools.testing.test_api_endpoints import APIEndpointTests
        suite = APIEndpointTests()
        return suite.run_all(category=category)
    
    def run_agent_tests(self, phase: str = None) -> TestSuiteResults:
        """Run agent tests"""
        from tools.testing.test_all_agents import AgentTests
        suite = AgentTests()
        return suite.run_all(phase=phase, parallel=self.parallel)
    
    def run_service_tests(self, service: str = None) -> TestSuiteResults:
        """Run service tests"""
        from tools.testing.test_all_services import ServiceTests
        suite = ServiceTests()
        return suite.run_all(service=service)
    
    def run_model_tests(self, model: str = None) -> TestSuiteResults:
        """Run database model tests"""
        from tools.testing.test_database_models import DatabaseModelTests
        suite = DatabaseModelTests()
        return suite.run_all(model=model)
    
    def run_integration_tests(self, workflow: str = None) -> TestSuiteResults:
        """Run integration tests"""
        from tools.testing.test_integration import IntegrationTests
        suite = IntegrationTests()
        return suite.run_all(workflow=workflow)
    
    def run_all(self, categories: List[str] = None) -> Dict[str, TestSuiteResults]:
        """
        Run all test suites
        
        Args:
            categories: List of categories to run (None = all)
            
        Returns:
            Dictionary of suite name to results
        """
        print("\n" + "=" * 70)
        print("🧪 DOD CONTRACTING SYSTEM - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Parallel: {'Yes' if self.parallel else 'No'}")
        
        # Define available test suites
        all_suites = {
            'api': ('API Endpoints', self.run_api_tests),
            'agents': ('Document Agents', self.run_agent_tests),
            'services': ('Backend Services', self.run_service_tests),
            'models': ('Database Models', self.run_model_tests),
            'integration': ('Integration Workflows', self.run_integration_tests),
        }
        
        # Filter categories if specified
        if categories:
            suites = {k: v for k, v in all_suites.items() if k in categories}
        else:
            suites = all_suites
        
        print(f"Categories: {', '.join(suites.keys())}")
        print("=" * 70)
        
        # Validate environment
        issues = self.validate_environment()
        
        # Run suites
        if self.parallel:
            with ThreadPoolExecutor(max_workers=len(suites)) as executor:
                futures = {}
                for suite_id, (suite_name, suite_fn) in suites.items():
                    futures[executor.submit(suite_fn)] = (suite_id, suite_name)
                
                for future in as_completed(futures):
                    suite_id, suite_name = futures[future]
                    try:
                        results = future.result()
                        self.suite_results[suite_id] = results
                    except Exception as e:
                        print(f"❌ {suite_name} failed: {e}")
        else:
            for suite_id, (suite_name, suite_fn) in suites.items():
                print(f"\n{'='*70}")
                print(f"📋 {suite_name.upper()}")
                print('='*70)
                
                try:
                    results = suite_fn()
                    self.suite_results[suite_id] = results
                except Exception as e:
                    print(f"❌ {suite_name} failed: {e}")
        
        return self.suite_results
    
    def generate_summary(self) -> Dict:
        """
        Generate summary of all test results
        
        Returns:
            Summary dictionary
        """
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        total_duration_ms = 0
        
        for suite_results in self.suite_results.values():
            total_tests += suite_results.total
            total_passed += suite_results.passed
            total_failed += suite_results.failed
            total_skipped += suite_results.skipped
            total_errors += suite_results.errors
            total_duration_ms += suite_results.total_duration_ms
        
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'skipped': total_skipped,
            'errors': total_errors,
            'pass_rate': f"{(total_passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
            'duration_seconds': total_duration_ms / 1000,
            'suites': {k: v.to_dict() for k, v in self.suite_results.items()}
        }
    
    def print_summary(self):
        """Print summary to console"""
        summary = self.generate_summary()
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        # Per-suite summary
        for suite_id, results in self.suite_results.items():
            pass_icon = "✅" if results.failed == 0 and results.errors == 0 else "❌"
            print(f"  {pass_icon} {results.suite_name}: {results.passed}/{results.total} passed")
        
        print("-" * 70)
        print(f"Total Tests:    {summary['total_tests']}")
        print(f"  ✅ Passed:    {summary['passed']}")
        print(f"  ❌ Failed:    {summary['failed']}")
        print(f"  ⏭️  Skipped:   {summary['skipped']}")
        print(f"  💥 Errors:    {summary['errors']}")
        print(f"Pass Rate:      {summary['pass_rate']}")
        print(f"Duration:       {summary['duration_seconds']:.2f}s")
        print("=" * 70)
        
        # Print failed tests
        all_failed = []
        for suite_id, results in self.suite_results.items():
            for result in results.results:
                if result.status in (TestStatus.FAILED, TestStatus.ERROR):
                    all_failed.append((suite_id, result))
        
        if all_failed:
            print("\n❌ FAILED TESTS:")
            for suite_id, result in all_failed:
                print(f"  [{suite_id}] {result.name}: {result.message}")
    
    def save_reports(self) -> Dict[str, Path]:
        """
        Save reports to files
        
        Returns:
            Dictionary of report type to file path
        """
        reports = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON report
        json_path = TestConfig.REPORTS_DIR / f"test_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.generate_summary(), f, indent=2)
        reports['json'] = json_path
        
        # HTML report
        html_path = TestConfig.REPORTS_DIR / f"test_report_{timestamp}.html"
        self._generate_html_report(html_path)
        reports['html'] = html_path
        
        print(f"\n📄 Reports saved:")
        print(f"  JSON: {json_path}")
        print(f"  HTML: {html_path}")
        
        return reports
    
    def _generate_html_report(self, filepath: Path):
        """Generate HTML report"""
        summary = self.generate_summary()
        
        # Calculate pass rate for color
        pass_rate = summary['passed'] / summary['total_tests'] * 100 if summary['total_tests'] > 0 else 0
        status_color = '#22c55e' if pass_rate >= 80 else '#eab308' if pass_rate >= 60 else '#ef4444'
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {summary['start_time'][:10]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; color: #1f2937; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        h1 {{ font-size: 1.875rem; font-weight: 700; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #6b7280; margin-bottom: 2rem; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: white; border-radius: 0.5rem; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .card-title {{ font-size: 0.875rem; color: #6b7280; margin-bottom: 0.5rem; }}
        .card-value {{ font-size: 2rem; font-weight: 700; }}
        .card-value.passed {{ color: #22c55e; }}
        .card-value.failed {{ color: #ef4444; }}
        .card-value.skipped {{ color: #eab308; }}
        .card-value.rate {{ color: {status_color}; }}
        .suite {{ background: white; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .suite-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }}
        .suite-name {{ font-size: 1.25rem; font-weight: 600; }}
        .suite-stats {{ color: #6b7280; }}
        .progress-bar {{ height: 0.5rem; background: #e5e7eb; border-radius: 0.25rem; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: #22c55e; transition: width 0.3s; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; }}
        .status {{ padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }}
        .status.passed {{ background: #dcfce7; color: #166534; }}
        .status.failed {{ background: #fee2e2; color: #991b1b; }}
        .status.skipped {{ background: #fef3c7; color: #92400e; }}
        .status.error {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 DoD Contracting System Test Report</h1>
        <p class="subtitle">Generated: {summary['start_time']}</p>
        
        <div class="summary-grid">
            <div class="card">
                <div class="card-title">Total Tests</div>
                <div class="card-value">{summary['total_tests']}</div>
            </div>
            <div class="card">
                <div class="card-title">Passed</div>
                <div class="card-value passed">{summary['passed']}</div>
            </div>
            <div class="card">
                <div class="card-title">Failed</div>
                <div class="card-value failed">{summary['failed']}</div>
            </div>
            <div class="card">
                <div class="card-title">Pass Rate</div>
                <div class="card-value rate">{summary['pass_rate']}</div>
            </div>
        </div>
"""
        
        # Add suite details
        for suite_id, results in self.suite_results.items():
            suite_pass_rate = (results.passed / results.total * 100) if results.total > 0 else 0
            html += f"""
        <div class="suite">
            <div class="suite-header">
                <span class="suite-name">{results.suite_name}</span>
                <span class="suite-stats">{results.passed}/{results.total} passed ({suite_pass_rate:.1f}%)</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {suite_pass_rate}%"></div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
"""
            for result in results.results:
                status_class = result.status.value
                html += f"""
                    <tr>
                        <td>{result.name}</td>
                        <td><span class="status {status_class}">{result.status.value.upper()}</span></td>
                        <td>{result.duration_ms:.0f}ms</td>
                        <td>{result.message[:100] if result.message else '-'}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w') as f:
            f.write(html)
    
    def get_exit_code(self) -> int:
        """
        Get exit code based on results
        
        Returns:
            0 if all tests passed, 1 otherwise
        """
        for results in self.suite_results.values():
            if results.failed > 0 or results.errors > 0:
                return 1
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run comprehensive test suite for DoD Contracting System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_tests.py                     # Run all tests
  python run_all_tests.py -c api              # Run only API tests
  python run_all_tests.py -c api agents       # Run API and agent tests
  python run_all_tests.py --parallel          # Run suites in parallel
  python run_all_tests.py --dry-run           # Validate environment only
        """
    )
    
    parser.add_argument(
        '--category', '-c',
        nargs='+',
        choices=['api', 'agents', 'services', 'models', 'integration'],
        help='Test categories to run (default: all)'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run test suites in parallel'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate environment without running tests'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = TestRunner(parallel=args.parallel, verbose=not args.quiet)
    
    # Dry run - just validate
    if args.dry_run:
        print("\n🔍 DRY RUN - Validating environment...")
        issues = runner.validate_environment()
        
        print("\n📋 Available test categories:")
        print("  - api: 92 API endpoint tests")
        print("  - agents: 40+ document agent tests")
        print("  - services: 13 backend service tests")
        print("  - models: 6 database model tests")
        print("  - integration: 8 workflow tests")
        
        if issues:
            print("\n⚠️  Some tests may be skipped due to environment issues")
            sys.exit(1)
        else:
            print("\n✅ Ready to run tests")
            sys.exit(0)
    
    # Run tests
    runner.run_all(categories=args.category)
    
    # Print summary
    runner.print_summary()
    
    # Save reports
    if not args.no_report:
        runner.save_reports()
    
    # Exit with appropriate code
    sys.exit(runner.get_exit_code())


if __name__ == '__main__':
    main()
