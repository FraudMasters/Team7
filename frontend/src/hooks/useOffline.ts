/**
 * useOffline Hook
 *
 * A custom hook for tracking online/offline status.
 * Provides real-time network status detection and automatic
 * reconnection monitoring for offline-capable applications.
 *
 * @module hooks/useOffline
 */

import { useEffect, useState } from 'react';

/**
 * Offline status result
 *
 * Provides current online/offline status and utilities
 * for monitoring network connectivity changes.
 */
export interface OfflineResult {
  /**
   * Current online status
   * - true: Device has network connectivity
   * - false: Device is offline
   */
  online: boolean;

  /**
   * Current offline status (inverse of online)
   * - true: Device is offline
   * - false: Device has network connectivity
   */
  offline: boolean;

  /**
   * Timestamp when the current status was detected
   * Useful for displaying "Last online" information
   */
  since: Date;
}

/**
 * useOffline Hook
 *
 * Tracks the browser's online/offline status using the Navigator API.
 * Automatically updates when network connectivity changes.
 *
 * @returns OfflineResult object with current status information
 *
 * @example
 * ```tsx
 * function NetworkStatus() {
 *   const { online, offline, since } = useOffline();
 *
 *   return (
 *     <Alert severity={online ? 'success' : 'warning'}>
 *       {online ? 'You are online' : 'You are offline'}
 *       <Typography variant="caption" display="block">
 *         Since: {since.toLocaleTimeString()}
 *       </Typography>
 *     </Alert>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * function SaveButton() {
 *   const { online } = useOffline();
 *
 *   const handleSave = async () => {
 *     if (!online) {
 *       // Queue for later sync
 *       queueOfflineAction(saveAction);
 *       return;
 *     }
 *     // Save immediately
 *     await saveData();
 *   };
 *
 *   return <Button onClick={handleSave}>Save</Button>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * function DataSyncIndicator() {
 *   const { offline } = useOffline();
 *
 *   useEffect(() => {
 *     if (offline) {
 *       // Switch to offline mode
 *       enableOfflineMode();
 *     } else {
 *       // Sync pending changes
 *       syncPendingChanges();
 *     }
 *   }, [offline]);
 *
 *   return null;
 * }
 * ```
 */
export function useOffline(): OfflineResult {
  const [status, setStatus] = useState<{ online: boolean; since: Date }>(() => ({
    online: typeof navigator !== 'undefined' ? navigator.onLine : true,
    since: new Date(),
  }));

  useEffect(() => {
    // Skip if navigator is not available (SSR)
    if (typeof navigator === 'undefined' || typeof window === 'undefined') {
      return;
    }

    // Handle online event
    const handleOnline = () => {
      setStatus({
        online: true,
        since: new Date(),
      });
    };

    // Handle offline event
    const handleOffline = () => {
      setStatus({
        online: false,
        since: new Date(),
      });
    };

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup event listeners on unmount
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Memoize result to prevent unnecessary re-renders
  const result: OfflineResult = {
    online: status.online,
    offline: !status.online,
    since: status.since,
  };

  return result;
}

export default useOffline;
