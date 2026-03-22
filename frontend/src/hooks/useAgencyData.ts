import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agenciesClient, clientTenantsClient } from '@/api';
import type {
  AgencyCreate,
  AgencyUpdate,
  AgencyResponse,
  ClientTenantCreate,
  ClientTenantUpdate,
  ClientTenantResponse,
} from '@/api/agencies';

/**
 * Agency analytics metrics
 */
export interface AgencyAnalytics {
  total_clients: number;
  active_clients: number;
  total_candidates: number;
  total_placements: number;
  monthly_revenue: number;
}

/**
 * Client billing data
 */
export interface ClientBillingData {
  tenant_id: string;
  name: string;
  status: string;
  monthly_fee: number;
  usage_costs: number;
  total_billing: number;
  candidates_count: number;
  active_jobs_count: number;
}

/**
 * Agency billing metrics
 */
export interface AgencyBillingData {
  total_revenue: number;
  monthly_recurring: number;
  usage_costs: number;
  active_clients_count: number;
  clients: ClientBillingData[];
}

/**
 * Hook for fetching agencies list
 *
 * @param isActive - Optional filter for active agencies
 * @param search - Optional search query
 * @returns Query result with agencies list
 */
export function useAgencies(isActive?: boolean, search?: string) {
  return useQuery({
    queryKey: ['agencies', { isActive, search }],
    queryFn: async () => {
      const response = await agenciesClient.listAgencies(isActive, search);
      return response;
    },
  });
}

/**
 * Hook for fetching a single agency by ID
 *
 * @param agencyId - Agency ID
 * @returns Query result with agency details
 */
export function useAgency(agencyId: string | undefined) {
  return useQuery({
    queryKey: ['agency', agencyId],
    queryFn: async () => {
      if (!agencyId) throw new Error('Agency ID is required');
      const response = await agenciesClient.getAgency(agencyId);
      return response;
    },
    enabled: !!agencyId,
  });
}

/**
 * Hook for creating an agency
 *
 * @returns Mutation function for creating agencies
 */
export function useCreateAgency() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AgencyCreate) => {
      const response = await agenciesClient.createAgency(data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agencies'] });
    },
  });
}

/**
 * Hook for updating an agency
 *
 * @returns Mutation function for updating agencies
 */
export function useUpdateAgency() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ agencyId, data }: { agencyId: string; data: AgencyUpdate }) => {
      const response = await agenciesClient.updateAgency(agencyId, data);
      return response;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agencies'] });
      queryClient.invalidateQueries({ queryKey: ['agency', variables.agencyId] });
    },
  });
}

/**
 * Hook for deleting an agency
 *
 * @returns Mutation function for deleting agencies
 */
export function useDeleteAgency() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (agencyId: string) => {
      await agenciesClient.deleteAgency(agencyId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agencies'] });
    },
  });
}

/**
 * Hook for fetching client tenants
 *
 * @param agencyId - Optional agency ID filter
 * @param organizationId - Optional organization ID filter
 * @param status - Optional status filter
 * @returns Query result with client tenants list
 */
export function useClientTenants(
  agencyId?: string,
  organizationId?: string,
  status?: string
) {
  return useQuery({
    queryKey: ['client-tenants', { agencyId, organizationId, status }],
    queryFn: async () => {
      const response = await clientTenantsClient.listClientTenants(
        agencyId,
        organizationId,
        status
      );
      return response;
    },
  });
}

/**
 * Hook for fetching a single client tenant by ID
 *
 * @param tenantId - Client tenant ID
 * @returns Query result with client tenant details
 */
export function useClientTenant(tenantId: string | undefined) {
  return useQuery({
    queryKey: ['client-tenant', tenantId],
    queryFn: async () => {
      if (!tenantId) throw new Error('Tenant ID is required');
      const response = await clientTenantsClient.getClientTenant(tenantId);
      return response;
    },
    enabled: !!tenantId,
  });
}

/**
 * Hook for creating a client tenant
 *
 * @returns Mutation function for creating client tenants
 */
export function useCreateClientTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ClientTenantCreate) => {
      const response = await clientTenantsClient.createClientTenant(data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-tenants'] });
    },
  });
}

/**
 * Hook for updating a client tenant
 *
 * @returns Mutation function for updating client tenants
 */
export function useUpdateClientTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tenantId, data }: { tenantId: string; data: ClientTenantUpdate }) => {
      const response = await clientTenantsClient.updateClientTenant(tenantId, data);
      return response;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['client-tenants'] });
      queryClient.invalidateQueries({ queryKey: ['client-tenant', variables.tenantId] });
    },
  });
}

/**
 * Hook for deleting a client tenant
 *
 * @returns Mutation function for deleting client tenants
 */
export function useDeleteClientTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      await clientTenantsClient.deleteClientTenant(tenantId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-tenants'] });
    },
  });
}

/**
 * Hook for fetching agency analytics
 *
 * @returns Query result with agency analytics metrics
 */
export function useAgencyAnalytics() {
  return useQuery({
    queryKey: ['agency-analytics'],
    queryFn: async () => {
      const response = await agenciesClient.getAxiosInstance().get<AgencyAnalytics>(
        '/api/agencies/analytics'
      );
      return response.data;
    },
  });
}

/**
 * Hook for fetching agency billing data
 *
 * @param startDate - Optional start date for filtering
 * @param endDate - Optional end date for filtering
 * @returns Query result with agency billing metrics and per-client breakdown
 */
export function useAgencyBilling(params?: { startDate?: string; endDate?: string }) {
  return useQuery({
    queryKey: ['agency-billing', params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.startDate) queryParams.append('start_date', params.startDate);
      if (params?.endDate) queryParams.append('end_date', params.endDate);

      const url = `/api/agencies/billing${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await agenciesClient.getAxiosInstance().get<AgencyBillingData>(url);
      return response.data;
    },
  });
}
