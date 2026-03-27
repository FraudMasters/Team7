import { useState, useEffect, useCallback, createContext, useContext } from 'react';

/**
 * Tenant context state
 */
export interface TenantContext {
  tenantId: string | null;
  agencyId: string | null;
  organizationId: string | null;
}

/**
 * Tenant context value with actions
 */
export interface TenantContextValue extends TenantContext {
  setTenantId: (tenantId: string | null) => void;
  setAgencyId: (agencyId: string | null) => void;
  setOrganizationId: (organizationId: string | null) => void;
  clearContext: () => void;
}

/**
 * Local storage keys for tenant context
 */
const STORAGE_KEYS = {
  TENANT_ID: 'agenthr_tenant_id',
  AGENCY_ID: 'agenthr_agency_id',
  ORGANIZATION_ID: 'agenthr_organization_id',
} as const;

/**
 * React context for tenant state (optional, for global state management)
 */
export const TenantContext = createContext<TenantContextValue | null>(null);

/**
 * Hook for managing tenant context in multi-tenant agency mode
 *
 * This hook provides access to the current tenant context (tenant ID, agency ID,
 * organization ID) and methods to update it. The context is persisted to local
 * storage and used to set appropriate headers for API requests.
 *
 * @returns Tenant context state and actions
 *
 * @example
 * ```tsx
 * function ClientSelector() {
 *   const { tenantId, agencyId, setTenantId, setAgencyId } = useTenantContext();
 *
 *   const handleSelectClient = (tenant: ClientTenantResponse) => {
 *     setTenantId(tenant.id);
 *     setAgencyId(tenant.agency_id);
 *   };
 *
 *   return (
 *     <div>
 *       <p>Current Tenant: {tenantId}</p>
 *       <p>Current Agency: {agencyId}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTenantContext(): TenantContextValue {
  // Try to use context first (if available)
  const context = useContext(TenantContext);

  // If context is available, use it
  if (context) {
    return context;
  }

  // Otherwise, use local state (for standalone usage)
  const [tenantId, setTenantIdState] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.TENANT_ID);
  });

  const [agencyId, setAgencyIdState] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.AGENCY_ID);
  });

  const [organizationId, setOrganizationIdState] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(STORAGE_KEYS.ORGANIZATION_ID);
  });

  const setTenantId = useCallback((id: string | null) => {
    setTenantIdState(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem(STORAGE_KEYS.TENANT_ID, id);
      } else {
        localStorage.removeItem(STORAGE_KEYS.TENANT_ID);
      }
    }
  }, []);

  const setAgencyId = useCallback((id: string | null) => {
    setAgencyIdState(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem(STORAGE_KEYS.AGENCY_ID, id);
      } else {
        localStorage.removeItem(STORAGE_KEYS.AGENCY_ID);
      }
    }
  }, []);

  const setOrganizationId = useCallback((id: string | null) => {
    setOrganizationIdState(id);
    if (typeof window !== 'undefined') {
      if (id) {
        localStorage.setItem(STORAGE_KEYS.ORGANIZATION_ID, id);
      } else {
        localStorage.removeItem(STORAGE_KEYS.ORGANIZATION_ID);
      }
    }
  }, []);

  const clearContext = useCallback(() => {
    setTenantId(null);
    setAgencyId(null);
    setOrganizationId(null);
  }, [setTenantId, setAgencyId, setOrganizationId]);

  return {
    tenantId,
    agencyId,
    organizationId,
    setTenantId,
    setAgencyId,
    setOrganizationId,
    clearContext,
  };
}

/**
 * Hook to get current tenant context headers for API requests
 *
 * Returns headers object with X-Tenant-ID and X-Agency-ID if they are set.
 *
 * @returns Headers object for API requests
 *
 * @example
 * ```ts
 * const headers = useTenantHeaders();
 * const response = await fetch('/api/candidates', { headers });
 * ```
 */
export function useTenantHeaders(): Record<string, string> {
  const { tenantId, agencyId } = useTenantContext();

  const headers: Record<string, string> = {};

  if (tenantId) {
    headers['X-Tenant-ID'] = tenantId;
  }

  if (agencyId) {
    headers['X-Agency-ID'] = agencyId;
  }

  return headers;
}
