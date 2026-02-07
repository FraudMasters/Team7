/**
 * OIDC Configuration for Keycloak
 */
const oidcConfig = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY || 'http://localhost:8080/realms/agenthr',
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID || 'agenthr-frontend',
  redirect_uri: window.location.origin + '/callback',
  post_logout_redirect_uri: window.location.origin,
  response_type: 'code' as const,
  scope: 'openid profile email roles',
  automaticSilentRenew: true,
  loadUserInfo: true,
};

export default oidcConfig;
