"""
WebSocket connection manager for real-time updates

Features:
- Direct WebSocket connections for frontend clients
- Redis pub/sub integration for cross-process messaging
- Enables Celery workers to send WebSocket updates

Architecture:
    Frontend <--WebSocket--> FastAPI <--Redis PubSub--> Celery Workers
"""
import os
import json
import asyncio
import threading
from datetime import datetime
from fastapi import WebSocket
from typing import Dict, List, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates.

    Features:
    - Direct WebSocket messaging to connected clients
    - Redis pub/sub subscription for cross-process messages
    - Automatic message routing from Celery workers to WebSocket clients
    """

    def __init__(self):
        # Dictionary of project_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # Redis pub/sub components
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._subscriber_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = []

        self.active_connections[project_id].append(websocket)
        print(f"✅ WebSocket connected for project {project_id}")

        # Start Redis subscriber if not already running
        if os.getenv("USE_WEBSOCKET_PROGRESS", "true").lower() == "true":
            await self._ensure_redis_subscriber()

    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            try:
                self.active_connections[project_id].remove(websocket)
            except ValueError:
                pass  # Already removed

            # Clean up empty lists
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

        print(f"❌ WebSocket disconnected for project {project_id}")

    async def send_message(self, project_id: str, message: dict):
        """Send a message to all connections for a specific project"""
        if project_id in self.active_connections:
            # Copy list to avoid modification during iteration
            connections = self.active_connections[project_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message: {e}")
                    # Remove broken connection
                    try:
                        self.active_connections[project_id].remove(connection)
                    except (ValueError, KeyError):
                        pass

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        for project_id in list(self.active_connections.keys()):
            await self.send_message(project_id, message)

    async def send_progress_update(
        self,
        project_id: str,
        phase: str,
        message: str,
        percentage: int
    ):
        """Send a progress update for document generation"""
        await self.send_message(project_id, {
            "type": "progress",
            "phase": phase,
            "message": message,
            "percentage": percentage
        })

    async def send_generation_started(self, project_id: str, document_type: str):
        """Notify clients that document generation has started"""
        await self.send_message(project_id, {
            "type": "generation_started",
            "document_type": document_type,
            "timestamp": str(datetime.now())
        })

    async def send_generation_complete(
        self,
        project_id: str,
        document_type: str,
        document_url: str
    ):
        """Notify clients that document generation is complete"""
        await self.send_message(project_id, {
            "type": "generation_complete",
            "document_type": document_type,
            "document_url": document_url,
            "timestamp": str(datetime.now())
        })

    async def send_error(self, project_id: str, error_message: str):
        """Send an error notification"""
        await self.send_message(project_id, {
            "type": "error",
            "message": error_message,
            "timestamp": str(datetime.now())
        })

    # ========================================
    # Redis Pub/Sub Integration
    # ========================================

    async def _ensure_redis_subscriber(self):
        """Ensure Redis subscriber is running."""
        if not REDIS_AVAILABLE:
            return

        if self._running:
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self._redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True
            )
            self._redis_client.ping()

            self._running = True
            self._subscriber_task = asyncio.create_task(
                self._redis_subscriber_loop()
            )
            print("🔴 WebSocket Redis subscriber started")

        except Exception as e:
            print(f"⚠️  Failed to connect WebSocket Redis subscriber: {e}")

    async def _redis_subscriber_loop(self):
        """
        Background task that listens for Redis pub/sub messages
        and routes them to WebSocket connections.
        """
        if not self._redis_client:
            return

        try:
            self._pubsub = self._redis_client.pubsub()

            # Subscribe to all project channels using pattern
            self._pubsub.psubscribe("dod:ws:*")

            while self._running:
                try:
                    # Non-blocking get with timeout
                    message = self._pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=0.1
                    )

                    if message and message["type"] == "pmessage":
                        # Extract project_id from channel name
                        # Channel format: dod:ws:{project_id}
                        channel = message["channel"]
                        if channel.startswith("dod:ws:"):
                            project_id = channel[7:]  # Remove "dod:ws:" prefix
                            data = message["data"]

                            # Parse and forward message
                            try:
                                parsed = json.loads(data) if isinstance(data, str) else data
                                await self.send_message(project_id, parsed)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON in Redis message: {data}")

                    # Small delay to prevent busy loop
                    await asyncio.sleep(0.01)

                except Exception as e:
                    if self._running:
                        print(f"Error in Redis subscriber: {e}")
                        await asyncio.sleep(1)  # Backoff on error

        except Exception as e:
            print(f"Redis subscriber loop error: {e}")

        finally:
            self._running = False

    async def stop_redis_subscriber(self):
        """Stop the Redis subscriber."""
        self._running = False

        if self._pubsub:
            try:
                self._pubsub.punsubscribe()
                self._pubsub.close()
            except Exception:
                pass

        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass

        if self._redis_client:
            self._redis_client.close()

        print("🔴 WebSocket Redis subscriber stopped")

    def get_stats(self) -> Dict:
        """Get WebSocket connection statistics."""
        return {
            "total_connections": sum(
                len(conns) for conns in self.active_connections.values()
            ),
            "projects_connected": len(self.active_connections),
            "redis_subscriber_running": self._running,
            "project_ids": list(self.active_connections.keys())
        }


# Global instance
ws_manager = WebSocketManager()
