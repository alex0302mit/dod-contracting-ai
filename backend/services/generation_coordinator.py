"""
Generation Coordinator Service

Coordinates document generation using specialized agents, phase detection,
and intelligent routing. Replaces generic Claude calls with agent-based generation.
"""

from typing import List, Dict, Optional, Callable
import os
import asyncio
import time
from datetime import datetime

from backend.services.agent_router import get_agent_router
from backend.services.phase_detector import get_phase_detector
from backend.services.rag_service import get_rag_service
from backend.services.dependency_graph import get_dependency_graph
from backend.services.context_manager import get_context_manager
# Quality analysis agent for precomputing scores during generation
from backend.agents.quality_agent import QualityAgent


class GenerationTask:
    """
    Represents a single document generation task

    Tracks status, progress, and results for a document generation request.
    """

    def __init__(
        self,
        task_id: str,
        document_names: List[str],
        assumptions: List[Dict[str, str]],
        linked_assumptions: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize generation task

        Args:
            task_id: Unique task identifier
            document_names: List of document names to generate
            assumptions: List of assumption dictionaries
            linked_assumptions: Optional mapping of document -> assumption IDs
        """
        self.task_id = task_id
        self.document_names = document_names
        self.assumptions = assumptions
        self.linked_assumptions = linked_assumptions or {}

        # Status tracking
        self.status = "pending"  # pending, in_progress, completed, failed
        self.progress = 0  # 0-100
        self.message = "Initializing..."
        self.created_at = datetime.now()

        # Results
        self.sections: Dict[str, str] = {}
        self.citations: List[Dict] = []
        self.agent_metadata: Dict[str, Dict] = {}  # Track which agent generated each doc
        self.phase_info: Optional[Dict] = None
        self.collaboration_metadata: Optional[Dict] = None  # Phase 4: Collaboration info
        self.errors: List[str] = []
        
        # Quality analysis results per section (precomputed during generation)
        # Stores QualityAgent results for each document section for immediate display
        self.quality_analysis: Dict[str, Dict] = {}


class GenerationCoordinator:
    """
    Coordinates multi-document generation using specialized agents

    Key responsibilities:
    1. Phase detection and validation
    2. Agent routing and selection
    3. Progress tracking and status updates
    4. RAG context retrieval
    5. Citation management
    6. Error handling and recovery
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_specialized_agents: bool = True,
        enable_collaboration: bool = True
    ):
        """
        Initialize generation coordinator

        Args:
            api_key: Anthropic API key (defaults to env var)
            use_specialized_agents: Whether to use specialized agents (vs generic)
            enable_collaboration: Whether to enable Phase 4 collaboration (default True)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.use_specialized_agents = use_specialized_agents
        self.enable_collaboration = enable_collaboration

        # Initialize services
        self.rag_service = get_rag_service()

        if self.use_specialized_agents:
            # Initialize agent router with RAG retriever
            self.agent_router = get_agent_router(
                api_key=self.api_key,
                retriever=self.rag_service.retriever if hasattr(self.rag_service, 'retriever') else None
            )
            self.phase_detector = get_phase_detector()

            # Phase 4: Collaboration services
            if self.enable_collaboration:
                self.dependency_graph = get_dependency_graph()
                self.context_manager = get_context_manager()
                print("✓ Phase 4: Collaboration enabled")
            else:
                self.dependency_graph = None
                self.context_manager = None
        else:
            self.agent_router = None
            self.phase_detector = None
            self.dependency_graph = None
            self.context_manager = None

    def analyze_generation_plan(
        self,
        document_names: List[str]
    ) -> Dict:
        """
        Analyze document selection and provide recommendations

        Args:
            document_names: List of document names to generate

        Returns:
            Dictionary with phase analysis and recommendations
        """
        if not self.use_specialized_agents or not self.phase_detector:
            return {
                "phase_detection_enabled": False,
                "message": "Phase detection disabled (using generic generation)"
            }

        # Detect phase
        phase_result = self.phase_detector.detect_phase(document_names)

        # Get phase information
        phase_info = None
        if phase_result["primary_phase"]:
            phase_info = self.phase_detector.get_phase_info(phase_result["primary_phase"])

        # Validate completeness
        validation = None
        if phase_result["primary_phase"]:
            validation = self.phase_detector.validate_phase_completeness(
                phase_result["primary_phase"],
                document_names
            )

        return {
            "phase_detection_enabled": True,
            "primary_phase": phase_result["primary_phase"],
            "confidence": phase_result["confidence"],
            "mixed_phases": phase_result["mixed_phases"],
            "phase_breakdown": phase_result["phase_breakdown"],
            "document_phase_map": phase_result.get("document_phase_map", {}),
            "warnings": phase_result.get("warnings", []),
            "recommendations": phase_result.get("recommendations", []),
            "phase_info": phase_info,
            "validation": validation
        }

    async def generate_documents(
        self,
        task: GenerationTask,
        progress_callback: Optional[Callable[[GenerationTask], None]] = None
    ) -> GenerationTask:
        """
        Generate multiple documents using specialized agents

        Args:
            task: GenerationTask with request details
            progress_callback: Optional callback for progress updates

        Returns:
            Updated GenerationTask with results
        """
        try:
            # Update status
            task.status = "in_progress"
            task.progress = 5
            task.message = "Analyzing document selection..."
            if progress_callback:
                progress_callback(task)

            # Phase detection
            if self.use_specialized_agents:
                task.phase_info = self.analyze_generation_plan(task.document_names)
                task.progress = 10
                task.message = f"Detected phase: {task.phase_info.get('primary_phase', 'unknown')}"
                if progress_callback:
                    progress_callback(task)

            # Build assumptions context
            assumptions_text = self._build_assumptions_context(task.assumptions)

            task.progress = 15
            task.message = "Gathering relevant context from knowledge base..."
            if progress_callback:
                progress_callback(task)

            # Retrieve RAG context
            rag_context = await self._retrieve_rag_context(task.document_names)
            context_text = self._format_context(rag_context)

            task.progress = 25
            task.message = f"Generating {len(task.document_names)} documents..."
            if progress_callback:
                progress_callback(task)

            # Phase 4: Use collaboration if enabled
            if self.enable_collaboration and self.dependency_graph:
                # Clear context manager for new task
                self.context_manager.clear()

                # Get generation batches (respects dependencies)
                generation_batches = self.dependency_graph.get_generation_order(task.document_names)

                # Generate batch by batch with collaboration
                collaboration_metadata = await self._generate_with_collaboration(
                    task=task,
                    generation_batches=generation_batches,
                    assumptions_text=assumptions_text,
                    context_text=context_text,
                    progress_callback=progress_callback
                )

                # Store collaboration metadata for frontend
                task.collaboration_metadata = collaboration_metadata
            else:
                # Legacy sequential generation (Phase 1-3)
                progress_per_doc = 70 / len(task.document_names)

                for idx, doc_name in enumerate(task.document_names):
                    task.message = f"Generating {doc_name}..."
                    if progress_callback:
                        progress_callback(task)

                    # Get linked assumptions for this document
                    doc_assumptions = self._get_linked_assumptions(
                        doc_name,
                        task.assumptions,
                        task.linked_assumptions
                    )

                    # Generate document using appropriate agent
                    result = await self._generate_single_document(
                        document_name=doc_name,
                        assumptions=doc_assumptions,
                        context=context_text,
                        all_assumptions=assumptions_text
                    )

                    # Store results
                    task.sections[doc_name] = result["content"]
                    task.agent_metadata[doc_name] = result["metadata"]
                    task.citations.extend(result.get("citations", []))
                    
                    # Run quality analysis on generated content (precompute for immediate display)
                    # This ensures the editor shows AI-verified scores immediately on load
                    try:
                        quality_agent = QualityAgent(api_key=self.api_key)
                        quality_result = quality_agent.evaluate(
                            content=result["content"],
                            document_type=doc_name,
                            project_info={"assumptions": doc_assumptions}
                        )
                        # Store quality analysis results in the format expected by frontend
                        task.quality_analysis[doc_name] = {
                            "overall_score": quality_result.get("overall_score", 0),
                            "breakdown": {
                                "hallucination": quality_result.get("detailed_checks", {}).get("hallucination", {}),
                                "vague_language": quality_result.get("detailed_checks", {}).get("vague_language", {}),
                                "citations": quality_result.get("detailed_checks", {}).get("citations", {}),
                                "compliance": quality_result.get("detailed_checks", {}).get("compliance", {}),
                                "completeness": quality_result.get("detailed_checks", {}).get("completeness", {}),
                            },
                            "analyzed_at": datetime.now().isoformat()
                        }
                    except Exception as qa_error:
                        # Don't fail generation if quality analysis fails
                        task.quality_analysis[doc_name] = {
                            "overall_score": 0,
                            "error": str(qa_error),
                            "analyzed_at": datetime.now().isoformat()
                        }

                    # Update progress
                    task.progress = int(25 + (idx + 1) * progress_per_doc)
                    if progress_callback:
                        progress_callback(task)

            # Finalize
            task.progress = 95
            task.message = "Finalizing citations and formatting..."
            if progress_callback:
                progress_callback(task)

            # Deduplicate citations
            task.citations = self._deduplicate_citations(task.citations)

            # Mark complete
            task.status = "completed"
            task.progress = 100
            task.message = "Document generation complete!"
            if progress_callback:
                progress_callback(task)

            return task

        except Exception as e:
            import traceback
            task.status = "failed"
            task.message = f"Generation failed: {str(e)}"
            task.errors.append(str(e))
            task.errors.append(traceback.format_exc())

            if progress_callback:
                progress_callback(task)

            return task

    async def _generate_single_document(
        self,
        document_name: str,
        assumptions: List[Dict[str, str]],
        context: str,
        all_assumptions: str
    ) -> Dict:
        """
        Generate a single document using specialized agent or generic generation

        Args:
            document_name: Name of document to generate
            assumptions: Linked assumptions for this document
            context: RAG context text
            all_assumptions: All assumptions formatted

        Returns:
            Dictionary with content, metadata, and citations
        """
        # Try to get specialized agent
        agent = None
        agent_name = "GenericClaude"

        if self.use_specialized_agents and self.agent_router:
            agent = self.agent_router.get_agent_for_document(document_name)
            if agent:
                agent_name = agent.__class__.__name__

        # Generate using specialized agent if available
        if agent:
            try:
                # Call specialized agent's generate method
                result = await self._call_specialized_agent(
                    agent=agent,
                    document_name=document_name,
                    assumptions=assumptions,
                    context=context
                )

                return {
                    "content": result["content"],
                    "metadata": {
                        "agent": agent_name,
                        "method": "specialized_agent",
                        "agent_info": self.agent_router.get_agent_info(document_name)
                    },
                    "citations": result.get("citations", [])
                }

            except Exception as e:
                print(f"Error with specialized agent {agent_name}: {e}")
                # Fall back to generic generation
                pass

        # Generic generation fallback
        return await self._generate_generic(
            document_name=document_name,
            assumptions=all_assumptions,
            context=context
        )

    async def _call_specialized_agent(
        self,
        agent,
        document_name: str,
        assumptions: List[Dict[str, str]],
        context: str
    ) -> Dict:
        """
        Call a specialized agent's generation method

        Args:
            agent: Specialized agent instance
            document_name: Name of document
            assumptions: Assumptions for this document
            context: RAG context

        Returns:
            Generation result with content and citations
        """
        # Build prompt for agent
        assumptions_text = "\n".join([
            f"- {a['text']} (Source: {a.get('source', 'User')})"
            for a in assumptions
        ])

        # Check if agent has async generate method
        if hasattr(agent, 'generate_async'):
            result = await agent.generate_async(
                requirements=assumptions_text,
                context=context
            )
        elif hasattr(agent, 'generate'):
            # Synchronous generate
            result = agent.generate(
                requirements=assumptions_text,
                context=context
            )
        elif hasattr(agent, 'execute'):
            # Legacy execute method (Phase 1 agents)
            task = {
                'requirements': assumptions_text,
                'context': context,
                'assumptions': assumptions
            }
            result = agent.execute(task)
            # Convert execute result format to generate result format
            if isinstance(result, dict) and 'content' in result:
                return result
            elif isinstance(result, str):
                return {
                    "content": result,
                    "citations": []
                }
            else:
                raise ValueError(f"Unexpected result format from {agent.__class__.__name__}.execute()")
        else:
            raise ValueError(f"Agent {agent.__class__.__name__} has no generate/execute method")

        return result

    # ============================================================
    # Phase 4: Collaboration Methods
    # ============================================================

    async def _generate_with_collaboration(
        self,
        task: GenerationTask,
        generation_batches: List[List[str]],
        assumptions_text: str,
        context_text: str,
        progress_callback: Optional[Callable[[GenerationTask], None]]
    ) -> Dict:
        """
        Generate documents batch by batch with collaboration

        Args:
            task: GenerationTask instance
            generation_batches: List of batches (each batch is list of doc names)
            assumptions_text: Formatted assumptions
            context_text: RAG context
            progress_callback: Progress callback

        Returns:
            Collaboration metadata dictionary
        """
        total_docs = len(task.document_names)
        progress_per_doc = 70 / total_docs
        docs_generated = 0

        # Track generation order for metadata
        generation_order = []
        batch_info = []

        for batch_idx, batch in enumerate(generation_batches):
            batch_start_time = time.time()

            task.message = f"Generating batch {batch_idx + 1}/{len(generation_batches)} ({len(batch)} documents)..."
            if progress_callback:
                progress_callback(task)

            # Generate all documents in this batch (can be parallel)
            batch_results = await self._generate_batch(
                batch=batch,
                task=task,
                assumptions_text=assumptions_text,
                context_text=context_text
            )

            # Store results and add to context manager
            for doc_name, result in batch_results.items():
                task.sections[doc_name] = result["content"]
                task.agent_metadata[doc_name] = result["metadata"]
                task.citations.extend(result.get("citations", []))

                # Add to context manager for next batches
                self.context_manager.add_content(
                    doc_name=doc_name,
                    content=result["content"],
                    metadata=result["metadata"]
                )

                # Track generation order
                generation_order.append(doc_name)

                # Update progress
                docs_generated += 1
                task.progress = int(25 + docs_generated * progress_per_doc)
                if progress_callback:
                    progress_callback(task)

            # Track batch info
            batch_time = time.time() - batch_start_time
            batch_info.append({
                "batch_number": batch_idx + 1,
                "documents": batch,
                "generation_time_seconds": round(batch_time, 2)
            })

        # Get cross-references from context manager
        cross_references = self.context_manager.get_cross_references()

        # Build collaboration metadata
        collaboration_metadata = {
            "enabled": True,
            "generation_order": generation_order,
            "batch_count": len(generation_batches),
            "batches": batch_info,
            "cross_references": cross_references,
            "context_pool_stats": self.context_manager.get_statistics()
        }

        return collaboration_metadata

    async def _generate_batch(
        self,
        batch: List[str],
        task: GenerationTask,
        assumptions_text: str,
        context_text: str
    ) -> Dict[str, Dict]:
        """
        Generate all documents in a batch (parallel if multiple docs)

        Args:
            batch: List of document names in this batch
            task: GenerationTask instance
            assumptions_text: Formatted assumptions
            context_text: RAG context

        Returns:
            Dictionary mapping doc_name -> result
        """
        if len(batch) == 1:
            # Single document - generate directly
            doc_name = batch[0]
            result = await self._generate_single_with_context(
                document_name=doc_name,
                task=task,
                assumptions_text=assumptions_text,
                context_text=context_text
            )
            return {doc_name: result}

        # Multiple documents - generate in parallel
        tasks_list = [
            self._generate_single_with_context(
                document_name=doc_name,
                task=task,
                assumptions_text=assumptions_text,
                context_text=context_text
            )
            for doc_name in batch
        ]

        results = await asyncio.gather(*tasks_list)

        # Map results to document names
        return {doc_name: result for doc_name, result in zip(batch, results)}

    async def _generate_single_with_context(
        self,
        document_name: str,
        task: GenerationTask,
        assumptions_text: str,
        context_text: str
    ) -> Dict:
        """
        Generate a single document with dependency context from context manager

        Args:
            document_name: Name of document to generate
            task: GenerationTask instance
            assumptions_text: Formatted assumptions
            context_text: RAG context

        Returns:
            Generation result dictionary
        """
        # Get linked assumptions for this document
        doc_assumptions = self._get_linked_assumptions(
            document_name,
            task.assumptions,
            task.linked_assumptions
        )

        # Get dependencies from dependency graph
        dependencies = self.dependency_graph.get_dependencies(document_name)

        # Retrieve dependency content from context manager
        dependency_content = {}
        if dependencies:
            dependency_content = self.context_manager.get_related_content(
                doc_name=document_name,
                dependency_list=dependencies,
                max_summary_length=1000
            )

        # Get agent for this document
        agent = None
        if self.use_specialized_agents and self.agent_router:
            agent = self.agent_router.get_agent_for_document(document_name)

        # If agent has collaboration enabled, use collaborative generation
        if agent and hasattr(agent, 'has_collaboration_enabled') and agent.has_collaboration_enabled():
            # Pass dependencies to agent
            result = await self._call_specialized_agent_with_collaboration(
                agent=agent,
                document_name=document_name,
                assumptions=doc_assumptions,
                context=context_text,
                dependencies=dependency_content
            )
        else:
            # Legacy generation (no collaboration)
            result = await self._generate_single_document(
                document_name=document_name,
                assumptions=doc_assumptions,
                context=context_text,
                all_assumptions=assumptions_text
            )

        return result

    async def _call_specialized_agent_with_collaboration(
        self,
        agent,
        document_name: str,
        assumptions: List[Dict[str, str]],
        context: str,
        dependencies: Dict[str, str]
    ) -> Dict:
        """
        Call specialized agent with collaboration features

        Args:
            agent: Specialized agent instance
            document_name: Name of document
            assumptions: Assumptions for this document
            context: RAG context
            dependencies: Dictionary of dependency_name -> content

        Returns:
            Generation result with content and citations
        """
        # Build assumptions text
        assumptions_text = "\n".join([
            f"- {a['text']} (Source: {a.get('source', 'User')})"
            for a in assumptions
        ])

        # Check if agent has collaborative generate method
        if hasattr(agent, 'generate_with_collaboration'):
            # Phase 4 agent with collaboration support
            result = await agent.generate_with_collaboration(
                requirements=assumptions_text,
                context=context,
                dependencies=dependencies
            )
        elif hasattr(agent, 'generate_async'):
            # Phase 2/3 agent - use standard generation
            result = await agent.generate_async(
                requirements=assumptions_text,
                context=context
            )
        elif hasattr(agent, 'generate'):
            # Synchronous generate
            result = agent.generate(
                requirements=assumptions_text,
                context=context
            )
        else:
            # Fall back to base method
            return await self._call_specialized_agent(
                agent=agent,
                document_name=document_name,
                assumptions=assumptions,
                context=context
            )

        return result

    async def _call_claude_with_retry(
        self,
        client,
        model: str,
        max_tokens: int,
        messages: List[Dict],
        max_retries: int = 3
    ):
        """
        Call Claude API with exponential backoff retry logic

        Args:
            client: Anthropic client
            model: Model name
            max_tokens: Max tokens to generate
            messages: Message list
            max_retries: Maximum retry attempts (default 3)

        Returns:
            API response

        Raises:
            Exception: If all retries fail
        """
        import anthropic

        for attempt in range(max_retries):
            try:
                return client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages
                )
            except anthropic.RateLimitError as e:
                # Rate limit hit - wait and retry
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (0.5 * attempt)  # Exponential backoff: 1s, 2.5s, 5s
                    print(f"⏳ Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                else:
                    raise Exception(f"Rate limit exceeded after {max_retries} attempts: {str(e)}")
            except anthropic.APIStatusError as e:
                # API error (including 529 Overloaded)
                if e.status_code == 529:  # Overloaded
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + (0.5 * attempt)
                        print(f"⏳ API overloaded (529), retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise Exception(f"API overloaded after {max_retries} attempts. Please try again in a few minutes.")
                else:
                    # Other API errors - don't retry
                    raise Exception(f"API error {e.status_code}: {str(e)}")
            except Exception as e:
                # Unknown error - don't retry
                raise Exception(f"Unexpected error calling Claude: {str(e)}")

    async def _generate_generic(
        self,
        document_name: str,
        assumptions: str,
        context: str
    ) -> Dict:
        """
        Generic document generation using Claude (fallback)

        Args:
            document_name: Name of document to generate
            assumptions: Formatted assumptions text
            context: RAG context text

        Returns:
            Generation result dictionary
        """
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        prompt = f"""You are a DoD acquisition expert writing {document_name} for a federal procurement.

ASSUMPTIONS TO INCORPORATE:
{assumptions}

RELEVANT SOURCE MATERIAL:
{context}

INSTRUCTIONS:
1. Write professional, compliant content for {document_name}
2. Include proper FAR/DFARS citations where applicable
3. Reference the assumptions provided
4. Use DoD acquisition terminology
5. Keep it concise but comprehensive (2-4 paragraphs)
6. Use inline citations like [1], [2], etc. for source references

Write the section content now:"""

        # Call with retry logic
        message = await self._call_claude_with_retry(
            client=client,
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text.strip()

        return {
            "content": content,
            "metadata": {
                "agent": "GenericClaude",
                "method": "generic_generation",
                "agent_info": {"has_specialized_agent": False}
            },
            "citations": []
        }

    async def _retrieve_rag_context(
        self,
        document_names: List[str]
    ) -> List[Dict]:
        """
        Retrieve relevant context from RAG for documents

        Args:
            document_names: List of document names

        Returns:
            List of context chunks with metadata
        """
        all_context = []

        for doc_name in document_names:
            # Search for relevant content
            search_query = f"{doc_name} DoD acquisition federal requirements"
            results = self.rag_service.search_documents(query=search_query, k=5)
            all_context.extend(results)

        # Return top 20 unique chunks
        return all_context[:20]

    def _build_assumptions_context(
        self,
        assumptions: List[Dict[str, str]]
    ) -> str:
        """Build formatted assumptions text"""
        return "\n".join([
            f"- {a['text']} (Source: {a.get('source', 'User')})"
            for a in assumptions
        ])

    def _format_context(
        self,
        context_chunks: List[Dict]
    ) -> str:
        """Format RAG context chunks into text"""
        return "\n\n---\n\n".join([
            f"Source: {c['metadata'].get('source', 'Unknown')}\n{c['content']}"
            for c in context_chunks
        ])

    def _get_linked_assumptions(
        self,
        document_name: str,
        all_assumptions: List[Dict[str, str]],
        linked_assumptions: Dict[str, List[str]]
    ) -> List[Dict[str, str]]:
        """
        Get assumptions linked to a specific document

        Args:
            document_name: Name of document
            all_assumptions: All assumptions
            linked_assumptions: Mapping of doc -> assumption IDs

        Returns:
            List of linked assumptions
        """
        if document_name not in linked_assumptions:
            return all_assumptions  # Return all if no specific linking

        linked_ids = linked_assumptions[document_name]
        return [
            a for a in all_assumptions
            if a.get('id') in linked_ids
        ]

    def _deduplicate_citations(
        self,
        citations: List[Dict]
    ) -> List[Dict]:
        """Remove duplicate citations"""
        seen = set()
        unique = []

        for citation in citations:
            # Use source + page as key
            key = (citation.get('source', ''), citation.get('page', 0))
            if key not in seen:
                seen.add(key)
                unique.append(citation)

        return unique[:10]  # Limit to 10 citations


# Singleton instance
_coordinator_instance: Optional[GenerationCoordinator] = None


def get_generation_coordinator(
    api_key: Optional[str] = None,
    use_specialized_agents: bool = True
) -> GenerationCoordinator:
    """
    Get singleton generation coordinator instance

    Args:
        api_key: Anthropic API key (optional)
        use_specialized_agents: Whether to use specialized agents

    Returns:
        GenerationCoordinator instance
    """
    global _coordinator_instance

    if _coordinator_instance is None:
        _coordinator_instance = GenerationCoordinator(
            api_key=api_key,
            use_specialized_agents=use_specialized_agents
        )

    return _coordinator_instance
