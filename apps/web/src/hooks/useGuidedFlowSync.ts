/**
 * Guided Flow WebSocket Sync Hook
 *
 * Real-time collaboration for guided flow.
 * Syncs field updates, locks, and collaborator presence.
 */

import { useEffect, useRef, useCallback } from 'react';
import type {
  WSMessage,
  WSFieldUpdateMessage,
  WSCollaboratorJoinedMessage,
  WSCollaboratorLeftMessage,
  WSFieldLockedMessage,
  User
} from '@/types/guidedFlow';

interface UseGuidedFlowSyncOptions {
  documentId: string;
  currentUser: User;
  enabled?: boolean;
  onFieldUpdate?: (message: WSFieldUpdateMessage) => void;
  onCollaboratorJoined?: (message: WSCollaboratorJoinedMessage) => void;
  onCollaboratorLeft?: (message: WSCollaboratorLeftMessage) => void;
  onFieldLocked?: (message: WSFieldLockedMessage) => void;
}

interface UseGuidedFlowSyncReturn {
  isConnected: boolean;
  sendFieldUpdate: (fieldId: string, value: any, status: string) => void;
  sendFieldLock: (fieldId: string) => void;
  sendFieldUnlock: (fieldId: string) => void;
  disconnect: () => void;
}

/**
 * Hook for WebSocket-based real-time collaboration
 *
 * Automatically connects on mount, disconnects on unmount.
 * Handles reconnection on connection loss.
 */
export function useGuidedFlowSync({
  documentId,
  currentUser,
  enabled = true,
  onFieldUpdate,
  onCollaboratorJoined,
  onCollaboratorLeft,
  onFieldLocked
}: UseGuidedFlowSyncOptions): UseGuidedFlowSyncReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const isConnectedRef = useRef(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  // ========================================================================
  // WebSocket Connection
  // ========================================================================

  const connect = useCallback(() => {
    if (!enabled) return;

    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      // Construct WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/ws/guided-flow/${documentId}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[GuidedFlow WS] Connected');
        isConnectedRef.current = true;
        reconnectAttempts.current = 0;

        // Send join message
        ws.send(JSON.stringify({
          event: 'join',
          documentId,
          userId: currentUser.id,
          userName: currentUser.name
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('[GuidedFlow WS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[GuidedFlow WS] Error:', error);
      };

      ws.onclose = () => {
        console.log('[GuidedFlow WS] Disconnected');
        isConnectedRef.current = false;
        wsRef.current = null;

        // Attempt reconnection with exponential backoff
        if (enabled && reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          console.log(`[GuidedFlow WS] Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[GuidedFlow WS] Connection error:', error);
    }
  }, [enabled, documentId, currentUser]);

  // ========================================================================
  // Message Handlers
  // ========================================================================

  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.event) {
      case 'field_update':
        // Don't process our own updates
        if (message.userId !== currentUser.id) {
          onFieldUpdate?.(message);
        }
        break;

      case 'collaborator_joined':
        // Don't announce ourselves
        if (message.collaborator.userId !== currentUser.id) {
          onCollaboratorJoined?.(message);
        }
        break;

      case 'collaborator_left':
        if (message.userId !== currentUser.id) {
          onCollaboratorLeft?.(message);
        }
        break;

      case 'field_locked':
        if (message.userId !== currentUser.id) {
          onFieldLocked?.(message);
        }
        break;

      default:
        console.warn('[GuidedFlow WS] Unknown message type:', (message as any).event);
    }
  }, [currentUser.id, onFieldUpdate, onCollaboratorJoined, onCollaboratorLeft, onFieldLocked]);

  // ========================================================================
  // Send Methods
  // ========================================================================

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('[GuidedFlow WS] Cannot send - not connected');
    }
  }, []);

  const sendFieldUpdate = useCallback((fieldId: string, value: any, status: string) => {
    sendMessage({
      event: 'field_update',
      documentId,
      fieldId,
      value,
      status,
      userId: currentUser.id,
      timestamp: new Date().toISOString()
    });
  }, [documentId, currentUser.id, sendMessage]);

  const sendFieldLock = useCallback((fieldId: string) => {
    sendMessage({
      event: 'field_lock',
      documentId,
      fieldId,
      userId: currentUser.id,
      userName: currentUser.name
    });
  }, [documentId, currentUser.id, currentUser.name, sendMessage]);

  const sendFieldUnlock = useCallback((fieldId: string) => {
    sendMessage({
      event: 'field_unlock',
      documentId,
      fieldId,
      userId: currentUser.id
    });
  }, [documentId, currentUser.id, sendMessage]);

  // ========================================================================
  // Disconnect
  // ========================================================================

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      // Send leave message before closing
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          event: 'leave',
          documentId,
          userId: currentUser.id
        }));
      }

      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectedRef.current = false;
  }, [documentId, currentUser.id]);

  // ========================================================================
  // Lifecycle
  // ========================================================================

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // ========================================================================
  // Return
  // ========================================================================

  return {
    isConnected: isConnectedRef.current,
    sendFieldUpdate,
    sendFieldLock,
    sendFieldUnlock,
    disconnect
  };
}
