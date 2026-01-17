# Create: scripts/benchmark_system.py
#!/usr/bin/env python3
"""
Comprehensive system benchmark after changes
"""
import time
import os
from datetime import datetime

def benchmark_system():
    print("="*70)
    print("COMPREHENSIVE SYSTEM BENCHMARK")
    print("="*70)
    
    start_time = time.time()
    
    tests = [
        ('RAG System', 'python scripts/test_rag_system.py'),
        ('Phase 1 Agents', 'python scripts/test_phase1_complete.py'),
        ('Phase 2 Agent 1', 'python scripts/test_acquisition_plan_agent.py'),
        ('Optional Sections', 'python scripts/test_optional_sections.py'),
        ('Quality Systems', 'python scripts/test_quality_agent.py')
    ]
    
    results = []
    
    for test_name, command in tests:
        print(f"\n🧪 Running: {test_name}")
        test_start = time.time()
        
        exit_code = os.system(command)
        
        test_duration = time.time() - test_start
        status = "✅ PASS" if exit_code == 0 else "❌ FAIL"
        results.append((test_name, status, test_duration))
        
        print(f"   {status} - Duration: {test_duration:.1f}s")
    
    total_duration = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("BENCHMARK SUMMARY")
    print('='*70)
    print(f"Total test time: {total_duration:.1f}s")
    print(f"Tests run: {len(tests)}")
    
    passed = sum(1 for _, status, _ in results if "PASS" in status)
    print(f"Tests passed: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    
    print(f"\nDetailed results:")
    for name, status, duration in results:
        print(f"  {status} {name:<20} ({duration:.1f}s)")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = benchmark_system()
    exit(0 if success else 1)