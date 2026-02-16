/**
 * Hook for fetching and managing standalone documents.
 */

import { useState, useEffect, useCallback } from 'react';
import { standaloneApi, type StandaloneDocument } from '@/services/api';

export function useStandaloneDocuments() {
  const [documents, setDocuments] = useState<StandaloneDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await standaloneApi.listDocuments();
      setDocuments(response.documents);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const deleteDocument = useCallback(async (documentId: string) => {
    await standaloneApi.deleteDocument(documentId);
    setDocuments(prev => prev.filter(d => d.id !== documentId));
  }, []);

  return { documents, loading, error, refetch: fetchDocuments, deleteDocument };
}
