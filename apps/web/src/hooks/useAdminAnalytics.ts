/**
 * useAdminAnalytics Hook
 *
 * Fetches organization-wide analytics data for the admin dashboard.
 * Uses React Query for caching and state management.
 *
 * Features:
 * - Configurable time period (7, 30, 90 days)
 * - 5-minute cache to avoid excessive API calls
 * - Automatic refetch when days parameter changes
 *
 * Dependencies:
 * - @tanstack/react-query for data fetching
 * - analyticsApi.getAnalytics() for API call
 */

import { useQuery } from '@tanstack/react-query';
import { analyticsApi, type AdminAnalyticsData } from '@/services/api';

/**
 * Hook options for configuring the analytics query
 */
interface UseAdminAnalyticsOptions {
  // Number of days to include in the analysis (default: 30)
  days?: number;
  // Whether to enable the query (default: true)
  enabled?: boolean;
}

/**
 * Hook for fetching admin analytics data.
 *
 * @param options - Configuration options
 * @param options.days - Number of days to analyze (7, 30, or 90 recommended)
 * @param options.enabled - Whether to fetch data (default: true)
 *
 * @returns Object containing analytics data, loading state, error, and refetch function
 */
export function useAdminAnalytics(options: UseAdminAnalyticsOptions = {}) {
  const { days = 30, enabled = true } = options;

  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    // Include days in query key so changing period triggers refetch
    queryKey: ['admin-analytics', days],
    queryFn: async (): Promise<AdminAnalyticsData> => {
      return analyticsApi.getAnalytics(days);
    },
    enabled,
    // Cache for 5 minutes since analytics data doesn't change frequently
    staleTime: 5 * 60 * 1000,
    // Keep data in cache for 10 minutes
    gcTime: 10 * 60 * 1000,
    // Retry once on failure
    retry: 1,
  });

  return {
    // Analytics data (null while loading)
    data,
    // Initial loading state
    loading: isLoading,
    // Background refetch state
    fetching: isFetching,
    // Error message (null if no error)
    error: error ? (error as Error).message : null,
    // Function to manually refresh data
    refetch,
  };
}
