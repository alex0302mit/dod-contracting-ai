import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/services/api';

export function useProjectTeam(projectId: string | null) {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['project-team', projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await projectsApi.getTeam(projectId);
      return response.team;
    },
    enabled: !!projectId,
  });

  const addMemberMutation = useMutation({
    mutationFn: ({ userId, permissionLevel }: { userId: string; permissionLevel: string }) =>
      projectsApi.addTeamMember(projectId!, userId, permissionLevel),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project-team', projectId] }),
  });

  const updateMemberMutation = useMutation({
    mutationFn: ({ userId, permissionLevel }: { userId: string; permissionLevel: string }) =>
      projectsApi.updateTeamMember(projectId!, userId, permissionLevel),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project-team', projectId] }),
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) =>
      projectsApi.removeTeamMember(projectId!, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['project-team', projectId] }),
  });

  return {
    team: data ?? [],
    loading: isLoading,
    error: error as Error | null,
    addMember: addMemberMutation.mutateAsync,
    updateMember: updateMemberMutation.mutateAsync,
    removeMember: removeMemberMutation.mutateAsync,
  };
}
