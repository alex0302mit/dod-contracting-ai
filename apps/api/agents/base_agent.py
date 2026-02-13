"""
Base Agent: Foundation for all specialized agents
Provides common functionality like LLM interaction, memory, and logging

Phase 4: Enhanced with collaboration methods for cross-referencing
"""

from typing import Dict, List, Optional, TYPE_CHECKING
import anthropic
from datetime import datetime
import re  # Used for markdown cleanup in _clean_markdown_lists()

# Type checking import for ReasoningTracker (avoids circular imports)
if TYPE_CHECKING:
    from backend.services.reasoning_tracker import ReasoningTracker


class BaseAgent:
    """
    Base class for all agents in the system

    Provides:
    - LLM interaction via Claude
    - Memory/state management
    - Logging capabilities
    - Common utilities
    - Phase 4: Collaboration methods for cross-referencing

    Dependencies:
    - anthropic: Claude API client
    - context_manager: Shared context pool (Phase 4)
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        retriever = None,
        context_manager = None
    ):
        """
        Initialize base agent

        Args:
            name: Agent name for identification
            api_key: Anthropic API key
            model: Claude model to use
            temperature: Sampling temperature
            retriever: Optional RAG retriever (Phase 2)
            context_manager: Optional context manager for collaboration (Phase 4)
        """
        self.name = name
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature

        # Phase 2: RAG retriever
        self.retriever = retriever

        # Phase 4: Context manager for collaboration
        self.context_manager = context_manager

        # Memory: stores conversation history and important findings
        self.memory = []
        self.findings = {}

        # Logging
        self.logs = []
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{self.name}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def call_llm(
        self,
        prompt: str,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None,
        tracker: Optional['ReasoningTracker'] = None
    ) -> str:
        """
        Call Claude LLM with optional reasoning tracking.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt
            tracker: Optional ReasoningTracker for Chain-of-Thought capture.
                     If not provided, will use self._current_tracker if available.

        Returns:
            LLM response text
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)

            # Use explicit tracker or fall back to instance tracker if available
            # This allows agents to set self._current_tracker in execute() and
            # automatically track all LLM calls without modifying each call site
            effective_tracker = tracker or getattr(self, '_current_tracker', None)
            if effective_tracker:
                effective_tracker.record_llm_call(response, prompt=prompt)

            # Clean up markdown list formatting to prevent empty bullets
            return self._clean_markdown_lists(response.content[0].text)

        except Exception as e:
            self.log(f"LLM call failed: {e}", "ERROR")
            raise
    
    def _clean_markdown_lists(self, content: str) -> str:
        """
        Remove empty list items and collapse blank lines between list items.
        
        LLMs (especially Claude) frequently generate markdown with:
        1. Empty bullet points ("- " or "* " with no content after the marker)
        2. Blank lines between consecutive list items (renders as separate lists)
        3. Bullets with only whitespace after the marker ("- \t\n")
        
        These cause empty bullet dots to appear in the rendered document.
        
        Strategy: Remove empty items FIRST (multiple passes to catch consecutive
        empties), then collapse blank lines between remaining items.
        
        Args:
            content: Markdown content from LLM
            
        Returns:
            Cleaned markdown with proper list formatting
        """
        # ── Pass 1: Remove empty bullet items (- or * with no text content) ──
        # Uses re.MULTILINE so ^ matches the start of every line, catching
        # empty bullets at the start of content, middle, or end.
        # Runs 3 passes to handle consecutive empty bullets (each pass may
        # reveal new empty lines that look like bullets).
        for _ in range(3):
            # Lines that are ONLY a bullet marker (- or *) with optional whitespace
            content = re.sub(r'^\s*[-*]\s*$', '', content, flags=re.MULTILINE)
            # Lines that are ONLY a numbered marker (1. 2. etc.) with optional whitespace
            content = re.sub(r'^\s*\d+\.\s*$', '', content, flags=re.MULTILINE)

        # ── Pass 2: Collapse blank lines between bullet list items ──
        # After removing empty bullets, there may be leftover blank lines
        # between real list items. Collapse those to single newlines.
        # Uses re.MULTILINE so ^ works per-line.
        content = re.sub(
            r'(^[ \t]*[-*]\s+[^\n]+)\n\n+([ \t]*[-*]\s)',
            r'\1\n\2',
            content,
            flags=re.MULTILINE
        )

        # ── Pass 3: Collapse blank lines between numbered list items ──
        content = re.sub(
            r'(^[ \t]*\d+\.\s+[^\n]+)\n\n+([ \t]*\d+\.\s)',
            r'\1\n\2',
            content,
            flags=re.MULTILINE
        )

        # ── Pass 4: Clean up multiple consecutive blank lines left behind ──
        # Reducing 3+ blank lines to 2 (standard markdown paragraph break)
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content
    
    def add_to_memory(self, key: str, value: any) -> None:
        """
        Add item to agent memory
        
        Args:
            key: Memory key
            value: Value to store
        """
        self.memory.append({
            'timestamp': datetime.now().isoformat(),
            'key': key,
            'value': value
        })
    
    def get_from_memory(self, key: str) -> Optional[any]:
        """
        Retrieve from memory
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        for item in reversed(self.memory):
            if item['key'] == key:
                return item['value']
        return None
    
    def store_finding(self, category: str, content: any) -> None:
        """
        Store a finding for later use
        
        Args:
            category: Finding category
            content: Finding content
        """
        if category not in self.findings:
            self.findings[category] = []
        self.findings[category].append(content)
    
    def get_findings(self, category: str = None) -> Dict:
        """
        Get stored findings
        
        Args:
            category: Optional category filter
            
        Returns:
            Findings dictionary or category contents
        """
        if category:
            return self.findings.get(category, [])
        return self.findings
    
    def execute(self, task: Dict) -> Dict:
        """
        Execute a task (to be implemented by subclasses)

        Args:
            task: Task dictionary with parameters

        Returns:
            Result dictionary
        """
        raise NotImplementedError("Subclasses must implement execute()")

    # ============================================================
    # Reasoning Tracker Helper Methods
    # ============================================================

    def get_tracker_from_task(self, task: Dict) -> Optional['ReasoningTracker']:
        """
        Extract reasoning tracker from task dict if present.
        
        The generation coordinator passes the tracker via the task dict
        so agents can record actual token usage from LLM calls.
        
        Usage in agent execute() methods:
            tracker = self.get_tracker_from_task(task)
            response = self.call_llm(prompt, tracker=tracker)
        
        Args:
            task: Task dictionary that may contain 'reasoning_tracker'
            
        Returns:
            ReasoningTracker instance if present, None otherwise
        """
        return task.get('reasoning_tracker') if task else None

    # ============================================================
    # Phase 4: Collaboration Methods
    # ============================================================

    def get_related_content(self, dependency_list: List[str], max_length: int = 1000) -> Dict[str, str]:
        """
        Retrieve previously generated content for dependencies

        Phase 4: Allows agents to reference other documents

        Args:
            dependency_list: List of document names this agent depends on
            max_length: Maximum characters per dependency (default 1000)

        Returns:
            Dictionary mapping document name -> content summary
        """
        if not self.context_manager:
            self.log("No context manager available for collaboration", "WARNING")
            return {}

        related = self.context_manager.get_related_content(
            doc_name=self.name,
            dependency_list=dependency_list,
            max_summary_length=max_length
        )

        if related:
            self.log(f"Retrieved {len(related)} dependencies for collaboration", "INFO")

        return related

    def reference_section(self, target_doc: str, reference_text: str) -> str:
        """
        Create and track a reference to another document section

        Phase 4: Formats reference and tracks cross-reference

        Args:
            target_doc: Name of document being referenced
            reference_text: Brief description of what's being referenced

        Returns:
            Formatted reference string
        """
        # Track cross-reference if context manager available
        if self.context_manager:
            self.context_manager.add_cross_reference(
                from_doc=self.name,
                to_doc=target_doc,
                reference_text=reference_text
            )

        # Format reference for insertion into content
        formatted_ref = f"[See {target_doc}: {reference_text}]"

        self.log(f"Created reference to '{target_doc}'", "INFO")

        return formatted_ref

    def build_collaborative_prompt(self,
                                   base_requirements: str,
                                   dependencies: Dict[str, str],
                                   context: str = "") -> str:
        """
        Build enhanced prompt with context from dependent documents

        Phase 4: Combines base requirements with dependency content

        Args:
            base_requirements: Core requirements for this document
            dependencies: Dict of doc_name -> content from dependencies
            context: Optional RAG context (Phase 2)

        Returns:
            Enhanced prompt with collaborative context
        """
        if not dependencies:
            # No dependencies, return base prompt
            prompt = f"{base_requirements}\n\n"
            if context:
                prompt += f"### REFERENCE CONTEXT\n{context}\n\n"
            return prompt

        # Build collaborative prompt
        prompt = "### PREVIOUSLY GENERATED DOCUMENTS\n"
        prompt += "Reference and build upon these documents where appropriate:\n\n"

        for doc_name, content in dependencies.items():
            # Truncate if very long
            summary = content[:1500] + "..." if len(content) > 1500 else content
            prompt += f"#### {doc_name}\n{summary}\n\n"

        prompt += "### YOUR REQUIREMENTS\n"
        prompt += base_requirements + "\n\n"

        if context:
            prompt += f"### REFERENCE CONTEXT (FAR/DFARS)\n{context}\n\n"

        prompt += "### INSTRUCTIONS\n"
        prompt += "Generate content that:\n"
        prompt += "1. References and aligns with the previously generated documents above\n"
        prompt += "2. Uses the reference_section() method to cite specific content\n"
        prompt += "3. Ensures consistency with prior documents\n"
        prompt += "4. Avoids contradictions or duplications\n\n"
        
        # Add list formatting requirements to prevent double bullets
        prompt += "### LIST FORMATTING REQUIREMENTS (MANDATORY)\n"
        prompt += "- Do NOT include blank lines between bullet list items\n"
        prompt += "- Keep all list items in a continuous block with single newlines\n"
        prompt += "- CORRECT format: item1\\n- item2\\n- item3\n"
        prompt += "- WRONG format: item1\\n\\n- item2\\n\\n- item3\n"

        self.log(f"Built collaborative prompt with {len(dependencies)} dependencies", "INFO")

        return prompt

    def has_collaboration_enabled(self) -> bool:
        """
        Check if collaboration is enabled for this agent

        Returns:
            True if context manager is available, False otherwise
        """
        return self.context_manager is not None
