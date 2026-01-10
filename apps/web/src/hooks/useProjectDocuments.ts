/**
 * useProjectDocuments Hook
 * 
 * Manages project documents using React Query for:
 * - Automatic request deduplication (same projectId = 1 request across all components)
 * - Smart caching with stale-while-revalidate
 * - Conditional fetching (only when projectId is provided)
 * - Background refetching without blocking UI
 * 
 * Dependencies:
 * - @tanstack/react-query for data fetching and caching
 * - projectsApi from services/api for API calls
 */
import { useMemo, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/services/api';

export interface ProjectDocument {
  id: string;
  project_id: string;
  document_name: string;
  description: string | null;
  category: string;
  phase: string | null;
  is_required: boolean;
  status: 'pending' | 'uploaded' | 'under_review' | 'approved' | 'rejected' | 'expired';
  deadline: string | null;
  expiration_date: string | null;
  requires_approval: boolean;
  assigned_user_id: string | null;
  notes: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
  // AI Generation fields
  generation_status?: 'not_generated' | 'generating' | 'generated' | 'failed';
  generated_content?: string | null;
  generated_at?: string | null;
  generation_task_id?: string | null;
  ai_quality_score?: number | null;
  assigned_user?: {
    name: string;
    email: string;
  };
  latest_upload?: {
    id: string;
    file_name: string;
    file_size: number;
    upload_date: string;
    uploaded_by: string;
    uploader?: {
      name: string;
    };
  };
  pending_approvals?: number;
}

// Query key factory for project documents - includes projectId for unique caching
const getDocumentsQueryKey = (projectId: string | null) => ['project-documents', projectId] as const;

export function useProjectDocuments(projectId: string | null) {
  const queryClient = useQueryClient();

  // Fetch documents using React Query
  // - enabled: only fetch when projectId is provided
  // - Automatically deduplicates requests for same projectId
  // - Uses longer staleTime to reduce dashboard polling overhead
  const {
    data: documents = [],
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: getDocumentsQueryKey(projectId),
    queryFn: async () => {
      if (!projectId) return [];

      // Fetch documents from backend API
      const response = await projectsApi.getDocuments(projectId);
      
      // Map backend documents to ProjectDocument format
      const mappedDocs: ProjectDocument[] = (response.documents || []).map((doc: any) => ({
        ...doc,
        description: doc.description || null,
        category: 'general',
        phase: null,
        is_required: false,
        deadline: null,
        expiration_date: null,
        requires_approval: false,
        assigned_user_id: null,
        notes: null,
        display_order: 0,
        created_at: doc.uploaded_at || new Date().toISOString(),
        updated_at: doc.uploaded_at || new Date().toISOString(),
      }));
      
      return mappedDocs;
    },
    enabled: !!projectId, // Only fetch when projectId exists
    staleTime: 30000, // Consider data fresh for 30 seconds (reduce polling on dashboard)
    refetchInterval: 60000, // Refetch every 60 seconds instead of 10
  });

  // Helper to invalidate documents cache (for future mutations)
  const invalidateDocuments = useCallback(() => {
    if (projectId) {
      queryClient.invalidateQueries({ queryKey: getDocumentsQueryKey(projectId) });
    }
  }, [queryClient, projectId]);

  // Placeholder functions for future backend implementation
  const initializeDocumentsFromTemplate = async (contractType: string) => {
    if (!projectId) return;
    console.log('Initialize documents from template:', contractType);
    // Future: Call backend API to initialize documents from template
    // Then: invalidateDocuments();
  };

  const addDocument = async (document: Partial<ProjectDocument>) => {
    if (!projectId) return;
    console.log('Add document:', document);
    // Future: Call backend API to add document
    // Then: invalidateDocuments();
    alert('Document management features are being migrated to the new backend. This feature will be available soon.');
  };

  const updateDocument = async (documentId: string, updates: Partial<ProjectDocument>) => {
    console.log('Update document:', documentId, updates);
    // Future: Call backend API to update document
    // Then: invalidateDocuments();
  };

  const deleteDocument = async (documentId: string) => {
    console.log('Delete document:', documentId);
    // Future: Call backend API to delete document
    // Then: invalidateDocuments();
  };

  // Memoized document stats calculation - only recalculates when documents change
  const getDocumentStats = useCallback(() => {
    const total = documents.length;
    const pending = documents.filter((d) => d.status === 'pending').length;
    const uploaded = documents.filter((d) => d.status === 'uploaded').length;
    const underReview = documents.filter((d) => d.status === 'under_review').length;
    const approved = documents.filter((d) => d.status === 'approved').length;
    const rejected = documents.filter((d) => d.status === 'rejected').length;
    const expired = documents.filter((d) => d.status === 'expired').length;
    const required = documents.filter((d) => d.is_required).length;
    const requiredComplete = documents.filter((d) => d.is_required && d.status === 'approved').length;

    return {
      total,
      pending,
      uploaded,
      underReview,
      approved,
      rejected,
      expired,
      required,
      requiredComplete,
      completionPercentage: required > 0 ? Math.round((requiredComplete / required) * 100) : 0,
    };
  }, [documents]);

  return {
    documents,
    loading,
    error: error ? (error instanceof Error ? error.message : 'Failed to fetch documents') : null,
    initializeDocumentsFromTemplate,
    addDocument,
    updateDocument,
    deleteDocument,
    getDocumentStats,
    refetch,
  };
}
