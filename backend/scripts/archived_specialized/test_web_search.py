"""
Test script for Web Search Tool
Demonstrates various search capabilities using Tavily API
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports

from backend.agents.tools.web_search_tool import WebSearchTool
from dotenv import load_dotenv


def test_market_pricing():
    """Test market pricing search"""
    print("\n" + "="*70)
    print("TEST 1: MARKET PRICING SEARCH")
    print("="*70 + "\n")

    tool = WebSearchTool()

    print("Searching for cloud infrastructure services pricing...")
    results = tool.search_market_pricing(
        service_type="cloud infrastructure services",
        naics_code="541519",
        year=2025
    )

    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Score: {result['score']:.2f}")
        print(f"   Preview: {result['content'][:200]}...")
        print()

    return len(results) > 0


def test_recent_awards():
    """Test recent contract awards search"""
    print("\n" + "="*70)
    print("TEST 2: RECENT CONTRACT AWARDS")
    print("="*70 + "\n")

    tool = WebSearchTool()

    print("Searching for recent DOD cybersecurity contract awards...")
    awards = tool.search_recent_awards(
        service_type="cybersecurity services",
        agency="DOD",
        days_back=30
    )

    print(f"\nFound {len(awards)} recent awards:\n")
    for i, award in enumerate(awards[:3], 1):
        print(f"{i}. {award['title']}")
        print(f"   Date: {award.get('published_date', 'Unknown')}")
        print(f"   URL: {award['url']}")
        print(f"   Score: {award['score']:.2f}")
        print()

    return len(awards) > 0


def test_vendor_search():
    """Test vendor information search"""
    print("\n" + "="*70)
    print("TEST 3: VENDOR INFORMATION SEARCH")
    print("="*70 + "\n")

    tool = WebSearchTool()

    vendor_name = "Lockheed Martin"
    print(f"Searching for vendor information: {vendor_name}...")

    results = tool.search_vendor_information(
        company_name=vendor_name,
        naics_code="541512"  # Computer Systems Design Services
    )

    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Preview: {result['content'][:200]}...")
        print()

    return len(results) > 0


def test_small_business_search():
    """Test small business certification search"""
    print("\n" + "="*70)
    print("TEST 4: SMALL BUSINESS CERTIFICATION SEARCH")
    print("="*70 + "\n")

    tool = WebSearchTool()

    company_name = "8(a) certified company"
    print(f"Searching for small business certifications...")

    results = tool.search_small_business_info(company_name=company_name)

    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Preview: {result['content'][:200]}...")
        print()

    return len(results) > 0


def test_general_search():
    """Test general web search"""
    print("\n" + "="*70)
    print("TEST 5: GENERAL WEB SEARCH")
    print("="*70 + "\n")

    tool = WebSearchTool()

    query = "FAR Part 15 source selection procedures"
    print(f"Searching for: {query}...")

    results = tool.search(
        query=query,
        max_results=5,
        search_depth="advanced"
    )

    print(f"\nFound {len(results)} results:\n")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Score: {result['score']:.2f}")
        print(f"   Preview: {result['content'][:200]}...")
        print()

    return len(results) > 0


def test_pricing_extraction():
    """Test pricing data extraction from results"""
    print("\n" + "="*70)
    print("TEST 6: PRICING DATA EXTRACTION")
    print("="*70 + "\n")

    tool = WebSearchTool()

    print("Searching for pricing data and extracting dollar amounts...")
    results = tool.search_market_pricing(
        service_type="IT consulting services hourly rates",
        year=2025
    )

    # Extract pricing
    pricing_data = tool.extract_pricing_from_results(results)

    print(f"\nExtracted {len(pricing_data['prices_found'])} price points:\n")
    for i, price in enumerate(pricing_data['prices_found'][:5], 1):
        print(f"{i}. {price['value']}")
        print(f"   Source: {price['title']}")
        print(f"   URL: {price['source']}")
        print()

    if pricing_data['date_ranges']:
        print(f"Date ranges found: {set(pricing_data['date_ranges'])}")

    return len(pricing_data['prices_found']) > 0


def main():
    """Run all web search tests"""
    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.environ.get('TAVILY_API_KEY'):
        print("❌ ERROR: TAVILY_API_KEY not found in environment variables")
        print("Please add it to your .env file")
        return

    print("\n" + "="*70)
    print("WEB SEARCH TOOL - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"\nAPI Key loaded: {os.environ.get('TAVILY_API_KEY')[:20]}...")

    # Run tests
    tests = [
        ("Market Pricing Search", test_market_pricing),
        ("Recent Awards Search", test_recent_awards),
        ("Vendor Information Search", test_vendor_search),
        ("Small Business Search", test_small_business_search),
        ("General Web Search", test_general_search),
        ("Pricing Extraction", test_pricing_extraction),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "✅ PASSED" if success else "⚠️  NO RESULTS"
        except Exception as e:
            results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"\n❌ Error in {test_name}: {e}\n")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")

    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)

    print(f"\n{passed}/{total} tests passed")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
