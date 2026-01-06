"""
Base Agent: Foundation for all specialized agents
Provides common functionality like LLM interaction, memory, and logging

Phase 4: Enhanced with collaboration methods for cross-referencing
"""

from typing import Dict, List, Optional
import anthropic
from datetime import datetime


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
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Call Claude LLM
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt
            
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
            return response.content[0].text
        
        except Exception as e:
            self.log(f"LLM call failed: {e}", "ERROR")
            raise
    
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
        prompt += "4. Avoids contradictions or duplications\n"

        self.log(f"Built collaborative prompt with {len(dependencies)} dependencies", "INFO")

        return prompt

    def has_collaboration_enabled(self) -> bool:
        """
        Check if collaboration is enabled for this agent

        Returns:
            True if context manager is available, False otherwise
        """
        return self.context_manager is not None
