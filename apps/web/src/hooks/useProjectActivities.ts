import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/services/api';

export function useProjectActivities(projectId: string | null, limit: number = 20) {
  const { data, isLoading, error, fetchNextPage, hasNextPage } = useQuery({
    queryKey: ['project-activities', projectId, limit],
    queryFn: async () => {
      if (!projectId) return { activities: [], total: 0 };
      return projectsApi.getActivities(projectId, limit, 0);
    },
    enabled: !!projectId,
  });

  return {
    activities: data?.activities ?? [],
    total: data?.total ?? 0,
    loading: isLoading,
    error: error as Error | null,
  };
}
