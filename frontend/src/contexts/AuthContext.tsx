import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { login as apiLogin, register as apiRegister, logout as apiLogout, refreshToken as apiRefreshToken } from '@/api/auth';
import type { UserRole } from '@/hooks/useRoles';

/**
 * User role type for role-based access control
 *
 * Standardized role names following PascalCase convention.
 * - JobSeeker: Can browse and apply for jobs
 * - Recruiter: Can manage vacancies and candidates
 * - Admin: Has superuser privileges and can access all routes
 */
export type { UserRole };

/**
 * User information interface
 *
 * Represents the authenticated user with their associated data.
 */
export interface UserInfo {
  /** User's unique identifier */
  id: string;
  /** User's email address */
  email: string;
  /** User's full name (optional) */
  full_name?: string;
  /** Roles assigned to the user */
  roles?: UserRole[];
  /** User's profile information from OIDC */
  profile?: {
    preferred_username?: string;
    name?: string;
    email?: string;
    sub?: string;
  };
}

/**
 * Login response from API
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: UserInfo;
}

/**
 * Register response from API
 */
export interface RegisterResponse {
  message: string;
  user: UserInfo;
}

/**
 * Local storage keys for authentication persistence
 */
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'auth_user';

/**
 * Authentication Context State Interface
 */
interface AuthState {
  /** Current authenticated user */
  user: UserInfo | null;
  /** Access token for API requests */
  accessToken: string | null;
  /** Refresh token for obtaining new access tokens */
  refreshToken: string | null;
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Whether authentication state is loading */
  isLoading: boolean;
  /** Whether authentication state has been initialized */
  isInitialized: boolean;
  /** Authentication error message */
  error: string | null;
}

/**
 * Authentication Context Actions Interface
 */
interface AuthActions {
  /** Register a new user */
  register: (email: string, password: string, fullName?: string) => Promise<RegisterResponse>;
  /** Login with email and password */
  login: (email: string, password: string) => Promise<LoginResponse>;
  /** Logout and clear auth state */
  logout: () => Promise<void>;
  /** Refresh access token */
  refreshAccessToken: () => Promise<void>;
  /** Clear authentication error */
  clearError: () => void;
  /** Check if user has a specific role */
  hasRole: (role: UserRole) => boolean;
  /** Check if user has at least one of the specified roles */
  hasAnyRole: (roles: UserRole[]) => boolean;
  /** Whether authentication state has been initialized */
  isInitialized: boolean;
}

/**
 * Combined Authentication Context Interface
 */
interface AuthContextValue extends AuthState, AuthActions {}

/**
 * Authentication Context Props
 */
interface AuthProviderProps {
  /** Children components */
  children: ReactNode;
}

/**
 * Get initial authentication state from localStorage
 */
const getInitialAuthState = (): Partial<AuthState> => {
  try {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);

    const user = userStr ? JSON.parse(userStr) : null;

    return {
      accessToken,
      refreshToken,
      user,
      isAuthenticated: !!accessToken && !!user,
      isLoading: false,
      error: null,
    };
  } catch (error) {
    // If localStorage is corrupted, clear it and return default state
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    return {
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    };
  }
};

/**
 * Authentication Context
 *
 * Provides authentication state and management for the application.
 * Handles user registration, login, logout, token refresh, and auth state persistence.
 *
 * @example
 * ```tsx
 * // Wrap your app with AuthProvider
 * <AuthProvider>
 *   <App />
 * </AuthProvider>
 *
 * // Use in components
 * const { user, login, logout, isAuthenticated } = useAuthContext();
 *
 * // Login
 * await login('user@example.com', 'password123');
 *
 * // Logout
 * await logout();
 *
 * // Check authentication
 * if (isAuthenticated) {
 *   console.log('Logged in as:', user?.email);
 * }
 * ```
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Authentication Provider Component
 *
 * Manages application authentication state and provides auth functionality.
 * Handles authentication changes and persists auth state to localStorage.
 * Automatically refreshes access tokens when they expire.
 *
 * @param props - Provider props
 * @returns Authentication context provider
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
}) => {
  const initialState = getInitialAuthState();

  const [user, setUser] = useState<UserInfo | null>(initialState.user || null);
  const [accessToken, setAccessToken] = useState<string | null>(initialState.accessToken || null);
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(initialState.refreshToken || null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInitialized, setIsInitialized] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Initialize authentication state
   * Sets isInitialized to true after checking localStorage
   */
  useEffect(() => {
    // Small delay to ensure smooth loading state
    const timer = setTimeout(() => {
      setIsInitialized(true);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  /**
   * Update localStorage with auth state
   */
  const updateStorage = useCallback((
    newAccessToken: string | null,
    newRefreshToken: string | null,
    newUser: UserInfo | null
  ) => {
    try {
      if (newAccessToken) {
        localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
      } else {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
      }

      if (newRefreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
      } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      }

      if (newUser) {
        localStorage.setItem(USER_KEY, JSON.stringify(newUser));
      } else {
        localStorage.removeItem(USER_KEY);
      }
    } catch (storageError) {
      // Log error but don't throw - UI already updated
      console.warn('Failed to persist auth state to localStorage:', storageError);
    }
  }, []);

  /**
   * Register a new user
   *
   * Creates a new user account with the provided credentials.
   * After successful registration, the user is logged in automatically.
   *
   * @param email - User's email address
   * @param password - User's password
   * @param fullName - User's full name (optional)
   * @returns Promise resolving to registration response
   */
  const register = useCallback(async (
    email: string,
    password: string,
    fullName?: string
  ): Promise<RegisterResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiRegister({
        email,
        password,
        full_name: fullName,
      });

      // Note: Registration doesn't return tokens by default
      // User needs to login after registration
      setIsLoading(false);

      return response;
    } catch (err) {
      setIsLoading(false);
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      throw err;
    }
  }, []);

  /**
   * Login with email and password
   *
   * Authenticates a user and stores the received tokens.
   *
   * @param email - User's email address
   * @param password - User's password
   * @returns Promise resolving to login response with tokens
   */
  const login = useCallback(async (
    email: string,
    password: string
  ): Promise<LoginResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiLogin(email, password);

      // Update state
      setUser(response.user);
      setAccessToken(response.access_token);
      setRefreshTokenValue(response.refresh_token);

      // Persist to localStorage
      updateStorage(
        response.access_token,
        response.refresh_token,
        response.user
      );

      setIsLoading(false);

      return response;
    } catch (err) {
      setIsLoading(false);
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    }
  }, [updateStorage]);

  /**
   * Logout and clear auth state
   *
   * Invalidates the refresh token on the server and clears all auth state.
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Call logout API if we have a refresh token
      if (refreshTokenValue) {
        await apiLogout(refreshTokenValue);
      }
    } catch (err) {
      // Log error but continue with cleanup
      console.warn('Logout API call failed:', err);
    } finally {
      // Clear state regardless of API call success
      setUser(null);
      setAccessToken(null);
      setRefreshTokenValue(null);

      // Clear localStorage
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);

      setIsLoading(false);
    }
  }, [refreshTokenValue]);

  /**
   * Refresh access token
   *
   * Obtains a new access token using the refresh token.
   * Called automatically when the access token expires.
   */
  const refreshAccessToken = useCallback(async () => {
    if (!refreshTokenValue) {
      throw new Error('No refresh token available');
    }

    setError(null);

    try {
      const response = await apiRefreshToken(refreshTokenValue);

      // Update access token (keep the same refresh token)
      setAccessToken(response.access_token);

      // Update localStorage
      localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);

      return response;
    } catch (err) {
      // If refresh fails, clear auth state (token likely expired or revoked)
      const errorMessage = err instanceof Error ? err.message : 'Token refresh failed';
      setError(errorMessage);

      // Clear auth state on refresh failure
      setUser(null);
      setAccessToken(null);
      setRefreshTokenValue(null);
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);

      throw err;
    }
  }, [refreshTokenValue]);

  /**
   * Clear authentication error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Check if user has a specific role
   *
   * @param role - Role to check
   * @returns true if user has the role
   */
  const hasRole = useCallback((role: UserRole): boolean => {
    if (!user?.roles) return false;
    return user.roles.includes(role);
  }, [user]);

  /**
   * Check if user has at least one of the specified roles
   *
   * @param roles - Array of roles to check
   * @returns true if user has at least one of the roles
   */
  const hasAnyRole = useCallback((roles: UserRole[]): boolean => {
    if (!user?.roles) return false;
    return roles.some(role => user.roles?.includes(role));
  }, [user]);

  const contextValue: AuthContextValue = {
    user,
    accessToken,
    refreshToken: refreshTokenValue,
    isAuthenticated: !!accessToken && !!user,
    isLoading,
    isInitialized,
    error,
    register,
    login,
    logout,
    refreshAccessToken,
    clearError,
    hasRole,
    hasAnyRole,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * useAuthContext Hook
 *
 * Access authentication context state and functions.
 * Must be used within an AuthProvider.
 *
 * @throws Error if used outside of AuthProvider
 * @returns Authentication context state
 *
 * @example
 * ```tsx
 * const { user, login, logout, isAuthenticated, isLoading, hasRole, hasAnyRole } = useAuthContext();
 *
 * // Display user info
 * {user && <p>Welcome, {user.email}</p>}
 *
 * // Login form
 * <button onClick={() => login(email, password)}>
 *   Login
 * </button>
 *
 * // Logout button
 * <button onClick={logout}>
 *   Logout
 * </button>
 *
 * // Show loading state
 * {isLoading && <p>Loading...</p>}
 *
 * // Check user role
 * {hasRole('Admin') && <AdminPanel />}
 *
 * // Check if user has any of the specified roles
 * {hasAnyRole(['Recruiter', 'Admin']) && <RecruiterFeatures />}
 * ```
 */
export const useAuthContext = (): AuthContextValue => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error(
      'useAuthContext must be used within an AuthProvider. ' +
        'Wrap your component tree with <AuthProvider>.'
    );
  }

  return context;
};

export default AuthContext;
