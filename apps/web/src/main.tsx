import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.tsx';
import './index.css';
import { Toaster } from '@/components/ui/sonner';

// Create a client with optimized defaults for reduced polling
// These settings prevent excessive API calls while keeping data reasonably fresh
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // Data is fresh for 30 seconds (increased from 10s)
      refetchInterval: 60000, // Auto-refetch every 60 seconds (increased from 30s)
      refetchOnWindowFocus: true, // Refetch when user returns to tab
      retry: 1, // Retry failed requests once
      refetchOnMount: 'always', // Always refetch on mount for fresh data
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster />
    </QueryClientProvider>
  </StrictMode>
);
