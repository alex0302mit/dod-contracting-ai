"""
Grounding Verifier: Ensures content is grounded in source material
Prevents hallucinations by verifying claims against retrieved documents
"""

from typing import Dict, List
import anthropic


class GroundingVerifier:
    """
    Verifies that generated content is grounded in source material
    
    Uses LLM to check if claims in content are supported by:
    - Project information (ground truth)
    - Retrieved RAG documents
    
    Dependencies:
    - anthropic: Claude API for verification
    """
    
    def __init__(self, api_key: str):
        """
        Initialize grounding verifier
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def verify_content(
        self,
        content: str,
        project_info: Dict,
        retrieved_docs: List[Dict]
    ) -> Dict:
        """
        Verify content is grounded in sources
        
        Args:
            content: Generated content to verify
            project_info: Project information (ground truth)
            retrieved_docs: Retrieved RAG documents
            
        Returns:
            Dictionary with:
                - is_grounded: bool
                - hallucinations: List of specific hallucinations
                - unsupported_claims: List of unsupported claims
                - grounding_score: 0-100
        """
        # Format sources
        sources = self._format_sources(project_info, retrieved_docs)
        
        # Create verification prompt
        prompt = f"""You are a fact-checker verifying content against source material.

SOURCE MATERIAL (Ground Truth):
{sources}

CONTENT TO VERIFY:
{content}

Your task: Identify EVERY claim in the content that is NOT directly supported by the source material.

Be strict:
- Specific numbers, dates, names must be in sources
- Technical capabilities must be explicitly mentioned
- "Elaborations" or "reasonable inferences" are NOT acceptable
- Flag anything that seems invented or assumed

Output format:

GROUNDING STATUS: [FULLY GROUNDED / PARTIALLY GROUNDED / POORLY GROUNDED]

HALLUCINATIONS (invented facts):
- [List each specific claim that appears fabricated]
- [Include the text that seems made up]

UNSUPPORTED CLAIMS (may be reasonable but not in sources):
- [List claims not traceable to source material]

SUPPORTED CLAIMS (correctly grounded):
- [List claims that ARE properly sourced]

GROUNDING SCORE: [0-100, where 100 = all claims supported]
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0.1,  # Low temperature for consistency
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse response
        result = self._parse_verification_response(response_text)
        result['raw_analysis'] = response_text
        
        return result
    
    def _format_sources(self, project_info: Dict, retrieved_docs: List[Dict]) -> str:
        """Format source material for verification"""
        parts = []
        
        # Project info
        parts.append("PROJECT INFORMATION:")
        for key, value in project_info.items():
            parts.append(f"- {key}: {value}")
        parts.append("")
        
        # Retrieved documents
        if retrieved_docs:
            parts.append("RETRIEVED DOCUMENTS:")
            for i, doc in enumerate(retrieved_docs, 1):
                source = doc.get('metadata', {}).get('source', 'Unknown')
                content = doc.get('content', '')
                parts.append(f"\n[Document {i}: {source}]")
                parts.append(content[:500])  # Limit length
                parts.append("")
        
        return "\n".join(parts)
    
    def _parse_verification_response(self, response: str) -> Dict:
        """Parse LLM verification response"""
        import re
        
        # Extract grounding status
        status_match = re.search(
            r'GROUNDING STATUS:\s*(FULLY GROUNDED|PARTIALLY GROUNDED|POORLY GROUNDED)',
            response,
            re.IGNORECASE
        )
        status = status_match.group(1).upper() if status_match else 'PARTIALLY GROUNDED'
        
        # Extract hallucinations
        hall_section = re.search(
            r'HALLUCINATIONS.*?:(.*?)(?=UNSUPPORTED CLAIMS|SUPPORTED CLAIMS|GROUNDING SCORE|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        hallucinations = []
        if hall_section:
            hall_text = hall_section.group(1)
            hallucinations = [
                line.strip('- ').strip()
                for line in hall_text.split('\n')
                if line.strip().startswith('-')
            ]
        
        # Extract unsupported claims
        unsup_section = re.search(
            r'UNSUPPORTED CLAIMS.*?:(.*?)(?=SUPPORTED CLAIMS|GROUNDING SCORE|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )
        unsupported = []
        if unsup_section:
            unsup_text = unsup_section.group(1)
            unsupported = [
                line.strip('- ').strip()
                for line in unsup_text.split('\n')
                if line.strip().startswith('-')
            ]
        
        # Extract grounding score
        score_match = re.search(r'GROUNDING SCORE:\s*(\d+)', response)
        grounding_score = int(score_match.group(1)) if score_match else 50
        
        is_grounded = status == 'FULLY GROUNDED' and grounding_score >= 85
        
        return {
            'is_grounded': is_grounded,
            'status': status,
            'grounding_score': grounding_score,
            'hallucinations': hallucinations,
            'unsupported_claims': unsupported
        }
