/**
 * Integrations Hooks
 *
 * React Query hooks for managing HRIS/ATS platform integrations.
 *
 * @example
 * ```tsx
 * import { useIntegrations, useCreateIntegration, useTriggerSync } from '@/hooks/useIntegrations';
 *
 * function IntegrationsPage() {
 *   const { data: integrations, isLoading } = useIntegrations();
 *   const createIntegration = useCreateIntegration();
 *   const triggerSync = useTriggerSync();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *
 *   return (
 *     <div>
 *       {integrations?.integrations.map(integration => (
 *         <div key={integration.id}>
 *           <h3>{integration.name}</h3>
 *           <button onClick={() => triggerSync.mutate(integration.id)}>
 *             Sync Now
 *           </button>
 *         </div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integrationsClient } from '@/api/integrations';
import type {
  IntegrationCreate,
  IntegrationUpdate,
  SyncTriggerRequest,
} from '@/types/api';

/**
 * Query key factory for integrations queries
 */
export const integrationsKeys = {
  all: ['integrations'] as const,
  lists: () => [...integrationsKeys.all, 'list'] as const,
  list: (filters?: { platform?: string; status?: string }) =>
    [...integrationsKeys.lists(), filters] as const,
  details: () => [...integrationsKeys.all, 'detail'] as const,
  detail: (id: string) => [...integrationsKeys.details(), id] as const,
  syncHistory: (id: string) => [...integrationsKeys.all, 'sync-history', id] as const,
  syncStatus: (id: string, syncId: string) =>
    [...integrationsKeys.all, 'sync-status', id, syncId] as const,
};

/**
 * Hook to fetch all integrations with optional filters
 *
 * @param platform - Optional filter by platform type
 * @param status - Optional filter by status
 * @param skip - Number of records to skip (pagination)
 * @param limit - Maximum number of records to return
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useIntegrations();
 * const { data: workdayIntegrations } = useIntegrations('workday');
 * const { data: activeIntegrations } = useIntegrations(undefined, 'active');
 * ```
 */
export function useIntegrations(
  platform?: string,
  status?: string,
  skip: number = 0,
  limit: number = 100
) {
  return useQuery({
    queryKey: integrationsKeys.list({ platform, status }),
    queryFn: () => integrationsClient.listIntegrations(platform, status, skip, limit),
  });
}

/**
 * Hook to fetch a single integration by ID
 *
 * @param integrationId - Integration ID
 *
 * @example
 * ```tsx
 * const { data: integration, isLoading, error } = useIntegration('integration-uuid');
 * ```
 */
export function useIntegration(integrationId: string) {
  return useQuery({
    queryKey: integrationsKeys.detail(integrationId),
    queryFn: () => integrationsClient.getIntegration(integrationId),
    enabled: !!integrationId,
  });
}

/**
 * Hook to create a new integration
 *
 * @example
 * ```tsx
 * const createIntegration = useCreateIntegration();
 *
 * const handleCreate = async (data: IntegrationCreate) => {
 *   try {
 *     await createIntegration.mutateAsync(data);
 *     toast.success('Integration created successfully');
 *   } catch (error) {
 *     toast.error('Failed to create integration');
 *   }
 * };
 * ```
 */
export function useCreateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: IntegrationCreate) =>
      integrationsClient.createIntegration(request),
    onSuccess: () => {
      // Invalidate and refetch integrations list
      queryClient.invalidateQueries({ queryKey: integrationsKeys.lists() });
    },
  });
}

/**
 * Hook to update an integration
 *
 * @example
 * ```tsx
 * const updateIntegration = useUpdateIntegration();
 *
 * const handleUpdate = async (id: string, data: IntegrationUpdate) => {
 *   await updateIntegration.mutateAsync({ id, data });
 * };
 * ```
 */
export function useUpdateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      integrationId,
      request,
    }: {
      integrationId: string;
      request: IntegrationUpdate;
    }) => integrationsClient.updateIntegration(integrationId, request),
    onSuccess: (_, variables) => {
      // Invalidate the specific integration and the list
      queryClient.invalidateQueries({
        queryKey: integrationsKeys.detail(variables.integrationId),
      });
      queryClient.invalidateQueries({ queryKey: integrationsKeys.lists() });
    },
  });
}

/**
 * Hook to delete an integration
 *
 * @example
 * ```tsx
 * const deleteIntegration = useDeleteIntegration();
 *
 * const handleDelete = async (id: string) => {
 *   if (confirm('Are you sure you want to delete this integration?')) {
 *     await deleteIntegration.mutateAsync(id);
 *   }
 * };
 * ```
 */
export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (integrationId: string) =>
      integrationsClient.deleteIntegration(integrationId),
    onSuccess: () => {
      // Invalidate integrations list
      queryClient.invalidateQueries({ queryKey: integrationsKeys.lists() });
    },
  });
}

/**
 * Hook to test connection to an external platform
 *
 * @example
 * ```tsx
 * const testConnection = useTestConnection();
 *
 * const handleTest = async (id: string) => {
 *   try {
 *     const result = await testConnection.mutateAsync(id);
 *     if (result.success) {
 *       toast.success('Connection successful');
 *     } else {
 *       toast.error(`Connection failed: ${result.message}`);
 *     }
 *   } catch (error) {
 *     toast.error('Connection test failed');
 *   }
 * };
 * ```
 */
export function useTestConnection() {
  return useMutation({
    mutationFn: (integrationId: string) =>
      integrationsClient.testConnection(integrationId),
  });
}

/**
 * Hook to trigger a sync operation
 *
 * @example
 * ```tsx
 * const triggerSync = useTriggerSync();
 *
 * const handleSync = async (id: string, type: SyncType) => {
 *   await triggerSync.mutateAsync({
 *     integrationId: id,
 *     request: { sync_type: type }
 *   });
 * };
 * ```
 */
export function useTriggerSync() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      integrationId,
      request,
    }: {
      integrationId: string;
      request: SyncTriggerRequest;
    }) => integrationsClient.triggerSync(integrationId, request),
    onSuccess: (_, variables) => {
      // Invalidate sync history for this integration
      queryClient.invalidateQueries({
        queryKey: integrationsKeys.syncHistory(variables.integrationId),
      });
      // Invalidate the integration to update last sync info
      queryClient.invalidateQueries({
        queryKey: integrationsKeys.detail(variables.integrationId),
      });
    },
  });
}

/**
 * Hook to fetch sync history for an integration
 *
 * @param integrationId - Integration ID
 * @param skip - Number of records to skip (pagination)
 * @param limit - Maximum number of records to return
 *
 * @example
 * ```tsx
 * const { data: history, isLoading } = useSyncHistory('integration-uuid');
 * console.log(`Total syncs: ${history?.total_syncs}`);
 * ```
 */
export function useSyncHistory(
  integrationId: string,
  skip: number = 0,
  limit: number = 50
) {
  return useQuery({
    queryKey: integrationsKeys.syncHistory(integrationId),
    queryFn: () => integrationsClient.getSyncHistory(integrationId, skip, limit),
    enabled: !!integrationId,
    refetchInterval: (data) => {
      // Poll if there's a running sync
      const hasRunningSync = data?.syncs.some(
        (sync) => sync.status === 'running' || sync.status === 'pending'
      );
      return hasRunningSync ? 5000 : false; // Poll every 5 seconds if running
    },
  });
}

/**
 * Hook to fetch sync status for a specific sync operation
 *
 * @param integrationId - Integration ID
 * @param syncId - Sync operation ID
 *
 * @example
 * ```tsx
 * const { data: status } = useSyncStatus('integration-uuid', 'sync-uuid');
 * console.log(`Status: ${status?.status}`);
 * ```
 */
export function useSyncStatus(integrationId: string, syncId: string) {
  return useQuery({
    queryKey: integrationsKeys.syncStatus(integrationId, syncId),
    queryFn: () => integrationsClient.getSyncStatus(integrationId, syncId),
    enabled: !!(integrationId && syncId),
    refetchInterval: (data) => {
      // Poll if sync is still running
      const isRunning = data?.status === 'running' || data?.status === 'pending';
      return isRunning ? 3000 : false; // Poll every 3 seconds if running
    },
  });
}
