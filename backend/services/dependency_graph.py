"""
Dependency Graph Service

Manages document dependencies and determines optimal generation order
using topological sorting and batch parallelization.

Phase 4: Agent Collaboration
"""

import json
import os
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict, deque


class DocumentNode:
    """
    Represents a document in the dependency graph

    Attributes:
        name: Document name
        priority: Generation priority (lower = earlier)
        depends_on: List of document names this document depends on
        dependents: List of document names that depend on this document
        references: Types of references this document makes
    """

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.priority = config.get('priority', 99)
        self.depends_on = config.get('depends_on', [])
        self.references = config.get('references', [])
        self.description = config.get('description', '')
        self.dependents: List[str] = []

    def __repr__(self):
        return f"DocumentNode({self.name}, priority={self.priority}, deps={len(self.depends_on)})"


class DependencyGraph:
    """
    Manages document dependencies and generation order

    Provides:
    - Topological sorting for generation order
    - Batch identification for parallel generation
    - Dependency validation
    - Missing dependency detection
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize dependency graph from configuration

        Args:
            config_path: Path to document_dependencies.json
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                '../config/document_dependencies.json'
            )

        self.config_path = config_path
        self.nodes: Dict[str, DocumentNode] = {}
        self.config = {}

        self._load_config()
        self._build_graph()

    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Dependency configuration not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dependency configuration: {e}")

    def _build_graph(self):
        """Build graph from configuration"""
        dependencies = self.config.get('dependencies', {})

        # Create nodes
        for doc_name, doc_config in dependencies.items():
            self.nodes[doc_name] = DocumentNode(doc_name, doc_config)

        # Build dependents (reverse edges)
        for node in self.nodes.values():
            for dep_name in node.depends_on:
                if dep_name in self.nodes:
                    self.nodes[dep_name].dependents.append(node.name)

    def get_generation_order(self, selected_docs: List[str]) -> List[List[str]]:
        """
        Determine generation order for selected documents

        Uses topological sort with batching for parallel generation.
        Documents in the same batch have no dependencies on each other.

        Args:
            selected_docs: List of document names to generate

        Returns:
            List of batches, where each batch is a list of document names
            Example: [["PWS"], ["Section L"], ["Section M", "Section H"]]
        """
        if not selected_docs:
            return []

        # Get all documents including dependencies
        all_needed = self._get_all_dependencies(selected_docs)

        # Build in-degree map (count of dependencies)
        in_degree = {doc: 0 for doc in all_needed}
        dependency_map = {doc: [] for doc in all_needed}

        for doc in all_needed:
            if doc in self.nodes:
                for dep in self.nodes[doc].depends_on:
                    if dep in all_needed:
                        in_degree[doc] += 1
                        dependency_map[dep].append(doc)

        # Topological sort with batching
        batches = []
        remaining = set(all_needed)

        while remaining:
            # Find all documents with no remaining dependencies (in-degree = 0)
            batch = [doc for doc in remaining if in_degree[doc] == 0]

            if not batch:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected in documents: {remaining}")

            # Sort batch by priority for consistent ordering
            batch.sort(key=lambda d: (
                self.nodes[d].priority if d in self.nodes else 99,
                d  # Secondary sort by name for consistency
            ))

            batches.append(batch)

            # Remove batch from remaining and update in-degrees
            for doc in batch:
                remaining.remove(doc)
                for dependent in dependency_map[doc]:
                    in_degree[dependent] -= 1

        # Filter out documents not originally selected (dependencies only needed for context)
        selected_set = set(selected_docs)
        filtered_batches = []
        for batch in batches:
            filtered_batch = [doc for doc in batch if doc in selected_set]
            if filtered_batch:
                filtered_batches.append(filtered_batch)

        return filtered_batches

    def _get_all_dependencies(self, doc_names: List[str]) -> Set[str]:
        """
        Get all documents including transitive dependencies

        Args:
            doc_names: Initial list of document names

        Returns:
            Set of all document names including dependencies
        """
        result = set()
        queue = deque(doc_names)

        while queue:
            doc = queue.popleft()
            if doc in result:
                continue

            result.add(doc)

            if doc in self.nodes:
                for dep in self.nodes[doc].depends_on:
                    if dep not in result:
                        queue.append(dep)

        return result

    def get_dependencies(self, doc_name: str) -> List[str]:
        """
        Get direct dependencies for a document

        Args:
            doc_name: Document name

        Returns:
            List of document names this document depends on
        """
        if doc_name in self.nodes:
            return self.nodes[doc_name].depends_on.copy()
        return []

    def get_dependents(self, doc_name: str) -> List[str]:
        """
        Get documents that depend on this document

        Args:
            doc_name: Document name

        Returns:
            List of document names that depend on this document
        """
        if doc_name in self.nodes:
            return self.nodes[doc_name].dependents.copy()
        return []

    def validate_selection(self, selected_docs: List[str]) -> Dict:
        """
        Validate document selection for completeness

        Checks for:
        - Missing required dependencies
        - Circular dependencies
        - Documents without agents

        Args:
            selected_docs: List of document names to validate

        Returns:
            {
                "valid": bool,
                "warnings": List[str],
                "missing_dependencies": List[str],
                "has_circular_dependency": bool
            }
        """
        result = {
            "valid": True,
            "warnings": [],
            "missing_dependencies": [],
            "has_circular_dependency": False
        }

        # Check for missing dependencies
        validation_rules = self.config.get('validation_rules', {})
        warn_if_missing = validation_rules.get('warn_if_missing', {})

        for doc in selected_docs:
            if doc in warn_if_missing:
                required_deps = warn_if_missing[doc]
                missing = [dep for dep in required_deps if dep not in selected_docs]
                if missing:
                    result["warnings"].append(
                        f"{doc} is selected but these related documents are missing: {', '.join(missing)}"
                    )
                    result["missing_dependencies"].extend(missing)

        # Check for circular dependencies
        try:
            self.get_generation_order(selected_docs)
        except ValueError as e:
            if "Circular dependency" in str(e):
                result["valid"] = False
                result["has_circular_dependency"] = True
                result["warnings"].append(str(e))

        # Remove duplicates from missing_dependencies
        result["missing_dependencies"] = list(set(result["missing_dependencies"]))

        return result

    def get_cross_reference_patterns(self) -> Dict:
        """
        Get predefined cross-reference patterns

        Returns:
            Dictionary of cross-reference patterns for agents to use
        """
        return self.config.get('cross_reference_patterns', {})

    def suggest_additional_documents(self, selected_docs: List[str]) -> List[Tuple[str, str]]:
        """
        Suggest additional documents that would complement the selection

        Args:
            selected_docs: Currently selected documents

        Returns:
            List of (doc_name, reason) tuples
        """
        suggestions = []
        selected_set = set(selected_docs)

        # Check validation rules
        validation_rules = self.config.get('validation_rules', {})
        warn_if_missing = validation_rules.get('warn_if_missing', {})

        for doc in selected_docs:
            if doc in warn_if_missing:
                for suggested_doc in warn_if_missing[doc]:
                    if suggested_doc not in selected_set:
                        reason = f"Often used with {doc} for complete package"
                        if (suggested_doc, reason) not in suggestions:
                            suggestions.append((suggested_doc, reason))

        # Check dependents (documents that depend on selected docs)
        for doc in selected_docs:
            dependents = self.get_dependents(doc)
            for dependent in dependents:
                if dependent not in selected_set:
                    reason = f"Depends on {doc} and would benefit from its content"
                    if (dependent, reason) not in suggestions:
                        suggestions.append((dependent, reason))

        return suggestions[:5]  # Limit to top 5 suggestions

    def get_document_info(self, doc_name: str) -> Optional[Dict]:
        """
        Get detailed information about a document

        Args:
            doc_name: Document name

        Returns:
            Dictionary with document information or None if not found
        """
        if doc_name not in self.nodes:
            return None

        node = self.nodes[doc_name]
        return {
            "name": node.name,
            "priority": node.priority,
            "description": node.description,
            "depends_on": node.depends_on,
            "dependents": node.dependents,
            "references": node.references
        }


# Singleton pattern for global access
_dependency_graph_instance = None

def get_dependency_graph(config_path: Optional[str] = None) -> DependencyGraph:
    """
    Get or create the singleton DependencyGraph instance

    Args:
        config_path: Optional custom config path

    Returns:
        DependencyGraph instance
    """
    global _dependency_graph_instance

    if _dependency_graph_instance is None or config_path is not None:
        _dependency_graph_instance = DependencyGraph(config_path)

    return _dependency_graph_instance
