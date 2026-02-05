import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import axios from 'axios';

/**
 * Organization branding data structure
 */
export interface OrganizationBranding {
  id: string;
  organization_id: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color?: string;
  text_color?: string;
  font_family?: string;
  logo_url?: string;
  favicon_url?: string;
  is_active: boolean;
}

/**
 * Organization data structure
 */
export interface OrganizationData {
  id: string;
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  is_active: boolean;
}

/**
 * Organization Context State Interface
 */
interface OrganizationState {
  /** Current organization data */
  organization: OrganizationData | null;
  /** Current organization branding settings */
  branding: OrganizationBranding | null;
  /** Loading state */
  loading: boolean;
  /** Error state */
  error: string | null;
  /** Refresh organization data */
  refreshOrganization: () => Promise<void>;
  /** Get primary brand color */
  getPrimaryColor: () => string;
  /** Get secondary brand color */
  getSecondaryColor: () => string;
  /** Get accent brand color */
  getAccentColor: () => string;
  /** Get organization logo URL */
  getLogoUrl: () => string | null;
}

/**
 * Organization Context Props
 */
interface OrganizationProviderProps {
  /** Children components */
  children: ReactNode;
  /** Organization ID to load (optional) */
  organizationId?: string;
}

/**
 * Organization Context
 *
 * Provides organization state and branding data for the application.
 * Handles organization data loading and provides access to branding settings.
 *
 * @example
 * ```tsx
 * // Wrap your app with OrganizationProvider
 * <OrganizationProvider organizationId="org-123">
 *   <App />
 * </OrganizationProvider>
 *
 * // Use in components
 * const { organization, branding, getLogoUrl } = useOrganizationContext();
 *
 * // Display organization name
 * <p>{organization?.name}</p>
 *
 * // Get logo URL
 * <img src={getLogoUrl()} alt="Logo" />
 * ```
 */
const OrganizationContext = createContext<OrganizationState | undefined>(undefined);

/**
 * Organization Provider Component
 *
 * Manages organization state and branding data.
 * Handles organization data loading from the backend API.
 *
 * @param props - Provider props
 * @returns Organization context provider
 */
export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({
  children,
  organizationId,
}) => {
  const [organization, setOrganization] = useState<OrganizationData | null>(null);
  const [branding, setBranding] = useState<OrganizationBranding | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load organization and branding data from backend
   */
  const refreshOrganization = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // If organizationId is provided, load that organization
      // Otherwise, try to get the first active organization
      let targetOrgId = organizationId;

      if (!targetOrgId) {
        try {
          // Get first active organization
          const orgsResponse = await axios.get<{ organizations: OrganizationData[]; total_count: number }>(
            '/api/organizations/',
            { params: { is_active: true, limit: 1 } }
          );

          if (orgsResponse.data.organizations && orgsResponse.data.organizations.length > 0) {
            targetOrgId = orgsResponse.data.organizations[0].id;
            setOrganization(orgsResponse.data.organizations[0]);
          } else {
            // No organization found - use defaults
            setOrganization(null);
            setBranding(null);
            setLoading(false);
            return;
          }
        } catch (orgErr: unknown) {
          const axiosErr = orgErr as { response?: { status?: number } };
          // If 404, organizations API doesn't exist - use defaults
          if (axiosErr.response?.status === 404) {
            console.info('Organizations API not available - using default theme');
            setOrganization(null);
            setBranding(null);
            setLoading(false);
            return;
          }
          throw orgErr;
        }
      } else if (!organization) {
        // Load specific organization
        const orgResponse = await axios.get<OrganizationData>(`/api/organizations/${targetOrgId}`);
        setOrganization(orgResponse.data);
      }

      // Load branding settings for the organization
      if (targetOrgId) {
        try {
          const brandingResponse = await axios.get<{ branding_settings: OrganizationBranding[]; total_count: number }>(
            '/api/branding/',
            { params: { organization_id: targetOrgId, is_active: true, limit: 1 } }
          );

          if (brandingResponse.data.branding_settings && brandingResponse.data.branding_settings.length > 0) {
            setBranding(brandingResponse.data.branding_settings[0]);
          } else {
            setBranding(null);
          }
        } catch (brandingError) {
          // Branding settings are optional, don't fail if not found
          console.warn('No branding settings found for organization:', targetOrgId);
          setBranding(null);
        }
      }
    } catch (err) {
      console.error('Error loading organization data:', err);
      setError('Failed to load organization data');
      setOrganization(null);
      setBranding(null);
    } finally {
      setLoading(false);
    }
  }, [organizationId, organization]);

  /**
   * Load organization data on mount
   */
  useEffect(() => {
    refreshOrganization();
  }, [organizationId]);

  /**
   * Get primary brand color
   * Falls back to default color if not set
   */
  const getPrimaryColor = useCallback((): string => {
    return branding?.primary_color || '#1976d2';
  }, [branding]);

  /**
   * Get secondary brand color
   * Falls back to default color if not set
   */
  const getSecondaryColor = useCallback((): string => {
    return branding?.secondary_color || '#dc004e';
  }, [branding]);

  /**
   * Get accent brand color
   * Falls back to default color if not set
   */
  const getAccentColor = useCallback((): string => {
    return branding?.accent_color || '#F59E0B';
  }, [branding]);

  /**
   * Get organization logo URL
   * Returns null if not set
   */
  const getLogoUrl = useCallback((): string | null => {
    return branding?.logo_url || organization?.logo_url || null;
  }, [branding, organization]);

  const contextValue: OrganizationState = {
    organization,
    branding,
    loading,
    error,
    refreshOrganization,
    getPrimaryColor,
    getSecondaryColor,
    getAccentColor,
    getLogoUrl,
  };

  return (
    <OrganizationContext.Provider value={contextValue}>
      {children}
    </OrganizationContext.Provider>
  );
};

/**
 * useOrganizationContext Hook
 *
 * Access organization context state and functions.
 * Must be used within an OrganizationProvider.
 *
 * @throws Error if used outside of OrganizationProvider
 * @returns Organization context state
 *
 * @example
 * ```tsx
 * const { organization, branding, getLogoUrl, getPrimaryColor } = useOrganizationContext();
 *
 * // Display organization name
 * <h1>{organization?.name}</h1>
 *
 * // Use brand colors
 * <Button style={{ backgroundColor: getPrimaryColor() }}>
 *   Click Me
 * </Button>
 *
 * // Display logo
 * {getLogoUrl() && <img src={getLogoUrl()} alt="Logo" />}
 * ```
 */
export const useOrganizationContext = (): OrganizationState => {
  const context = useContext(OrganizationContext);

  if (context === undefined) {
    throw new Error(
      'useOrganizationContext must be used within an OrganizationProvider. ' +
        'Wrap your component tree with <OrganizationProvider>.'
    );
  }

  return context;
};

export default OrganizationContext;
