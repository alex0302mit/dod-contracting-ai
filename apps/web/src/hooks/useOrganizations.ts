import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsApi } from '@/services/api';

const ORGS_KEY = ['organizations'] as const;

export function useOrganizations() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ORGS_KEY,
    queryFn: async () => {
      const response = await organizationsApi.list();
      return response.organizations;
    },
  });

  const createMutation = useMutation({
    mutationFn: organizationsApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ORGS_KEY }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string; parent_id?: string } }) =>
      organizationsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ORGS_KEY }),
  });

  return {
    organizations: data ?? [],
    loading: isLoading,
    error: error as Error | null,
    createOrganization: createMutation.mutateAsync,
    updateOrganization: updateMutation.mutateAsync,
  };
}

export function useOrgMembers(orgId: string | null) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['org-members', orgId],
    queryFn: async () => {
      if (!orgId) return [];
      const response = await organizationsApi.getMembers(orgId);
      return response.members;
    },
    enabled: !!orgId,
  });

  const addMemberMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      organizationsApi.addMember(orgId!, userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['org-members', orgId] }),
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => organizationsApi.removeMember(orgId!, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['org-members', orgId] }),
  });

  return {
    members: data ?? [],
    loading: isLoading,
    addMember: addMemberMutation.mutateAsync,
    removeMember: removeMemberMutation.mutateAsync,
  };
}
