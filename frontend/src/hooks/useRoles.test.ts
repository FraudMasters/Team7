/**
 * Tests for useRoles Hook
 *
 * Tests the role management hook including:
 * - Mock role support when AUTH_ENABLED is false
 * - Role checking helpers (hasRole, hasAnyRole, hasAllRoles)
 * - Role validation and normalization
 * - Feature flag integration
 * - Role hierarchy comparison
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useRoles, UserRole, isValidRole, normalizeRole, getRoleLevel, compareRoles } from './useRoles';

// Mock the feature flags
vi.mock('@/config/features', () => ({
  FEATURE_FLAGS: {
    AUTH_ENABLED: false,
    AUTH_DEBUG: false,
    MOCK_ROLE: 'Admin',
  },
  getFeatureFlag: vi.fn((flag: string) => {
    switch (flag) {
      case 'MOCK_ROLE':
        return 'Admin';
      default:
        return undefined;
    }
  }),
}));

// Import after mocking
import { FEATURE_FLAGS, getFeatureFlag } from '@/config/features';

describe('useRoles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to default: auth disabled, Admin role
    (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
    (FEATURE_FLAGS.MOCK_ROLE as string) = 'Admin';
    vi.mocked(getFeatureFlag).mockImplementation((flag: string) => {
      switch (flag) {
        case 'MOCK_ROLE':
          return 'Admin';
        default:
          return undefined;
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Mock Mode (AUTH_ENABLED=false)', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
    });

    it('should return mock role from feature flag', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.roles).toEqual(['Admin']);
      expect(result.current.primaryRole).toBe('Admin');
    });

    it('should return correct hasRole for mock role', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.hasRole('Admin')).toBe(true);
      expect(result.current.hasRole('Recruiter')).toBe(false);
      expect(result.current.hasRole('JobSeeker')).toBe(false);
    });

    it('should return correct hasAnyRole for mock role', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAnyRole(['Admin'])).toBe(true);
      expect(result.current.hasAnyRole(['Admin', 'Recruiter'])).toBe(true);
      expect(result.current.hasAnyRole(['Recruiter', 'JobSeeker'])).toBe(false);
    });

    it('should return correct hasAllRoles for mock role', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAllRoles(['Admin'])).toBe(true);
      expect(result.current.hasAllRoles(['Admin', 'Admin'])).toBe(true);
      expect(result.current.hasAllRoles(['Admin', 'Recruiter'])).toBe(false);
    });

    it('should be authenticated in mock mode', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should have undefined user in mock mode', () => {
      const { result } = renderHook(() => useRoles());

      expect(result.current.user).toBeUndefined();
    });
  });

  describe('Mock Role Variations', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
    });

    it('should support Recruiter mock role', () => {
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'Recruiter';
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      const { result } = renderHook(() => useRoles());

      expect(result.current.roles).toEqual(['Recruiter']);
      expect(result.current.primaryRole).toBe('Recruiter');
      expect(result.current.hasRole('Recruiter')).toBe(true);
      expect(result.current.hasRole('Admin')).toBe(false);
    });

    it('should support JobSeeker mock role', () => {
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'JobSeeker';
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      const { result } = renderHook(() => useRoles());

      expect(result.current.roles).toEqual(['JobSeeker']);
      expect(result.current.primaryRole).toBe('JobSeeker');
      expect(result.current.hasRole('JobSeeker')).toBe(true);
      expect(result.current.hasRole('Admin')).toBe(false);
    });

    it('should default to Admin for invalid mock role', () => {
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'InvalidRole';
      vi.mocked(getFeatureFlag).mockReturnValue('InvalidRole');

      const { result } = renderHook(() => useRoles());

      expect(result.current.roles).toEqual(['Admin']);
      expect(result.current.primaryRole).toBe('Admin');
    });
  });

  describe('Auth Mode (AUTH_ENABLED=true)', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
    });

    it('should return fallback role when auth is enabled', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      const { result } = renderHook(() => useRoles());

      expect(result.current.roles).toEqual(['Admin']);
      expect(result.current.primaryRole).toBe('Admin');
    });

    it('should use fallback role for role checks in auth mode', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasRole('Recruiter')).toBe(true);
      expect(result.current.hasRole('Admin')).toBe(false);
    });
  });

  describe('Debug Mode', () => {
    it('should log debug info when AUTH_DEBUG is true in mock mode', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.AUTH_DEBUG as boolean) = true;

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderHook(() => useRoles());

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should log debug info when AUTH_DEBUG is true in auth mode', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      (FEATURE_FLAGS.AUTH_DEBUG as boolean) = true;

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      renderHook(() => useRoles());

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('Role Type', () => {
    it('should export UserRole type', () => {
      const adminRole: UserRole = 'Admin';
      const recruiterRole: UserRole = 'Recruiter';
      const jobSeekerRole: UserRole = 'JobSeeker';

      expect(adminRole).toBe('Admin');
      expect(recruiterRole).toBe('Recruiter');
      expect(jobSeekerRole).toBe('JobSeeker');
    });

    it('should accept all valid UserRole values', () => {
      const roles: UserRole[] = ['JobSeeker', 'Recruiter', 'Admin'];
      expect(roles).toHaveLength(3);
    });
  });

  describe('Helper Functions', () => {
    describe('isValidRole', () => {
      it('should return true for valid roles', () => {
        expect(isValidRole('Admin')).toBe(true);
        expect(isValidRole('Recruiter')).toBe(true);
        expect(isValidRole('JobSeeker')).toBe(true);
      });

      it('should return false for invalid roles', () => {
        expect(isValidRole('admin')).toBe(false);
        expect(isValidRole('recruiter')).toBe(false);
        expect(isValidRole('job_seeker')).toBe(false);
        expect(isValidRole('Invalid')).toBe(false);
        expect(isValidRole('')).toBe(false);
      });
    });

    describe('normalizeRole', () => {
      it('should normalize lowercase to PascalCase', () => {
        expect(normalizeRole('admin')).toBe('Admin');
        expect(normalizeRole('recruiter')).toBe('Recruiter');
        expect(normalizeRole('jobseeker')).toBe('JobSeeker');
      });

      it('should normalize snake_case to PascalCase', () => {
        expect(normalizeRole('job_seeker')).toBe('JobSeeker');
        expect(normalizeRole('job_seeker_role')).toBe('JobSeekerRole');
      });

      it('should normalize kebab-case to PascalCase', () => {
        expect(normalizeRole('job-seeker')).toBe('JobSeeker');
      });

      it('should normalize with spaces to PascalCase', () => {
        expect(normalizeRole('job seeker')).toBe('JobSeeker');
      });

      it('should return undefined for invalid roles', () => {
        expect(normalizeRole('invalid')).toBeUndefined();
        expect(normalizeRole('')).toBeUndefined();
        expect(normalizeRole('random_text')).toBeUndefined();
      });

      it('should handle already normalized roles', () => {
        expect(normalizeRole('Admin')).toBe('Admin');
        expect(normalizeRole('Recruiter')).toBe('Recruiter');
        expect(normalizeRole('JobSeeker')).toBe('JobSeeker');
      });
    });

    describe('getRoleLevel', () => {
      it('should return correct levels for all roles', () => {
        expect(getRoleLevel('Admin')).toBe(3);
        expect(getRoleLevel('Recruiter')).toBe(2);
        expect(getRoleLevel('JobSeeker')).toBe(1);
      });
    });

    describe('compareRoles', () => {
      it('should return positive when first role is higher', () => {
        expect(compareRoles('Admin', 'Recruiter')).toBeGreaterThan(0);
        expect(compareRoles('Admin', 'JobSeeker')).toBeGreaterThan(0);
        expect(compareRoles('Recruiter', 'JobSeeker')).toBeGreaterThan(0);
      });

      it('should return negative when first role is lower', () => {
        expect(compareRoles('JobSeeker', 'Recruiter')).toBeLessThan(0);
        expect(compareRoles('JobSeeker', 'Admin')).toBeLessThan(0);
        expect(compareRoles('Recruiter', 'Admin')).toBeLessThan(0);
      });

      it('should return zero for equal roles', () => {
        expect(compareRoles('Admin', 'Admin')).toBe(0);
        expect(compareRoles('Recruiter', 'Recruiter')).toBe(0);
        expect(compareRoles('JobSeeker', 'JobSeeker')).toBe(0);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty hasAnyRole array', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAnyRole([])).toBe(false);
    });

    it('should handle empty hasAllRoles array', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAllRoles([])).toBe(true);
    });

    it('should handle duplicate roles in hasAnyRole', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAnyRole(['Admin', 'Admin'])).toBe(true);
    });

    it('should handle duplicate roles in hasAllRoles', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAllRoles(['Admin', 'Admin'])).toBe(true);
    });

    it('should handle all three roles in hasAnyRole', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasAnyRole(['JobSeeker', 'Recruiter', 'Admin'])).toBe(true);
    });
  });

  describe('Integration Scenarios', () => {
    it('should support Admin accessing all role-specific content', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'Admin';
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasRole('Admin')).toBe(true);
      expect(result.current.hasAnyRole(['Admin', 'Recruiter'])).toBe(true);
      expect(result.current.hasAnyRole(['Admin', 'JobSeeker'])).toBe(true);
      expect(result.current.hasAnyRole(['Recruiter', 'JobSeeker'])).toBe(false);
    });

    it('should support Recruiter accessing recruiter-specific content', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'Recruiter';
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasRole('Recruiter')).toBe(true);
      expect(result.current.hasAnyRole(['Recruiter', 'Admin'])).toBe(true);
      expect(result.current.hasRole('Admin')).toBe(false);
      expect(result.current.hasAnyRole(['JobSeeker'])).toBe(false);
    });

    it('should support JobSeeker accessing jobseeker-specific content', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.MOCK_ROLE as string) = 'JobSeeker';
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      const { result } = renderHook(() => useRoles());

      expect(result.current.hasRole('JobSeeker')).toBe(true);
      expect(result.current.hasRole('Recruiter')).toBe(false);
      expect(result.current.hasRole('Admin')).toBe(false);
    });
  });
});
