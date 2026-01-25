"""
Redis Cache Service Module

Provides a caching layer for expensive operations like RAG searches,
embeddings, and analytics queries. Uses Redis with connection pooling
for high performance.

Features:
- Connection pooling for efficient resource use
- Automatic JSON serialization/deserialization
- Key namespacing for organized cache structure
- Graceful fallback when Redis is unavailable
- TTL-based expiration
"""

import os
import json
import hashlib
from typing import Optional, Any, List, Dict, Callable
from datetime import timedelta
import asyncio
from functools import wraps

try:
    import redis
    from redis import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None


# Cache key namespace prefixes
class CacheNamespace:
    """Namespace prefixes for organized cache keys"""
    RAG_SEARCH = "dod:cache:rag:search"
    RAG_EMBEDDINGS = "dod:cache:rag:embeddings"
    RAG_DOCS_LIST = "dod:cache:rag:docs:list"
    ANALYTICS_ADMIN = "dod:cache:analytics:admin"
    ANALYTICS_USER = "dod:cache:analytics:user"
    GENERATION_HASH = "dod:cache:generation:document"
    PUBSUB_CHANNEL = "dod:cache:invalidation"
    WS_CHANNEL = "dod:ws"


# Default TTL values (in seconds)
class CacheTTL:
    """Default TTL values for different cache types"""
    RAG_SEARCH = 30 * 60          # 30 minutes
    RAG_EMBEDDINGS = 24 * 60 * 60  # 24 hours
    RAG_DOCS_LIST = 60 * 60        # 1 hour
    ANALYTICS_ADMIN = 5 * 60       # 5 minutes
    ANALYTICS_USER = 15 * 60       # 15 minutes
    GENERATION_RESULT = 7 * 24 * 60 * 60  # 7 days


class CacheService:
    """
    Redis cache service with connection pooling and graceful fallback.

    Provides caching for:
    - RAG search results
    - Embedding vectors
    - Document lists
    - Analytics queries
    - Generation results (for incremental generation)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enabled: bool = True,
        max_connections: int = 10
    ):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (defaults to env var)
            enabled: Whether caching is enabled
            max_connections: Maximum connections in the pool
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self.max_connections = max_connections

        if self.enabled:
            self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Redis connection pool."""
        if not REDIS_AVAILABLE:
            print("⚠️  Redis package not installed. Caching disabled.")
            self.enabled = False
            return

        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()
            self._connected = True
            print(f"✅ Redis cache connected: {self.redis_url}")

        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}. Caching disabled.")
            self._connected = False
            self.enabled = False

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected and self.enabled

    def _compute_hash(self, *args) -> str:
        """Compute a hash from arguments for cache keys."""
        key_data = json.dumps(args, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/error
        """
        if not self.is_connected:
            return None

        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error for {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "dod:cache:rag:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_connected:
            return 0

        try:
            keys = list(self._client.scan_iter(match=pattern))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def publish(self, channel: str, message: Dict) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name
            message: Message dictionary

        Returns:
            True if published, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            self._client.publish(channel, json.dumps(message, default=str))
            return True
        except Exception as e:
            print(f"Cache publish error: {e}")
            return False

    # ========================================
    # RAG Search Caching
    # ========================================

    def get_rag_search_key(
        self,
        query: str,
        project_id: Optional[str] = None,
        phase: Optional[str] = None,
        k: int = 5
    ) -> str:
        """Generate cache key for RAG search."""
        query_hash = self._compute_hash(query, project_id, phase, k)
        return f"{CacheNamespace.RAG_SEARCH}:{query_hash}"

    def get_rag_search(
        self,
        query: str,
        project_id: Optional[str] = None,
        phase: Optional[str] = None,
        k: int = 5
    ) -> Optional[List[Dict]]:
        """Get cached RAG search results."""
        key = self.get_rag_search_key(query, project_id, phase, k)
        return self.get(key)

    def set_rag_search(
        self,
        query: str,
        results: List[Dict],
        project_id: Optional[str] = None,
        phase: Optional[str] = None,
        k: int = 5
    ) -> bool:
        """Cache RAG search results."""
        key = self.get_rag_search_key(query, project_id, phase, k)
        return self.set(key, results, ttl=CacheTTL.RAG_SEARCH)

    # ========================================
    # Embeddings Caching
    # ========================================

    def get_embeddings_key(self, text: str) -> str:
        """Generate cache key for embeddings."""
        text_hash = self._compute_hash(text)
        return f"{CacheNamespace.RAG_EMBEDDINGS}:{text_hash}"

    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """Get cached embeddings for text."""
        key = self.get_embeddings_key(text)
        return self.get(key)

    def set_embeddings(self, text: str, embeddings: List[float]) -> bool:
        """Cache embeddings for text."""
        key = self.get_embeddings_key(text)
        return self.set(key, embeddings, ttl=CacheTTL.RAG_EMBEDDINGS)

    def get_batch_embeddings(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """
        Get cached embeddings for multiple texts.

        Returns dict mapping text -> embeddings (None if not cached).
        """
        if not self.is_connected:
            return {text: None for text in texts}

        results = {}
        try:
            pipe = self._client.pipeline()
            keys = [self.get_embeddings_key(text) for text in texts]

            for key in keys:
                pipe.get(key)

            values = pipe.execute()

            for text, value in zip(texts, values):
                if value:
                    results[text] = json.loads(value)
                else:
                    results[text] = None

        except Exception as e:
            print(f"Batch embeddings cache error: {e}")
            results = {text: None for text in texts}

        return results

    def set_batch_embeddings(self, embeddings_map: Dict[str, List[float]]) -> bool:
        """
        Cache multiple embeddings at once.

        Args:
            embeddings_map: Dict mapping text -> embeddings
        """
        if not self.is_connected:
            return False

        try:
            pipe = self._client.pipeline()

            for text, embeddings in embeddings_map.items():
                key = self.get_embeddings_key(text)
                pipe.setex(key, CacheTTL.RAG_EMBEDDINGS, json.dumps(embeddings))

            pipe.execute()
            return True

        except Exception as e:
            print(f"Batch embeddings cache set error: {e}")
            return False

    # ========================================
    # Document List Caching
    # ========================================

    def get_docs_list_key(self, project_id: Optional[str] = None) -> str:
        """Generate cache key for document list."""
        return f"{CacheNamespace.RAG_DOCS_LIST}:{project_id or 'all'}"

    def get_docs_list(self, project_id: Optional[str] = None) -> Optional[List[Dict]]:
        """Get cached document list."""
        key = self.get_docs_list_key(project_id)
        return self.get(key)

    def set_docs_list(
        self,
        docs: List[Dict],
        project_id: Optional[str] = None
    ) -> bool:
        """Cache document list."""
        key = self.get_docs_list_key(project_id)
        return self.set(key, docs, ttl=CacheTTL.RAG_DOCS_LIST)

    # ========================================
    # Analytics Caching
    # ========================================

    def get_admin_analytics_key(self, days: int) -> str:
        """Generate cache key for admin analytics."""
        return f"{CacheNamespace.ANALYTICS_ADMIN}:{days}"

    def get_admin_analytics(self, days: int) -> Optional[Dict]:
        """Get cached admin analytics."""
        key = self.get_admin_analytics_key(days)
        return self.get(key)

    def set_admin_analytics(self, days: int, analytics: Dict) -> bool:
        """Cache admin analytics."""
        key = self.get_admin_analytics_key(days)
        return self.set(key, analytics, ttl=CacheTTL.ANALYTICS_ADMIN)

    def get_user_analytics_key(self, user_id: str) -> str:
        """Generate cache key for user analytics."""
        return f"{CacheNamespace.ANALYTICS_USER}:{user_id}"

    def get_user_analytics(self, user_id: str) -> Optional[Dict]:
        """Get cached user analytics."""
        key = self.get_user_analytics_key(user_id)
        return self.get(key)

    def set_user_analytics(self, user_id: str, analytics: Dict) -> bool:
        """Cache user analytics."""
        key = self.get_user_analytics_key(user_id)
        return self.set(key, analytics, ttl=CacheTTL.ANALYTICS_USER)

    # ========================================
    # Generation Hash Caching (for incremental generation)
    # ========================================

    def get_generation_hash_key(self, document_id: str) -> str:
        """Generate cache key for generation input hash."""
        return f"{CacheNamespace.GENERATION_HASH}:{document_id}:input_hash"

    def get_generation_result_key(self, document_id: str) -> str:
        """Generate cache key for generation result."""
        return f"{CacheNamespace.GENERATION_HASH}:{document_id}:result"

    def get_generation_cache(self, document_id: str) -> Optional[Dict]:
        """
        Get cached generation result and hash.

        Returns dict with 'input_hash' and 'result' if cached.
        """
        if not self.is_connected:
            return None

        try:
            pipe = self._client.pipeline()
            pipe.get(self.get_generation_hash_key(document_id))
            pipe.get(self.get_generation_result_key(document_id))

            hash_val, result_val = pipe.execute()

            if hash_val and result_val:
                return {
                    "input_hash": hash_val,
                    "result": json.loads(result_val)
                }
            return None

        except Exception as e:
            print(f"Generation cache get error: {e}")
            return None

    def set_generation_cache(
        self,
        document_id: str,
        input_hash: str,
        result: Dict
    ) -> bool:
        """
        Cache generation result with its input hash.

        Args:
            document_id: Document ID
            input_hash: Hash of generation inputs
            result: Generation result to cache
        """
        if not self.is_connected:
            return False

        try:
            pipe = self._client.pipeline()
            pipe.setex(
                self.get_generation_hash_key(document_id),
                CacheTTL.GENERATION_RESULT,
                input_hash
            )
            pipe.setex(
                self.get_generation_result_key(document_id),
                CacheTTL.GENERATION_RESULT,
                json.dumps(result, default=str)
            )
            pipe.execute()
            return True

        except Exception as e:
            print(f"Generation cache set error: {e}")
            return False

    # ========================================
    # WebSocket Pub/Sub (for cross-process notifications)
    # ========================================

    def publish_ws_message(self, project_id: str, message: Dict) -> bool:
        """
        Publish a WebSocket message via Redis pub/sub.

        This enables Celery workers to send WebSocket updates
        through the main FastAPI process.

        Args:
            project_id: Project ID for the message
            message: WebSocket message payload
        """
        channel = f"{CacheNamespace.WS_CHANNEL}:{project_id}"
        return self.publish(channel, message)

    def get_ws_channel(self, project_id: str) -> str:
        """Get WebSocket pub/sub channel name for a project."""
        return f"{CacheNamespace.WS_CHANNEL}:{project_id}"

    # ========================================
    # Cache Statistics
    # ========================================

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats and connection info
        """
        if not self.is_connected:
            return {
                "enabled": self.enabled,
                "connected": False,
                "message": "Redis not connected"
            }

        try:
            info = self._client.info(section="memory")
            keyspace = self._client.info(section="keyspace")

            # Count keys by namespace
            namespace_counts = {}
            for ns_name, ns_prefix in vars(CacheNamespace).items():
                if not ns_name.startswith("_"):
                    count = len(list(self._client.scan_iter(match=f"{ns_prefix}*", count=100)))
                    namespace_counts[ns_name.lower()] = count

            return {
                "enabled": True,
                "connected": True,
                "redis_url": self.redis_url,
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "total_keys": sum(
                    v.get("keys", 0) if isinstance(v, dict) else 0
                    for v in keyspace.values()
                ),
                "namespace_counts": namespace_counts
            }

        except Exception as e:
            return {
                "enabled": self.enabled,
                "connected": self._connected,
                "error": str(e)
            }

    def close(self) -> None:
        """Close Redis connections."""
        if self._pool:
            self._pool.disconnect()
            self._connected = False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get or create the cache service singleton.

    Returns:
        CacheService instance
    """
    global _cache_service

    if _cache_service is None:
        enabled = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
        _cache_service = CacheService(enabled=enabled)

    return _cache_service


def initialize_cache_service(
    redis_url: Optional[str] = None,
    enabled: bool = True
) -> CacheService:
    """
    Explicitly initialize the cache service.

    Called by FastAPI on startup.

    Args:
        redis_url: Redis connection URL
        enabled: Whether caching is enabled

    Returns:
        Initialized CacheService instance
    """
    global _cache_service
    _cache_service = CacheService(redis_url=redis_url, enabled=enabled)
    return _cache_service


# Decorator for caching function results
def cached(
    namespace: str,
    ttl: int,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results.

    Args:
        namespace: Cache key namespace
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from args

    Example:
        @cached("my_func", 300)
        def expensive_operation(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()

            if not cache.is_connected:
                return func(*args, **kwargs)

            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = cache._compute_hash(args, kwargs)

            key = f"{namespace}:{key_suffix}"

            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)

            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service()

            if not cache.is_connected:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = cache._compute_hash(args, kwargs)

            key = f"{namespace}:{key_suffix}"

            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
