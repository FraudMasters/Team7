/**
 * Query Persister Utility
 *
 * Provides a React Query persister using IndexedDB for offline cache persistence.
 * This enables React Query to restore cached data from browser storage,
 * allowing the app to display previously fetched data while offline.
 *
 * @module utils/queryPersister
 *
 * @example
 * ```ts
 * import { persistQueryClient } from '@tanstack/react-query-persist-client';
 * import { persister } from '@/utils/queryPersister';
 *
 * persistQueryClient({
 *   queryClient: queryClient,
 *   persister: persister,
 * });
 * ```
 */

import { IDBPDatabase, openDB } from 'idb';

/**
 * IndexedDB database and store names
 */
const DB_NAME = 'react-query-persist';
const STORE_NAME = 'queries';

/**
 * Stored query data
 */
interface StoredQuery {
  buster: string;
  data: Array<[string, { state: unknown; queryKey: unknown[] }]>;
}

/**
 * React Query Persister using IndexedDB
 *
 * Persists and restores React Query cache using IndexedDB.
 * Implements the Persister interface required by @tanstack/react-query-persist-client.
 */
export const persister = {
  /**
   * Persist query client data to IndexedDB
   *
   * @param client - React Query client data to persist
   * @returns Promise that resolves when data is persisted
   */
  async persist(client: StoredQuery): Promise<void> {
    try {
      const db = await getDatabase();
      await db.put(STORE_NAME, client, 'react-query');
    } catch (error) {
      console.error('[QueryPersister] Error persisting query data:', error);
    }
  },

  /**
   * Restore query client data from IndexedDB
   *
   * @returns Promise resolving to stored client data or undefined if not found
   */
  async restore(): Promise<StoredQuery | undefined> {
    try {
      const db = await getDatabase();
      const data = await db.get<StoredQuery>(STORE_NAME, 'react-query');

      // Validate restored data structure
      if (data && Array.isArray(data.data)) {
        return data;
      }

      return undefined;
    } catch (error) {
      console.error('[QueryPersister] Error restoring query data:', error);
      return undefined;
    }
  },

  /**
   * Remove persisted query data from IndexedDB
   *
   * @returns Promise that resolves when data is removed
   */
  async remove(): Promise<void> {
    try {
      const db = await getDatabase();
      await db.delete(STORE_NAME, 'react-query');
    } catch (error) {
      console.error('[QueryPersister] Error removing query data:', error);
    }
  },
};

/**
 * Database connection cache
 */
let databasePromise: Promise<IDBPDatabase> | null = null;

/**
 * Get or create IndexedDB database connection
 *
 * Opens (or creates) the IndexedDB database for persisting React Query cache.
 * Connection is cached to avoid opening multiple connections.
 *
 * @returns Promise resolving to IndexedDB database instance
 */
function getDatabase(): Promise<IDBPDatabase> {
  if (databasePromise) {
    return databasePromise;
  }

  databasePromise = openDB(DB_NAME, 1, {
    upgrade(database) {
      // Create object store if it doesn't exist
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME);
      }
    },
    blocked() {
      console.warn(
        '[QueryPersister] Database is blocked. Close other tabs and try again.'
      );
    },
    blocking() {
      console.warn(
        '[QueryPersister] This connection is blocking the database from upgrading.'
      );
    },
  });

  return databasePromise;
}

/**
 * Export persister as default
 */
export default persister;
