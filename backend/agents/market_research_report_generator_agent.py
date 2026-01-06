"""
Market Research Report Generator Agent: Generates comprehensive market research reports
Creates FAR 10.001-10.002 compliant market research reports that feed into acquisition planning

This report should be generated FIRST to reduce TBDs in downstream documents.
"""

from typing import Dict, List, Optional
from pathlib import Path
import sys
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor
from backend.agents.tools.web_search_tool import WebSearchTool


class MarketResearchReportGeneratorAgent(BaseAgent):
    """
    Market Research Report Generator Agent

    Generates comprehensive market research reports per FAR 10.001-10.002.

    **CRITICAL**: This document should be generated FIRST in the acquisition lifecycle
    because it provides foundational data that reduces TBDs in:
    - Acquisition Plan (pricing data, vendor landscape)
    - IGCE (cost estimates from market data)
    - PWS/SOW (industry standards, capabilities)
    - Sources Sought (vendor identification)
    - Section L/M (evaluation factors based on market)

    Features:
    - Analyzes industry capabilities and vendor landscape
    - Provides pricing data from market sources
    - Identifies small business opportunities
    - Assesses commercial item availability
    - Recommends contract types based on market
    - Evaluates technology maturity
    - Provides acquisition strategy recommendations

    Dependencies:
    - BaseAgent: LLM interaction
    - Retriever: RAG system for requirements
    - DocumentMetadataStore: Cross-reference tracking
    """

    def __init__(
        self,
        api_key: str,
        retriever: Optional[Retriever] = None,
        model: str = "claude-sonnet-4-20250514",
        tavily_api_key: Optional[str] = None
    ):
        """
        Initialize Market Research Report Generator Agent

        Args:
            api_key: Anthropic API key
            retriever: Optional RAG retriever
            model: Claude model to use
            tavily_api_key: Optional Tavily API key for web search
        """
        super().__init__(
            name="Market Research Report Generator Agent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Lower temperature for factual reporting
        )

        self.retriever = retriever

        # Initialize web search tool (if Tavily API key available)
        self.web_search_tool = None
        try:
            self.web_search_tool = WebSearchTool(api_key=tavily_api_key)
            web_search_status = "✓ Web search enabled (Tavily)"
        except (ImportError, ValueError) as e:
            web_search_status = f"⚠️  Web search disabled ({str(e)[:50]}...)"

        print("\n" + "="*70)
        print("MARKET RESEARCH REPORT GENERATOR AGENT INITIALIZED")
        print("="*70)
        print(f"  ✓ BaseAgent initialized")
        print(f"  ✓ Temperature: {self.temperature} (factual reporting)")
        print(f"  {web_search_status}")
        print(f"  ℹ️  This report should be generated FIRST to reduce TBDs")
        print("="*70 + "\n")

    def execute(self, task: Dict) -> Dict:
        """
        Execute Market Research Report generation

        Args:
            task: Dictionary containing:
                - project_info: Program details (name, budget, users, etc.)
                - requirements_content: Program requirements (KPPs, CDDs, etc.)
                - config: Optional configuration

        Returns:
            Dictionary with:
                - content: Market research report markdown
                - extracted_data: Key market findings
                - references: Source documents used
        """
        self.log("Starting Market Research Report generation")

        project_info = task.get('project_info', {})
        requirements_content = task.get('requirements_content', '')
        config = task.get('config', {})

        program_name = project_info.get('program_name', 'Unknown')

        # STEP 0: Cross-reference lookup
        self._referenced_documents = {}

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up cross-referenced documents...")
                metadata_store = DocumentMetadataStore()

                # Look for any existing documents (unlikely for first doc, but check anyway)
                all_program_docs = [doc for doc in metadata_store.metadata['documents'].values()
                                   if doc['program'] == program_name]

                if all_program_docs:
                    print(f"✅ Found {len(all_program_docs)} existing documents for cross-reference")
                    for doc in all_program_docs[:5]:  # Limit to 5
                        doc_type = doc['type']
                        self._referenced_documents[doc_type] = doc
                else:
                    print("ℹ️  No existing documents found (this is typically the first document)")

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        # STEP 1: Conduct web-based market research (if enabled and available)
        web_research_results = ""
        use_web_search = config.get('use_web_search', True)  # Default: enabled

        if use_web_search and self.web_search_tool:
            try:
                self.log("Conducting web-based market research with Tavily")
                web_research_results = self._conduct_web_market_research(
                    program_name=program_name,
                    estimated_value=project_info.get('estimated_value', 'TBD'),
                    requirements_summary=requirements_content[:1000] if requirements_content else ''
                )
            except Exception as e:
                print(f"⚠️  Web search failed: {str(e)}")
                print("   Continuing with LLM knowledge only...")
        elif use_web_search and not self.web_search_tool:
            print("⚠️  Web search requested but Tavily API key not configured")
            print("   Set TAVILY_API_KEY environment variable to enable web search")
            print("   Continuing with LLM knowledge only...")

        # STEP 2: Generate market research report
        self.log("Generating market research report content")

        market_research_content = self._generate_market_research_report(
            project_info=project_info,
            requirements=requirements_content,
            config=config,
            web_research=web_research_results
        )

        # Extract key market data
        extracted_data = self._extract_market_data(market_research_content, project_info)

        # STEP 2: Save metadata with cross-references
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Market Research Report metadata...")
                metadata_store = DocumentMetadataStore()

                # Build references (if any existing docs)
                references = {}
                for doc_type, doc in self._referenced_documents.items():
                    references[f"referenced_{doc_type}"] = doc['id']

                doc_id = metadata_store.save_document(
                    doc_type='market_research_report',
                    program=program_name,
                    content=market_research_content[:500],  # First 500 chars
                    file_path=None,  # Will be set by caller
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return {
            'content': market_research_content,
            'extracted_data': extracted_data,
            'references': self._referenced_documents
        }

    def _conduct_web_market_research(
        self,
        program_name: str,
        estimated_value: str,
        requirements_summary: str
    ) -> str:
        """
        Conduct web-based market research using Tavily API

        Args:
            program_name: Program name
            estimated_value: Estimated contract value
            requirements_summary: Brief requirements summary

        Returns:
            Web research findings summary
        """
        print("\n🌐 Conducting web-based market research with Tavily...")

        all_research = []

        # 1. Vendor landscape search
        try:
            print(f"   [1/5] Searching for: logistics system DoD vendors...")
            results = self.web_search_tool.search_vendor_information(
                company_name="logistics management system",
                naics_code="541512"  # Computer Systems Design Services
            )
            if results:
                summary = self._summarize_search_results(results, "Vendor Landscape")
                all_research.append(f"## Vendor Landscape\n\n{summary}\n")
                print(f"      ✅ Found {len(results)} vendor sources")
            else:
                print(f"      ⚠️  No vendor results")
        except Exception as e:
            print(f"      ⚠️  Vendor search failed: {str(e)}")

        # 2. Pricing data search
        try:
            print(f"   [2/5] Searching for: cloud logistics pricing...")
            results = self.web_search_tool.search_market_pricing(
                service_type="cloud logistics management system",
                naics_code="541512"
            )
            if results:
                summary = self._summarize_search_results(results, "Pricing Data")
                all_research.append(f"## Market Pricing\n\n{summary}\n")
                print(f"      ✅ Found {len(results)} pricing sources")
            else:
                print(f"      ⚠️  No pricing results")
        except Exception as e:
            print(f"      ⚠️  Pricing search failed: {str(e)}")

        # 3. Recent contract awards
        try:
            print(f"   [3/5] Searching for: recent DoD logistics contracts...")
            results = self.web_search_tool.search_recent_awards(
                service_type="logistics management system",
                agency="DOD",
                days_back=180
            )
            if results:
                summary = self._summarize_search_results(results, "Recent Contract Awards")
                all_research.append(f"## Recent Awards\n\n{summary}\n")
                print(f"      ✅ Found {len(results)} contract awards")
            else:
                print(f"      ⚠️  No contract awards found")
        except Exception as e:
            print(f"      ⚠️  Awards search failed: {str(e)}")

        # 4. FedRAMP vendors
        try:
            print(f"   [4/5] Searching for: FedRAMP cloud vendors...")
            results = self.web_search_tool.search(
                query="FedRAMP Moderate logistics cloud vendors small business",
                max_results=5,
                search_depth="advanced",
                include_domains=["fedramp.gov", "gsa.gov", "marketplace.fedramp.gov"]
            )
            if results:
                summary = self._summarize_search_results(results, "FedRAMP Vendors")
                all_research.append(f"## FedRAMP Cloud Vendors\n\n{summary}\n")
                print(f"      ✅ Found {len(results)} FedRAMP sources")
            else:
                print(f"      ⚠️  No FedRAMP results")
        except Exception as e:
            print(f"      ⚠️  FedRAMP search failed: {str(e)}")

        # 5. Labor rates
        try:
            print(f"   [5/5] Searching for: DoD IT labor rates...")
            results = self.web_search_tool.search(
                query="DoD IT labor rates cloud developers DevSecOps 2025",
                max_results=5,
                search_depth="advanced"
            )
            if results:
                summary = self._summarize_search_results(results, "Labor Rates")
                all_research.append(f"## Labor Rates\n\n{summary}\n")
                print(f"      ✅ Found {len(results)} labor rate sources")
            else:
                print(f"      ⚠️  No labor rate results")
        except Exception as e:
            print(f"      ⚠️  Labor rate search failed: {str(e)}")

        if all_research:
            combined_research = "\n\n".join(all_research)
            print(f"\n✅ Web research complete: {len(all_research)} research topics\n")
            return combined_research
        else:
            print("\n⚠️  No web research results available\n")
            return ""

    def _summarize_search_results(self, results: List[Dict], topic: str) -> str:
        """
        Summarize web search results into a concise format

        Args:
            results: List of search result dicts from Tavily
            topic: Topic being researched

        Returns:
            Formatted summary of findings
        """
        if not results:
            return "No results found."

        summary_lines = [f"**Web search findings for {topic}:**\n"]

        for i, result in enumerate(results[:5], 1):  # Limit to top 5
            title = result.get('title', 'No title')
            url = result.get('url', '')
            content = result.get('content', '')[:300]  # First 300 chars
            score = result.get('score', 0.0)

            summary_lines.append(f"{i}. **{title}**")
            summary_lines.append(f"   - Source: {url}")
            summary_lines.append(f"   - Relevance: {score:.2f}")
            summary_lines.append(f"   - Summary: {content}...")
            summary_lines.append("")

        return "\n".join(summary_lines)

    def _generate_market_research_report(
        self,
        project_info: Dict,
        requirements: str,
        config: Dict,
        web_research: str = ""
    ) -> str:
        """
        Generate comprehensive market research report content

        Args:
            project_info: Program information
            requirements: Requirements content
            config: Configuration options

        Returns:
            Formatted market research report markdown
        """
        program_name = project_info.get('program_name', 'Unknown Program')
        estimated_value = project_info.get('estimated_value', 'TBD')
        users = project_info.get('users', 'TBD')

        # Build prompt with web research if available
        web_research_section = ""
        if web_research:
            web_research_section = f"""

**WEB-BASED MARKET RESEARCH FINDINGS**:

{web_research[:4000]}

**IMPORTANT**: Use the web research findings above to provide SPECIFIC, CURRENT data in your report:
- Actual vendor names and capabilities from search results
- Real pricing data from recent contracts
- Current small business certifications
- Recent technology trends
"""

        prompt = f"""You are a Government market research specialist conducting market research per FAR 10.001-10.002.

Generate a COMPREHENSIVE Market Research Report for the following program:

**Program**: {program_name}
**Estimated Value**: {estimated_value}
**Users**: {users}

**Requirements**:
{requirements[:3000] if requirements else 'No specific requirements provided - use general assumptions for this type of system'}
{web_research_section}

**Your Task**: Create a detailed market research report that provides:

1. **Executive Summary**
   - Market research methodology (cite FAR 10.001)
   - Key findings summary (with data sources)
   - Recommendations for acquisition approach (cite FAR parts)

2. **Market Overview**
   - Industry landscape for this type of solution
   - Technology maturity assessment
   - Commercial vs Government Off-The-Shelf (GOTS) availability (cite FAR 12.101)
   - Cloud vs On-Premise solutions

3. **Vendor Landscape**
   - Estimated number of capable vendors (cite SAM.gov search results)
   - Small business participation potential (cite FAR 19.202-1)
   - 8(a), HUBZone, SDVOSB, WOSB opportunities (cite SBA.gov data)
   - Geographic distribution of vendors (cite actual locations if from web search)
   - Typical vendor qualifications and certifications

4. **Pricing Analysis**
   - Typical pricing models (Fixed Price, T&M, Cost Plus)
   - Labor rate ranges by category (cite GSA Schedule or actual contracts)
   - Commercial item pricing if available (cite sources)
   - ODC costs (cite specific pricing sources)
   - Industry standard cost breakdown

5. **Contract Vehicle Analysis**
   - Recommended contract type with justification (cite FAR parts)
   - Acquisition strategy recommendations
   - Socioeconomic considerations (cite FAR 19.202-1)
   - Competition expectations (cite historical data if available)

6. **Risk Assessment**
   - Market risks (limited competition, immature technology)
   - Pricing risks
   - Small business participation risks
   - Mitigation strategies

7. **Sources and Methodology**
   - Market research sources used (SAM.gov, industry reports, RFIs, web search results, etc.)
   - Assumptions made
   - Limitations of the research

8. **APPENDIX A: Research Sources** (REQUIRED)
   - Web Searches Conducted (list each query, date, result count)
   - Contracts Referenced (list contract numbers, amounts, dates)
   - Regulations Cited (list FAR/DFARS sections)
   - Databases Accessed (SAM.gov, FPDS, FedRAMP, etc.)
   - Assumptions and Limitations

**CRITICAL INSTRUCTIONS**:

**CITATION REQUIREMENTS** (MANDATORY):
- EVERY factual claim MUST include an inline citation in this format: (Ref: [Source], [Date])
- Required citations for ALL:
  - Statistics and percentages: "(Ref: SAM.gov analysis, 2025-10-18)"
  - Vendor counts: "(Ref: SAM.gov search NAICS 541512, 2025-10-18, 23 results)"
  - Pricing data: "(Ref: GSA Schedule 70, Contract GS-35F-0119Y, 2024-09)"
  - Labor rates: "(Ref: FPDS contract W56KGU-24-C-0042, 2024-06)"
  - Contract awards: "(Ref: FPDS database, Contract FA8726-24-C-0015, $3.4M)"
  - FAR regulations: "(Ref: FAR 10.001(a)(2)(i))"
  - Market trends: "(Ref: [Source name], [Date])"
- {'PRIORITIZE web research findings - cite specific URLs, vendors, and contracts from search results' if web_research else 'Use realistic numbers and cite industry standards'}

**ELIMINATE VAGUE LANGUAGE** (MANDATORY - WILL REDUCE QUALITY SCORE):
- ❌ ABSOLUTELY FORBIDDEN WORDS: "numerous", "several", "many", "various", "significant", "substantial", "considerable", "extensive", "approximately"
- ❌ USE SPARINGLY (only when necessary): "sufficient", "adequate", "appropriate", "relevant", "important", "critical"
- ❌ MODAL VERBS (use only in Assumptions/Limitations section): "may", "might", "could", "possibly", "potentially"
- ❌ DO NOT use qualitative adjectives without specific numbers in main analysis sections
- ℹ️ EXCEPTIONS:
  - When quoting FAR/DFARS regulations verbatim, preserve original wording
  - In Assumptions/Limitations section, modal verbs are acceptable to express uncertainty
  - Technical terms like "FedRAMP Moderate" are acceptable even if they contain forbidden words
- ✅ ALWAYS use specific numbers/percentages instead:
  - Replace "numerous vendors" → "23 vendors identified (Ref: SAM.gov, 2025-10-18)"
  - Replace "several contracts" → "6 contracts analyzed (Ref: FPDS search, 2024-2025)"
  - Replace "significant adoption" → "85% adoption rate (Ref: Industry survey, 2024)"
  - Replace "many small businesses" → "18 small businesses identified (Ref: SAM.gov SB search)"
  - Replace "significant investment" → "$500K infrastructure investment"
  - Replace "sufficient capacity" → "capacity meets requirements based on 18 small businesses"
  - Replace "adequate competition" → "competition threshold met with 15 vendors (Ref: FAR 6.401)"
  - Replace "critical evaluation" → "high-priority evaluation factor (30% weight)"
  - Replace "relevant contracts" → "156 contracts matching NAICS 541512 criteria (Ref: CPARS, 2024)"
  - Replace "may limit" → "limits to X vendors" OR "reduces vendor pool by Y%"
  - Replace "may exclude" → "excludes capabilities in NAICS codes X, Y, Z"

**DATA SPECIFICITY REQUIREMENTS**:
- Provide exact vendor counts with source
- Include specific contract numbers and amounts
- Give precise labor rate ranges with citations
- Reference actual company names when available from web search
- Include exact percentages, not ranges (or cite why range is necessary)

**REGULATORY CITATIONS** (MANDATORY):
- FAR 10.001 - Market research requirements
- FAR 10.002(b)(2) - Commercial item market research
- FAR 12.101 - Commercial item determination
- FAR 19.202-1 - Small business set-aside requirements
- FAR Parts 12 and 13 for simplified acquisitions

**APPENDIX A REQUIREMENTS** (CRITICAL - DO NOT SKIP):
YOU MUST INCLUDE APPENDIX A AS SECTION 8 OF THE REPORT. This is MANDATORY.
- List EVERY web search query performed with date and result count
- List EVERY contract referenced with full contract number and amount
- List EVERY FAR/DFARS section cited with brief description
- Document ALL assumptions made
- Acknowledge research limitations clearly

Example APPENDIX A format:
---
## 8. APPENDIX A: RESEARCH SOURCES

### Web Searches Conducted
1. SAM.gov search NAICS 541512 - Date: 2025-01-15 - Results: 23 vendors
2. FPDS search "logistics management system" - Date: 2025-01-15 - Results: 15 contracts
...

### Contracts Referenced
1. Contract GS-35F-0119Y - Amount: $4.2M - GSA Schedule 70 - Date: 2024-09
2. Contract W56KGU-24-C-0042 - Amount: $2.1M - Army logistics services - Date: 2024-06
...

### Regulations Cited
1. FAR 10.001 - Market research requirements
2. FAR 19.202-1 - Small business set-aside determination
...
---

Generate a comprehensive, professional market research report (2500-3500 words) with citations for EVERY factual claim and a complete APPENDIX A section that acquisition professionals can use to make informed decisions and reduce TBDs in downstream documents."""

        response = self.call_llm(prompt, max_tokens=8000)

        # Add metadata footer
        web_search_note = ""
        if web_research:
            web_search_note = """
**Research Methods**:
- ✅ Web-based market research (current vendor/pricing data)
- ✅ LLM analysis of ALMS requirements
- ✅ Industry standard comparisons
"""
        else:
            web_search_note = """
**Research Methods**:
- LLM analysis of ALMS requirements
- Industry standard comparisons
- Note: Web search was not used (can be enabled with config={'use_web_search': True})
"""

        footer = f"""

---

## Document Metadata

**Document Type**: Market Research Report
**Program**: {program_name}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Authority**: FAR 10.001-10.002 (Market Research)
**Purpose**: Inform acquisition strategy and reduce TBDs in downstream documents
{web_search_note}

**Downstream Impact**: This report provides foundational data for:
- Acquisition Plan (vendor landscape, competition)
- IGCE (pricing data, labor rates)
- PWS/SOW (industry standards, capabilities)
- Sources Sought (vendor identification)
- Section L/M (evaluation factors)

---
"""

        return response + footer

    def _extract_market_data(self, content: str, project_info: Dict) -> Dict:
        """
        Extract structured market data from the generated report

        Args:
            content: Generated market research report
            project_info: Program information

        Returns:
            Dictionary of extracted market data
        """
        # Extract key data points using patterns
        vendor_count_match = re.search(r'(\d+)[-\s]?(\d+)?\s+(?:vendors?|companies?|contractors?)\s+capable', content, re.IGNORECASE)
        small_business_match = re.search(r'small business.*?(\d+)%', content, re.IGNORECASE)

        # Extract pricing ranges
        labor_rate_matches = re.findall(r'\$(\d+)[-–]?\$?(\d+)?\s*(?:per hour|/hr|hourly)', content)

        extracted = {
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'program_name': project_info.get('program_name', 'Unknown'),
            'vendor_count_estimate': 'TBD',
            'small_business_potential': 'TBD',
            'recommended_contract_type': 'TBD',
            'competition_expected': True,
            'commercial_items_available': 'Partial',
            'labor_rate_ranges': {},
            'key_findings': []
        }

        # Parse vendor count
        if vendor_count_match:
            if vendor_count_match.group(2):
                extracted['vendor_count_estimate'] = f"{vendor_count_match.group(1)}-{vendor_count_match.group(2)}"
            else:
                extracted['vendor_count_estimate'] = vendor_count_match.group(1)

        # Parse small business potential
        if small_business_match:
            extracted['small_business_potential'] = f"{small_business_match.group(1)}%"

        # Parse labor rates
        if labor_rate_matches:
            if len(labor_rate_matches) > 0:
                first_rate = labor_rate_matches[0]
                if first_rate[1]:
                    extracted['labor_rate_ranges']['general'] = f"${first_rate[0]}-${first_rate[1]}/hour"
                else:
                    extracted['labor_rate_ranges']['general'] = f"${first_rate[0]}/hour"

        # Extract contract type recommendation
        contract_types = ['Firm Fixed Price', 'Fixed Price', 'Time and Materials', 'Cost Plus']
        for ct in contract_types:
            if f'recommend.*{ct}' in content.lower() or f'{ct}.*recommended' in content.lower():
                extracted['recommended_contract_type'] = ct
                break

        return extracted


if __name__ == "__main__":
    print("Market Research Report Generator Agent")
    print("=" * 70)
    print("This agent should be run FIRST in the acquisition lifecycle")
    print("It provides foundational market data that reduces TBDs in:")
    print("  - Acquisition Plan")
    print("  - IGCE")
    print("  - PWS/SOW")
    print("  - Sources Sought")
    print("  - Section L/M")
    print("=" * 70)
