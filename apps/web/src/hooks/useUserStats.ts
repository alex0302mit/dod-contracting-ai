/**
 * useUserStats Hook
 *
 * Fetches personal analytics for the current user from /api/users/me/stats.
 * Designed for lazy loading - data is only fetched when explicitly triggered
 * (e.g., when the profile dropdown opens).
 *
 * Returns:
 * - stats: User statistics (documents generated, hours saved, projects contributed)
 * - loading: Whether the fetch is in progress
 * - error: Error message if fetch failed
 * - fetchStats: Function to trigger data fetch
 * - hasLoaded: Whether data has been successfully loaded at least once
 *
 * Dependencies:
 * - @tanstack/react-query for caching and state management
 * - authApi.getUserStats() for API call
 */

import { useQuery } from '@tanstack/react-query';
import { authApi, type UserStats } from '@/services/api';

/**
 * Transformed stats with camelCase properties for frontend use
 */
export interface UserStatsDisplay {
  documentsGenerated: number;
  estimatedHoursSaved: number;
  projectsContributed: number;
  period: string;
}

/**
 * Hook for fetching user personal analytics with lazy loading.
 * Data is only fetched when fetchStats() is called or when the component
 * mounts with enabled=true.
 *
 * @param options.enabled - Whether to fetch immediately on mount (default: false for lazy loading)
 */
export function useUserStats(options?: { enabled?: boolean }) {
  const {
    data,
    isLoading,
    error,
    refetch,
    isFetched,
  } = useQuery({
    queryKey: ['user-stats'],
    queryFn: async (): Promise<UserStats> => {
      return authApi.getUserStats();
    },
    // Don't fetch on mount by default - wait for explicit trigger
    enabled: options?.enabled ?? false,
    // Cache for 5 minutes since stats don't change frequently
    staleTime: 5 * 60 * 1000,
    // Keep data in cache for 10 minutes
    gcTime: 10 * 60 * 1000,
    // Don't retry on failure to avoid spamming
    retry: false,
  });

  // Transform snake_case API response to camelCase for frontend
  const stats: UserStatsDisplay | null = data
    ? {
        documentsGenerated: data.documents_generated,
        estimatedHoursSaved: data.estimated_hours_saved,
        projectsContributed: data.projects_contributed,
        period: data.period,
      }
    : null;

  return {
    // Transformed stats ready for display
    stats,
    // Loading state
    loading: isLoading,
    // Error message (null if no error)
    error: error ? (error as Error).message : null,
    // Function to trigger fetch (for lazy loading)
    fetchStats: refetch,
    // Whether we've successfully loaded data at least once
    hasLoaded: isFetched && !error && !!data,
  };
}
