/**
 * useProcurementProjects Hook
 *
 * Manages procurement projects using React Query for:
 * - Automatic request deduplication (multiple components = 1 request)
 * - Smart caching with stale-while-revalidate
 * - Background refetching without blocking UI
 * - Automatic cache invalidation on mutations
 * - Organization-scoped project filtering
 *
 * Dependencies:
 * - @tanstack/react-query for data fetching and caching
 * - projectsApi from services/api for API calls
 * - useAuth for active organization context
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, type Project } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

export function useProcurementProjects() {
  const queryClient = useQueryClient();
  const { activeOrgId } = useAuth();

  // Include activeOrgId in query key so project list refetches when org changes
  const queryKey = ['projects', activeOrgId] as const;

  // Fetch projects scoped to active organization
  const {
    data,
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: async () => {
      const response = await projectsApi.list(activeOrgId ?? undefined);
      return response.projects;
    },
  });

  // Create project mutation
  const createMutation = useMutation({
    mutationFn: async (projectData: {
      name: string;
      description: string;
      project_type: string;
      estimated_value: number;
      contracting_officer_id?: string;
      program_manager_id?: string;
      organization_id?: string;
    }) => {
      const response = await projectsApi.create(projectData);
      return response.project;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  // Update project mutation
  const updateMutation = useMutation({
    mutationFn: async ({ projectId, updates }: { projectId: string; updates: Partial<Project> }) => {
      await projectsApi.update(projectId, updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  // Delete project mutation
  const deleteMutation = useMutation({
    mutationFn: async (projectId: string) => {
      await projectsApi.delete(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  // Wrapper functions to maintain backward compatibility with existing components
  const createProject = async (projectData: {
    name: string;
    description: string;
    project_type: string;
    estimated_value: number;
    contracting_officer_id?: string;
    program_manager_id?: string;
    organization_id?: string;
  }) => {
    return createMutation.mutateAsync(projectData);
  };

  const updateProject = async (projectId: string, updates: Partial<Project>) => {
    await updateMutation.mutateAsync({ projectId, updates });
  };

  const deleteProject = async (projectId: string) => {
    await deleteMutation.mutateAsync(projectId);
  };

  return {
    projects: data ?? [],
    loading,
    error: error as Error | null,
    createProject,
    updateProject,
    deleteProject,
    refresh: refetch,
  };
}
