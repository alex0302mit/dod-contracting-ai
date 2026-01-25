"""
Cache Invalidation Service Module

Handles cache invalidation events to maintain cache consistency.
Uses Redis pub/sub for cross-process invalidation notifications.

Invalidation Triggers:
- Document upload → invalidate RAG search and document list caches
- Document delete → same as above
- Vector store rebuild → invalidate all RAG caches
- User stats update → invalidate user analytics cache
- Admin analytics change → invalidate admin analytics cache
"""

import os
import json
import threading
from typing import Optional, Dict, Callable, List
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class InvalidationEvent(str, Enum):
    """Types of cache invalidation events"""
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    VECTOR_STORE_REBUILT = "vector_store_rebuilt"
    PROJECT_UPDATED = "project_updated"
    USER_STATS_CHANGED = "user_stats_changed"
    ADMIN_ANALYTICS_STALE = "admin_analytics_stale"


class CacheInvalidationService:
    """
    Manages cache invalidation through Redis pub/sub.

    This service:
    1. Publishes invalidation events when data changes
    2. Subscribes to invalidation events and clears affected caches
    3. Runs a background thread to listen for events (in subscriber mode)
    """

    CHANNEL = "dod:cache:invalidation"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize cache invalidation service.

        Args:
            redis_url: Redis connection URL
            enabled: Whether invalidation is enabled
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._handlers: Dict[InvalidationEvent, List[Callable]] = {
            event: [] for event in InvalidationEvent
        }

        if self.enabled:
            self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Redis connection for pub/sub."""
        if not REDIS_AVAILABLE:
            self.enabled = False
            return

        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            self._client.ping()
            print(f"✅ Cache invalidation service connected")
        except Exception as e:
            print(f"⚠️  Cache invalidation connection failed: {e}")
            self.enabled = False

    def register_handler(
        self,
        event: InvalidationEvent,
        handler: Callable[[Dict], None]
    ) -> None:
        """
        Register a handler for an invalidation event.

        Args:
            event: Event type to handle
            handler: Callback function that receives event data
        """
        self._handlers[event].append(handler)

    def publish_invalidation(
        self,
        event: InvalidationEvent,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Publish a cache invalidation event.

        Args:
            event: Type of invalidation event
            data: Additional event data (project_id, document_id, etc.)

        Returns:
            True if published successfully
        """
        if not self.enabled or not self._client:
            return False

        try:
            message = {
                "event": event.value,
                "data": data or {}
            }
            self._client.publish(self.CHANNEL, json.dumps(message))
            print(f"📤 Cache invalidation published: {event.value}")
            return True
        except Exception as e:
            print(f"Failed to publish invalidation: {e}")
            return False

    def invalidate_on_document_upload(
        self,
        project_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate caches after document upload.

        Clears:
        - RAG search caches (search results may change)
        - Document list caches
        """
        return self.publish_invalidation(
            InvalidationEvent.DOCUMENT_UPLOADED,
            {"project_id": project_id, "document_id": document_id}
        )

    def invalidate_on_document_delete(
        self,
        project_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate caches after document deletion.

        Clears:
        - RAG search caches
        - Document list caches
        """
        return self.publish_invalidation(
            InvalidationEvent.DOCUMENT_DELETED,
            {"project_id": project_id, "document_id": document_id}
        )

    def invalidate_on_vector_store_rebuild(self) -> bool:
        """
        Invalidate all RAG caches after vector store rebuild.

        Clears all RAG-related caches.
        """
        return self.publish_invalidation(InvalidationEvent.VECTOR_STORE_REBUILT)

    def invalidate_user_stats(self, user_id: str) -> bool:
        """
        Invalidate user analytics cache.

        Args:
            user_id: User whose stats should be invalidated
        """
        return self.publish_invalidation(
            InvalidationEvent.USER_STATS_CHANGED,
            {"user_id": user_id}
        )

    def invalidate_admin_analytics(self) -> bool:
        """Invalidate admin analytics cache."""
        return self.publish_invalidation(InvalidationEvent.ADMIN_ANALYTICS_STALE)

    def start_listener(self) -> None:
        """
        Start background thread to listen for invalidation events.

        This should be called in the main FastAPI process to receive
        invalidation messages from other processes (e.g., Celery workers).
        """
        if not self.enabled or self._running:
            return

        try:
            self._pubsub = self._client.pubsub()
            self._pubsub.subscribe(self.CHANNEL)
            self._running = True

            self._listener_thread = threading.Thread(
                target=self._listen_for_events,
                daemon=True
            )
            self._listener_thread.start()
            print("🎧 Cache invalidation listener started")

        except Exception as e:
            print(f"Failed to start invalidation listener: {e}")

    def _listen_for_events(self) -> None:
        """Background thread that listens for invalidation events."""
        while self._running:
            try:
                message = self._pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    self._handle_message(message["data"])
            except Exception as e:
                if self._running:
                    print(f"Error in invalidation listener: {e}")

    def _handle_message(self, data: str) -> None:
        """
        Handle an incoming invalidation message.

        Args:
            data: JSON-encoded message data
        """
        try:
            message = json.loads(data)
            event_name = message.get("event")
            event_data = message.get("data", {})

            # Find matching event
            try:
                event = InvalidationEvent(event_name)
            except ValueError:
                print(f"Unknown invalidation event: {event_name}")
                return

            # Call registered handlers
            for handler in self._handlers[event]:
                try:
                    handler(event_data)
                except Exception as e:
                    print(f"Error in invalidation handler: {e}")

            # Also perform default invalidation
            self._default_invalidation(event, event_data)

        except json.JSONDecodeError:
            print(f"Invalid invalidation message: {data}")

    def _default_invalidation(
        self,
        event: InvalidationEvent,
        data: Dict
    ) -> None:
        """
        Perform default cache invalidation based on event type.

        Args:
            event: Invalidation event type
            data: Event data
        """
        from backend.services.cache_service import get_cache_service, CacheNamespace

        cache = get_cache_service()
        if not cache.is_connected:
            return

        project_id = data.get("project_id")

        if event in [InvalidationEvent.DOCUMENT_UPLOADED, InvalidationEvent.DOCUMENT_DELETED]:
            # Clear RAG search caches
            cache.delete_pattern(f"{CacheNamespace.RAG_SEARCH}:*")

            # Clear document list caches
            if project_id:
                cache.delete(cache.get_docs_list_key(project_id))
            cache.delete(cache.get_docs_list_key(None))  # Clear 'all' list

            print(f"🗑️  Cleared RAG caches for event: {event.value}")

        elif event == InvalidationEvent.VECTOR_STORE_REBUILT:
            # Clear all RAG caches
            cache.delete_pattern(f"{CacheNamespace.RAG_SEARCH}:*")
            cache.delete_pattern(f"{CacheNamespace.RAG_DOCS_LIST}:*")
            cache.delete_pattern(f"{CacheNamespace.RAG_EMBEDDINGS}:*")
            print("🗑️  Cleared all RAG caches after vector store rebuild")

        elif event == InvalidationEvent.USER_STATS_CHANGED:
            user_id = data.get("user_id")
            if user_id:
                cache.delete(cache.get_user_analytics_key(user_id))
                print(f"🗑️  Cleared user stats cache for user: {user_id}")

        elif event == InvalidationEvent.ADMIN_ANALYTICS_STALE:
            # Clear all admin analytics caches
            cache.delete_pattern(f"{CacheNamespace.ANALYTICS_ADMIN}:*")
            print("🗑️  Cleared admin analytics caches")

    def stop_listener(self) -> None:
        """Stop the background listener thread."""
        self._running = False
        if self._pubsub:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except Exception:
                pass

        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)

    def close(self) -> None:
        """Close all connections."""
        self.stop_listener()
        if self._client:
            self._client.close()


# Singleton instance
_invalidation_service: Optional[CacheInvalidationService] = None


def get_invalidation_service() -> CacheInvalidationService:
    """
    Get or create the invalidation service singleton.

    Returns:
        CacheInvalidationService instance
    """
    global _invalidation_service

    if _invalidation_service is None:
        enabled = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
        _invalidation_service = CacheInvalidationService(enabled=enabled)

    return _invalidation_service


def initialize_invalidation_service(
    redis_url: Optional[str] = None,
    enabled: bool = True,
    start_listener: bool = True
) -> CacheInvalidationService:
    """
    Explicitly initialize the invalidation service.

    Called by FastAPI on startup.

    Args:
        redis_url: Redis connection URL
        enabled: Whether invalidation is enabled
        start_listener: Whether to start the background listener

    Returns:
        Initialized CacheInvalidationService instance
    """
    global _invalidation_service
    _invalidation_service = CacheInvalidationService(
        redis_url=redis_url,
        enabled=enabled
    )

    if start_listener:
        _invalidation_service.start_listener()

    return _invalidation_service
