"""
Agent Comparison Service

Enables comparison of document generation across different agents and models.
Part of Phase 6: Advanced Features
"""

from typing import List, Dict, Optional, Tuple
import asyncio
import time
from datetime import datetime
import hashlib

from backend.services.agent_router import AgentRouter
from backend.services.rag_service import RAGService


class AgentVariant:
    """Represents a specific agent configuration for comparison"""

    def __init__(
        self,
        variant_id: str,
        name: str,
        model: str = "claude-sonnet-4",
        temperature: float = 0.7,
        agent_class: Optional[str] = None,
        description: str = ""
    ):
        self.variant_id = variant_id
        self.name = name
        self.model = model
        self.temperature = temperature
        self.agent_class = agent_class
        self.description = description


class ComparisonResult:
    """Stores comparison results for a single variant"""

    def __init__(
        self,
        variant: AgentVariant,
        content: str,
        metadata: Dict,
        quality_score: float,
        generation_time: float,
        word_count: int,
        citations_count: int
    ):
        self.variant = variant
        self.content = content
        self.metadata = metadata
        self.quality_score = quality_score
        self.generation_time = generation_time
        self.word_count = word_count
        self.citations_count = citations_count
        self.generated_at = datetime.now()


class ComparisonTask:
    """Represents a multi-agent comparison task"""

    def __init__(
        self,
        task_id: str,
        document_name: str,
        variants: List[AgentVariant],
        requirements: str,
        context: str = ""
    ):
        self.task_id = task_id
        self.document_name = document_name
        self.variants = variants
        self.requirements = requirements
        self.context = context

        # Results
        self.results: List[ComparisonResult] = []
        self.status = "pending"
        self.progress = 0
        self.message = "Initializing comparison..."
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None


class AgentComparisonService:
    """
    Service for comparing multiple agent configurations

    Enables A/B testing of agents, models, and parameters to find
    optimal configurations for different document types.
    """

    def __init__(
        self,
        api_key: str,
        agent_router: AgentRouter,
        rag_service: RAGService
    ):
        self.api_key = api_key
        self.agent_router = agent_router
        self.rag_service = rag_service
        self.active_comparisons: Dict[str, ComparisonTask] = {}

    def create_comparison_task(
        self,
        document_name: str,
        requirements: str,
        variants: List[AgentVariant],
        context: str = ""
    ) -> str:
        """
        Create a new comparison task

        Args:
            document_name: Name of document to generate
            requirements: Requirements/assumptions for generation
            variants: List of agent variants to compare
            context: Optional additional context

        Returns:
            task_id: Unique identifier for this comparison
        """
        # Generate unique task ID
        task_id = hashlib.md5(
            f"{document_name}-{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        task = ComparisonTask(
            task_id=task_id,
            document_name=document_name,
            variants=variants,
            requirements=requirements,
            context=context
        )

        self.active_comparisons[task_id] = task
        return task_id

    async def run_comparison(self, task_id: str) -> ComparisonTask:
        """
        Run comparison across all variants

        Args:
            task_id: ID of comparison task

        Returns:
            ComparisonTask with results populated
        """
        task = self.active_comparisons.get(task_id)
        if not task:
            raise ValueError(f"Comparison task {task_id} not found")

        task.status = "running"
        task.message = f"Generating {len(task.variants)} variants..."

        # Generate all variants in parallel
        generation_tasks = []
        for variant in task.variants:
            gen_task = self._generate_variant(
                task.document_name,
                task.requirements,
                task.context,
                variant
            )
            generation_tasks.append(gen_task)

        # Await all generations
        results = await asyncio.gather(*generation_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle error
                task.status = "partial_failure"
                task.message = f"Variant {i+1} failed: {str(result)}"
                continue

            task.results.append(result)
            task.progress = int((i + 1) / len(task.variants) * 100)

        task.status = "completed"
        task.message = f"Comparison complete: {len(task.results)}/{len(task.variants)} variants"
        task.completed_at = datetime.now()

        return task

    async def _generate_variant(
        self,
        document_name: str,
        requirements: str,
        context: str,
        variant: AgentVariant
    ) -> ComparisonResult:
        """
        Generate a single variant

        Args:
            document_name: Document name
            requirements: Requirements text
            context: Context text
            variant: Agent variant configuration

        Returns:
            ComparisonResult with generation output
        """
        start_time = time.time()

        # Get agent for this variant
        if variant.agent_class:
            # Use specific agent class
            agent = self.agent_router.get_agent(document_name)
            if agent:
                # Override model and temperature
                agent.model = variant.model
                # Note: temperature override would require agent API support
        else:
            # Use default agent for this document
            agent = self.agent_router.get_agent(document_name)

        # Retrieve RAG context
        rag_context = await self.rag_service.retrieve_context(
            document_name,
            requirements
        )

        # Combine contexts
        full_context = f"{context}\n\n{rag_context}" if context else rag_context

        # Generate content
        if agent:
            result = await agent.execute_async({
                "requirements": requirements,
                "context": full_context
            })
        else:
            # Fallback to generic generation
            result = {
                "content": f"[Generic generation for {document_name}]",
                "citations": [],
                "metadata": {"method": "generic", "agent": "none"}
            }

        # Calculate metrics
        generation_time = time.time() - start_time
        content = result.get("content", "")
        word_count = len(content.split())
        citations_count = len(result.get("citations", []))

        # Calculate quality score (simplified)
        quality_score = self._calculate_quality_score(
            content,
            citations_count,
            word_count
        )

        return ComparisonResult(
            variant=variant,
            content=content,
            metadata=result.get("metadata", {}),
            quality_score=quality_score,
            generation_time=generation_time,
            word_count=word_count,
            citations_count=citations_count
        )

    def _calculate_quality_score(
        self,
        content: str,
        citations_count: int,
        word_count: int
    ) -> float:
        """
        Calculate simple quality score

        In production, this would use the full quality_agent.py logic

        Returns:
            Quality score from 0-100
        """
        # Basic heuristics
        score = 50.0

        # Length (prefer 500-2000 words)
        if 500 <= word_count <= 2000:
            score += 20
        elif word_count > 2000:
            score += 10

        # Citations (prefer 3-10)
        if 3 <= citations_count <= 10:
            score += 15
        elif citations_count > 0:
            score += 5

        # Content checks
        if "shall" in content.lower():
            score += 5  # Proper regulatory language
        if "FAR" in content or "DFARS" in content:
            score += 10  # Regulatory references

        return min(100.0, score)

    def get_comparison_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a comparison task"""
        task = self.active_comparisons.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "document_name": task.document_name,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "variants_count": len(task.variants),
            "results_count": len(task.results),
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }

    def get_comparison_results(self, task_id: str) -> Optional[Dict]:
        """Get full results of a comparison task"""
        task = self.active_comparisons.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "document_name": task.document_name,
            "status": task.status,
            "results": [
                {
                    "variant_id": result.variant.variant_id,
                    "variant_name": result.variant.name,
                    "model": result.variant.model,
                    "content": result.content,
                    "quality_score": result.quality_score,
                    "generation_time": result.generation_time,
                    "word_count": result.word_count,
                    "citations_count": result.citations_count,
                    "metadata": result.metadata,
                    "generated_at": result.generated_at.isoformat()
                }
                for result in task.results
            ],
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }

    def get_winner(self, task_id: str, criteria: str = "quality") -> Optional[ComparisonResult]:
        """
        Get the best variant based on criteria

        Args:
            task_id: Comparison task ID
            criteria: "quality", "speed", "length", or "citations"

        Returns:
            Best ComparisonResult or None
        """
        task = self.active_comparisons.get(task_id)
        if not task or not task.results:
            return None

        if criteria == "quality":
            return max(task.results, key=lambda r: r.quality_score)
        elif criteria == "speed":
            return min(task.results, key=lambda r: r.generation_time)
        elif criteria == "length":
            return max(task.results, key=lambda r: r.word_count)
        elif criteria == "citations":
            return max(task.results, key=lambda r: r.citations_count)
        else:
            return max(task.results, key=lambda r: r.quality_score)

    def clear_completed_comparisons(self, max_age_hours: int = 24):
        """Clear old completed comparisons to free memory"""
        now = datetime.now()
        to_delete = []

        for task_id, task in self.active_comparisons.items():
            if task.status in ["completed", "failed", "partial_failure"]:
                if task.completed_at:
                    age_hours = (now - task.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_delete.append(task_id)

        for task_id in to_delete:
            del self.active_comparisons[task_id]


# Singleton instance
_comparison_service: Optional[AgentComparisonService] = None


def get_comparison_service(
    api_key: Optional[str] = None,
    agent_router: Optional[AgentRouter] = None,
    rag_service: Optional[RAGService] = None
) -> AgentComparisonService:
    """Get singleton comparison service instance"""
    global _comparison_service

    if _comparison_service is None:
        if not api_key:
            import os
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Import services if not provided
        if not agent_router:
            from backend.services.agent_router import get_agent_router
            agent_router = get_agent_router(api_key=api_key)

        if not rag_service:
            from backend.services.rag_service import get_rag_service
            rag_service = get_rag_service()

        _comparison_service = AgentComparisonService(
            api_key=api_key,
            agent_router=agent_router,
            rag_service=rag_service
        )

    return _comparison_service
