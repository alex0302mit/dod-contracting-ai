"""
Research Agent: Enhanced with web search capabilities
Combines RAG system with live web search for comprehensive research
"""

from typing import Dict, List, Optional
from .base_agent import BaseAgent
from backend.rag.retriever import Retriever
from backend.utils.document_metadata_store import DocumentMetadataStore
from backend.utils.document_extractor import DocumentDataExtractor


class ResearchAgent(BaseAgent):
    """
    Research Agent: Hybrid information gathering with RAG + Web Search

    Responsibilities:
    - Query knowledge base for regulatory/policy information
    - Search web for current market data and news
    - Synthesize findings from multiple sources
    - Identify gaps in available information
    - Provide citations and sources

    Dependencies:
    - RAG system (Retriever) for internal knowledge
    - Web Search Tool (optional) for current market data
    - Base agent LLM capabilities
    """

    def __init__(
        self,
        api_key: str,
        retriever: Retriever,
        tavily_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize research agent with optional web search

        Args:
            api_key: Anthropic API key
            retriever: RAG Retriever instance
            tavily_api_key: Tavily API key for web search (optional)
            model: Claude model to use
        """
        super().__init__(
            name="ResearchAgent",
            api_key=api_key,
            model=model,
            temperature=0.3  # Lower temperature for factual research
        )
        self.retriever = retriever

        # Initialize web search tool (optional)
        self.web_search = None
        self.web_search_enabled = False

        try:
            from .tools.web_search_tool import WebSearchTool
            self.web_search = WebSearchTool(api_key=tavily_api_key)
            self.web_search_enabled = True
            self.log("✓ Web search enabled")
        except ImportError:
            self.log("Web search tool not available (tavily-python not installed)", "WARNING")
        except ValueError as e:
            self.log(f"Web search disabled: {e}", "WARNING")
        except Exception as e:
            self.log(f"Web search initialization failed: {e}", "WARNING")
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute enhanced research task with multiple data sources

        Args:
            task: Dictionary with:
                - query: Search query
                - section: Section name (optional)
                - context: Additional context (optional)
                - use_web_search: Whether to include web search (default: True)
                - search_type: Type of search ('general', 'pricing', 'vendors', 'awards')

        Returns:
            Dictionary with:
                - findings: Synthesized research findings
                - sources: List of source documents
                - confidence: Confidence level
                - gaps: Identified information gaps
                - web_results: Web search results (if enabled)
        """
        query = task.get('query', '')
        section = task.get('section', '')
        context = task.get('context', {})
        use_web_search = task.get('use_web_search', True)
        search_type = task.get('search_type', 'general')
        program_name = context.get('program_name', 'Unknown')

        self.log(f"Starting enhanced research for: '{query}'")

        # STEP 0: Cross-reference lookup for existing research
        self._document_references = []

        if program_name != 'Unknown':
            try:
                print("\n🔍 Looking up existing research and documents...")
                metadata_store = DocumentMetadataStore()

                # Get all program documents for context
                all_program_docs = [doc for doc in metadata_store._documents.values()
                                   if doc['program'] == program_name]

                if all_program_docs:
                    print(f"✅ Found {len(all_program_docs)} existing documents")
                    self._document_references = all_program_docs

                    # Add to context for research synthesis
                    context['existing_documents'] = [
                        {'type': doc['doc_type'], 'id': doc['id'], 'data': doc['extracted_data']}
                        for doc in all_program_docs
                    ]

            except Exception as e:
                print(f"⚠️  Cross-reference lookup failed: {str(e)}")

        # Step 1: Always search RAG system first (internal knowledge)
        self.log("Retrieving from knowledge base...")
        rag_documents = self.retriever.retrieve(query, k=7)

        if rag_documents:
            self.log(f"✓ Found {len(rag_documents)} documents in knowledge base")
        else:
            self.log("⚠️  No documents in knowledge base", "WARNING")

        # Step 2: Web search for current/supplementary information (if enabled)
        web_results = []
        if use_web_search and self.web_search_enabled:
            self.log("Searching web for current information...")
            web_results = self._perform_web_search(query, search_type, context)

            if web_results:
                self.log(f"✓ Found {len(web_results)} web results")
            else:
                self.log("No relevant web results found")

        # Step 3: Synthesize findings from all sources
        self.log("Synthesizing findings from all sources...")
        synthesis = self._synthesize_multi_source_findings(
            query=query,
            section=section,
            rag_documents=rag_documents,
            web_results=web_results,
            context=context
        )

        # Store in memory
        self.add_to_memory(f"research_{section}", synthesis)

        # STEP 2: Save research metadata
        if program_name != 'Unknown':
            try:
                print("\n💾 Saving Research metadata...")
                metadata_store = DocumentMetadataStore()

                # Extract Research specific data
                extracted_data = {
                    'query': query,
                    'section': section,
                    'search_type': search_type,
                    'sources_count': len(synthesis.get('sources', [])),
                    'confidence': synthesis.get('confidence', 'medium'),
                    'gaps_identified': len(synthesis.get('gaps', [])),
                    'web_search_used': use_web_search and self.web_search_enabled,
                    'rag_documents_found': len(rag_documents) if rag_documents else 0,
                    'web_results_found': len(web_results) if web_results else 0
                }

                # Track references (existing documents that informed research)
                references = {}
                for i, doc in enumerate(self._document_references[:10]):  # Limit to 10
                    references[f"context_{doc['doc_type']}_{i+1}"] = doc['id']

                doc_id = metadata_store.save_document(
                    doc_type='research',
                    program=program_name,
                    content=synthesis.get('findings', ''),
                    file_path=None,
                    extracted_data=extracted_data,
                    references=references
                )

                print(f"✅ Metadata saved: {doc_id}")

            except Exception as e:
                print(f"⚠️  Failed to save metadata: {str(e)}")

        return synthesis

    def _perform_web_search(
        self,
        query: str,
        search_type: str,
        context: Dict
    ) -> List[Dict]:
        """
        Perform appropriate web search based on type

        Args:
            query: Search query
            search_type: Type of search
            context: Additional context

        Returns:
            Web search results
        """
        if not self.web_search:
            return []

        try:
            if search_type == 'pricing':
                # Search for market pricing
                service_type = context.get('product_service', query)
                naics = context.get('naics_code')
                return self.web_search.search_market_pricing(
                    service_type=service_type,
                    naics_code=naics
                )

            elif search_type == 'vendors':
                # Search for vendor information
                return self.web_search.search(
                    query=f"{query} government contractors vendors capabilities",
                    max_results=7,
                    search_depth="advanced"
                )

            elif search_type == 'awards':
                # Search for recent contract awards
                agency = context.get('organization', '').split('/')[0] if context.get('organization') else None
                return self.web_search.search_recent_awards(
                    service_type=query,
                    agency=agency
                )

            else:  # general
                # General web search
                return self.web_search.search(
                    query=query,
                    max_results=5,
                    search_depth="basic"
                )

        except Exception as e:
            self.log(f"Web search error: {e}", "WARNING")
            return []

    def _synthesize_multi_source_findings(
        self,
        query: str,
        section: str,
        rag_documents: List[Dict],
        web_results: List[Dict],
        context: Dict
    ) -> Dict:
        """
        Synthesize findings from both RAG and web sources

        Args:
            query: Original query
            section: Section name
            rag_documents: Documents from RAG
            web_results: Results from web search
            context: Additional context

        Returns:
            Comprehensive synthesis
        """
        # Format RAG documents
        rag_text = ""
        if rag_documents:
            rag_text = "\n\n---\n\n".join([
                f"[Internal Document: {doc['metadata']['source']}]\n{doc['content']}"
                for doc in rag_documents
            ])
        else:
            rag_text = "No internal documents found."

        # Format web results
        web_text = ""
        if web_results:
            web_text = "\n\n---\n\n".join([
                f"[Web Source: {result['title']}]\nURL: {result['url']}\nPublished: {result.get('published_date', 'Unknown')}\n{result['content']}"
                for result in web_results
            ])
        else:
            web_text = "No current web information found."

        # Create enhanced synthesis prompt
        prompt = f"""You are a research analyst synthesizing information from multiple sources for a government market research report.

RESEARCH QUERY: {query}
SECTION: {section}

PROJECT CONTEXT:
{self._format_context(context)}

INTERNAL KNOWLEDGE BASE (Regulations, Templates, Past Research):
{rag_text}

CURRENT WEB INFORMATION (Market Data, Recent News, Vendor Info):
{web_text}

Your task:
1. **Synthesize findings from BOTH sources** - combine regulatory knowledge with current market data
2. **Identify specific facts, numbers, and dates** - be precise
3. **Note source for each claim** - distinguish between internal docs and web sources
4. **Highlight current market conditions** - what's happening NOW in the market
5. **Identify any gaps** - what information is still missing
6. **Assess confidence level** - how reliable is this information

CRITICAL: When citing information:
- Internal documents: "Per [document name]"
- Web sources: "According to [source] dated [date]"
- Be specific about dates for web information

Provide response in this format:

FINDINGS:
[Comprehensive synthesis combining regulatory guidance with current market data]

REGULATORY/POLICY GUIDANCE:
[Key points from internal knowledge base - FAR, templates, etc.]

CURRENT MARKET INTELLIGENCE:
[Recent data from web - pricing, vendors, awards, trends]

SOURCES USED:
Internal Documents:
- [Source 1]: [What it provided]
- [Source 2]: [What it provided]

Web Sources:
- [Source 1] (URL): [What it provided]
- [Source 2] (URL): [What it provided]

CONFIDENCE LEVEL: [High/Medium/Low]
REASONING: [Why this confidence level]

INFORMATION GAPS:
- [Gap 1]
- [Gap 2]

RECOMMENDATIONS FOR SECTION:
[How to use these findings effectively]
"""

        self.log("Calling LLM for multi-source synthesis...")
        response = self.call_llm(
            prompt,
            max_tokens=4000,
            system_prompt="You are an expert research analyst specializing in government contracting and market research. You synthesize information from multiple sources including regulatory documents and current market data."
        )

        # Parse response
        findings_dict = self._parse_multi_source_response(response)

        # Add raw sources for reference
        findings_dict['rag_documents'] = rag_documents
        findings_dict['web_results'] = web_results

        return findings_dict

    def _parse_multi_source_response(self, response: str) -> Dict:
        """
        Parse multi-source synthesis response

        Args:
            response: LLM response text

        Returns:
            Structured findings dictionary
        """
        import re

        # Extract sections
        findings = ""
        regulatory_guidance = ""
        market_intelligence = ""
        sources = []
        confidence = "Medium"
        gaps = []
        recommendations = ""

        # Extract FINDINGS
        findings_match = re.search(r'FINDINGS:(.*?)(?=REGULATORY/POLICY GUIDANCE:|SOURCES USED:|$)', response, re.DOTALL)
        if findings_match:
            findings = findings_match.group(1).strip()

        # Extract REGULATORY/POLICY GUIDANCE
        reg_match = re.search(r'REGULATORY/POLICY GUIDANCE:(.*?)(?=CURRENT MARKET INTELLIGENCE:|SOURCES USED:|$)', response, re.DOTALL)
        if reg_match:
            regulatory_guidance = reg_match.group(1).strip()

        # Extract CURRENT MARKET INTELLIGENCE
        market_match = re.search(r'CURRENT MARKET INTELLIGENCE:(.*?)(?=SOURCES USED:|$)', response, re.DOTALL)
        if market_match:
            market_intelligence = market_match.group(1).strip()

        # Extract SOURCES
        sources_match = re.search(r'SOURCES USED:(.*?)(?=CONFIDENCE LEVEL:|INFORMATION GAPS:|$)', response, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1).strip()
            sources = [line.strip() for line in sources_text.split('\n') if line.strip().startswith('-')]

        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE LEVEL:\s*(High|Medium|Low)', response, re.IGNORECASE)
        if confidence_match:
            confidence = confidence_match.group(1)

        # Extract GAPS
        gaps_match = re.search(r'INFORMATION GAPS:(.*?)(?=RECOMMENDATIONS:|$)', response, re.DOTALL)
        if gaps_match:
            gaps_text = gaps_match.group(1).strip()
            gaps = [line.strip('- ').strip() for line in gaps_text.split('\n') if line.strip().startswith('-')]

        # Extract RECOMMENDATIONS
        rec_match = re.search(r'RECOMMENDATIONS FOR SECTION:(.*?)$', response, re.DOTALL)
        if rec_match:
            recommendations = rec_match.group(1).strip()

        return {
            'findings': findings,
            'regulatory_guidance': regulatory_guidance,
            'market_intelligence': market_intelligence,
            'sources': sources,
            'confidence': confidence.lower(),
            'gaps': gaps,
            'recommendations': recommendations,
            'raw_response': response
        }

    def _synthesize_findings(
        self,
        query: str,
        section: str,
        documents: List[Dict],
        context: Dict
    ) -> Dict:
        """
        Synthesize findings from retrieved documents
        
        Args:
            query: Original query
            section: Section name
            documents: Retrieved documents
            context: Additional context
            
        Returns:
            Synthesis dictionary
        """
        # Format documents for LLM
        doc_text = "\n\n---\n\n".join([
            f"[Source: {doc['metadata']['source']}]\n{doc['content']}"
            for doc in documents
        ])
        
        # Create synthesis prompt
        prompt = f"""You are a research analyst gathering information for a government market research report.

RESEARCH QUERY: {query}
SECTION: {section}

ADDITIONAL CONTEXT:
{self._format_context(context)}

RETRIEVED DOCUMENTS:
{doc_text}

Your task:
1. Synthesize the key findings relevant to the query
2. Identify specific facts, numbers, and dates
3. Note which sources provide which information
4. Identify any gaps in the available information
5. Assess confidence level in the findings

Provide your response in this format:

FINDINGS:
[Synthesized findings with specific facts and numbers]

SOURCES USED:
- [Source 1]: [What information it provided]
- [Source 2]: [What information it provided]

CONFIDENCE LEVEL: [High/Medium/Low]
REASONING: [Why this confidence level]

INFORMATION GAPS:
- [Gap 1]
- [Gap 2]

RECOMMENDATIONS FOR SECTION:
[How to use these findings in the report section]
"""
        
        self.log("Synthesizing findings with LLM...")
        response = self.call_llm(
            prompt,
            max_tokens=3000,
            system_prompt="You are an expert research analyst specializing in government contracting and market research."
        )
        
        # Parse response
        findings_dict = self._parse_synthesis_response(response)
        
        return findings_dict
    
    def _parse_synthesis_response(self, response: str) -> Dict:
        """
        Parse LLM synthesis response into structured format
        
        Args:
            response: LLM response text
            
        Returns:
            Structured findings dictionary
        """
        import re
        
        # Extract sections using markers
        findings = ""
        sources = []
        confidence = "Medium"
        gaps = []
        recommendations = ""
        
        # Extract FINDINGS
        findings_match = re.search(r'FINDINGS:(.*?)(?=SOURCES USED:|CONFIDENCE LEVEL:|$)', response, re.DOTALL)
        if findings_match:
            findings = findings_match.group(1).strip()
        
        # Extract SOURCES
        sources_match = re.search(r'SOURCES USED:(.*?)(?=CONFIDENCE LEVEL:|INFORMATION GAPS:|$)', response, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1).strip()
            sources = [line.strip() for line in sources_text.split('\n') if line.strip().startswith('-')]
        
        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE LEVEL:\s*(High|Medium|Low)', response, re.IGNORECASE)
        if confidence_match:
            confidence = confidence_match.group(1)
        
        # Extract GAPS
        gaps_match = re.search(r'INFORMATION GAPS:(.*?)(?=RECOMMENDATIONS:|$)', response, re.DOTALL)
        if gaps_match:
            gaps_text = gaps_match.group(1).strip()
            gaps = [line.strip('- ').strip() for line in gaps_text.split('\n') if line.strip().startswith('-')]
        
        # Extract RECOMMENDATIONS
        rec_match = re.search(r'RECOMMENDATIONS FOR SECTION:(.*?)$', response, re.DOTALL)
        if rec_match:
            recommendations = rec_match.group(1).strip()
        
        return {
            'findings': findings,
            'sources': sources,
            'confidence': confidence.lower(),
            'gaps': gaps,
            'recommendations': recommendations,
            'raw_response': response
        }
    
    def _extract_sources(self, documents: List[Dict]) -> List[Dict]:
        """
        Extract source information from documents
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of source metadata
        """
        sources = []
        for doc in documents:
            sources.append({
                'source': doc['metadata']['source'],
                'file_path': doc['metadata'].get('file_path', ''),
                'chunk_id': doc['chunk_id'],
                'score': doc.get('score', 0.0)
            })
        return sources
    
    def _format_context(self, context: Dict) -> str:
        """Format context dictionary as text"""
        if not context:
            return "No additional context provided."
        
        lines = []
        for key, value in context.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"- {formatted_key}: {value}")
        
        return "\n".join(lines)
    
    def research_for_section(
        self,
        section_name: str,
        section_guidance: str,
        project_info: Dict
    ) -> Dict:
        """
        Conduct research specifically for a report section
        
        Args:
            section_name: Name of the report section
            section_guidance: Guidance text for the section
            project_info: Project information dictionary
            
        Returns:
            Research findings dictionary
        """
        self.log(f"Researching for section: {section_name}")
        
        # Build comprehensive query
        query = f"{section_name}: {section_guidance[:300]}"
        
        # Execute research
        task = {
            'query': query,
            'section': section_name,
            'context': project_info
        }
        
        return self.execute(task)
