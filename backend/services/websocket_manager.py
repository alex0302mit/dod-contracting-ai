"""
WebSocket connection manager for real-time updates
"""
from fastapi import WebSocket
from typing import Dict, List
import json


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Dictionary of project_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = []

        self.active_connections[project_id].append(websocket)
        print(f"✅ WebSocket connected for project {project_id}")

    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

        print(f"❌ WebSocket disconnected for project {project_id}")

    async def send_message(self, project_id: str, message: dict):
        """Send a message to all connections for a specific project"""
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        for project_id in self.active_connections:
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


from datetime import datetime

# Global instance
ws_manager = WebSocketManager()
