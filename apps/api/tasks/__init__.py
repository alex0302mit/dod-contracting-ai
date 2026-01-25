"""
Celery Tasks Package

Contains background task definitions for:
- Document generation (single and batch)
- Quality analysis
- Export operations

Tasks are automatically discovered and registered with Celery.
"""

from backend.tasks.base import ProgressTask
from backend.tasks.generation_tasks import (
    generate_single_document,
    generate_batch_documents,
    run_quality_analysis,
)

__all__ = [
    "ProgressTask",
    "generate_single_document",
    "generate_batch_documents",
    "run_quality_analysis",
]
