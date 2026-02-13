"""
Document Generator Service

Bridges the ProjectDocument model with the GenerationCoordinator to enable
AI-powered document generation from the document checklist.

Key responsibilities:
1. Map document names to appropriate agent types
2. Retrieve project context (other approved docs, assumptions)
3. Check and enforce document dependencies
4. Call GenerationCoordinator for content generation
5. Save results to ProjectDocument.generated_content
6. Record document lineage for explainability

Dependencies:
- backend.models.document: ProjectDocument, GenerationStatus
- backend.models.lineage: DocumentLineage, InfluenceType
- backend.services.generation_coordinator: GenerationCoordinator, GenerationTask
- backend.services.rag_service: RAGService for chunk tracking
"""

import os
import yaml
import asyncio
import uuid as uuid_lib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.document import ProjectDocument, GenerationStatus
from backend.models.procurement import ProcurementProject, PhaseName
from backend.services.generation_coordinator import GenerationCoordinator, GenerationTask, get_generation_coordinator


# Document dependencies - documents that must exist/be approved before generating others
# Loaded from phase_definitions.yaml
DOCUMENT_DEPENDENCIES: Dict[str, List[str]] = {}


def load_document_dependencies() -> Dict[str, List[str]]:
    """Load document dependencies from phase_definitions.yaml"""
    global DOCUMENT_DEPENDENCIES
    
    if DOCUMENT_DEPENDENCIES:
        return DOCUMENT_DEPENDENCIES
    
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "phase_definitions.yaml"
        )
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Collect dependencies from all phases
        for phase_name, phase_data in config.get('phases', {}).items():
            deps = phase_data.get('dependencies', {})
            for doc, doc_deps in deps.items():
                DOCUMENT_DEPENDENCIES[doc] = doc_deps
        
        return DOCUMENT_DEPENDENCIES
    except Exception as e:
        print(f"Warning: Could not load document dependencies: {e}")
        return {}


class DocumentGenerator:
    """
    Service for generating AI content for ProjectDocument records.
    
    Integrates with the existing GenerationCoordinator while providing
    document-specific context gathering and dependency checking.
    """
    
    def __init__(self, use_specialized_agents: bool = True):
        """
        Initialize the document generator.
        
        Args:
            use_specialized_agents: Whether to use specialized agents (vs generic)
        """
        self.use_specialized_agents = use_specialized_agents
        self.coordinator = get_generation_coordinator(use_specialized_agents=use_specialized_agents)
        self.dependencies = load_document_dependencies()
    
    def check_dependencies(
        self,
        db: Session,
        project_id: str,
        document_name: str
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check if all dependencies for a document are met.
        
        Args:
            db: Database session
            project_id: Project UUID
            document_name: Name of document to check dependencies for
            
        Returns:
            Tuple of (dependencies_met, missing_deps, available_deps)
        """
        deps = self.dependencies.get(document_name, [])
        
        if not deps:
            return True, [], []
        
        # Get existing documents for this project
        existing_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()
        
        existing_doc_names = {doc.document_name: doc for doc in existing_docs}
        
        missing = []
        available = []
        
        for dep_name in deps:
            dep_doc = existing_doc_names.get(dep_name)
            if dep_doc:
                # Check if dependency has content (either uploaded, approved, or generated)
                if dep_doc.status in ['approved', 'uploaded'] or dep_doc.generated_content:
                    available.append(dep_name)
                else:
                    missing.append(dep_name)
            else:
                missing.append(dep_name)
        
        return len(missing) == 0, missing, available
    
    def get_project_context(
        self,
        db: Session,
        project_id: str,
        document_name: str
    ) -> Dict:
        """
        Gather context from the project for document generation.
        
        Args:
            db: Database session
            project_id: Project UUID
            document_name: Name of document being generated
            
        Returns:
            Dictionary with project context for generation
        """
        # Get project details
        project = db.query(ProcurementProject).filter(
            ProcurementProject.id == project_id
        ).first()
        
        if not project:
            return {}
        
        # Get existing documents with content
        existing_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_name != document_name
        ).all()

        # Collect generated/approved content from dependencies
        dependency_content = {}
        deps = self.dependencies.get(document_name, [])
        
        for doc in existing_docs:
            if doc.document_name in deps:
                if doc.generated_content:
                    dependency_content[doc.document_name] = doc.generated_content

        # Build and return context dictionary
        return {
            "project_name": project.name,
            "project_description": project.description,
            "project_type": project.project_type.value if project.project_type else None,
            "current_phase": project.current_phase.value if hasattr(project, 'current_phase') and project.current_phase else None,
            # Use estimated_value which is the actual field on ProcurementProject model
            "estimated_value": str(project.estimated_value) if project.estimated_value else None,
            "dependency_documents": dependency_content,
            "existing_documents": [
                {
                    "name": doc.document_name,
                    "status": doc.status.value,
                    "has_content": bool(doc.generated_content)
                }
                for doc in existing_docs
            ]
        }
    
    async def generate_document(
        self,
        db: Session,
        document: ProjectDocument,
        assumptions: List[Dict[str, str]],
        additional_context: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        force_regenerate: bool = False,
        external_task_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Generate AI content for a single document.

        Features incremental generation - if inputs haven't changed,
        returns cached result instead of regenerating.

        Args:
            db: Database session
            document: ProjectDocument to generate content for
            assumptions: List of assumption dictionaries
            additional_context: Optional additional context from user
            progress_callback: Optional callback for progress updates
            force_regenerate: Skip cache check and always regenerate

        Returns:
            Tuple of (success, content_or_error, metadata)
        """
        try:
            # Check dependencies - ensures required documents are generated first
            deps_met, missing_deps, available_deps = self.check_dependencies(
                db, str(document.project_id), document.document_name
            )

            # Incremental generation: check if inputs have changed
            if not force_regenerate:
                cached_result = await self._check_incremental_cache(
                    db=db,
                    document=document,
                    assumptions=assumptions,
                    additional_context=additional_context,
                    progress_callback=progress_callback
                )
                if cached_result is not None:
                    return cached_result
            
            if not deps_met:
                return False, f"Missing dependencies: {', '.join(missing_deps)}", None
            
            # Get project context including name, description, type, and dependency content
            project_context = self.get_project_context(
                db, str(document.project_id), document.document_name
            )

            # Build generation assumptions including project context
            generation_assumptions = assumptions.copy()
            
            # Add project context as assumptions
            if project_context.get("project_name"):
                generation_assumptions.append({
                    "id": "project_name",
                    "text": f"Project: {project_context['project_name']}",
                    "source": "Project Settings"
                })
            
            if project_context.get("project_description"):
                generation_assumptions.append({
                    "id": "project_desc",
                    "text": project_context['project_description'],
                    "source": "Project Description"
                })
            
            if additional_context:
                generation_assumptions.append({
                    "id": "user_context",
                    "text": additional_context,
                    "source": "User Input"
                })
            
            # Add dependency content as assumptions
            for dep_name, dep_content in project_context.get("dependency_documents", {}).items():
                # Truncate very long content to avoid token limits
                content_preview = dep_content[:2000] + "..." if len(dep_content) > 2000 else dep_content
                generation_assumptions.append({
                    "id": f"dep_{dep_name.lower().replace(' ', '_')}",
                    "text": f"From {dep_name}: {content_preview}",
                    "source": dep_name
                })
            
            # Create generation task with unique ID
            # Use external_task_id if provided (e.g., from Celery task or API endpoint)
            # This ensures consistent task ID tracking across the system
            task_id = external_task_id or f"doc_{document.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            task = GenerationTask(
                task_id=task_id,
                document_names=[document.document_name],
                assumptions=generation_assumptions,
                linked_assumptions={document.document_name: [a.get("id", "") for a in generation_assumptions]},
                document_ids={document.document_name: str(document.id)}
            )

            # Update document status to show generation in progress
            # Only update task_id if we don't have an external one (to avoid overwriting)
            document.generation_status = GenerationStatus.GENERATING
            if not external_task_id:
                document.generation_task_id = task_id
            db.commit()
            
            # Run generation via the coordinator (handles agent routing and AI calls)
            completed_task = await self.coordinator.generate_documents(
                task=task,
                progress_callback=progress_callback
            )
            
            if completed_task.status == "completed" and completed_task.sections:
                # Get the generated content from sections dictionary
                content = completed_task.sections.get(
                    document.document_name,
                    list(completed_task.sections.values())[0] if completed_task.sections else ""
                )
                
                # Get quality score if available from quality analysis
                quality_score = None
                if completed_task.quality_analysis:
                    doc_quality = completed_task.quality_analysis.get(document.document_name, {})
                    quality_score = doc_quality.get("score", doc_quality.get("overall_score"))
                
                # Return metadata for frontend display
                metadata = {
                    "agent_metadata": completed_task.agent_metadata,
                    "citations": completed_task.citations,
                    "quality_analysis": completed_task.quality_analysis,
                    "phase_info": completed_task.phase_info
                }
                
                # Record lineage for explainability
                # Track which sources influenced this AI-generated document
                await self._record_generation_lineage(
                    db=db,
                    document=document,
                    task=completed_task,
                    project_context=project_context
                )

                # Store result in incremental generation cache
                await self._store_incremental_result(
                    document=document,
                    assumptions=assumptions,
                    additional_context=additional_context,
                    content=content,
                    metadata=metadata,
                    project_context=project_context
                )

                return True, content, metadata
            else:
                error_msg = completed_task.errors[0] if completed_task.errors else "Generation failed - no sections returned"
                return False, error_msg, None

        except Exception as e:
            return False, str(e), None
    
    async def _record_generation_lineage(
        self,
        db: Session,
        document: ProjectDocument,
        task: GenerationTask,
        project_context: Dict
    ) -> None:
        """
        Record lineage relationships after successful AI generation.
        
        This creates DocumentLineage records linking the generated document
        to its source documents (dependencies, RAG chunks, etc.) for:
        - Explainability: Users can see what influenced AI decisions
        - Auditability: Required for DoD/FAR compliance
        - Traceability: Track document evolution
        
        Args:
            db: Database session
            document: The generated ProjectDocument
            task: Completed GenerationTask with metadata
            project_context: Context used during generation
        """
        try:
            from backend.models.lineage import DocumentLineage, InfluenceType
            
            lineage_records = []
            
            # 1. Record dependency document lineage
            # These are other project documents used as context
            for dep_name, dep_content in project_context.get("dependency_documents", {}).items():
                # Find the dependency document in the database
                dep_doc = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == document.project_id,
                    ProjectDocument.document_name == dep_name
                ).first()
                
                if dep_doc:
                    # Calculate relevance based on content usage
                    # Higher score if dependency was heavily referenced
                    content_length = len(dep_content) if dep_content else 0
                    relevance = min(1.0, content_length / 5000) if content_length > 0 else 0.3
                    
                    lineage = DocumentLineage(
                        id=uuid_lib.uuid4(),
                        source_document_id=dep_doc.id,
                        derived_document_id=document.id,
                        influence_type=InfluenceType.DATA_SOURCE,
                        relevance_score=relevance,
                        chunk_ids_used=[],  # Dependency docs aren't chunked
                        chunks_used_count=0,
                        context=f"Used as dependency: {dep_name}"
                    )
                    lineage_records.append(lineage)
            
            # 2. Record RAG chunk lineage if available
            # This tracks which uploaded knowledge docs were retrieved
            if hasattr(task, 'rag_sources') and task.rag_sources:
                # Group chunks by source document
                sources_map: Dict[str, Dict] = {}
                
                for source in task.rag_sources:
                    source_file = source.get('source_document') or source.get('source')
                    if source_file:
                        if source_file not in sources_map:
                            sources_map[source_file] = {
                                'chunk_ids': [],
                                'total_score': 0.0,
                                'count': 0
                            }
                        
                        chunk_id = source.get('chunk_id')
                        if chunk_id:
                            sources_map[source_file]['chunk_ids'].append(chunk_id)
                        
                        score = source.get('score', source.get('relevance_score', 0.5))
                        sources_map[source_file]['total_score'] += score
                        sources_map[source_file]['count'] += 1
                
                # Create lineage records for each source
                for source_file, data in sources_map.items():
                    avg_score = data['total_score'] / data['count'] if data['count'] > 0 else 0.5
                    
                    lineage = DocumentLineage(
                        id=uuid_lib.uuid4(),
                        source_document_id=None,  # RAG docs may not be in project_documents
                        source_filename=source_file,
                        derived_document_id=document.id,
                        influence_type=InfluenceType.CONTEXT,
                        relevance_score=avg_score,
                        chunk_ids_used=data['chunk_ids'],
                        chunks_used_count=len(data['chunk_ids']),
                        context=f"Retrieved from RAG knowledge base"
                    )
                    lineage_records.append(lineage)
            
            # 3. Commit all lineage records
            if lineage_records:
                for record in lineage_records:
                    db.add(record)
                db.commit()
                print(f"✅ Recorded {len(lineage_records)} lineage relationships for {document.document_name}")
                
        except Exception as e:
            # Don't fail generation if lineage recording fails
            print(f"⚠️ Warning: Could not record lineage for {document.document_name}: {e}")
            import traceback
            traceback.print_exc()
    
    async def generate_batch(
        self,
        db: Session,
        project_id: str,
        document_ids: List[str],
        assumptions: List[Dict[str, str]],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Tuple[bool, str, Optional[Dict]]]:
        """
        Generate AI content for multiple documents in dependency order.
        
        Args:
            db: Database session
            project_id: Project UUID
            document_ids: List of document UUIDs to generate
            assumptions: List of assumption dictionaries
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping document_id to (success, content_or_error, metadata)
        """
        # Get documents
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.id.in_(document_ids)
        ).all()
        
        # Sort by dependencies
        sorted_docs = self._sort_by_dependencies(documents)
        
        results = {}
        
        for doc in sorted_docs:
            success, content_or_error, metadata = await self.generate_document(
                db=db,
                document=doc,
                assumptions=assumptions,
                progress_callback=progress_callback
            )
            
            results[str(doc.id)] = (success, content_or_error, metadata)
            
            if success:
                # Save generated content for downstream documents
                doc.generated_content = content_or_error
                doc.generated_at = datetime.utcnow()
                doc.generation_status = GenerationStatus.GENERATED
                if metadata and metadata.get("quality_analysis"):
                    doc_quality = metadata["quality_analysis"].get(doc.document_name, {})
                    doc.ai_quality_score = doc_quality.get("score", doc_quality.get("overall_score"))
                db.commit()
            else:
                doc.generation_status = GenerationStatus.FAILED
                db.commit()
        
        return results
    
    def _sort_by_dependencies(self, documents: List[ProjectDocument]) -> List[ProjectDocument]:
        """Sort documents by their dependencies (topological sort)."""
        doc_map = {doc.document_name: doc for doc in documents}
        result = []
        visited = set()
        
        def visit(doc_name: str):
            if doc_name in visited:
                return
            visited.add(doc_name)
            
            # Visit dependencies first
            for dep in self.dependencies.get(doc_name, []):
                if dep in doc_map:
                    visit(dep)
            
            if doc_name in doc_map:
                result.append(doc_map[doc_name])
        
        for doc in documents:
            visit(doc.document_name)
        
        return result
    
    def get_generation_estimate(self, document_name: str) -> Dict:
        """
        Get estimated generation time and info for a document.

        Args:
            document_name: Name of the document

        Returns:
            Dictionary with estimate info
        """
        # Rough estimates based on document complexity
        time_estimates = {
            "Market Research Report": 3,
            "Acquisition Plan": 4,
            "Performance Work Statement (PWS)": 4,
            "Independent Government Cost Estimate (IGCE)": 3,
            "Source Selection Plan": 3,
            "Section L - Instructions to Offerors": 3,
            "Section M - Evaluation Factors": 3,
        }

        deps = self.dependencies.get(document_name, [])

        return {
            "document_name": document_name,
            "estimated_minutes": time_estimates.get(document_name, 2),
            "dependencies": deps,
            "has_dependencies": len(deps) > 0
        }

    def sort_by_dependencies(self, document_names: List[str]) -> List[str]:
        """
        Sort document names by their dependencies (public method for Celery tasks).

        Args:
            document_names: List of document names

        Returns:
            Sorted list of document names
        """
        result = []
        visited = set()

        def visit(doc_name: str):
            if doc_name in visited:
                return
            visited.add(doc_name)

            # Visit dependencies first
            for dep in self.dependencies.get(doc_name, []):
                if dep in document_names:
                    visit(dep)

            result.append(doc_name)

        for name in document_names:
            visit(name)

        return result

    # ========================================
    # Incremental Generation Methods
    # ========================================

    async def _check_incremental_cache(
        self,
        db: Session,
        document: ProjectDocument,
        assumptions: List[Dict[str, str]],
        additional_context: Optional[str],
        progress_callback: Optional[callable]
    ) -> Optional[Tuple[bool, str, Optional[Dict]]]:
        """
        Check if we can return a cached result for incremental generation.

        Returns:
            Tuple of (success, content, metadata) if cache hit, None otherwise
        """
        try:
            from backend.services.generation_hash import (
                get_generation_hash_service,
                is_incremental_generation_enabled
            )

            if not is_incremental_generation_enabled():
                return None

            hash_service = get_generation_hash_service()

            # Get project context for hash computation
            project_context = self.get_project_context(
                db, str(document.project_id), document.document_name
            )

            # Compute dependency content hashes
            dep_names = self.dependencies.get(document.document_name, [])
            dep_hashes = hash_service.get_dependency_hashes(
                db, str(document.project_id), dep_names
            )

            # Compute current input hash
            input_hash = hash_service.compute_generation_hash(
                document_name=document.document_name,
                assumptions=assumptions,
                dependency_contents=dep_hashes,
                project_id=str(document.project_id),
                phase=project_context.get("current_phase"),
                additional_context=additional_context
            )

            # Check cache
            cached = hash_service.check_cache(str(document.id), input_hash)

            if cached:
                content = cached.get("content")
                metadata = cached.get("metadata")

                if content:
                    # Update progress to show cache hit
                    if progress_callback:
                        class CacheHitTask:
                            progress = 100
                            message = "Retrieved from cache (no changes detected)"
                        progress_callback(CacheHitTask())

                    print(f"[IncrementalGen] Returning cached result for {document.document_name}")
                    return True, content, metadata

        except ImportError:
            pass  # Generation hash service not available
        except Exception as e:
            print(f"[IncrementalGen] Cache check error: {e}")

        return None

    async def _store_incremental_result(
        self,
        document: ProjectDocument,
        assumptions: List[Dict[str, str]],
        additional_context: Optional[str],
        content: str,
        metadata: Optional[Dict],
        project_context: Dict
    ) -> None:
        """
        Store generation result for incremental generation cache.
        """
        try:
            from backend.services.generation_hash import (
                get_generation_hash_service,
                is_incremental_generation_enabled
            )

            if not is_incremental_generation_enabled():
                return

            hash_service = get_generation_hash_service()

            # Compute dependency hashes from context
            dep_hashes = {}
            for dep_name, dep_content in project_context.get("dependency_documents", {}).items():
                dep_hashes[dep_name] = hash_service.compute_content_hash(dep_content)

            # Compute input hash
            input_hash = hash_service.compute_generation_hash(
                document_name=document.document_name,
                assumptions=assumptions,
                dependency_contents=dep_hashes,
                project_id=str(document.project_id),
                phase=project_context.get("current_phase"),
                additional_context=additional_context
            )

            # Store result
            result = {
                "content": content,
                "metadata": metadata,
                "generated_at": datetime.utcnow().isoformat()
            }

            hash_service.store_result(str(document.id), input_hash, result)

        except ImportError:
            pass  # Generation hash service not available
        except Exception as e:
            print(f"[IncrementalGen] Store error: {e}")


# Singleton instance
_document_generator: Optional[DocumentGenerator] = None


def get_document_generator(use_specialized_agents: bool = True) -> DocumentGenerator:
    """Get or create the DocumentGenerator singleton."""
    global _document_generator
    if _document_generator is None:
        _document_generator = DocumentGenerator(use_specialized_agents=use_specialized_agents)
    return _document_generator
