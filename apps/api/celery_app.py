"""
Celery Application Configuration

Configures Celery for distributed task processing with:
- Redis as message broker
- Multiple queues for priority-based task routing
- Task result storage in Redis
- WebSocket integration for progress updates
"""

import os
from celery import Celery
from kombu import Queue, Exchange
from dotenv import load_dotenv

load_dotenv()

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Create Celery application
celery_app = Celery(
    "dod_procurement",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.generation_tasks",
    ]
)

# Define exchanges
default_exchange = Exchange("default", type="direct")
generation_exchange = Exchange("generation", type="direct")
quality_exchange = Exchange("quality", type="direct")

# Queue configuration with priorities
celery_app.conf.task_queues = (
    # High priority queue for single document generation
    Queue(
        "dod.generation.high",
        exchange=generation_exchange,
        routing_key="generation.high",
        queue_arguments={"x-max-priority": 10}
    ),
    # Batch generation queue (lower priority, more resource intensive)
    Queue(
        "dod.generation.batch",
        exchange=generation_exchange,
        routing_key="generation.batch",
        queue_arguments={"x-max-priority": 5}
    ),
    # Quality analysis queue
    Queue(
        "dod.quality",
        exchange=quality_exchange,
        routing_key="quality",
        queue_arguments={"x-max-priority": 7}
    ),
    # Default queue
    Queue(
        "celery",
        exchange=default_exchange,
        routing_key="celery"
    ),
)

# Task routing - automatically route tasks to appropriate queues
celery_app.conf.task_routes = {
    "backend.tasks.generation_tasks.generate_single_document": {
        "queue": "dod.generation.high",
        "routing_key": "generation.high"
    },
    "backend.tasks.generation_tasks.generate_batch_documents": {
        "queue": "dod.generation.batch",
        "routing_key": "generation.batch"
    },
    "backend.tasks.generation_tasks.run_quality_analysis": {
        "queue": "dod.quality",
        "routing_key": "quality"
    },
}

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=86400,  # 24 hours
    result_extended=True,  # Store task args and kwargs

    # Worker settings
    worker_prefetch_multiplier=1,  # Prevent worker from grabbing too many tasks
    worker_concurrency=4,  # Default worker concurrency

    # Task settings
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
    task_track_started=True,  # Track when tasks start

    # Rate limiting
    task_default_rate_limit="10/m",  # Default: 10 tasks per minute

    # Retry settings
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit

    # Beat scheduler (for periodic tasks if needed)
    beat_schedule={},
)


# Cache for worker availability check to avoid repeated Redis calls
# Format: (timestamp, is_available)
_worker_availability_cache = {"last_check": 0, "available": False}

def is_celery_enabled() -> bool:
    """
    Check if Celery tasks should be used.
    
    Returns True only if:
    1. USE_CELERY_TASKS env var is 'true' (default: 'true')
    2. At least one Celery worker is actually running and responding
    
    This prevents tasks from being queued to Celery when no workers
    are available, falling back to asyncio background tasks instead.
    """
    import time
    
    # First check: Is Celery enabled via environment?
    env_enabled = os.getenv("USE_CELERY_TASKS", "true").lower() == "true"
    if not env_enabled:
        return False
    
    # Cache worker availability for 30 seconds to avoid repeated Redis calls
    # This improves performance while still detecting worker availability changes
    current_time = time.time()
    cache_ttl = 30  # seconds
    
    if current_time - _worker_availability_cache["last_check"] < cache_ttl:
        return _worker_availability_cache["available"]
    
    # Second check: Are workers actually running?
    try:
        # Quick ping to check if any workers are responding
        # Use a short timeout to avoid blocking the request
        i = celery_app.control.inspect(timeout=1.0)
        ping_result = i.ping()
        
        # Workers are available if at least one responds to ping
        workers_available = bool(ping_result and len(ping_result) > 0)
        
        # Update cache
        _worker_availability_cache["last_check"] = current_time
        _worker_availability_cache["available"] = workers_available
        
        if not workers_available:
            print("⚠️  Celery enabled but no workers responding - using asyncio fallback")
        
        return workers_available
        
    except Exception as e:
        # If we can't connect to Redis or inspect workers, fall back to asyncio
        print(f"⚠️  Celery worker check failed ({e}) - using asyncio fallback")
        _worker_availability_cache["last_check"] = current_time
        _worker_availability_cache["available"] = False
        return False


# Health check function
def check_celery_health() -> dict:
    """
    Check Celery worker health.

    Returns:
        Dict with status and worker info
    """
    try:
        # Ping workers
        i = celery_app.control.inspect()
        ping = i.ping()

        if ping:
            workers = list(ping.keys())
            active = i.active()
            reserved = i.reserved()

            return {
                "status": "healthy",
                "workers": workers,
                "worker_count": len(workers),
                "active_tasks": sum(len(v) for v in (active or {}).values()),
                "reserved_tasks": sum(len(v) for v in (reserved or {}).values()),
            }
        else:
            return {
                "status": "no_workers",
                "message": "No Celery workers responding"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ========================================
# Worker Initialization
# ========================================

from celery.signals import worker_process_init

@worker_process_init.connect
def init_worker_process(**kwargs):
    """
    Initialize resources when a Celery worker PROCESS starts.

    Using worker_process_init (not worker_init) ensures this runs
    AFTER forking, which is required for PyTorch/SentenceTransformer
    models that are not fork-safe.

    For prefork pool: runs in each forked worker process
    For solo/threads pool: runs in the main worker process
    """
    import os
    print("🔧 Initializing Celery worker process resources...")

    try:
        # Preload cache service (fork-safe)
        from backend.services.cache_service import get_cache_service
        cache = get_cache_service()
        print(f"✅ Cache service: {'connected' if cache.is_connected else 'not connected'}")
    except Exception as e:
        print(f"⚠️  Cache service preload failed: {e}")

    try:
        # Preload RAG service (loads SentenceTransformer model + FAISS index)
        # This must happen AFTER fork to avoid SIGSEGV on macOS
        if os.environ.get("ANTHROPIC_API_KEY"):
            from backend.services.rag_service import get_rag_service
            rag = get_rag_service()
            print(f"✅ RAG service preloaded: {len(rag.vector_store.chunks)} chunks")
        else:
            print("⚠️  ANTHROPIC_API_KEY not set, skipping RAG preload")
    except Exception as e:
        print(f"⚠️  RAG service preload failed (will retry on first use): {e}")

    print("✅ Worker process initialization complete")


if __name__ == "__main__":
    # Allow running celery directly: python -m backend.celery_app worker
    celery_app.start()
