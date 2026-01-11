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
        print(f"  ✓ RAG retriever: {'enabled' if retriever else 'disabled'}")
        print(f"  ℹ️  This report should be generated FIRST to reduce TBDs")
        print("="*70 + "\n")

    def _retrieve_uploaded_document_context(
        self,
        program_name: str,
        requirements: str,
        description: str = ""
    ) -> str:
        """
        Retrieve relevant context from uploaded documents via RAG.
        
        This method queries the RAG system for documents that have been
        uploaded to the project's knowledge base, providing the LLM with
        actual project-specific context rather than relying solely on
        general knowledge or web search.
        
        Args:
            program_name: Name of the program (for targeted queries)
            requirements: Requirements content to help find relevant docs
            description: Optional project description
            
        Returns:
            Formatted string of relevant document excerpts with sources
        """
        if not self.retriever:
            print("⚠️  RAG retriever not available - skipping uploaded document context")
            return ""
        
        print("\n📚 Retrieving context from uploaded documents...")
        
        all_context = []
        
        try:
            # Query 1: Search for program-specific documents
            if program_name and program_name != 'Unknown':
                query1 = f"{program_name} market research capabilities requirements vendors"
                results1 = self.retriever.retrieve(query=query1, k=3)
                if results1:
                    print(f"   ✅ Found {len(results1)} documents matching program name")
                    all_context.extend(results1)
            
            # Query 2: Search based on requirements content
            if requirements:
                # Use first 500 chars of requirements as query
                query2 = requirements[:500] if len(requirements) > 500 else requirements
                results2 = self.retriever.retrieve(query=query2, k=3)
                if results2:
                    print(f"   ✅ Found {len(results2)} documents matching requirements")
                    all_context.extend(results2)
            
            # Query 3: Search for market research specific content
            query3 = "market research vendor analysis pricing NAICS small business competition"
            results3 = self.retriever.retrieve(query=query3, k=2)
            if results3:
                print(f"   ✅ Found {len(results3)} market research reference documents")
                all_context.extend(results3)
            
            if not all_context:
                print("   ℹ️  No relevant uploaded documents found in knowledge base")
                return ""
            
            # Deduplicate results based on content hash
            seen_content = set()
            unique_results = []
            for result in all_context:
                # Handle both dict and object formats from retriever
                content = result.get('content', '') if isinstance(result, dict) else getattr(result, 'content', '')
                content_hash = hash(content[:200]) if content else None
                if content_hash and content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)
            
            # Format results into context string
            context_parts = []
            for i, result in enumerate(unique_results[:8], 1):  # Limit to 8 unique chunks
                if isinstance(result, dict):
                    content = result.get('content', '')
                    source = result.get('source', result.get('metadata', {}).get('source', 'Unknown'))
                else:
                    content = getattr(result, 'content', '')
                    source = getattr(result, 'source', 'Unknown')
                
                # Truncate long content
                if len(content) > 800:
                    content = content[:800] + "..."
                
                context_parts.append(f"**Source {i}** ({source}):\n{content}\n")
            
            formatted_context = "\n".join(context_parts)
            print(f"   ✅ Retrieved {len(unique_results)} unique document excerpts for context")
            
            return formatted_context
            
        except Exception as e:
            print(f"   ⚠️  RAG retrieval failed: {str(e)}")
            return ""

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

        # STEP 1: Retrieve context from uploaded documents via RAG
        # This provides project-specific context from user-uploaded documents
        uploaded_doc_context = self._retrieve_uploaded_document_context(
            program_name=program_name,
            requirements=requirements_content,
            description=project_info.get('description', '')
        )

        # STEP 2: Conduct web-based market research (if enabled and available)
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

        # STEP 3: Generate market research report with all context
        self.log("Generating market research report content")

        market_research_content = self._generate_market_research_report(
            project_info=project_info,
            requirements=requirements_content,
            config=config,
            web_research=web_research_results,
            uploaded_context=uploaded_doc_context
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
        web_research: str = "",
        uploaded_context: str = ""
    ) -> str:
        """
        Generate comprehensive market research report content

        Args:
            project_info: Program information
            requirements: Requirements content
            config: Configuration options
            web_research: Web search results (optional)
            uploaded_context: Context from uploaded documents via RAG (optional)

        Returns:
            Formatted market research report markdown
        """
        program_name = project_info.get('program_name', 'Unknown Program')
        estimated_value = project_info.get('estimated_value', 'TBD')
        users = project_info.get('users', 'TBD')
        description = project_info.get('description', '')
        
        # Get current date for accurate timestamps in the report
        current_date = datetime.now().strftime('%B %d, %Y')
        current_date_iso = datetime.now().strftime('%Y-%m-%d')

        # Build section for uploaded document context (RAG) using XML tags
        # XML tags help the LLM clearly distinguish between data and instructions
        uploaded_context_section = ""
        if uploaded_context:
            uploaded_context_section = f"""
<uploaded_documents>
<content>
{uploaded_context[:5000]}
</content>
<instruction>Use this as PRIMARY context - it contains project-specific requirements, constraints, and background that should be reflected in the report.</instruction>
</uploaded_documents>
"""

        # Build prompt with web research if available using XML tags
        # XML tags help separate findings from instructions for better LLM comprehension
        web_research_section = ""
        if web_research:
            web_research_section = f"""
<web_research>
<findings>
{web_research[:4000]}
</findings>
<instruction>Use these findings for SPECIFIC, CURRENT vendor names, pricing data, small business certifications, and technology trends.</instruction>
</web_research>
"""

        # Build prompt using XML tags for clear separation of data, instructions, and rules
        # XML tags help the LLM:
        # 1. Distinguish between factual inputs and instructions
        # 2. Follow structured output requirements more reliably
        # 3. Reduce hallucination by clearly labeling source data
        prompt = f"""You are a Government market research specialist conducting market research per FAR 10.001-10.002.

<system_context>
<current_date>{current_date}</current_date>
<current_date_iso>{current_date_iso}</current_date_iso>
<date_rule>Use current_date_iso for ALL date references in the report. Do NOT use dates from 2024 or earlier unless citing historical contracts.</date_rule>
</system_context>

<project_info>
<program_name>{program_name}</program_name>
<estimated_value>{estimated_value}</estimated_value>
<users>{users}</users>
<description>{description if description else 'Not provided'}</description>
</project_info>

<requirements>
{requirements[:3000] if requirements else 'No specific requirements provided - use general assumptions for this type of system'}
</requirements>

{uploaded_context_section}
{web_research_section}

<output_structure>
Generate a Market Research Report with exactly these 8 sections:

1. Executive Summary
   - Market research methodology (cite FAR 10.001)
   - Key findings summary (with data sources)
   - Recommendations for acquisition approach (cite FAR parts)

2. Market Overview
   - Industry landscape for this type of solution
   - Technology maturity assessment
   - Commercial vs Government Off-The-Shelf (GOTS) availability (cite FAR 12.101)
   - Cloud vs On-Premise solutions

3. Vendor Landscape
   - Estimated number of capable vendors (cite SAM.gov search results)
   - Small business participation potential (cite FAR 19.202-1)
   - 8(a), HUBZone, SDVOSB, WOSB opportunities (cite SBA.gov data)
   - Geographic distribution of vendors
   - Typical vendor qualifications and certifications

4. Pricing Analysis
   - Typical pricing models (Fixed Price, T&M, Cost Plus)
   - Labor rate ranges by category (cite GSA Schedule or actual contracts)
   - Commercial item pricing if available (cite sources)
   - ODC costs (cite specific pricing sources)
   - Industry standard cost breakdown

5. Contract Vehicle Analysis
   - Recommended contract type with justification (cite FAR parts)
   - Acquisition strategy recommendations
   - Socioeconomic considerations (cite FAR 19.202-1)
   - Competition expectations (cite historical data if available)

6. Risk Assessment
   - Market risks (limited competition, immature technology)
   - Pricing risks
   - Small business participation risks
   - Mitigation strategies

7. Sources and Methodology
   - Market research sources used (SAM.gov, industry reports, RFIs, web search results)
   - Assumptions made
   - Limitations of the research

8. APPENDIX A: Research Sources (MANDATORY)
   - Web Searches Conducted (query, date, result count)
   - Contracts Referenced (number, amount, description, date)
   - Regulations Cited (FAR/DFARS section, brief description)
   - Assumptions and Limitations
</output_structure>

<citation_rules>
<format>(Ref: [Source], [Date])</format>
<required_citations>
- Statistics and percentages: "(Ref: SAM.gov analysis, {current_date_iso})"
- Vendor counts: "(Ref: SAM.gov search NAICS 541512, {current_date_iso}, X results)"
- Pricing data: "(Ref: GSA Schedule 70, Contract number, date)"
- Labor rates: "(Ref: FPDS contract number, date)"
- Contract awards: "(Ref: FPDS database, Contract number, amount)"
- FAR regulations: "(Ref: FAR 10.001(a)(2)(i))"
- Market trends: "(Ref: [Source name], [Date])"
</required_citations>
<rule>EVERY factual claim MUST include a citation. {'PRIORITIZE web research findings - cite specific URLs, vendors, and contracts from search results.' if web_research else 'Use realistic numbers and cite industry standards.'}</rule>
</citation_rules>

<forbidden_language>
<absolutely_forbidden>numerous, several, many, various, significant, substantial, considerable, extensive, approximately</absolutely_forbidden>
<use_sparingly>sufficient, adequate, appropriate, relevant, important, critical</use_sparingly>
<modal_verbs_restriction>Use "may", "might", "could", "possibly", "potentially" ONLY in the Assumptions/Limitations section</modal_verbs_restriction>
<exceptions>
- When quoting FAR/DFARS regulations verbatim, preserve original wording
- Technical terms like "FedRAMP Moderate" are acceptable
</exceptions>
<replacement_examples>
- "numerous vendors" -> "23 vendors identified (Ref: SAM.gov, {current_date_iso})"
- "several contracts" -> "6 contracts analyzed (Ref: FPDS search, {current_date_iso})"
- "significant adoption" -> "85% adoption rate (Ref: Industry survey, recent)"
- "many small businesses" -> "18 small businesses identified (Ref: SAM.gov SB search)"
- "adequate competition" -> "competition threshold met with 15 vendors (Ref: FAR 6.401)"
- "may limit" -> "limits to X vendors" OR "reduces vendor pool by Y%"
</replacement_examples>
</forbidden_language>

<data_specificity>
- Provide exact vendor counts with source
- Include specific contract numbers and amounts
- Give precise labor rate ranges with citations
- Reference actual company names when available from web search
- Include exact percentages, not ranges (or cite why range is necessary)
</data_specificity>

<formatting_rules>
- Do NOT include blank lines between bullet list items
- Keep all list items in continuous blocks with single newlines
- Use specific numbers, not vague qualifiers
- Include exact percentages with citations
</formatting_rules>

<regulatory_references>
Required FAR citations to include where appropriate:
- FAR 10.001 - Market research requirements
- FAR 10.002(b)(2) - Commercial item market research
- FAR 12.101 - Commercial item determination
- FAR 19.202-1 - Small business set-aside requirements
- FAR Parts 12 and 13 for simplified acquisitions
</regulatory_references>

<appendix_a_requirements>
MANDATORY - Include as Section 8 with this structure:

### Web Searches Conducted
1. SAM.gov search NAICS 541512 - Date: {current_date_iso} - Results: X vendors
2. FPDS search "[search term]" - Date: {current_date_iso} - Results: X contracts

### Contracts Referenced
1. Contract [number] - Amount: $X.XM - [Description] - Date: [date]

### Regulations Cited
1. FAR 10.001 - Market research requirements
2. FAR 19.202-1 - Small business set-aside determination

### Assumptions and Limitations
[Document ALL assumptions made and acknowledge research limitations]
</appendix_a_requirements>

<output_length>2500-3500 words with citations for EVERY factual claim</output_length>"""

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
