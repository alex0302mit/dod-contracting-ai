/**
 * useDashboardStats Hook
 *
 * Aggregates data from multiple sources for the Dashboard view:
 * - Project statistics (total, in_progress, completed, delayed)
 * - Pending approvals count
 * - Recent projects list
 *
 * Uses existing hooks and APIs to avoid backend changes.
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useProcurementProjects } from './useProcurementProjects';
import { approvalsApi } from '@/services/api';

export interface DashboardStats {
  projects: {
    total: number;
    in_progress: number;
    completed: number;
    delayed: number;
    not_started: number;
  };
  pendingApprovals: number;
}

export interface RecentProject {
  id: string;
  name: string;
  description?: string;
  overall_status: string;
  current_phase: string;
  updated_at?: string;
  created_at?: string;
  contracting_officer_name?: string;
}

export function useDashboardStats() {
  // Fetch projects using existing hook
  const { projects, loading: projectsLoading, refresh: refreshProjects } = useProcurementProjects();

  // Fetch pending approvals count
  const {
    data: approvalsData,
    isLoading: approvalsLoading,
    refetch: refreshApprovals
  } = useQuery({
    queryKey: ['dashboard-pending-approvals'],
    queryFn: async () => {
      try {
        const response = await approvalsApi.getPendingApprovals();
        return response;
      } catch {
        // Return empty if endpoint fails (may not be authorized)
        return { approvals: [], count: 0 };
      }
    },
    staleTime: 30000, // 30 seconds
  });

  // Calculate project statistics
  const stats = useMemo<DashboardStats>(() => {
    return {
      projects: {
        total: projects.length,
        in_progress: projects.filter(p => p.overall_status === 'in_progress').length,
        completed: projects.filter(p => p.overall_status === 'completed').length,
        delayed: projects.filter(p => p.overall_status === 'delayed').length,
        not_started: projects.filter(p => p.overall_status === 'not_started').length,
      },
      pendingApprovals: approvalsData?.count || 0,
    };
  }, [projects, approvalsData]);

  // Get 5 most recent projects (sorted by updated_at or created_at)
  const recentProjects = useMemo<RecentProject[]>(() => {
    return [...projects]
      .sort((a, b) => {
        const dateA = new Date(a.updated_at || a.created_at || 0).getTime();
        const dateB = new Date(b.updated_at || b.created_at || 0).getTime();
        return dateB - dateA; // Most recent first
      })
      .slice(0, 5)
      .map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        overall_status: p.overall_status,
        current_phase: p.current_phase,
        updated_at: p.updated_at,
        created_at: p.created_at,
        contracting_officer_name: p.contracting_officer_name,
      }));
  }, [projects]);

  // Combined loading state
  const loading = projectsLoading || approvalsLoading;

  // Refresh all data
  const refresh = () => {
    refreshProjects();
    refreshApprovals();
  };

  return {
    stats,
    recentProjects,
    loading,
    refresh,
  };
}
