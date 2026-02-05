import { useContext } from 'react';
import { useAuth as useOidcAuth } from 'react-oidc-context';

export type UserRole = 'admin' | 'recruiter' | 'job_seeker';

/**
 * Get user roles from the OIDC token
 * Roles can be in different locations in Keycloak tokens:
 * - realm_access.roles - realm-level roles
 * - resource_access.{client}.roles - client-level roles
 * - profile.roles - user profile roles
 */
export const getUserRoles = (): UserRole[] => {
  // Get auth from localStorage (for use outside React components)
  const authKey = Object.keys(localStorage).find(k => k.includes('oidc'));
  if (!authKey) return [];

  const authData = JSON.parse(localStorage.getItem(authKey) || '{}');
  const userProfile = authData?.user?.profile;

  if (!userProfile) return [];

  const roles = new Set<UserRole>();

  // 1. Check realm_access.roles (most common in Keycloak)
  const realmAccess = userProfile?.realm_access;
  if (realmAccess?.roles && Array.isArray(realmAccess.roles)) {
    realmAccess.roles
      .filter((r: string): r is UserRole => ['admin', 'recruiter', 'job_seeker'].includes(r))
      .forEach((role: UserRole) => roles.add(role));
  }

  // 2. Check resource_access for client-specific roles
  const resourceAccess = userProfile?.resource_access;
  if (resourceAccess) {
    Object.keys(resourceAccess).forEach((client) => {
      const clientRoles = resourceAccess[client]?.roles;
      if (clientRoles && Array.isArray(clientRoles)) {
        clientRoles
          .filter((r: string): r is UserRole => ['admin', 'recruiter', 'job_seeker'].includes(r))
          .forEach((role: UserRole) => roles.add(role));
      }
    });
  }

  return Array.from(roles);
};

/**
 * React Hook to get user roles from OIDC auth
 */
export const useUserRoles = (): UserRole[] => {
  const auth = useOidcAuth();

  if (!auth.user || !auth.user?.profile) {
    return [];
  }

  const roles = new Set<UserRole>();

  // 1. Check realm_access.roles
  const realmAccess = auth.user?.profile?.realm_access;
  if (realmAccess?.roles && Array.isArray(realmAccess.roles)) {
    realmAccess.roles
      .filter((r: string): r is UserRole => ['admin', 'recruiter', 'job_seeker'].includes(r))
      .forEach((role: UserRole) => roles.add(role));
  }

  // 2. Check resource_access
  const resourceAccess = auth.user?.profile?.resource_access;
  if (resourceAccess) {
    Object.keys(resourceAccess).forEach((client) => {
      const clientRoles = resourceAccess[client]?.roles;
      if (clientRoles && Array.isArray(clientRoles)) {
        clientRoles
          .filter((r: string): r is UserRole => ['admin', 'recruiter', 'job_seeker'].includes(r))
          .forEach((role: UserRole) => roles.add(role));
      }
    });
  }

  return Array.from(roles);
};

/**
 * Check if user has a specific role
 */
export const hasRole = (role: UserRole): boolean => {
  const roles = getUserRoles();
  return roles.includes(role);
};

/**
 * Check if user has any of the specified roles
 */
export const hasAnyRole = (roles: UserRole[]): boolean => {
  const userRoles = getUserRoles();
  return roles.some(role => userRoles.includes(role));
};

/**
 * Check if user is an admin
 */
export const isAdmin = (): boolean => hasRole('admin');

/**
 * Check if user is a recruiter
 */
export const isRecruiter = (): boolean => hasRole('recruiter');

/**
 * Check if user is a job seeker
 */
export const isJobSeeker = (): boolean => hasRole('job_seeker');

/**
 * React Hook version of role checks
 */
export const useHasRole = (role: UserRole): boolean => {
  const roles = useUserRoles();
  return roles.includes(role);
};

export const useHasAnyRole = (roles: UserRole[]): boolean => {
  const userRoles = useUserRoles();
  return roles.some(role => userRoles.includes(role));
};

export const useIsAdmin = (): boolean => useHasRole('admin');
export const useIsRecruiter = (): boolean => useHasRole('recruiter');
export const useIsJobSeeker = (): boolean => useHasRole('job_seeker');
