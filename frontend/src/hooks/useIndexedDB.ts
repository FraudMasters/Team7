/**
 * useIndexedDB Hook
 *
 * A custom hook for IndexedDB database operations using the idb library.
 * Provides a simplified interface for common IndexedDB operations including
 * get, put, delete, and clear operations on object stores.
 *
 * @module hooks/useIndexedDB
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { useCallback, useEffect, useState, useRef } from 'react';

/**
 * Database configuration options
 *
 * @interface UseIndexedDBOptions
 */
export interface UseIndexedDBOptions<T> {
  /**
   * Name of the database
   */
  dbName: string;

  /**
   * Version of the database schema
   * @default 1
   */
  version?: number;

  /**
   * Name of the object store (table)
   */
  storeName: string;

  /**
   * Key path for the object store (if using inline keys)
   * If not provided, uses out-of-line keys with auto-increment
   */
  keyPath?: string;

  /**
   * Array of indexes to create on the object store
   */
  indexes?: Array<{
    name: string;
    keyPath: string | string[];
    options?: IDBIndexParameters;
  }>;
}

/**
 * Result object returned by useIndexedDB hook
 *
 * Provides methods for database operations and state tracking
 *
 * @interface UseIndexedDBResult
 */
export interface UseIndexedDBResult<T> {
  /**
   * Indicates whether the database is ready for operations
   * - false: Database not yet opened or error occurred
   * - true: Database ready for operations
   */
  isReady: boolean;

  /**
   * Error that occurred during database operations (if any)
   */
  error: Error | null;

  /**
   * Retrieve a value from the object store by key
   *
   * @param key - The key of the value to retrieve
   * @returns Promise resolving to the value, or undefined if not found
   *
   * @example
   * ```ts
   * const { get } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * const user = await get('user-123');
   * ```
   */
  get: (key: IDBValidKey) => Promise<T | undefined>;

  /**
   * Retrieve all values from the object store
   *
   * @returns Promise resolving to an array of all values
   *
   * @example
   * ```ts
   * const { getAll } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * const users = await getAll();
   * ```
   */
  getAll: () => Promise<T[]>;

  /**
   * Store a value in the object store
   *
   * @param value - The value to store
   * @param key - Optional key (required if store uses out-of-line keys)
   * @returns Promise resolving to the key of the stored value
   *
   * @example
   * ```ts
   * const { put } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * await put({ id: 'user-123', name: 'John' });
   * ```
   */
  put: (value: T, key?: IDBValidKey) => Promise<IDBValidKey>;

  /**
   * Delete a value from the object store by key
   *
   * @param key - The key of the value to delete
   * @returns Promise resolving when deletion is complete
   *
   * @example
   * ```ts
   * const { delete: deleteItem } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * await deleteItem('user-123');
   * ```
   */
  delete: (key: IDBValidKey) => Promise<void>;

  /**
   * Clear all values from the object store
   *
   * @returns Promise resolving when clearing is complete
   *
   * @example
   * ```ts
   * const { clear } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * await clear(); // All users deleted
   * ```
   */
  clear: () => Promise<void>;

  /**
   * Count the number of values in the object store
   *
   * @returns Promise resolving to the count of values
   *
   * @example
   * ```ts
   * const { count } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * const userCount = await count();
   * ```
   */
  count: () => Promise<number>;

  /**
   * Get multiple values by their keys
   *
   * @param keys - Array of keys to retrieve
   * @returns Promise resolving to an array of values (undefined for missing keys)
   *
   * @example
   * ```ts
   * const { getMany } = useIndexedDB({ dbName: 'myDB', storeName: 'users' });
   * const users = await getMany(['user-1', 'user-2', 'user-3']);
   * ```
   */
  getMany: (keys: IDBValidKey[]) => Promise<(T | undefined)[]>;
}

/**
 * Database schema type for type safety
 *
 * @template T - Type of values stored in the object store
 */
export type IndexedDBSchema<T> = {
  [key: string]: {
    key: IDBValidKey;
    value: T;
    indexes: {
      [name: string]: T;
    };
  };
};

/**
 * useIndexedDB Hook
 *
 * Provides a simplified interface for IndexedDB operations using the idb library.
 * Handles database opening, schema creation, and provides methods for CRUD operations.
 *
 * @param options - Database configuration options
 * @returns UseIndexedDBResult object with database operation methods
 *
 * @example
 * ```tsx
 * interface User {
 *   id: string;
 *   name: string;
 *   email: string;
 * }
 *
 * function UserProfile({ userId }: { userId: string }) {
 *   const db = useIndexedDB<User>({
 *     dbName: 'user-database',
 *     storeName: 'users',
 *     keyPath: 'id',
 *     indexes: [
 *       { name: 'email', keyPath: 'email', options: { unique: true } }
 *     ]
 *   });
 *
 *   const [user, setUser] = useState<User | null>(null);
 *
 *   useEffect(() => {
 *     if (db.isReady) {
 *       db.get(userId).then(setUser);
 *     }
 *   }, [db.isReady, userId]);
 *
 *   if (!db.isReady) return <div>Loading...</div>;
 *   if (db.error) return <div>Error: {db.error.message}</div>;
 *
 *   return (
 *     <div>
 *       <h1>{user?.name}</h1>
 *       <p>{user?.email}</p>
 *       <button onClick={() => db.delete(userId)}>
 *         Delete User
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Offline cache for candidate data
 * interface CachedCandidate {
 *   id: string;
 *   data: CandidateData;
 *   cachedAt: number;
 * }
 *
 * function CandidateCache() {
 *   const cache = useIndexedDB<CachedCandidate>({
 *     dbName: 'candidate-cache',
 *     storeName: 'candidates',
 *     keyPath: 'id'
 *   });
 *
 *   const cacheCandidate = useCallback(
 *     async (candidate: CandidateData) => {
 *       await cache.put({
 *         id: candidate.id,
 *         data: candidate,
 *         cachedAt: Date.now()
 *       });
 *     },
 *     [cache]
 *   );
 *
 *   const getCachedCandidate = useCallback(
 *     async (id: string) => {
 *       const cached = await cache.get(id);
 *       if (cached && Date.now() - cached.cachedAt < 3600000) {
 *         return cached.data; // Cache is valid for 1 hour
 *       }
 *       return null; // Cache expired or not found
 *     },
 *     [cache]
 *   );
 *
 *   return { cacheCandidate, getCachedCandidate, ...cache };
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Shopping cart with persistence
 * interface CartItem {
 *   productId: string;
 *   quantity: number;
 *   price: number;
 * }
 *
 * function ShoppingCart() {
 *   const cart = useIndexedDB<CartItem>({
 *     dbName: 'shopping-cart',
 *     storeName: 'items',
 *     keyPath: 'productId'
 *   });
 *
 *   const [items, setItems] = useState<CartItem[]>([]);
 *
 *   useEffect(() => {
 *     if (cart.isReady) {
 *       cart.getAll().then(setItems);
 *     }
 *   }, [cart.isReady]);
 *
 *   const addItem = useCallback(
 *     async (item: CartItem) => {
 *       await cart.put(item);
 *       const updated = await cart.getAll();
 *       setItems(updated);
 *     },
 *     [cart]
 *   );
 *
 *   const clearCart = useCallback(async () => {
 *     await cart.clear();
 *     setItems([]);
 *   }, [cart]);
 *
 *   return (
 *     <div>
 *       {items.map(item => (
 *         <div key={item.productId}>
 *           {item.productId} - {item.quantity}
 *         </div>
 *       ))}
 *       <button onClick={clearCart}>Clear Cart</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useIndexedDB<T = unknown>(
  options: UseIndexedDBOptions<T>
): UseIndexedDBResult<T> {
  const { dbName, version = 1, storeName, keyPath, indexes = [] } = options;

  const [db, setDb] = useState<IDBPDatabase | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isReady, setIsReady] = useState(false);

  // Use ref to avoid reopening database on options prop changes
  const dbRef = useRef<IDBPDatabase | null>(null);
  const dbNameRef = useRef(dbName);
  const storeNameRef = useRef(storeName);

  // Open database connection
  useEffect(() => {
    // Skip if already opened for this db/store
    if (
      dbRef.current &&
      dbNameRef.current === dbName &&
      storeNameRef.current === storeName
    ) {
      setDb(dbRef.current);
      setIsReady(true);
      return;
    }

    let cancelled = false;

    const openDatabase = async () => {
      try {
        setError(null);

        const database = await openDB(dbName, version, {
          upgrade(db) {
            // Create object store if it doesn't exist
            if (!db.objectStoreNames.contains(storeName)) {
              const store = keyPath
                ? db.createObjectStore(storeName, { keyPath })
                : db.createObjectStore(storeName, {
                    autoIncrement: true,
                  });

              // Create indexes
              indexes.forEach(({ name, keyPath, options }) => {
                if (!store.indexNames.contains(name)) {
                  store.createIndex(name, keyPath, options);
                }
              });
            } else {
              // Add indexes to existing store
              const store = db.transaction(storeName, 'readonly').objectStore(storeName);
              indexes.forEach(({ name, keyPath, options }) => {
                if (!store.indexNames.contains(name)) {
                  store.createIndex(name, keyPath, options);
                }
              });
            }
          },
          blocked() {
            console.warn(
              `useIndexedDB: Database "${dbName}" is blocked. Close other tabs and try again.`
            );
          },
          blocking() {
            console.warn(
              `useIndexedDB: This connection is blocking the database "${dbName}" from upgrading.`
            );
          },
        });

        if (cancelled) {
          database.close();
          return;
        }

        dbRef.current = database;
        dbNameRef.current = dbName;
        storeNameRef.current = storeName;
        setDb(database);
        setIsReady(true);
      } catch (err) {
        const error =
          err instanceof Error
            ? err
            : new Error(`Failed to open database: ${String(err)}`);
        setError(error);
        setIsReady(false);
        console.error('useIndexedDB: Error opening database:', error);
      }
    };

    openDatabase();

    return () => {
      cancelled = true;
      // Don't close database on unmount - keep connection alive
    };
  }, [dbName, version, storeName, keyPath, indexes]);

  // Get operation
  const get = useCallback(
    async (key: IDBValidKey): Promise<T | undefined> => {
      if (!db) {
        throw new Error(
          'Database not ready. Wait for isReady to be true before calling get().'
        );
      }

      try {
        return await db.get(storeName, key);
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error(`Failed to get key: ${key}`);
        setError(error);
        console.error('useIndexedDB: Error in get():', error);
        throw error;
      }
    },
    [db, storeName]
  );

  // Get all operation
  const getAll = useCallback(async (): Promise<T[]> => {
    if (!db) {
      throw new Error(
        'Database not ready. Wait for isReady to be true before calling getAll().'
      );
    }

    try {
      return await db.getAll(storeName);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to get all');
      setError(error);
      console.error('useIndexedDB: Error in getAll():', error);
      throw error;
    }
  }, [db, storeName]);

  // Put operation
  const put = useCallback(
    async (value: T, key?: IDBValidKey): Promise<IDBValidKey> => {
      if (!db) {
        throw new Error(
          'Database not ready. Wait for isReady to be true before calling put().'
        );
      }

      try {
        return await db.put(storeName, value, key);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to put value');
        setError(error);
        console.error('useIndexedDB: Error in put():', error);
        throw error;
      }
    },
    [db, storeName]
  );

  // Delete operation
  const deleteItem = useCallback(
    async (key: IDBValidKey): Promise<void> => {
      if (!db) {
        throw new Error(
          'Database not ready. Wait for isReady to be true before calling delete().'
        );
      }

      try {
        await db.delete(storeName, key);
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error(`Failed to delete key: ${key}`);
        setError(error);
        console.error('useIndexedDB: Error in delete():', error);
        throw error;
      }
    },
    [db, storeName]
  );

  // Clear operation
  const clear = useCallback(async (): Promise<void> => {
    if (!db) {
      throw new Error(
        'Database not ready. Wait for isReady to be true before calling clear().'
      );
    }

    try {
      await db.clear(storeName);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to clear store');
      setError(error);
      console.error('useIndexedDB: Error in clear():', error);
      throw error;
    }
  }, [db, storeName]);

  // Count operation
  const count = useCallback(async (): Promise<number> => {
    if (!db) {
      throw new Error(
        'Database not ready. Wait for isReady to be true before calling count().'
      );
    }

    try {
      return await db.count(storeName);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to count');
      setError(error);
      console.error('useIndexedDB: Error in count():', error);
      throw error;
    }
  }, [db, storeName]);

  // Get many operation
  const getMany = useCallback(
    async (keys: IDBValidKey[]): Promise<(T | undefined)[]> => {
      if (!db) {
        throw new Error(
          'Database not ready. Wait for isReady to be true before calling getMany().'
        );
      }

      try {
        return await db.getAllKeys(storeName, keys);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to get many');
        setError(error);
        console.error('useIndexedDB: Error in getMany():', error);
        throw error;
      }
    },
    [db, storeName]
  );

  return {
    isReady,
    error,
    get,
    getAll,
    put,
    delete: deleteItem,
    clear,
    count,
    getMany,
  };
}

export default useIndexedDB;
