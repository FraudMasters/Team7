import React, { createContext, useContext, ReactNode } from 'react';
import { AuthProvider, useAuth as useOidcAuth } from 'react-oidc-context';
import type { User } from 'oidc-client-ts';

/**
 * User roles in the system
 */
export type UserRole = 'Admin' | 'Recruiter' | 'Viewer';

/**
 * Authentication state interface
 */
export interface AuthState {
  /** Current authenticated user */
  user: User | null;
  /** Whether user is currently authenticated */
  isAuthenticated: boolean;
  /** Whether authentication is still loading */
  isLoading: boolean;
  /** Error from authentication */
  error: Error | undefined;
  /** User's roles */
  roles: UserRole[];
  /** Trigger user login */
  login: () => void;
  /** Trigger user logout */
  logout: () => void;
  /** Check if user has a specific role */
  hasRole: (role: UserRole) => boolean;
  /** Check if user has any of the specified roles */
  hasAnyRole: (roles: UserRole[]) => boolean;
  /** Check if user has all of the specified roles */
  hasAllRoles: (roles: UserRole[]) => boolean;
}

/**
 * OIDC Configuration for Keycloak
 *
 * Configuration object for react-oidc-context to connect with Keycloak.
 * Uses environment variables for flexible deployment across environments.
 *
 * Environment variables:
 * - VITE_KEYCLOAK_URL: Keycloak server URL (default: http://localhost:8080)
 * - VITE_KEYCLOAK_REALM: Keycloak realm name (default: agenthr)
 * - VITE_KEYCLOAK_CLIENT_ID: OIDC client ID (default: agenthr-frontend)
 */
export const oidcConfig = {
  /** Keycloak realm URL */
  authority: import.meta.env.VITE_KEYCLOAK_URL
    ? `${import.meta.env.VITE_KEYCLOAK_URL}/realms/${import.meta.env.VITE_KEYCLOAK_REALM || 'agenthr'}`
    : 'http://localhost:8080/realms/agenthr',
  /** OIDC client ID from Keycloak */
  client_id: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'agenthr-frontend',
  /** Where to redirect after authentication */
  redirect_uri: window.location.origin + '/callback',
  /** Where to redirect after logout */
  post_logout_redirect_uri: window.location.origin,
  /** OIDC flow: authorization code flow (recommended for public clients) */
  response_type: 'code' as const,
  /** OAuth 2.0 scopes to request */
  scope: 'openid profile email',
  /** Enable automatic silent token renew before expiration */
  automaticSilentRenew: true,
  /** Include ID token in silent renew requests */
  includeIdTokenInSilentRenew: true,
  /** Monitor user session for changes (logout in another tab) */
  monitorSession: true,
  /** Check session interval in seconds */
  checkSessionIntervalInSeconds: 10,
  /** Load user profile from userinfo endpoint */
  loadUserInfo: true,
};

/**
 * Extract roles from Keycloak JWT token
 *
 * Keycloak stores realm roles in the resource_access claim of the JWT token.
 * This function extracts and validates roles for the frontend client.
 *
 * @param user - Authenticated user object from oidc-client-ts
 * @returns Array of validated user roles
 */
function extractUserRoles(user: User | null): UserRole[] {
  if (!user) {
    return [];
  }

  try {
    // Access the resource_access claim from JWT token
    const resourceAccess = user.profile.resource_access as Record<string, { roles: string[] }>;

    // Get roles for our client
    const clientId = oidcConfig.client_id;
    const clientRoles = resourceAccess?.[clientId]?.roles || [];

    // Validate roles against allowed values
    const validRoles: UserRole[] = ['Admin', 'Recruiter', 'Viewer'];
    const roles = clientRoles.filter((role): role is UserRole =>
      validRoles.includes(role as UserRole)
    );

    return roles;
  } catch (error) {
    // Log warning but don't fail authentication
    console.warn('Failed to extract user roles from token:', error);
    return [];
  }
}

/**
 * Authentication Context
 *
 * React context for authentication state and role-based access control.
 * Wraps react-oidc-context to provide Keycloak authentication.
 */
const AuthContext = createContext<AuthState | undefined>(undefined);

/**
 * Authentication Provider Props
 */
interface AuthProviderProps {
  /** Children components */
  children: ReactNode;
}

/**
 * Authentication Provider Component
 *
 * Wraps react-oidc-context AuthProvider and adds role-based access control.
 * Manages authentication state with Keycloak using OIDC protocol.
 *
 * @example
 * ```tsx
 * // Wrap your app with AuthContextProvider
 * <AuthContextProvider>
 *   <App />
 * </AuthContextProvider>
 *
 * // Use in components
 * const { user, isAuthenticated, login, logout, hasRole } = useAuthContext();
 *
 * // Trigger login
 * <button onClick={login}>Login</button>
 *
 * // Check authentication
 * {isAuthenticated ? <Welcome /> : <Login />}
 *
 * // Role-based rendering
 * {hasRole('Admin') && <AdminPanel />}
 * ```
 */
export const AuthenticationProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Get auth state from react-oidc-context
  const auth = useOidcAuth();

  // Extract user roles from JWT token
  const roles = extractUserRoles(auth.user);

  /**
   * Trigger login redirect to Keycloak
   * Redirects user to Keycloak login page and back to callback URL
   */
  const login = () => {
    auth.signinRedirect();
  };

  /**
   * Trigger logout and redirect to Keycloak
   * Logs out from Keycloak and redirects to post_logout_redirect_uri
   */
  const logout = () => {
    auth.signoutRedirect();
  };

  /**
   * Check if user has a specific role
   *
   * @param role - Role to check
   * @returns True if user has the role
   */
  const hasRole = (role: UserRole): boolean => {
    return roles.includes(role);
  };

  /**
   * Check if user has any of the specified roles
   *
   * @param roleList - List of roles to check
   * @returns True if user has at least one of the roles
   */
  const hasAnyRole = (roleList: UserRole[]): boolean => {
    return roleList.some((role) => roles.includes(role));
  };

  /**
   * Check if user has all of the specified roles
   *
   * @param roleList - List of roles to check
   * @returns True if user has all the roles
   */
  const hasAllRoles = (roleList: UserRole[]): boolean => {
    return roleList.every((role) => roles.includes(role));
  };

  // Context value with authentication state and functions
  const contextValue: AuthState = {
    user: auth.user,
    isAuthenticated: !!auth.user,
    isLoading: auth.isLoading,
    error: auth.error,
    roles,
    login,
    logout,
    hasRole,
    hasAnyRole,
    hasAllRoles,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Higher-Order Auth Provider
 *
 * Combines react-oidc-context AuthProvider with our custom AuthenticationProvider.
 * Use this to wrap your application.
 *
 * @example
 * ```tsx
 * <AuthContextProvider>
 *   <App />
 * </AuthContextProvider>
 * ```
 */
export const AuthContextProvider: React.FC<AuthProviderProps> = ({ children }) => {
  return (
    <AuthProvider {...oidcConfig}>
      <AuthenticationProvider>
        {children}
      </AuthenticationProvider>
    </AuthProvider>
  );
};

/**
 * useAuthContext Hook
 *
 * Access authentication context state and functions.
 * Must be used within an AuthContextProvider.
 *
 * @throws Error if used outside of AuthContextProvider
 * @returns Authentication context state
 *
 * @example
 * ```tsx
 * const { user, isAuthenticated, login, logout, hasRole } = useAuthContext();
 *
 * // Display user info
 * <p>Welcome, {user?.profile.preferred_username}</p>
 *
 * // Login button
 * <button onClick={login}>Login</button>
 *
 * // Logout button
 * <button onClick={logout}>Logout</button>
 *
 * // Role-based rendering
 * {hasRole('Admin') && <AdminPanel />}
 *
 * // Check multiple roles
 * {hasAnyRole(['Admin', 'Recruiter']) && <HiringWorkflow />}
 * ```
 */
export const useAuthContext = (): AuthState => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error(
      'useAuthContext must be used within an AuthContextProvider. ' +
        'Wrap your component tree with <AuthContextProvider>.'
    );
  }

  return context;
};

/**
 * Higher-Order Component for Authentication
 *
 * Wraps a component to require authentication.
 * Redirects to login if user is not authenticated.
 *
 * @example
 * ```tsx
 * const ProtectedComponent = withAuth(({ user }) => {
 *   return <div>Welcome {user?.profile.email}</div>;
 * });
 * ```
 */
export function withAuth<P extends object>(
  Component: React.ComponentType<P & { user: User | null }>
): React.ComponentType<P> {
  return function AuthenticatedComponent(props: P) {
    const { user, isAuthenticated, isLoading } = useAuthContext();

    if (isLoading) {
      return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
      return <div>Please log in to access this feature.</div>;
    }

    return <Component {...props} user={user} />;
  };
}

/**
 * Higher-Order Component for Role-Based Access
 *
 * Wraps a component to require specific roles.
 * Shows error message if user lacks required roles.
 *
 * @param requiredRoles - Single role or array of roles required
 * @returns HOC function
 *
 * @example
 * ```tsx
 * const AdminOnlyComponent = withRole('Admin')(({ user }) => {
 *   return <div>Admin Panel</div>;
 * });
 *
 * const MultiRoleComponent = withRole(['Admin', 'Recruiter'])(({ user }) => {
 *   return <div>Hiring Workflow</div>;
 * });
 * ```
 */
export function withRole<P extends object>(
  requiredRoles: UserRole | UserRole[]
): (Component: React.ComponentType<P>) => React.ComponentType<P> {
  return function RoleProtectedComponent(Component: React.ComponentType<P>) {
    return function ProtectedComponent(props: P) {
      const { user, isAuthenticated, isLoading, hasAnyRole, hasRole } = useAuthContext();

      if (isLoading) {
        return <div>Loading...</div>;
      }

      if (!isAuthenticated) {
        return <div>Please log in to access this feature.</div>;
      }

      const hasRequiredRole = Array.isArray(requiredRoles)
        ? hasAnyRole(requiredRoles)
        : hasRole(requiredRoles);

      if (!hasRequiredRole) {
        return <div>You do not have permission to access this feature.</div>;
      }

      return <Component {...props} />;
    };
  };
}

export default AuthContext;
