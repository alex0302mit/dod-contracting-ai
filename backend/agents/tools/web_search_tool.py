"""
Web Search Tool: Wrapper for Tavily API with acquisition-specific enhancements
"""

from typing import List, Dict, Optional
import os
from datetime import datetime


class WebSearchTool:
    """
    Web search tool optimized for government acquisition research
    
    Features:
    - General web search
    - News search (for recent developments)
    - Domain-specific search (SAM.gov, FPDS, etc.)
    - Result filtering and ranking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize web search tool
        
        Args:
            api_key: Tavily API key (or set TAVILY_API_KEY env var)
        """
        try:
            from tavily import TavilyClient
        except ImportError:
            raise ImportError(
                "Tavily not installed. Run: pip install tavily-python"
            )
        
        self.api_key = api_key or os.environ.get('TAVILY_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Tavily API key required. Set TAVILY_API_KEY environment variable "
                "or pass api_key parameter. Get free key at: https://tavily.com"
            )
        
        self.client = TavilyClient(api_key=self.api_key)
        
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        topic: str = "general"
    ) -> List[Dict]:
        """
        Perform web search
        
        Args:
            query: Search query
            max_results: Number of results (1-20)
            search_depth: "basic" or "advanced" (advanced is slower but better)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
            topic: "general" or "news"
            
        Returns:
            List of search result dictionaries with:
                - title: Result title
                - url: Result URL
                - content: Extracted content
                - score: Relevance score
                - published_date: Publication date (if available)
        """
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "topic": topic
            }
            
            if include_domains:
                search_params["include_domains"] = include_domains
            
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            
            # Execute search
            response = self.client.search(**search_params)
            
            # Format results
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0.0),
                    'published_date': result.get('published_date', ''),
                    'raw': result  # Keep original for debugging
                })
            
            return results
            
        except Exception as e:
            print(f"⚠️  Web search error: {e}")
            return []
    
    def search_vendor_information(
        self,
        company_name: str,
        naics_code: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for vendor/company information
        
        Args:
            company_name: Name of company to research
            naics_code: Optional NAICS code to refine search
            
        Returns:
            Search results focused on company capabilities
        """
        query_parts = [company_name, "government contractor"]
        
        if naics_code:
            query_parts.append(f"NAICS {naics_code}")
        
        query = " ".join(query_parts)
        
        # Search with preference for official sources
        return self.search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_domains=[
                "sam.gov",
                "fpds.gov",
                "sba.gov",
                "dnb.com",
                "bloomberg.gov"
            ]
        )
    
    def search_market_pricing(
        self,
        service_type: str,
        naics_code: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for current market pricing data
        
        Args:
            service_type: Type of service (e.g., "IT support", "cloud services")
            naics_code: NAICS code
            year: Year for pricing (defaults to current)
            
        Returns:
            Search results with pricing information
        """
        year = year or datetime.now().year
        
        query = f"{service_type} government contract pricing {year}"
        if naics_code:
            query += f" NAICS {naics_code}"
        
        return self.search(
            query=query,
            max_results=7,
            search_depth="advanced",
            topic="general"
        )
    
    def search_recent_awards(
        self,
        service_type: str,
        agency: Optional[str] = None,
        days_back: int = 90
    ) -> List[Dict]:
        """
        Search for recent contract awards
        
        Args:
            service_type: Type of service
            agency: Government agency (e.g., "DOD", "Army", "Air Force")
            days_back: How many days back to search
            
        Returns:
            Recent contract award announcements
        """
        query_parts = [service_type, "contract award"]
        
        if agency:
            query_parts.append(agency)
        
        query = " ".join(query_parts)
        
        return self.search(
            query=query,
            max_results=10,
            search_depth="basic",
            topic="news",  # Use news topic for recent awards
            include_domains=[
                "defense.gov",
                "army.mil",
                "af.mil",
                "navy.mil",
                "fpds.gov",
                "governmentcontractswon.com"
            ]
        )
    
    def search_small_business_info(
        self,
        company_name: str
    ) -> List[Dict]:
        """
        Search for small business certification information
        
        Args:
            company_name: Name of company
            
        Returns:
            Information about SB certifications
        """
        query = f"{company_name} small business 8a HUBZone WOSB SDVOSB certification"
        
        return self.search(
            query=query,
            max_results=5,
            search_depth="advanced",
            include_domains=[
                "sam.gov",
                "sba.gov",
                "certify.sba.gov"
            ]
        )
    
    def extract_pricing_from_results(
        self,
        results: List[Dict]
    ) -> Dict:
        """
        Extract pricing information from search results
        
        Args:
            results: Search results
            
        Returns:
            Dictionary with extracted pricing data
        """
        import re
        
        pricing_data = {
            'prices_found': [],
            'sources': [],
            'date_ranges': [],
            'labor_categories': {}
        }
        
        # Common pricing patterns
        price_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:per|/)\s*(?:hour|hr|year|yr|month|mo))?',
            r'[\d,]+\s+dollars?(?:\s*(?:per|/)\s*(?:hour|hr|year|yr))?',
        ]
        
        for result in results:
            content = result.get('content', '')
            
            # Extract prices
            for pattern in price_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    pricing_data['prices_found'].append({
                        'value': match,
                        'source': result.get('url', ''),
                        'title': result.get('title', '')
                    })
            
            # Extract year/date info
            year_matches = re.findall(r'20\d{2}', content)
            pricing_data['date_ranges'].extend(year_matches)
        
        return pricing_data