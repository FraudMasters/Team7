/**
 * Tests for Offline Cache Utility
 *
 * Tests offline caching strategies including network-first and cache-first
 * with IndexedDB persistence using fake-indexeddb for testing.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { offlineCache, OfflineCache } from './offlineCache';
import type { CacheOptions, CacheStrategy } from './offlineCache';

// Mock data for testing
interface TestData {
  id: string;
  name: string;
  value: number;
}

const mockData: TestData = {
  id: 'test-123',
  name: 'Test Candidate',
  value: 42,
};

const mockData2: TestData = {
  id: 'test-456',
  name: 'Another Candidate',
  value: 100,
};

describe('offlineCache', () => {
  let cacheInstance: OfflineCache;

  beforeEach(() => {
    // Create fresh instance for each test
    cacheInstance = new OfflineCache();
  });

  afterEach(async () => {
    // Clean up after each test
    await cacheInstance.close();
  });

  describe('Basic Cache Operations', () => {
    it('should set and get data from cache', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);

      const hasKey = await cacheInstance.has('test-store', 'key-1');
      expect(hasKey).toBe(true);

      // Verify we can retrieve via network-first with a mock that returns cached data
      const fetcher = vi.fn().mockResolvedValue(mockData);
      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(mockData);
      expect(fetcher).not.toHaveBeenCalled(); // Should use cache
    });

    it('should check if key exists in cache', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);

      const hasKey = await cacheInstance.has('test-store', 'key-1');
      expect(hasKey).toBe(true);

      const noKey = await cacheInstance.has('test-store', 'nonexistent');
      expect(noKey).toBe(false);
    });

    it('should delete specific cache entry', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);
      await cacheInstance.delete('test-store', 'key-1');

      const hasKey = await cacheInstance.has('test-store', 'key-1');
      expect(hasKey).toBe(false);
    });

    it('should clear all entries in a store', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);
      await cacheInstance.set('test-store', 'key-2', mockData2);

      await cacheInstance.clear('test-store');

      const keys = await cacheInstance.keys('test-store');
      expect(keys).toHaveLength(0);
    });

    it('should get all keys in a store', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);
      await cacheInstance.set('test-store', 'key-2', mockData2);

      const keys = await cacheInstance.keys('test-store');
      expect(keys).toHaveLength(2);
      expect(keys).toContain('key-1');
      expect(keys).toContain('key-2');
    });
  });

  describe('Network-First Strategy', () => {
    it('should fetch from network and cache response', async () => {
      const fetcher = vi.fn().mockResolvedValue(mockData);

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'network-first',
        cacheResponses: true,
      });

      expect(result).toEqual(mockData);
      expect(fetcher).toHaveBeenCalledTimes(1);

      // Verify data was cached
      const hasCached = await cacheInstance.has('test-store', 'key-1');
      expect(hasCached).toBe(true);
    });

    it('should fall back to cache when network fails', async () => {
      // Pre-populate cache
      await cacheInstance.set('test-store', 'key-1', mockData, 10000);

      const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'network-first',
      });

      expect(result).toEqual(mockData);
      expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('should throw error when both network and cache fail', async () => {
      const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));

      await expect(
        cacheInstance.get('test-store', 'key-1', fetcher, {
          strategy: 'network-first',
        })
      ).rejects.toThrow();
    });

    it('should not cache when cacheResponses is false', async () => {
      const fetcher = vi.fn().mockResolvedValue(mockData);

      await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'network-first',
        cacheResponses: false,
      });

      const hasCached = await cacheInstance.has('test-store', 'key-1');
      expect(hasCached).toBe(false);
    });

    it('should update cache with fresh network data', async () => {
      // Pre-populate cache with old data
      await cacheInstance.set('test-store', 'key-1', mockData, 10000);

      const updatedData = { ...mockData, value: 999 };
      const fetcher = vi.fn().mockResolvedValue(updatedData);

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'network-first',
      });

      expect(result).toEqual(updatedData);
      expect(fetcher).toHaveBeenCalledTimes(1);
    });
  });

  describe('Cache-First Strategy', () => {
    it('should return cached data without network call', async () => {
      // Pre-populate cache
      await cacheInstance.set('test-store', 'key-1', mockData, 10000);

      const fetcher = vi.fn().mockResolvedValue(mockData2);

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(mockData);
      expect(fetcher).not.toHaveBeenCalled();
    });

    it('should fetch from network on cache miss', async () => {
      const fetcher = vi.fn().mockResolvedValue(mockData);

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(mockData);
      expect(fetcher).toHaveBeenCalledTimes(1);

      // Verify data was cached
      const hasCached = await cacheInstance.has('test-store', 'key-1');
      expect(hasCached).toBe(true);
    });

    it('should return stale cache when network fails', async () => {
      // Pre-populate cache with short expiration
      await cacheInstance.set('test-store', 'key-1', mockData, 1);

      // Wait for cache to expire
      await new Promise((resolve) => setTimeout(resolve, 10));

      const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(mockData);
      expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('should throw error when cache miss and network fails', async () => {
      const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));

      await expect(
        cacheInstance.get('test-store', 'key-1', fetcher, {
          strategy: 'cache-first',
        })
      ).rejects.toThrow();
    });
  });

  describe('Cache Expiration', () => {
    it('should respect custom cache timeout', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData, 100); // 100ms

      // Immediately should be available
      expect(await cacheInstance.has('test-store', 'key-1')).toBe(true);

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 150));

      expect(await cacheInstance.has('test-store', 'key-1')).toBe(false);
    });

    it('should treat expired cache as invalid in cache-first', async () => {
      // Pre-populate with short expiration
      await cacheInstance.set('test-store', 'key-1', mockData, 50);

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 100));

      const fetcher = vi.fn().mockResolvedValue(mockData2);

      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      // Should fetch from network since cache expired
      expect(result).toEqual(mockData2);
      expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('should treat expired cache as invalid in network-first fallback', async () => {
      // Pre-populate with short expiration
      await cacheInstance.set('test-store', 'key-1', mockData, 50);

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 100));

      const fetcher = vi.fn().mockRejectedValue(new Error('Network error'));

      await expect(
        cacheInstance.get('test-store', 'key-1', fetcher, {
          strategy: 'network-first',
        })
      ).rejects.toThrow();
    });

    it('should handle entries with long expiration', async () => {
      // Set entry with very long expiration (24 hours)
      await cacheInstance.set('test-store', 'key-1', mockData, 24 * 60 * 60 * 1000);

      // Should be available
      expect(await cacheInstance.has('test-store', 'key-1')).toBe(true);
    });
  });

  describe('Cache Management', () => {
    it('should calculate cache size', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);
      await cacheInstance.set('test-store', 'key-2', mockData2);

      const size = await cacheInstance.size('test-store');
      expect(size).toBeGreaterThan(0);
    });

    it('should clean expired entries', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData, 50);
      await cacheInstance.set('test-store', 'key-2', mockData2, 10000);

      // Wait for first entry to expire
      await new Promise((resolve) => setTimeout(resolve, 100));

      const removed = await cacheInstance.cleanExpired('test-store');
      expect(removed).toBe(1);

      const keys = await cacheInstance.keys('test-store');
      expect(keys).toHaveLength(1);
      expect(keys).toContain('key-2');
    });

    it('should return zero removed when no expired entries', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData, 10000);

      const removed = await cacheInstance.cleanExpired('test-store');
      expect(removed).toBe(0);
    });
  });

  describe('Default Options', () => {
    it('should use default strategy when not specified', async () => {
      const fetcher = vi.fn().mockResolvedValue(mockData);

      // Default strategy is network-first
      await cacheInstance.get('test-store', 'key-1', fetcher);

      expect(fetcher).toHaveBeenCalledTimes(1);
    });

    it('should use default cache timeout when not specified', async () => {
      await cacheInstance.set('test-store', 'key-1', mockData);

      // Default is 1 hour, so should be available
      expect(await cacheInstance.has('test-store', 'key-1')).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should handle set errors gracefully', async () => {
      // Force error by closing database
      await cacheInstance.close();

      await expect(
        cacheInstance.set('test-store', 'key-1', mockData)
      ).rejects.toThrow();
    });

    it('should handle delete errors gracefully', async () => {
      await cacheInstance.close();

      // Should not throw, but log error
      await cacheInstance.delete('test-store', 'key-1');
    });

    it('should handle clear errors gracefully', async () => {
      await cacheInstance.close();

      // Should not throw, but log error
      await cacheInstance.clear('test-store');
    });
  });

  describe('Multiple Stores', () => {
    it('should isolate data between stores', async () => {
      await cacheInstance.set('store-1', 'key-1', mockData);
      await cacheInstance.set('store-2', 'key-1', mockData2);

      // Verify via has check
      expect(await cacheInstance.has('store-1', 'key-1')).toBe(true);
      expect(await cacheInstance.has('store-2', 'key-1')).toBe(true);

      // Verify via retrieval
      const fetcher1 = vi.fn().mockResolvedValue(mockData);
      const fetcher2 = vi.fn().mockResolvedValue(mockData2);

      const result1 = await cacheInstance.get('store-1', 'key-1', fetcher1, {
        strategy: 'cache-first',
      });
      const result2 = await cacheInstance.get('store-2', 'key-1', fetcher2, {
        strategy: 'cache-first',
      });

      expect(result1).toEqual(mockData);
      expect(result2).toEqual(mockData2);
      expect(fetcher1).not.toHaveBeenCalled();
      expect(fetcher2).not.toHaveBeenCalled();
    });

    it('should clear only specified store', async () => {
      await cacheInstance.set('store-1', 'key-1', mockData);
      await cacheInstance.set('store-2', 'key-1', mockData2);

      await cacheInstance.clear('store-1');

      expect(await cacheInstance.has('store-1', 'key-1')).toBe(false);
      expect(await cacheInstance.has('store-2', 'key-1')).toBe(true);
    });
  });

  describe('Singleton Instance', () => {
    it('should export singleton offlineCache instance', () => {
      expect(offlineCache).toBeInstanceOf(OfflineCache);
    });

    it('should use singleton instance across imports', async () => {
      await offlineCache.set('test-store', 'key-1', mockData);

      const hasCached = await offlineCache.has('test-store', 'key-1');
      expect(hasCached).toBe(true);

      // Clean up
      await offlineCache.clear('test-store');
    });
  });

  describe('Type Safety', () => {
    it('should preserve type information', async () => {
      interface CustomData {
        customField: string;
        items: number[];
      }

      const customData: CustomData = {
        customField: 'test',
        items: [1, 2, 3],
      };

      await cacheInstance.set<CustomData>('test-store', 'key-1', customData);

      const fetcher = vi.fn().mockResolvedValue(customData);
      const result = await cacheInstance.get<CustomData>('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(customData);
      expect(result.items).toEqual([1, 2, 3]);
      expect(fetcher).not.toHaveBeenCalled(); // Should use cache
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty data', async () => {
      const emptyData = { id: '', name: '', value: 0 };
      await cacheInstance.set('test-store', 'key-1', emptyData);

      const fetcher = vi.fn().mockResolvedValue(emptyData);
      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(emptyData);
      expect(fetcher).not.toHaveBeenCalled();
    });

    it('should handle special characters in keys', async () => {
      const specialKey = 'key/with/slashes&special=chars';

      await cacheInstance.set('test-store', specialKey, mockData);

      const hasCached = await cacheInstance.has('test-store', specialKey);
      expect(hasCached).toBe(true);
    });

    it('should handle very large data', async () => {
      const largeData = {
        id: 'large',
        data: 'x'.repeat(100000), // 100KB string
      };

      await cacheInstance.set('test-store', 'key-1', largeData);

      const fetcher = vi.fn().mockResolvedValue(largeData);
      const result = await cacheInstance.get('test-store', 'key-1', fetcher, {
        strategy: 'cache-first',
      });

      expect(result).toEqual(largeData);
      expect(fetcher).not.toHaveBeenCalled(); // Should use cache
    });
  });

  describe('Integration with useIndexedDB', () => {
    it('should be compatible with IndexedDB storage', async () => {
      // This test verifies that offlineCache works with the same IndexedDB
      // that useIndexedDB hook uses (same database pattern)

      await cacheInstance.set('candidates', 'candidate-123', {
        id: 'candidate-123',
        name: 'John Doe',
        email: 'john@example.com',
      });

      const hasCached = await cacheInstance.has('candidates', 'candidate-123');
      expect(hasCached).toBe(true);

      const keys = await cacheInstance.keys('candidates');
      expect(keys).toContain('candidate-123');
    });
  });
});
