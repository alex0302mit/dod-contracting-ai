"""
Context Manager Service

Manages shared context across agent generations for cross-referencing and collaboration.
Stores generated content temporarily and tracks cross-references between documents.

Phase 4: Agent Collaboration
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class GeneratedContent:
    """
    Represents generated content with metadata

    Attributes:
        doc_name: Document name
        content: Generated text content
        metadata: Agent metadata (agent name, method, etc.)
        generated_at: Timestamp of generation
        word_count: Number of words in content
        character_count: Number of characters in content
    """
    doc_name: str
    content: str
    metadata: Dict
    generated_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    character_count: int = 0

    def __post_init__(self):
        """Calculate word and character counts"""
        if self.word_count == 0:
            self.word_count = len(self.content.split())
        if self.character_count == 0:
            self.character_count = len(self.content)

    def get_summary(self, max_length: int = 500) -> str:
        """
        Get truncated summary of content

        Args:
            max_length: Maximum character length

        Returns:
            Truncated content with ellipsis if needed
        """
        if len(self.content) <= max_length:
            return self.content

        return self.content[:max_length] + "..."


@dataclass
class CrossReference:
    """
    Represents a cross-reference between documents

    Attributes:
        from_doc: Document making the reference
        to_doc: Document being referenced
        reference_text: Brief description of what's being referenced
        created_at: Timestamp of reference creation
    """
    from_doc: str
    to_doc: str
    reference_text: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "from": self.from_doc,
            "to": self.to_doc,
            "reference": self.reference_text,
            "created_at": self.created_at.isoformat()
        }


class ContextManager:
    """
    Manages shared context across agent generations

    Responsibilities:
    - Store generated content temporarily
    - Provide retrieval API for agents
    - Track cross-references between documents
    - Manage memory usage (clear between tasks)
    """

    def __init__(self, max_content_length: int = 10000):
        """
        Initialize context manager

        Args:
            max_content_length: Maximum characters to store per document (to manage memory)
        """
        self.max_content_length = max_content_length
        self._context_pool: Dict[str, GeneratedContent] = {}
        self._cross_references: List[CrossReference] = []
        self._created_at = datetime.now()

    def add_content(self, doc_name: str, content: str, metadata: Dict):
        """
        Add generated content to shared pool

        Args:
            doc_name: Document name
            content: Generated text content
            metadata: Agent metadata dictionary
        """
        # Truncate content if too long (to manage memory)
        if len(content) > self.max_content_length:
            truncated_content = content[:self.max_content_length]
            print(f"⚠️  Warning: Content for '{doc_name}' truncated from {len(content)} to {self.max_content_length} characters")
        else:
            truncated_content = content

        generated = GeneratedContent(
            doc_name=doc_name,
            content=truncated_content,
            metadata=metadata
        )

        self._context_pool[doc_name] = generated

        print(f"✓ Context Manager: Added '{doc_name}' ({generated.word_count} words)")

    def get_content(self, doc_name: str) -> Optional[str]:
        """
        Retrieve previously generated content

        Args:
            doc_name: Document name

        Returns:
            Content string or None if not found
        """
        if doc_name in self._context_pool:
            return self._context_pool[doc_name].content
        return None

    def get_content_obj(self, doc_name: str) -> Optional[GeneratedContent]:
        """
        Retrieve generated content object with metadata

        Args:
            doc_name: Document name

        Returns:
            GeneratedContent object or None if not found
        """
        return self._context_pool.get(doc_name)

    def get_related_content(self,
                           doc_name: str,
                           dependency_list: List[str],
                           max_summary_length: int = 1000) -> Dict[str, str]:
        """
        Get all dependent content for a document

        Args:
            doc_name: Name of document being generated
            dependency_list: List of document names to retrieve
            max_summary_length: Maximum length per dependency (default 1000 chars)

        Returns:
            Dictionary mapping doc_name -> content summary
        """
        related = {}

        for dep_name in dependency_list:
            if dep_name in self._context_pool:
                content_obj = self._context_pool[dep_name]
                # Use summary instead of full content to manage token usage
                related[dep_name] = content_obj.get_summary(max_summary_length)
            else:
                # Dependency not yet generated (shouldn't happen if generation order is correct)
                print(f"⚠️  Warning: Dependency '{dep_name}' not found for '{doc_name}'")

        if related:
            print(f"✓ Context Manager: Providing {len(related)} dependencies for '{doc_name}'")

        return related

    def add_cross_reference(self, from_doc: str, to_doc: str, reference_text: str):
        """
        Track that from_doc references to_doc

        Args:
            from_doc: Document making the reference
            to_doc: Document being referenced
            reference_text: Brief description of the reference
        """
        cross_ref = CrossReference(
            from_doc=from_doc,
            to_doc=to_doc,
            reference_text=reference_text
        )

        self._cross_references.append(cross_ref)

        print(f"✓ Context Manager: Tracked reference from '{from_doc}' to '{to_doc}'")

    def get_cross_references(self, doc_name: Optional[str] = None) -> List[Dict]:
        """
        Get all cross-references, optionally filtered by document

        Args:
            doc_name: Optional document name to filter by (returns refs from or to this doc)

        Returns:
            List of cross-reference dictionaries
        """
        if doc_name is None:
            # Return all cross-references
            return [ref.to_dict() for ref in self._cross_references]

        # Filter by document
        filtered = [
            ref.to_dict()
            for ref in self._cross_references
            if ref.from_doc == doc_name or ref.to_doc == doc_name
        ]

        return filtered

    def get_references_from(self, doc_name: str) -> List[Dict]:
        """
        Get cross-references made by a specific document

        Args:
            doc_name: Document name

        Returns:
            List of cross-reference dictionaries where this doc is the source
        """
        return [
            ref.to_dict()
            for ref in self._cross_references
            if ref.from_doc == doc_name
        ]

    def get_references_to(self, doc_name: str) -> List[Dict]:
        """
        Get cross-references pointing to a specific document

        Args:
            doc_name: Document name

        Returns:
            List of cross-reference dictionaries where this doc is the target
        """
        return [
            ref.to_dict()
            for ref in self._cross_references
            if ref.to_doc == doc_name
        ]

    def has_content(self, doc_name: str) -> bool:
        """
        Check if content exists for a document

        Args:
            doc_name: Document name

        Returns:
            True if content exists, False otherwise
        """
        return doc_name in self._context_pool

    def get_all_document_names(self) -> List[str]:
        """
        Get list of all documents in context pool

        Returns:
            List of document names
        """
        return list(self._context_pool.keys())

    def get_statistics(self) -> Dict:
        """
        Get statistics about the context pool

        Returns:
            Dictionary with context pool statistics
        """
        total_words = sum(content.word_count for content in self._context_pool.values())
        total_chars = sum(content.character_count for content in self._context_pool.values())
        total_refs = len(self._cross_references)

        return {
            "document_count": len(self._context_pool),
            "total_words": total_words,
            "total_characters": total_chars,
            "cross_reference_count": total_refs,
            "created_at": self._created_at.isoformat(),
            "documents": list(self._context_pool.keys())
        }

    def clear(self):
        """
        Clear all context (call between generation tasks)

        Frees memory and resets for next generation task.
        """
        doc_count = len(self._context_pool)
        ref_count = len(self._cross_references)

        self._context_pool.clear()
        self._cross_references.clear()
        self._created_at = datetime.now()

        if doc_count > 0 or ref_count > 0:
            print(f"✓ Context Manager: Cleared {doc_count} documents and {ref_count} cross-references")

    def __repr__(self):
        return f"ContextManager(docs={len(self._context_pool)}, refs={len(self._cross_references)})"


# Singleton pattern for global access
_context_manager_instance = None

def get_context_manager(max_content_length: int = 10000) -> ContextManager:
    """
    Get or create the singleton ContextManager instance

    Args:
        max_content_length: Maximum characters per document

    Returns:
        ContextManager instance
    """
    global _context_manager_instance

    if _context_manager_instance is None:
        _context_manager_instance = ContextManager(max_content_length)

    return _context_manager_instance
