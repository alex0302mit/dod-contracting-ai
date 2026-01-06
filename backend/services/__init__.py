"""
Backend Services

Core backend services for the DoD Procurement system:
- Document generation service
- WebSocket manager for real-time updates
"""

from backend.services.document_generator import DocumentGenerator, get_document_generator
from backend.services.websocket_manager import WebSocketManager, ws_manager

__all__ = [
    'DocumentGenerator',
    'get_document_generator',
    'WebSocketManager',
    'ws_manager',
]

