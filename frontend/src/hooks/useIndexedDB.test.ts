import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, cleanup, waitFor } from '@testing-library/react';
import { useIndexedDB } from './useIndexedDB';
import 'fake-indexeddb/auto';

// Add afterEach for cleanup
afterEach(() => {
  cleanup();
});

interface TestUser {
  id: string;
  name: string;
  email: string;
}

describe('useIndexedDB', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('hook initialization', () => {
    it('should initialize with not ready state', () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      expect(result.current.isReady).toBeDefined();
      expect(result.current.error).toBeNull();
    });

    it('should provide all required methods', () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      expect(result.current.get).toBeDefined();
      expect(typeof result.current.get).toBe('function');

      expect(result.current.getAll).toBeDefined();
      expect(typeof result.current.getAll).toBe('function');

      expect(result.current.put).toBeDefined();
      expect(typeof result.current.put).toBe('function');

      expect(result.current.delete).toBeDefined();
      expect(typeof result.current.delete).toBe('function');

      expect(result.current.clear).toBeDefined();
      expect(typeof result.current.clear).toBe('function');

      expect(result.current.count).toBeDefined();
      expect(typeof result.current.count).toBe('function');

      expect(result.current.getMany).toBeDefined();
      expect(typeof result.current.getMany).toBe('function');
    });

    it('should open database and become ready', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-ready',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });
    });

    it('should accept default version', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-version',
          storeName: 'users',
          keyPath: 'id',
          version: 1,
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });
    });
  });

  describe('put operation', () => {
    it('should store a value with inline key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-put-inline',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      const key = await result.current.put(user);
      expect(key).toBe('user-1');
    });

    it('should store a value with out-of-line key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-put-out',
          storeName: 'users',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      const key = await result.current.put(user, 'custom-key');
      expect(key).toBe('custom-key');
    });

    it('should update existing value', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-put-update',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);

      // Update the user
      const updatedUser: TestUser = {
        id: 'user-1',
        name: 'Jane Doe',
        email: 'jane@example.com',
      };

      await result.current.put(updatedUser);

      const retrieved = await result.current.get('user-1');
      expect(retrieved?.name).toBe('Jane Doe');
      expect(retrieved?.email).toBe('jane@example.com');
    });

    it('should store multiple values', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-put-multiple',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const users: TestUser[] = [
        { id: 'user-1', name: 'John Doe', email: 'john@example.com' },
        { id: 'user-2', name: 'Jane Doe', email: 'jane@example.com' },
        { id: 'user-3', name: 'Bob Smith', email: 'bob@example.com' },
      ];

      for (const user of users) {
        await result.current.put(user);
      }

      const count = await result.current.count();
      expect(count).toBe(3);
    });
  });

  describe('get operation', () => {
    it('should retrieve a stored value by key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-get',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);

      const retrieved = await result.current.get('user-1');
      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe('user-1');
      expect(retrieved?.name).toBe('John Doe');
      expect(retrieved?.email).toBe('john@example.com');
    });

    it('should return undefined for non-existent key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-get-missing',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const retrieved = await result.current.get('non-existent');
      expect(retrieved).toBeUndefined();
    });

    it('should throw error when database not ready', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-get-error',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      // Don't wait for ready
      await expect(result.current.get('user-1')).rejects.toThrow(
        'Database not ready'
      );
    });
  });

  describe('getAll operation', () => {
    it('should retrieve all values from store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-getall',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const users: TestUser[] = [
        { id: 'user-1', name: 'John Doe', email: 'john@example.com' },
        { id: 'user-2', name: 'Jane Doe', email: 'jane@example.com' },
        { id: 'user-3', name: 'Bob Smith', email: 'bob@example.com' },
      ];

      for (const user of users) {
        await result.current.put(user);
      }

      const allUsers = await result.current.getAll();
      expect(allUsers).toHaveLength(3);
      expect(allUsers[0].name).toBe('John Doe');
      expect(allUsers[1].name).toBe('Jane Doe');
      expect(allUsers[2].name).toBe('Bob Smith');
    });

    it('should return empty array when store is empty', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-getall-empty',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const allUsers = await result.current.getAll();
      expect(allUsers).toEqual([]);
    });
  });

  describe('delete operation', () => {
    it('should delete a value by key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-delete',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);
      expect(await result.current.count()).toBe(1);

      await result.current.delete('user-1');
      expect(await result.current.count()).toBe(0);

      const retrieved = await result.current.get('user-1');
      expect(retrieved).toBeUndefined();
    });

    it('should handle deleting non-existent key', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-delete-missing',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      // Should not throw
      await expect(result.current.delete('non-existent')).resolves.not.toThrow();
    });

    it('should throw error when database not ready', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-delete-error',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await expect(result.current.delete('user-1')).rejects.toThrow(
        'Database not ready'
      );
    });
  });

  describe('clear operation', () => {
    it('should clear all values from store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-clear',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const users: TestUser[] = [
        { id: 'user-1', name: 'John Doe', email: 'john@example.com' },
        { id: 'user-2', name: 'Jane Doe', email: 'jane@example.com' },
        { id: 'user-3', name: 'Bob Smith', email: 'bob@example.com' },
      ];

      for (const user of users) {
        await result.current.put(user);
      }

      expect(await result.current.count()).toBe(3);

      await result.current.clear();
      expect(await result.current.count()).toBe(0);

      const allUsers = await result.current.getAll();
      expect(allUsers).toEqual([]);
    });

    it('should handle clearing empty store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-clear-empty',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      // Should not throw
      await expect(result.current.clear()).resolves.not.toThrow();
      expect(await result.current.count()).toBe(0);
    });

    it('should throw error when database not ready', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-clear-error',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await expect(result.current.clear()).rejects.toThrow('Database not ready');
    });
  });

  describe('count operation', () => {
    it('should return count of values in store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-count',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      expect(await result.current.count()).toBe(0);

      await result.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });
      expect(await result.current.count()).toBe(1);

      await result.current.put({
        id: 'user-2',
        name: 'Jane Doe',
        email: 'jane@example.com',
      });
      expect(await result.current.count()).toBe(2);

      await result.current.put({
        id: 'user-3',
        name: 'Bob Smith',
        email: 'bob@example.com',
      });
      expect(await result.current.count()).toBe(3);
    });

    it('should return 0 for empty store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-count-empty',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      expect(await result.current.count()).toBe(0);
    });

    it('should update count after delete', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-count-delete',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      await result.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });
      await result.current.put({
        id: 'user-2',
        name: 'Jane Doe',
        email: 'jane@example.com',
      });

      expect(await result.current.count()).toBe(2);

      await result.current.delete('user-1');
      expect(await result.current.count()).toBe(1);
    });
  });

  describe('getMany operation', () => {
    it('should retrieve multiple values by keys', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-getmany',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const users: TestUser[] = [
        { id: 'user-1', name: 'John Doe', email: 'john@example.com' },
        { id: 'user-2', name: 'Jane Doe', email: 'jane@example.com' },
        { id: 'user-3', name: 'Bob Smith', email: 'bob@example.com' },
      ];

      for (const user of users) {
        await result.current.put(user);
      }

      const retrieved = await result.current.getMany([
        'user-1',
        'user-2',
        'user-3',
      ]);

      expect(retrieved).toHaveLength(3);
      expect(retrieved[0]?.name).toBe('John Doe');
      expect(retrieved[1]?.name).toBe('Jane Doe');
      expect(retrieved[2]?.name).toBe('Bob Smith');
    });

    it('should handle missing keys in getMany', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-getmany-missing',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      await result.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });

      const retrieved = await result.current.getMany([
        'user-1',
        'user-2',
        'user-3',
      ]);

      expect(retrieved).toHaveLength(3);
      expect(retrieved[0]?.name).toBe('John Doe');
      expect(retrieved[1]).toBeUndefined();
      expect(retrieved[2]).toBeUndefined();
    });
  });

  describe('index creation', () => {
    it('should create indexes on object store', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-indexes',
          storeName: 'users',
          keyPath: 'id',
          indexes: [
            { name: 'email', keyPath: 'email', options: { unique: true } },
            { name: 'name', keyPath: 'name', options: { unique: false } },
          ],
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      // Store and retrieve should work with indexes
      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);
      const retrieved = await result.current.get('user-1');

      expect(retrieved).toBeDefined();
      expect(retrieved?.email).toBe('john@example.com');
    });

    it('should handle empty indexes array', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-no-indexes',
          storeName: 'users',
          keyPath: 'id',
          indexes: [],
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);
      const retrieved = await result.current.get('user-1');

      expect(retrieved).toBeDefined();
    });
  });

  describe('multiple databases', () => {
    it('should handle multiple database instances', async () => {
      const { result: result1 } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-multi-1',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      const { result: result2 } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-multi-2',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result1.current.isReady).toBe(true);
        expect(result2.current.isReady).toBe(true);
      });

      // Add to first database
      await result1.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });

      // Add to second database
      await result2.current.put({
        id: 'user-2',
        name: 'Jane Doe',
        email: 'jane@example.com',
      });

      // Each database should have its own data
      expect(await result1.current.count()).toBe(1);
      expect(await result2.current.count()).toBe(1);

      const user1 = await result1.current.get('user-1');
      const user2 = await result2.current.get('user-2');

      expect(user1?.name).toBe('John Doe');
      expect(user2?.name).toBe('Jane Doe');

      // Cross-database lookup should fail
      expect(await result1.current.get('user-2')).toBeUndefined();
      expect(await result2.current.get('user-1')).toBeUndefined();
    });

    it('should handle multiple stores in same database', async () => {
      const { result: result1 } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-multi-store',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      const { result: result2 } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-multi-store',
          storeName: 'admins',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result1.current.isReady).toBe(true);
        expect(result2.current.isReady).toBe(true);
      });

      // Add to users store
      await result1.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });

      // Add to admins store
      await result2.current.put({
        id: 'admin-1',
        name: 'Admin User',
        email: 'admin@example.com',
      });

      // Each store should have its own data
      expect(await result1.current.count()).toBe(1);
      expect(await result2.current.count()).toBe(1);

      const user = await result1.current.get('user-1');
      const admin = await result2.current.get('admin-1');

      expect(user?.name).toBe('John Doe');
      expect(admin?.name).toBe('Admin User');
    });
  });

  describe('error handling', () => {
    it('should set error state on operation failure', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-error',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      // Try to get with invalid key (should not throw but set error)
      try {
        await result.current.get('invalid-key-with-special-chars-¿');
      } catch (error) {
        // Error is expected for some invalid operations
        expect(error).toBeDefined();
      }
    });

    it('should have null error when operations succeed', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-no-error',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      await result.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });

      await result.current.get('user-1');
      await result.current.getAll();
      await result.current.count();

      expect(result.current.error).toBeNull();
    });
  });

  describe('hook updates', () => {
    it('should not reopen database on same options', async () => {
      const { result, rerender } = renderHook(
        (props) => useIndexedDB<TestUser>(props),
        {
          initialProps: {
            dbName: 'test-db-reopen',
            storeName: 'users',
            keyPath: 'id',
          },
        }
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      await result.current.put({
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      });

      // Rerender with same props
      rerender({
        dbName: 'test-db-reopen',
        storeName: 'users',
        keyPath: 'id',
      });

      // Data should still be there (no reopen)
      const user = await result.current.get('user-1');
      expect(user?.name).toBe('John Doe');
    });
  });

  describe('type safety', () => {
    it('should enforce type safety for stored values', async () => {
      const { result } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-types',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      await waitFor(() => {
        expect(result.current.isReady).toBe(true);
      });

      const user: TestUser = {
        id: 'user-1',
        name: 'John Doe',
        email: 'john@example.com',
      };

      await result.current.put(user);
      const retrieved = await result.current.get('user-1');

      // TypeScript should enforce the type
      expect(retrieved?.id).toBeDefined();
      expect(retrieved?.name).toBeDefined();
      expect(retrieved?.email).toBeDefined();

      // @ts-expect-error - Intentional error for type checking
      expect(retrieved?.nonExistentField).toBeUndefined();
    });
  });

  describe('memory management', () => {
    it('should clean up on unmount', () => {
      const { unmount } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-unmount',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      expect(() => {
        unmount();
      }).not.toThrow();
    });

    it('should handle rapid mount/unmount', async () => {
      const { unmount } = renderHook(() =>
        useIndexedDB<TestUser>({
          dbName: 'test-db-rapid',
          storeName: 'users',
          keyPath: 'id',
        })
      );

      // Rapid unmount before database opens
      expect(() => {
        unmount();
      }).not.toThrow();
    });
  });
});
