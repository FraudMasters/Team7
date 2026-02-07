/**
 * Offline Cache Utility
 *
 * Provides cache strategies for offline data access including network-first
 * and cache-first strategies. Integrates with IndexedDB for persistent storage
 * and supports cache expiration and invalidation.
 *
 * @module utils/offlineCache
 *
 * @example
 * ```ts
 * import { offlineCache } from '@/utils/offlineCache';
 *
 * // Network-first: Try network, fall back to cache
 * const data = await offlineCache.get(
 *   'candidates',
 *   'candidate-123',
 *   () => fetchCandidate('candidate-123'),
 *   { strategy: 'network-first' }
 * );
 *
 * // Cache-first: Try cache, fall back to network
 * const data = await offlineCache.get(
 *   'candidates',
 *   'candidate-123',
 *   () => fetchCandidate('candidate-123'),
 *   { strategy: 'cache-first' }
 * );
 *
 * // Prefetch data for offline use
 * await offlineCache.set('candidates', 'candidate-123', candidateData);
 *
 * // Check if data is cached
 * const hasCached = await offlineCache.has('candidates', 'candidate-123');
 *
 * // Invalidate specific cache entry
 * await offlineCache.delete('candidates', 'candidate-123');
 *
 * // Clear all cached candidates
 * await offlineCache.clear('candidates');
 * ```
 */

import { openDB, IDBPDatabase } from 'idb';

/**
 * Cache strategy type
 *
 * - network-first: Try network first, fall back to cache if offline
 * - cache-first: Try cache first, fall back to network on cache miss
 */
export type CacheStrategy = 'network-first' | 'cache-first';

/**
 * Cache entry with metadata
 *
 * @interface CacheEntry
 */
interface CacheEntry<T> {
  /**
   * Cached data
   */
  data: T;

  /**
   * Timestamp when data was cached (milliseconds since epoch)
   */
  cachedAt: number;

  /**
   * Optional expiration timestamp (milliseconds since epoch)
   */
  expiresAt?: number;

  /**
   * Optional ETag for cache validation
   */
  etag?: string;
}

/**
 * Cache options for configuring cache behavior
 *
 * @interface CacheOptions
 */
export interface CacheOptions {
  /**
   * Cache strategy to use
   * @default 'network-first'
   */
  strategy?: CacheStrategy;

  /**
   * Cache expiration time in milliseconds
   * @default 3600000 (1 hour)
   */
  cacheTimeout?: number;

  /**
   * Whether to cache successful network responses
   * @default true
   */
  cacheResponses?: boolean;
}

/**
 * Default cache configuration
 */
const DEFAULT_CACHE_TIMEOUT = 60 * 60 * 1000; // 1 hour
const DB_NAME = 'offline-cache';
const DB_VERSION = 1;

/**
 * Database schema for offline cache
 */
interface CacheDBSchema {
  [storeName: string]: CacheEntry<unknown>;
}

/**
 * Offline Cache class
 *
 * Provides caching strategies with IndexedDB persistence for offline data access.
 */
class OfflineCache {
  private db: IDBPDatabase<CacheDBSchema> | null = null;
  private dbPromise: Promise<IDBPDatabase<CacheDBSchema>> | null = null;

  /**
   * Get or create database connection
   *
   * @returns Database instance
   */
  private async getDb(): Promise<IDBPDatabase<CacheDBSchema>> {
    if (this.db) {
      return this.db;
    }

    if (this.dbPromise) {
      return this.dbPromise;
    }

    this.dbPromise = openDB<CacheDBSchema>(DB_NAME, DB_VERSION, {
      upgrade(database) {
        // Create object stores for each cache namespace
        // Stores will be created on-demand when first accessed
      },
      blocked() {
        console.warn(
          '[OfflineCache] Database is blocked. Close other tabs and try again.'
        );
      },
      blocking() {
        console.warn(
          '[OfflineCache] This connection is blocking the database from upgrading.'
        );
      },
    });

    this.db = await this.dbPromise;
    return this.db;
  }

  /**
   * Ensure object store exists for a given namespace
   *
   * @param dbName - Database namespace (store name)
   */
  private async ensureStore(dbName: string): Promise<void> {
    const database = await this.getDb();

    // Check if store exists
    if (!database.objectStoreNames.contains(dbName)) {
      // Close current connection
      database.close();
      this.db = null;
      this.dbPromise = null;

      // Reopen with new store
      this.dbPromise = openDB<CacheDBSchema>(DB_NAME, DB_VERSION + 1, {
        upgrade(database) {
          if (!database.objectStoreNames.contains(dbName)) {
            database.createObjectStore(dbName);
          }
        },
      });

      this.db = await this.dbPromise;
    }
  }

  /**
   * Get data with cache strategy
   *
   * Tries to fetch data using the specified strategy:
   * - network-first: Try network first, fall back to cache
   * - cache-first: Try cache first, fall back to network
   *
   * @param storeName - Cache namespace/store name
   * @param key - Cache key
   * @param fetcher - Function to fetch data from network
   * @param options - Cache options
   * @returns Fetched or cached data
   * @throws Error if both network and cache fail
   *
   * @example
   * ```ts
   * const candidate = await offlineCache.get(
   *   'candidates',
   *   'candidate-123',
   *   () => apiClient.getCandidate('candidate-123'),
   *   { strategy: 'network-first', cacheTimeout: 1800000 }
   * );
   * ```
   */
  async get<T>(
    storeName: string,
    key: string,
    fetcher: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    const {
      strategy = 'network-first',
      cacheTimeout = DEFAULT_CACHE_TIMEOUT,
      cacheResponses = true,
    } = options;

    await this.ensureStore(storeName);

    if (strategy === 'network-first') {
      return this.networkFirst(storeName, key, fetcher, cacheTimeout, cacheResponses);
    } else {
      return this.cacheFirst(storeName, key, fetcher, cacheTimeout, cacheResponses);
    }
  }

  /**
   * Network-first strategy
   *
   * Tries network first, falls back to cache if offline or network fails
   *
   * @param storeName - Cache namespace
   * @param key - Cache key
   * @param fetcher - Network fetch function
   * @param cacheTimeout - Cache expiration time
   * @param cacheResponses - Whether to cache responses
   * @returns Data from network or cache
   */
  private async networkFirst<T>(
    storeName: string,
    key: string,
    fetcher: () => Promise<T>,
    cacheTimeout: number,
    cacheResponses: boolean
  ): Promise<T> {
    try {
      // Try network first
      const data = await fetcher();

      // Cache the successful response
      if (cacheResponses) {
        await this.set(storeName, key, data, cacheTimeout);
      }

      return data;
    } catch (networkError) {
      // Network failed, try cache
      const cached = await this.getCacheEntry<T>(storeName, key);

      if (cached && !this.isExpired(cached)) {
        return cached.data;
      }

      // Cache miss or expired
      throw new Error(
        `Network request failed and no valid cache available: ${(networkError as Error).message}`
      );
    }
  }

  /**
   * Cache-first strategy
   *
   * Tries cache first, falls back to network on cache miss
   *
   * @param storeName - Cache namespace
   * @param key - Cache key
   * @param fetcher - Network fetch function
   * @param cacheTimeout - Cache expiration time
   * @param cacheResponses - Whether to cache responses
   * @returns Data from cache or network
   */
  private async cacheFirst<T>(
    storeName: string,
    key: string,
    fetcher: () => Promise<T>,
    cacheTimeout: number,
    cacheResponses: boolean
  ): Promise<T> {
    // Try cache first
    const cached = await this.getCacheEntry<T>(storeName, key);

    if (cached && !this.isExpired(cached)) {
      return cached.data;
    }

    // Cache miss or expired, try network
    try {
      const data = await fetcher();

      // Cache the successful response
      if (cacheResponses) {
        await this.set(storeName, key, data, cacheTimeout);
      }

      return data;
    } catch (networkError) {
      // Network failed, return stale cache if available
      if (cached) {
        return cached.data;
      }

      throw networkError;
    }
  }

  /**
   * Check if cache entry is expired
   *
   * @param entry - Cache entry to check
   * @returns True if expired, false otherwise
   */
  private isExpired<T>(entry: CacheEntry<T>): boolean {
    if (!entry.expiresAt) {
      return false;
    }
    return Date.now() > entry.expiresAt;
  }

  /**
   * Get cache entry without applying strategy
   *
   * @param storeName - Cache namespace
   * @param key - Cache key
   * @returns Cache entry or undefined if not found
   */
  private async getCacheEntry<T>(
    storeName: string,
    key: string
  ): Promise<CacheEntry<T> | undefined> {
    try {
      const database = await this.getDb();
      return await database.get(storeName, key);
    } catch (error) {
      console.error('[OfflineCache] Error getting cache entry:', error);
      return undefined;
    }
  }

  /**
   * Set data in cache
   *
   * Stores data in cache with optional expiration time
   *
   * @param storeName - Cache namespace
   * @param key - Cache key
   * @param data - Data to cache
   * @param cacheTimeout - Optional cache expiration time (default: 1 hour)
   *
   * @example
   * ```ts
   * await offlineCache.set('candidates', 'candidate-123', candidateData);
   *
   * // Cache for 30 minutes
   * await offlineCache.set('candidates', 'candidate-123', candidateData, 1800000);
   * ```
   */
  async set<T>(
    storeName: string,
    key: string,
    data: T,
    cacheTimeout: number = DEFAULT_CACHE_TIMEOUT
  ): Promise<void> {
    try {
      await this.ensureStore(storeName);

      const database = await this.getDb();

      const entry: CacheEntry<T> = {
        data,
        cachedAt: Date.now(),
        expiresAt: Date.now() + cacheTimeout,
      };

      await database.put(storeName, entry, key);
    } catch (error) {
      console.error('[OfflineCache] Error setting cache entry:', error);
      throw error;
    }
  }

  /**
   * Check if key exists in cache and is not expired
   *
   * @param storeName - Cache namespace
   * @param key - Cache key
   * @returns True if key exists and is not expired
   *
   * @example
   * ```ts
   * const hasCandidate = await offlineCache.has('candidates', 'candidate-123');
   * if (hasCandidate) {
   *   // Candidate is cached
   * }
   * ```
   */
  async has(storeName: string, key: string): Promise<boolean> {
    try {
      const entry = await this.getCacheEntry(storeName, key);
      return entry !== undefined && !this.isExpired(entry);
    } catch (error) {
      console.error('[OfflineCache] Error checking cache entry:', error);
      return false;
    }
  }

  /**
   * Delete specific cache entry
   *
   * @param storeName - Cache namespace
   * @param key - Cache key to delete
   *
   * @example
   * ```ts
   * await offlineCache.delete('candidates', 'candidate-123');
   * ```
   */
  async delete(storeName: string, key: string): Promise<void> {
    try {
      const database = await this.getDb();
      await database.delete(storeName, key);
    } catch (error) {
      console.error('[OfflineCache] Error deleting cache entry:', error);
      throw error;
    }
  }

  /**
   * Clear all entries in a cache namespace
   *
   * @param storeName - Cache namespace to clear
   *
   * @example
   * ```ts
   * await offlineCache.clear('candidates');
   * ```
   */
  async clear(storeName: string): Promise<void> {
    try {
      const database = await this.getDb();
      await database.clear(storeName);
    } catch (error) {
      console.error('[OfflineCache] Error clearing cache:', error);
      throw error;
    }
  }

  /**
   * Get all keys in a cache namespace
   *
   * @param storeName - Cache namespace
   * @returns Array of all keys in the namespace
   *
   * @example
   * ```ts
   * const keys = await offlineCache.keys('candidates');
   * console.log(`Cached candidates: ${keys.length}`);
   * ```
   */
  async keys(storeName: string): Promise<string[]> {
    try {
      const database = await this.getDb();
      return await database.getAllKeys(storeName) as unknown as string[];
    } catch (error) {
      console.error('[OfflineCache] Error getting cache keys:', error);
      return [];
    }
  }

  /**
   * Get size of cache namespace in bytes (estimated)
   *
   * @param storeName - Cache namespace
   * @returns Estimated size in bytes
   *
   * @example
   * ```ts
   * const size = await offlineCache.size('candidates');
   * console.log(`Cache size: ${(size / 1024).toFixed(2)} KB`);
   * ```
   */
  async size(storeName: string): Promise<number> {
    try {
      const database = await this.getDb();
      const keys = await database.getAllKeys(storeName);
      let totalSize = 0;

      for (const key of keys) {
        const entry = await database.get(storeName, key);
        if (entry) {
          totalSize += JSON.stringify(entry).length;
        }
      }

      return totalSize;
    } catch (error) {
      console.error('[OfflineCache] Error calculating cache size:', error);
      return 0;
    }
  }

  /**
   * Clean expired entries from a cache namespace
   *
   * Removes all expired cache entries to free up storage space
   *
   * @param storeName - Cache namespace to clean
   * @returns Number of entries removed
   *
   * @example
   * ```ts
   * const removed = await offlineCache.cleanExpired('candidates');
   * console.log(`Removed ${removed} expired entries`);
   * ```
   */
  async cleanExpired(storeName: string): Promise<number> {
    try {
      const database = await this.getDb();
      const keys = await database.getAllKeys(storeName);
      let removedCount = 0;

      for (const key of keys) {
        const entry = await database.get(storeName, key);
        if (entry && this.isExpired(entry)) {
          await database.delete(storeName, key);
          removedCount++;
        }
      }

      return removedCount;
    } catch (error) {
      console.error('[OfflineCache] Error cleaning expired entries:', error);
      return 0;
    }
  }

  /**
   * Close database connection
   *
   * Call this when done using the cache to free up resources
   *
   * @example
   * ```ts
   * await offlineCache.close();
   * ```
   */
  async close(): Promise<void> {
    if (this.db) {
      this.db.close();
      this.db = null;
      this.dbPromise = null;
    }
  }
}

/**
 * Default offline cache instance
 *
 * Use this singleton instance for all offline caching operations
 */
export const offlineCache = new OfflineCache();

/**
 * Export OfflineCache class for custom instances
 */
export default OfflineCache;
