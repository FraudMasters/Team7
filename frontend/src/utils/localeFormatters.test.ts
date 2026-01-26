/**
 * Tests for Locale Formatters
 *
 * Tests locale-aware formatting utilities for dates, numbers, and currency.
 */

import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatDateShort,
  formatDateTime,
  formatTime,
  formatNumber,
  formatPercent,
  formatCurrency,
  formatFileSize,
  formatRelativeTime,
  getSupportedLocales,
} from './localeFormatters';
import type { SupportedLanguage } from '@/contexts/LanguageContext';

describe('localeFormatters', () => {
  const testDate = new Date('2024-01-15T14:30:00Z');

  describe('formatDate', () => {
    it('should format date in English locale', () => {
      const result = formatDate(testDate, 'en');
      expect(result).toMatch(/January/);
      expect(result).toMatch(/15/);
      expect(result).toMatch(/2024/);
    });

    it('should format date in Russian locale', () => {
      const result = formatDate(testDate, 'ru');
      // Russian date format: 15 января 2024 г.
      expect(result).toMatch(/15/);
      expect(result).toMatch(/января/);
      expect(result).toMatch(/2024/);
    });

    it('should accept ISO date string', () => {
      const result = formatDate('2024-01-15', 'en');
      expect(result).toMatch(/January/);
      expect(result).toMatch(/15/);
      expect(result).toMatch(/2024/);
    });

    it('should accept timestamp', () => {
      const timestamp = new Date('2024-01-15').getTime();
      const result = formatDate(timestamp, 'en');
      expect(result).toMatch(/January/);
      expect(result).toMatch(/15/);
      expect(result).toMatch(/2024/);
    });

    it('should accept custom format options', () => {
      const result = formatDate(testDate, 'en', { month: 'short' });
      expect(result).toMatch(/Jan/);
    });

    it('should throw error for invalid date string', () => {
      expect(() => formatDate('invalid-date', 'en')).toThrow();
    });

    it('should throw error for invalid locale', () => {
      expect(() => formatDate(testDate, 'de' as SupportedLanguage)).toThrow();
    });

    it('should throw error for invalid date object', () => {
      const invalidDate = new Date('invalid');
      expect(() => formatDate(invalidDate, 'en')).toThrow();
    });
  });

  describe('formatDateShort', () => {
    it('should format date with short month in English', () => {
      const result = formatDateShort(testDate, 'en');
      expect(result).toMatch(/Jan/);
      expect(result).toMatch(/15/);
      expect(result).toMatch(/2024/);
    });

    it('should format date with short month in Russian', () => {
      const result = formatDateShort(testDate, 'ru');
      // Russian short format: 15 янв. 2024 г.
      expect(result).toMatch(/15/);
      expect(result).toMatch(/янв/);
      expect(result).toMatch(/2024/);
    });
  });

  describe('formatDateTime', () => {
    it('should format date and time in English locale', () => {
      const result = formatDateTime(testDate, 'en');
      expect(result).toMatch(/January/);
      expect(result).toMatch(/15/);
      expect(result).toMatch(/2024/);
      // Time should be present
      expect(result).toMatch(/\d{2}:\d{2}/);
    });

    it('should format date and time in Russian locale', () => {
      const result = formatDateTime(testDate, 'ru');
      expect(result).toMatch(/15/);
      expect(result).toMatch(/января/);
      expect(result).toMatch(/2024/);
      // Time should be present (14:30 format in Russian)
      expect(result).toMatch(/14:30/);
    });
  });

  describe('formatTime', () => {
    it('should format time in English locale (12-hour)', () => {
      const result = formatTime(testDate, 'en');
      // English uses 12-hour format with AM/PM
      expect(result).toMatch(/(\d{1,2}:\d{2}\s?[AP]M)/);
    });

    it('should format time in Russian locale (24-hour)', () => {
      const result = formatTime(testDate, 'ru');
      // Russian uses 24-hour format
      expect(result).toMatch(/14:30/);
    });

    it('should accept custom format options', () => {
      const result = formatTime(testDate, 'en', { hour: 'numeric', minute: undefined });
      expect(result).toBeTruthy();
    });
  });

  describe('formatNumber', () => {
    it('should format integer in English locale', () => {
      const result = formatNumber(1234567, 'en');
      // English uses comma as thousand separator
      expect(result).toBe('1,234,567');
    });

    it('should format integer in Russian locale', () => {
      const result = formatNumber(1234567, 'ru');
      // Russian uses space as thousand separator
      expect(result).toBe('1 234 567');
    });

    it('should format decimal number in English locale', () => {
      const result = formatNumber(1234.56, 'en');
      // English uses period as decimal separator
      expect(result).toBe('1,234.56');
    });

    it('should format decimal number in Russian locale', () => {
      const result = formatNumber(1234.56, 'ru');
      // Russian uses comma as decimal separator
      expect(result).toBe('1 234,56');
    });

    it('should format large number correctly', () => {
      const result = formatNumber(1000000000, 'en');
      expect(result).toBe('1,000,000,000');
    });

    it('should format small decimal number', () => {
      const result = formatNumber(0.123, 'en');
      expect(result).toBe('0.123');
    });

    it('should accept custom format options', () => {
      const result = formatNumber(1234.567, 'en', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      expect(result).toBe('1,234.57');
    });

    it('should throw error for NaN', () => {
      expect(() => formatNumber(NaN, 'en')).toThrow();
    });

    it('should throw error for invalid locale', () => {
      expect(() => formatNumber(1234, 'de' as SupportedLanguage)).toThrow();
    });
  });

  describe('formatPercent', () => {
    it('should format percentage in English locale', () => {
      const result = formatPercent(0.75, 'en');
      expect(result).toBe('75.0%');
    });

    it('should format percentage in Russian locale', () => {
      const result = formatPercent(0.75, 'ru');
      // Russian uses comma as decimal separator
      expect(result).toBe('75,0%');
    });

    it('should format 100% correctly', () => {
      const result = formatPercent(1, 'en');
      expect(result).toBe('100.0%');
    });

    it('should format 0% correctly', () => {
      const result = formatPercent(0, 'en');
      expect(result).toBe('0.0%');
    });

    it('should format percentage with custom decimal places', () => {
      const result = formatPercent(0.7555, 'en', 2);
      expect(result).toBe('75.55%');
    });

    it('should throw error for NaN', () => {
      expect(() => formatPercent(NaN, 'en')).toThrow();
    });
  });

  describe('formatCurrency', () => {
    it('should format USD in English locale', () => {
      const result = formatCurrency(1234.56, 'en', 'USD');
      expect(result).toBe('$1,234.56');
    });

    it('should format RUB in Russian locale', () => {
      const result = formatCurrency(1234.56, 'ru', 'RUB');
      // Russian format: 1 234,56 ₽
      expect(result).toMatch(/1 234,56/);
      expect(result).toMatch(/₽/);
    });

    it('should format EUR in English locale', () => {
      const result = formatCurrency(1000, 'en', 'EUR');
      expect(result).toMatch(/€/);
      expect(result).toMatch(/1,000/);
    });

    it('should format integer amount correctly', () => {
      const result = formatCurrency(1000, 'en', 'USD');
      expect(result).toBe('$1,000.00');
    });

    it('should accept custom format options', () => {
      const result = formatCurrency(1234.56, 'en', 'USD', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      });
      expect(result).toBe('$1,235');
    });

    it('should throw error for NaN', () => {
      expect(() => formatCurrency(NaN, 'en', 'USD')).toThrow();
    });

    it('should throw error for invalid locale', () => {
      expect(() => formatCurrency(1234, 'de' as SupportedLanguage, 'USD')).toThrow();
    });
  });

  describe('formatFileSize', () => {
    it('should format bytes', () => {
      const result = formatFileSize(512, 'en');
      expect(result).toBe('512 B');
    });

    it('should format kilobytes in English locale', () => {
      const result = formatFileSize(1024, 'en');
      expect(result).toBe('1.0 KB');
    });

    it('should format kilobytes in Russian locale', () => {
      const result = formatFileSize(1024, 'ru');
      expect(result).toBe('1,0 KB');
    });

    it('should format megabytes in English locale', () => {
      const result = formatFileSize(1048576, 'en');
      expect(result).toBe('1.0 MB');
    });

    it('should format megabytes in Russian locale', () => {
      const result = formatFileSize(1048576, 'ru');
      expect(result).toBe('1,0 MB');
    });

    it('should format gigabytes', () => {
      const result = formatFileSize(1073741824, 'en');
      expect(result).toBe('1.0 GB');
    });

    it('should format with custom decimal places', () => {
      const result = formatFileSize(1536, 'en', 2);
      expect(result).toBe('1.50 KB');
    });

    it('should throw error for negative number', () => {
      expect(() => formatFileSize(-100, 'en')).toThrow();
    });

    it('should throw error for NaN', () => {
      expect(() => formatFileSize(NaN, 'en')).toThrow();
    });
  });

  describe('formatRelativeTime', () => {
    it('should format past time in days (English)', () => {
      const result = formatRelativeTime(-2, 'day', 'en');
      expect(result).toBe('2 days ago');
    });

    it('should format past time in days (Russian)', () => {
      const result = formatRelativeTime(-2, 'day', 'ru');
      expect(result).toBe('2 дня назад');
    });

    it('should format future time in hours (English)', () => {
      const result = formatRelativeTime(3, 'hour', 'en');
      expect(result).toBe('in 3 hours');
    });

    it('should format future time in hours (Russian)', () => {
      const result = formatRelativeTime(3, 'hour', 'ru');
      expect(result).toBe('через 3 часа');
    });

    it('should format past time in minutes', () => {
      const result = formatRelativeTime(-30, 'minute', 'en');
      expect(result).toBe('30 minutes ago');
    });

    it('should format past time in seconds', () => {
      const result = formatRelativeTime(-45, 'second', 'en');
      expect(result).toBe('45 seconds ago');
    });

    it('should format future time in weeks', () => {
      const result = formatRelativeTime(2, 'week', 'en');
      expect(result).toBe('in 2 weeks');
    });

    it('should format past time in months', () => {
      const result = formatRelativeTime(-6, 'month', 'en');
      expect(result).toBe('6 months ago');
    });

    it('should format past time in years', () => {
      const result = formatRelativeTime(-1, 'year', 'en');
      expect(result).toBe('1 year ago');
    });

    it('should throw error for invalid locale', () => {
      expect(() => formatRelativeTime(-2, 'day', 'de' as SupportedLanguage)).toThrow();
    });
  });

  describe('getSupportedLocales', () => {
    it('should return array of supported locales', () => {
      const result = getSupportedLocales();
      expect(result).toEqual(['en', 'ru']);
    });

    it('should return exactly two locales', () => {
      const result = getSupportedLocales();
      expect(result).toHaveLength(2);
    });

    it('should contain English', () => {
      const result = getSupportedLocales();
      expect(result).toContain('en');
    });

    it('should contain Russian', () => {
      const result = getSupportedLocales();
      expect(result).toContain('ru');
    });
  });

  describe('Edge Cases and Integration', () => {
    it('should handle leap year dates correctly', () => {
      const leapDate = new Date('2024-02-29');
      const result = formatDate(leapDate, 'en');
      expect(result).toMatch(/February/);
      expect(result).toMatch(/29/);
      expect(result).toMatch(/2024/);
    });

    it('should handle end of month dates', () => {
      const endDate = new Date('2024-01-31');
      const result = formatDate(endDate, 'ru');
      expect(result).toMatch(/31/);
      expect(result).toMatch(/января/);
    });

    it('should handle very large numbers', () => {
      const result = formatNumber(999999999999, 'en');
      expect(result).toBe('999,999,999,999');
    });

    it('should handle very small decimals', () => {
      const result = formatNumber(0.000001, 'en');
      expect(result).toBeTruthy();
      expect(result).toMatch(/0/);
    });

    it('should handle zero values', () => {
      expect(formatNumber(0, 'en')).toBe('0');
      expect(formatCurrency(0, 'en', 'USD')).toBe('$0.00');
      expect(formatPercent(0, 'en')).toBe('0.0%');
      expect(formatFileSize(0, 'en')).toBe('0 B');
    });

    it('should handle negative numbers', () => {
      const result = formatNumber(-1234.56, 'en');
      expect(result).toMatch(/-/);
      expect(result).toMatch(/1,234.56/);
    });

    it('should handle negative currency', () => {
      const result = formatCurrency(-100, 'en', 'USD');
      expect(result).toMatch(/-/);
      expect(result).toMatch(/\$100/);
    });
  });
});
