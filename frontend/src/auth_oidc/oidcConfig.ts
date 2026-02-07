/**
 * OIDC Configuration for Keycloak
 *
 * This configuration is used by react-oidc-context to connect
 * to the Keycloak authentication server.
 *
 * Environment variables (set in .env):
 * - VITE_OIDC_AUTHORITY: Keycloak URL (e.g., http://localhost:8080/realms/agenthr)
 * - VITE_OIDC_CLIENT_ID: OIDC Client ID
 * - VITE_OIDC_REDIRECT_URI: Where Keycloak redirects after auth (default: /callback)
 */

const oidcConfig = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY || 'http://localhost:8080/realms/agenthr',
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID || 'agenthr-frontend',
  redirect_uri: window.location.origin + '/callback',
  post_logout_redirect_uri: window.location.origin,
  response_type: 'code' as const,
  scope: 'openid profile email',
  automaticSilentRenew: true,
  loadUserInfo: true,
};

export default oidcConfig;
