import React, { useEffect, useRef } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { persister } from '@/utils/queryPersister';
import type { StoredQuery } from '@/utils/queryPersister';

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * Create QueryClient with offline-aware configuration
 *
 * Features:
 * - Longer cache times for offline data persistence
 * - Retry with exponential backoff for network failures
 * - Network-aware retries (no retry when offline)
 * - Cache data persists across page reloads
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data stays fresh for 5 minutes
      staleTime: 5 * 60 * 1000,
      // Cache persists for 24 hours (longer for offline access)
      gcTime: 24 * 60 * 60 * 1000,
      // Retry failed requests up to 3 times
      retry: 3,
      // Use exponential backoff for retries
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Don't refetch on window focus (reduces unnecessary network requests)
      refetchOnWindowFocus: false,
      // Refetch on reconnect if data is stale
      refetchOnReconnect: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
  },
});

/**
 * Query Provider Component
 *
 * Provides React Query client with offline caching support.
 * Automatically persists and restores query cache using IndexedDB.
 *
 * @param props - Component props
 * @param props.children - Child components to wrap
 * @returns QueryClientProvider with offline support
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <QueryProvider>
 *       <YourApp />
 *     </QueryProvider>
 *   );
 * }
 * ```
 */
const QueryProvider: React.FC<QueryProviderProps> = ({ children }) => {
  const restoreAttempted = useRef(false);

  useEffect(() => {
    /**
     * Restore query cache from IndexedDB on mount
     * This allows previously fetched data to be available offline
     */
    const restoreCache = async () => {
      if (restoreAttempted.current) {
        return;
      }

      restoreAttempted.current = true;

      try {
        const storedData = await persister.restore();

        if (storedData && Array.isArray(storedData.data)) {
          // Restore each query to the query client cache
          storedData.data.forEach(([queryKey, queryData]) => {
            queryClient.setQueryData(
              queryKey as unknown as string[],
              (queryData as { state: unknown }).state
            );
          });

          console.log(
            `[QueryProvider] Restored ${storedData.data.length} cached queries`
          );
        }
      } catch (error) {
        console.error('[QueryProvider] Error restoring query cache:', error);
      }
    };

    restoreCache();
  }, []);

  useEffect(() => {
    /**
     * Persist query cache to IndexedDB periodically
     * This ensures data is available for offline access
     */
    const persistCache = () => {
      try {
        // Get all queries from the cache
        const queries = queryClient.getQueryCache().getAll();

        // Format data for storage
        const data = queries.map((query) => {
          return [query.queryKey, { state: query.state }];
        });

        const storedData: StoredQuery = {
          buster: 'v1', // Version for cache invalidation
          data: data as Array<[string, { state: unknown; queryKey: unknown[] }]>,
        };

        persister.persist(storedData);
      } catch (error) {
        console.error('[QueryProvider] Error persisting query cache:', error);
      }
    };

    // Persist cache immediately
    persistCache();

    // Persist cache every 30 seconds
    const intervalId = setInterval(persistCache, 30000);

    // Persist cache before page unload
    const handleBeforeUnload = () => {
      persistCache();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};

export default QueryProvider;
