/**
 * useAuth Hook
 *
 * A custom hook for accessing authentication state and methods.
 * Provides a convenient interface for user authentication, login, logout,
 * registration, and token management.
 *
 * @module hooks/useAuth
 */

import { useAuthContext } from '@/contexts/AuthContext';
import type { AuthContextValue } from '@/contexts/AuthContext';

/**
 * useAuth Hook
 *
 * Provides access to authentication state and methods.
 * This is a convenience wrapper around useAuthContext for a cleaner API.
 * Must be used within an AuthProvider.
 *
 * @returns AuthContextValue object with authentication state and methods
 *
 * @throws Error if used outside of AuthProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, login, logout, isAuthenticated, isLoading } = useAuth();
 *
 *   if (isLoading) {
 *     return <CircularProgress />;
 *   }
 *
 *   if (isAuthenticated) {
 *     return (
 *       <Box>
 *         <Typography>Welcome, {user?.email}</Typography>
 *         <Button onClick={logout}>Logout</Button>
 *       </Box>
 *     );
 *   }
 *
 *   return <LoginPage />;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function LoginForm() {
 *   const { login, error } = useAuth();
 *   const [email, setEmail] = useState('');
 *   const [password, setPassword] = useState('');
 *
 *   const handleSubmit = async (e: FormEvent) => {
 *     e.preventDefault();
 *     try {
 *       await login(email, password);
 *       // Redirect to dashboard
 *     } catch (err) {
 *       // Error is already set in auth state
 *       console.error('Login failed:', error);
 *     }
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       {error && <Alert severity="error">{error}</Alert>}
 *       <TextField
 *         label="Email"
 *         value={email}
 *         onChange={(e) => setEmail(e.target.value)}
 *       />
 *       <TextField
 *         label="Password"
 *         type="password"
 *         value={password}
 *         onChange={(e) => setPassword(e.target.value)}
 *       />
 *       <Button type="submit">Login</Button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function ProtectedRoute({ children }: { children: ReactNode }) {
 *   const { isAuthenticated, isLoading } = useAuth();
 *
 *   if (isLoading) {
 *     return <CircularProgress />;
 *   }
 *
 *   if (!isAuthenticated) {
 *     return <Navigate to="/login" replace />;
 *   }
 *
 *   return <>{children}</>;
 * }
 * ```
 */
export function useAuth(): AuthContextValue {
  return useAuthContext();
}

/**
 * Type export for authentication context value
 *
 * @example
 * ```tsx
 * type AuthContext = AuthContextValue;
 * ```
 */
export type { AuthContextValue };
