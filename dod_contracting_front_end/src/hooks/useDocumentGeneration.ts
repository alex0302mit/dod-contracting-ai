/**
 * WebSocket Hook for Real-time Document Generation Updates
 * Connects to the Python backend WebSocket for live progress updates
 */

import { useEffect, useState, useRef } from 'react';
import { createWebSocket, type WebSocketMessage } from '@/services/api';

interface DocumentGenerationState {
  progress: number;
  message: string;
  status: 'idle' | 'generating' | 'complete' | 'error';
  documentUrl: string | null;
  documentType: string | null;
  error: string | null;
}

export function useDocumentGeneration(projectId: string) {
  const [state, setState] = useState<DocumentGenerationState>({
    progress: 0,
    message: '',
    status: 'idle',
    documentUrl: null,
    documentType: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Don't connect if no project ID
    if (!projectId) return;

    // Create WebSocket connection
    const ws = createWebSocket(projectId);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('📡 WebSocket connected for project:', projectId);
    };

    ws.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);

      switch (data.type) {
        case 'generation_started':
          setState({
            progress: 0,
            message: data.message || 'Starting document generation...',
            status: 'generating',
            documentUrl: null,
            documentType: data.document_type || null,
            error: null,
          });
          break;

        case 'progress':
          setState((prev) => ({
            ...prev,
            progress: data.percentage || 0,
            message: data.message || 'Processing...',
          }));
          break;

        case 'generation_complete':
          setState({
            progress: 100,
            message: data.message || 'Document generated successfully!',
            status: 'complete',
            documentUrl: data.document_url || null,
            documentType: data.document_type || null,
            error: null,
          });
          break;

        case 'phase_update':
          setState((prev) => ({
            ...prev,
            message: data.message || `Phase ${data.phase} - ${data.status}`,
          }));
          break;

        case 'error':
          setState({
            progress: 0,
            message: data.message || 'An error occurred',
            status: 'error',
            documentUrl: null,
            documentType: null,
            error: data.message || 'Unknown error',
          });
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setState((prev) => ({
        ...prev,
        status: 'error',
        message: 'Connection error',
        error: 'Failed to connect to server',
      }));
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected for project:', projectId);
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [projectId]);

  const reset = () => {
    setState({
      progress: 0,
      message: '',
      status: 'idle',
      documentUrl: null,
      documentType: null,
      error: null,
    });
  };

  return {
    ...state,
    reset,
  };
}

/**
 * Hook for monitoring multiple projects
 */
export function useProjectUpdates(projectIds: string[]) {
  const [updates, setUpdates] = useState<Record<string, WebSocketMessage>>({});
  const wsRefs = useRef<Record<string, WebSocket>>({});

  useEffect(() => {
    // Close existing connections
    Object.values(wsRefs.current).forEach((ws) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    });
    wsRefs.current = {};

    // Create new connections for each project
    projectIds.forEach((projectId) => {
      const ws = createWebSocket(projectId);
      wsRefs.current[projectId] = ws;

      ws.onmessage = (event) => {
        const data: WebSocketMessage = JSON.parse(event.data);
        setUpdates((prev) => ({
          ...prev,
          [projectId]: data,
        }));
      };
    });

    // Cleanup
    return () => {
      Object.values(wsRefs.current).forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });
    };
  }, [projectIds.join(',')]);

  return updates;
}
