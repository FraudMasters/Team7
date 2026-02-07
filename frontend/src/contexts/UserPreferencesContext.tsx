import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import * as preferencesAPI from '@/api/preferences';
import type {
  UserProfileResponse,
  DashboardConfigResponse,
  FilterPreferencesResponse,
  ApiKeyResponse,
  ApiKeyCreate,
} from '@/types/api';

/**
 * User Preferences Context State Interface
 */
interface UserPreferencesState {
  /** User profile information */
  profile: UserProfileResponse | null;
  /** Dashboard configuration */
  dashboardConfig: DashboardConfigResponse | null;
  /** Filter preferences */
  filterPreferences: FilterPreferencesResponse | null;
  /** List of API keys */
  apiKeys: ApiKeyResponse[];
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: string | null;
  /** Fetch all preferences */
  fetchAllPreferences: () => Promise<void>;
  /** Update user profile */
  updateProfile: (profileData: Partial<UserProfileResponse>) => Promise<UserProfileResponse>;
  /** Update dashboard configuration */
  updateDashboardConfig: (configData: Record<string, unknown>) => Promise<DashboardConfigResponse>;
  /** Update filter preferences */
  updateFilterPreferences: (filtersData: Record<string, unknown>) => Promise<FilterPreferencesResponse>;
  /** Create API key */
  createApiKey: (keyData: ApiKeyCreate) => Promise<ApiKeyResponse>;
  /** Delete API key */
  deleteApiKey: (keyId: string) => Promise<void>;
  /** Refresh API keys list */
  refreshApiKeys: () => Promise<void>;
}

/**
 * User Preferences Context Props
 */
interface UserPreferencesProviderProps {
  /** Children components */
  children: ReactNode;
  /** Whether to fetch preferences on mount (default: true) */
  fetchOnMount?: boolean;
}

/**
 * User Preferences Context
 *
 * Provides user profile and preferences state management for the application.
 * Integrates with backend preferences API for data persistence.
 *
 * @example
 * ```tsx
 * // Wrap your app with UserPreferencesProvider
 * <UserPreferencesProvider>
 *   <App />
 * </UserPreferencesProvider>
 *
 * // Use in components
 * const { profile, updateProfile, dashboardConfig } = useUserPreferences();
 *
 * // Update profile
 * await updateProfile({ name: 'John Doe', role: 'recruiter' });
 * ```
 */
const UserPreferencesContext = createContext<UserPreferencesState | undefined>(undefined);

/**
 * User Preferences Provider Component
 *
 * Manages user profile and preferences state.
 * Handles fetching and updating preferences data.
 *
 * @param props - Provider props
 * @returns User preferences context provider
 */
export const UserPreferencesProvider: React.FC<UserPreferencesProviderProps> = ({
  children,
  fetchOnMount = true,
}) => {
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [dashboardConfig, setDashboardConfig] = useState<DashboardConfigResponse | null>(null);
  const [filterPreferences, setFilterPreferences] = useState<FilterPreferencesResponse | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKeyResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch all user preferences
   *
   * Loads profile, dashboard config, filter preferences, and API keys.
   */
  const fetchAllPreferences = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all preferences in parallel
      const [profileData, dashboardData, filtersData, keysData] = await Promise.all([
        preferencesAPI.getUserProfile().catch((err) => {
          // Log error but don't fail entire operation
          console.warn('Failed to fetch user profile:', err);
          return null;
        }),
        preferencesAPI.getDashboardConfig().catch((err) => {
          console.warn('Failed to fetch dashboard config:', err);
          return null;
        }),
        preferencesAPI.getFilterPreferences().catch((err) => {
          console.warn('Failed to fetch filter preferences:', err);
          return null;
        }),
        preferencesAPI.listApiKeys().catch((err) => {
          console.warn('Failed to fetch API keys:', err);
          return { api_keys: [] };
        }),
      ]);

      if (profileData) setProfile(profileData);
      if (dashboardData) setDashboardConfig(dashboardData);
      if (filtersData) setFilterPreferences(filtersData);
      if (keysData) setApiKeys(keysData.api_keys || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch preferences';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch preferences on mount if enabled
   */
  useEffect(() => {
    if (fetchOnMount) {
      fetchAllPreferences();
    }
  }, [fetchOnMount, fetchAllPreferences]);

  /**
   * Update user profile
   *
   * @param profileData - Profile fields to update
   * @returns Updated profile data
   */
  const updateProfile = useCallback(
    async (profileData: Partial<UserProfileResponse>): Promise<UserProfileResponse> => {
      try {
        const updated = await preferencesAPI.updateUserProfile(profileData);
        setProfile(updated);
        return updated;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update profile';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Update dashboard configuration
   *
   * @param configData - Dashboard configuration fields to update
   * @returns Updated dashboard configuration
   */
  const updateDashboardConfig = useCallback(
    async (configData: Record<string, unknown>): Promise<DashboardConfigResponse> => {
      try {
        const updated = await preferencesAPI.updateDashboardConfig(configData);
        setDashboardConfig(updated);
        return updated;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update dashboard configuration';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Update filter preferences
   *
   * @param filtersData - Filter preferences to set
   * @returns Updated filter preferences
   */
  const updateFilterPreferences = useCallback(
    async (filtersData: Record<string, unknown>): Promise<FilterPreferencesResponse> => {
      try {
        const updated = await preferencesAPI.updateFilterPreferences(filtersData);
        setFilterPreferences(updated);
        return updated;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update filter preferences';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Create a new API key
   *
   * @param keyData - API key creation data
   * @returns Created API key
   */
  const createApiKey = useCallback(async (keyData: ApiKeyCreate): Promise<ApiKeyResponse> => {
    try {
      const newKey = await preferencesAPI.createApiKey(keyData);
      setApiKeys((prev) => [...prev, newKey]);
      return newKey;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create API key';
      setError(message);
      throw err;
    }
  }, []);

  /**
   * Delete an API key
   *
   * @param keyId - API key ID to delete
   */
  const deleteApiKey = useCallback(async (keyId: string): Promise<void> => {
    try {
      await preferencesAPI.deleteApiKey(keyId);
      setApiKeys((prev) => prev.filter((key) => key.id !== keyId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete API key';
      setError(message);
      throw err;
    }
  }, []);

  /**
   * Refresh API keys list
   */
  const refreshApiKeys = useCallback(async (): Promise<void> => {
    try {
      const data = await preferencesAPI.listApiKeys();
      setApiKeys(data.api_keys || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh API keys';
      setError(message);
      throw err;
    }
  }, []);

  const contextValue: UserPreferencesState = {
    profile,
    dashboardConfig,
    filterPreferences,
    apiKeys,
    isLoading,
    error,
    fetchAllPreferences,
    updateProfile,
    updateDashboardConfig,
    updateFilterPreferences,
    createApiKey,
    deleteApiKey,
    refreshApiKeys,
  };

  return (
    <UserPreferencesContext.Provider value={contextValue}>
      {children}
    </UserPreferencesContext.Provider>
  );
};

/**
 * useUserPreferences Hook
 *
 * Access user preferences context state and functions.
 * Must be used within a UserPreferencesProvider.
 *
 * @throws Error if used outside of UserPreferencesProvider
 * @returns User preferences context state
 *
 * @example
 * ```tsx
 * const { profile, updateProfile, dashboardConfig, isLoading } = useUserPreferences();
 *
 * // Display user profile
 * <p>Welcome, {profile?.name}</p>
 *
 * // Update profile on button click
 * <button onClick={() => updateProfile({ name: 'John' })}>
 *   Update Name
 * </button>
 * ```
 */
export const useUserPreferences = (): UserPreferencesState => {
  const context = useContext(UserPreferencesContext);

  if (context === undefined) {
    throw new Error(
      'useUserPreferences must be used within a UserPreferencesProvider. ' +
        'Wrap your component tree with <UserPreferencesProvider>.'
    );
  }

  return context;
};

export default UserPreferencesContext;
