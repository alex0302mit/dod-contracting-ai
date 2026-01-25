"""
Generation Hash Service Module

Computes deterministic hashes of generation inputs to enable
incremental generation - avoiding regeneration when nothing has changed.

Hash computation includes:
1. Document name
2. Sorted assumptions (id + text)
3. Dependency document content hashes
4. RAG query hash (phase + project context)
5. Agent version/config hash
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime


class GenerationHashService:
    """
    Computes and validates generation input hashes for incremental generation.

    When inputs haven't changed, we can return cached results instead of
    regenerating, saving time and API costs.
    """

    # Version string to invalidate cache when logic changes
    HASH_VERSION = "v1.0"

    def __init__(self):
        self._cache_service = None

    @property
    def cache(self):
        """Lazy load cache service."""
        if self._cache_service is None:
            try:
                from backend.services.cache_service import get_cache_service
                self._cache_service = get_cache_service()
            except ImportError:
                pass
        return self._cache_service

    def compute_generation_hash(
        self,
        document_name: str,
        assumptions: List[Dict[str, str]],
        dependency_contents: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        phase: Optional[str] = None,
        additional_context: Optional[str] = None,
        agent_config: Optional[Dict] = None
    ) -> str:
        """
        Compute a deterministic hash of all generation inputs.

        The hash is used to detect when inputs have changed and
        regeneration is needed.

        Args:
            document_name: Name of document being generated
            assumptions: List of assumption dictionaries
            dependency_contents: Dict mapping dependency name -> content hash
            project_id: Optional project ID
            phase: Optional procurement phase
            additional_context: Optional additional context string
            agent_config: Optional agent configuration

        Returns:
            SHA-256 hash string (first 32 chars)
        """
        # Build canonical representation of inputs
        hash_inputs = {
            "version": self.HASH_VERSION,
            "document_name": document_name,
            "assumptions": self._normalize_assumptions(assumptions),
            "dependencies": dependency_contents or {},
            "project_id": project_id,
            "phase": phase,
            "additional_context": additional_context or "",
            "agent_config": self._normalize_agent_config(agent_config),
        }

        # Create deterministic JSON string
        canonical_json = json.dumps(
            hash_inputs,
            sort_keys=True,
            separators=(',', ':'),
            default=str
        )

        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))
        return hash_obj.hexdigest()[:32]

    def _normalize_assumptions(
        self,
        assumptions: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Normalize assumptions for consistent hashing.

        Sorts by ID and removes any transient fields.
        """
        normalized = []
        for a in assumptions:
            normalized.append({
                "id": a.get("id", ""),
                "text": a.get("text", ""),
                # Don't include source as it might vary
            })

        # Sort by ID for deterministic ordering
        return sorted(normalized, key=lambda x: x.get("id", ""))

    def _normalize_agent_config(
        self,
        config: Optional[Dict]
    ) -> Dict:
        """
        Normalize agent configuration for hashing.

        Only include fields that affect output.
        """
        if not config:
            return {}

        return {
            "model": config.get("model", ""),
            "temperature": config.get("temperature", 0),
            "version": config.get("version", ""),
        }

    def compute_content_hash(self, content: str) -> str:
        """
        Compute hash of document content.

        Used for dependency content comparison.

        Args:
            content: Document content string

        Returns:
            SHA-256 hash string (first 16 chars)
        """
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

    def get_dependency_hashes(
        self,
        db,
        project_id: str,
        dependency_names: List[str]
    ) -> Dict[str, str]:
        """
        Get content hashes for dependency documents.

        Args:
            db: Database session
            project_id: Project ID
            dependency_names: List of dependency document names

        Returns:
            Dict mapping document name -> content hash
        """
        from backend.models.document import ProjectDocument, GenerationStatus

        hashes = {}

        for dep_name in dependency_names:
            doc = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.document_name == dep_name,
                ProjectDocument.generation_status == GenerationStatus.GENERATED
            ).first()

            if doc and doc.generated_content:
                hashes[dep_name] = self.compute_content_hash(doc.generated_content)

        return hashes

    def check_cache(
        self,
        document_id: str,
        input_hash: str
    ) -> Optional[Dict]:
        """
        Check if we have a cached result for the given input hash.

        Args:
            document_id: Document ID
            input_hash: Computed input hash

        Returns:
            Cached result dict if found and hash matches, None otherwise
        """
        if not self.cache or not self.cache.is_connected:
            return None

        cached = self.cache.get_generation_cache(document_id)
        if not cached:
            return None

        # Check if hash matches
        if cached.get("input_hash") == input_hash:
            print(f"[IncrementalGen] Cache HIT for document {document_id}")
            return cached.get("result")

        print(f"[IncrementalGen] Cache MISS - hash changed for document {document_id}")
        return None

    def store_result(
        self,
        document_id: str,
        input_hash: str,
        result: Dict
    ) -> bool:
        """
        Store generation result with its input hash.

        Args:
            document_id: Document ID
            input_hash: Computed input hash
            result: Generation result to cache

        Returns:
            True if stored successfully
        """
        if not self.cache or not self.cache.is_connected:
            return False

        # Store in cache
        success = self.cache.set_generation_cache(
            document_id=document_id,
            input_hash=input_hash,
            result=result
        )

        if success:
            print(f"[IncrementalGen] Stored result for document {document_id}")

        return success

    def invalidate_cache(self, document_id: str) -> bool:
        """
        Invalidate cached result for a document.

        Call this when a document is manually edited or dependencies change.

        Args:
            document_id: Document ID to invalidate

        Returns:
            True if invalidated successfully
        """
        if not self.cache or not self.cache.is_connected:
            return False

        # Delete both hash and result keys
        self.cache.delete(self.cache.get_generation_hash_key(document_id))
        self.cache.delete(self.cache.get_generation_result_key(document_id))

        print(f"[IncrementalGen] Invalidated cache for document {document_id}")
        return True


# Singleton instance
_hash_service: Optional[GenerationHashService] = None


def get_generation_hash_service() -> GenerationHashService:
    """
    Get or create the generation hash service singleton.

    Returns:
        GenerationHashService instance
    """
    global _hash_service

    if _hash_service is None:
        _hash_service = GenerationHashService()

    return _hash_service


def is_incremental_generation_enabled() -> bool:
    """Check if incremental generation is enabled."""
    return os.getenv("ENABLE_INCREMENTAL_GENERATION", "true").lower() == "true"
