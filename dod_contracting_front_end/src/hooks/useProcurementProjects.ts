/**
 * useProcurementProjects Hook
 * 
 * Manages procurement projects using React Query for:
 * - Automatic request deduplication (multiple components = 1 request)
 * - Smart caching with stale-while-revalidate
 * - Background refetching without blocking UI
 * - Automatic cache invalidation on mutations
 * 
 * Dependencies:
 * - @tanstack/react-query for data fetching and caching
 * - projectsApi from services/api for API calls
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, type Project } from '@/services/api';

// Query key for projects - used for cache management and invalidation
const PROJECTS_QUERY_KEY = ['projects'] as const;

export function useProcurementProjects() {
  const queryClient = useQueryClient();

  // Fetch all projects using React Query
  // - Automatically caches data
  // - Deduplicates concurrent requests
  // - Refetches based on QueryClient defaults (staleTime, refetchInterval)
  const {
    data,
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: async () => {
      const response = await projectsApi.list();
      return response.projects;
    },
  });

  // Create project mutation
  // - Automatically invalidates projects cache on success
  // - Returns the created project
  const createMutation = useMutation({
    mutationFn: async (projectData: {
      name: string;
      description: string;
      project_type: string;
      estimated_value: number;
      contracting_officer_id?: string;
    }) => {
      const response = await projectsApi.create(projectData);
      return response.project;
    },
    onSuccess: () => {
      // Invalidate and refetch projects list after successful creation
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
    },
  });

  // Update project mutation
  const updateMutation = useMutation({
    mutationFn: async ({ projectId, updates }: { projectId: string; updates: Partial<Project> }) => {
      await projectsApi.update(projectId, updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
    },
  });

  // Delete project mutation
  const deleteMutation = useMutation({
    mutationFn: async (projectId: string) => {
      await projectsApi.delete(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
    },
  });

  // Wrapper functions to maintain backward compatibility with existing components
  const createProject = async (projectData: {
    name: string;
    description: string;
    project_type: string;
    estimated_value: number;
    contracting_officer_id?: string;
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
