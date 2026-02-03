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
  formatDuration,
  formatPhoneNumber,
  formatAddress,
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

  describe('formatDuration', () => {
    describe('with seconds input (number)', () => {
      it('should format seconds only in English', () => {
        const result = formatDuration(30, 'en');
        expect(result).toBe('30s');
      });

      it('should format seconds only in Russian', () => {
        const result = formatDuration(30, 'ru');
        expect(result).toBe('30 с');
      });

      it('should format minutes only in English', () => {
        const result = formatDuration(2700, 'en'); // 45 minutes
        expect(result).toBe('45m');
      });

      it('should format minutes only in Russian', () => {
        const result = formatDuration(2700, 'ru'); // 45 minutes
        expect(result).toBe('45 мин');
      });

      it('should format hours and minutes in English', () => {
        const result = formatDuration(9000, 'en'); // 2h 30m
        expect(result).toBe('2h 30m');
      });

      it('should format hours and minutes in Russian', () => {
        const result = formatDuration(9000, 'ru'); // 2h 30m
        expect(result).toBe('2 ч 30 мин');
      });

      it('should format days and hours in English', () => {
        const result = formatDuration(176400, 'en'); // 2d 1h
        expect(result).toBe('2d 1h');
      });

      it('should format days and hours in Russian', () => {
        const result = formatDuration(176400, 'ru'); // 2d 1h
        expect(result).toBe('2 д 1 ч');
      });

      it('should format full duration with all units in English', () => {
        const result = formatDuration(93784, 'en'); // 1d 2h 3m 4s
        expect(result).toBe('1d 2h 3m 4s');
      });

      it('should format full duration with all units in Russian', () => {
        const result = formatDuration(93784, 'ru'); // 1d 2h 3m 4s
        expect(result).toBe('1 д 2 ч 3 мин 4 с');
      });

      it('should format zero duration in English', () => {
        const result = formatDuration(0, 'en');
        expect(result).toBe('0s');
      });

      it('should format zero duration in Russian', () => {
        const result = formatDuration(0, 'ru');
        expect(result).toBe('0 с');
      });

      it('should format large duration with multiple days in English', () => {
        const result = formatDuration(345600, 'en'); // 4 days
        expect(result).toBe('4d');
      });

      it('should format large duration with multiple days in Russian', () => {
        const result = formatDuration(345600, 'ru'); // 4 days
        expect(result).toBe('4 д');
      });
    });

    describe('with DurationObject input', () => {
      it('should format days only in English', () => {
        const result = formatDuration({ days: 3 }, 'en');
        expect(result).toBe('3d');
      });

      it('should format days only in Russian', () => {
        const result = formatDuration({ days: 3 }, 'ru');
        expect(result).toBe('3 д');
      });

      it('should format hours only in English', () => {
        const result = formatDuration({ hours: 5 }, 'en');
        expect(result).toBe('5h');
      });

      it('should format hours only in Russian', () => {
        const result = formatDuration({ hours: 5 }, 'ru');
        expect(result).toBe('5 ч');
      });

      it('should format minutes only in English', () => {
        const result = formatDuration({ minutes: 45 }, 'en');
        expect(result).toBe('45m');
      });

      it('should format minutes only in Russian', () => {
        const result = formatDuration({ minutes: 45 }, 'ru');
        expect(result).toBe('45 мин');
      });

      it('should format seconds only in English', () => {
        const result = formatDuration({ seconds: 30 }, 'en');
        expect(result).toBe('30s');
      });

      it('should format seconds only in Russian', () => {
        const result = formatDuration({ seconds: 30 }, 'ru');
        expect(result).toBe('30 с');
      });

      it('should format days and hours in English', () => {
        const result = formatDuration({ days: 1, hours: 4 }, 'en');
        expect(result).toBe('1d 4h');
      });

      it('should format days and hours in Russian', () => {
        const result = formatDuration({ days: 1, hours: 4 }, 'ru');
        expect(result).toBe('1 д 4 ч');
      });

      it('should format hours and minutes in English', () => {
        const result = formatDuration({ hours: 2, minutes: 30 }, 'en');
        expect(result).toBe('2h 30m');
      });

      it('should format hours and minutes in Russian', () => {
        const result = formatDuration({ hours: 2, minutes: 30 }, 'ru');
        expect(result).toBe('2 ч 30 мин');
      });

      it('should format minutes and seconds in English', () => {
        const result = formatDuration({ minutes: 15, seconds: 45 }, 'en');
        expect(result).toBe('15m 45s');
      });

      it('should format minutes and seconds in Russian', () => {
        const result = formatDuration({ minutes: 15, seconds: 45 }, 'ru');
        expect(result).toBe('15 мин 45 с');
      });

      it('should format all units in English', () => {
        const result = formatDuration({ days: 1, hours: 2, minutes: 3, seconds: 4 }, 'en');
        expect(result).toBe('1d 2h 3m 4s');
      });

      it('should format all units in Russian', () => {
        const result = formatDuration({ days: 1, hours: 2, minutes: 3, seconds: 4 }, 'ru');
        expect(result).toBe('1 д 2 ч 3 мин 4 с');
      });

      it('should handle zero values in DurationObject', () => {
        const result = formatDuration({ days: 0, hours: 0, minutes: 0, seconds: 0 }, 'en');
        expect(result).toBe('0s');
      });

      it('should handle partial DurationObject with zeros', () => {
        const result = formatDuration({ days: 1, hours: 0, minutes: 30 }, 'en');
        expect(result).toBe('1d 30m');
      });

      it('should handle missing properties in DurationObject', () => {
        const result = formatDuration({ days: 2, minutes: 15 }, 'en');
        expect(result).toBe('2d 15m');
      });
    });

    describe('error handling', () => {
      it('should throw error for negative number', () => {
        expect(() => formatDuration(-100, 'en')).toThrow();
      });

      it('should throw error for Infinity', () => {
        expect(() => formatDuration(Infinity, 'en')).toThrow();
      });

      it('should throw error for NaN', () => {
        expect(() => formatDuration(NaN, 'en')).toThrow();
      });

      it('should throw error for negative days in DurationObject', () => {
        expect(() => formatDuration({ days: -1 }, 'en')).toThrow();
      });

      it('should throw error for negative hours in DurationObject', () => {
        expect(() => formatDuration({ hours: -5 }, 'en')).toThrow();
      });

      it('should throw error for negative minutes in DurationObject', () => {
        expect(() => formatDuration({ minutes: -30 }, 'en')).toThrow();
      });

      it('should throw error for negative seconds in DurationObject', () => {
        expect(() => formatDuration({ seconds: -45 }, 'en')).toThrow();
      });

      it('should throw error for mixed negative values in DurationObject', () => {
        expect(() => formatDuration({ days: 1, hours: -2 }, 'en')).toThrow();
      });

      it('should throw error for invalid locale with number input', () => {
        expect(() => formatDuration(3600, 'de' as SupportedLanguage)).toThrow();
      });

      it('should throw error for invalid locale with DurationObject', () => {
        expect(() => formatDuration({ hours: 2 }, 'de' as SupportedLanguage)).toThrow();
      });

      it('should throw error for null input', () => {
        expect(() => formatDuration(null as any, 'en')).toThrow();
      });

      it('should throw error for undefined input', () => {
        expect(() => formatDuration(undefined as any, 'en')).toThrow();
      });

      it('should throw error for string input', () => {
        expect(() => formatDuration('invalid' as any, 'en')).toThrow();
      });
    });

    describe('edge cases', () => {
      it('should handle 1 second', () => {
        const result = formatDuration(1, 'en');
        expect(result).toBe('1s');
      });

      it('should handle 1 minute', () => {
        const result = formatDuration(60, 'en');
        expect(result).toBe('1m');
      });

      it('should handle 1 hour', () => {
        const result = formatDuration(3600, 'en');
        expect(result).toBe('1h');
      });

      it('should handle 1 day', () => {
        const result = formatDuration(86400, 'en');
        expect(result).toBe('1d');
      });

      it('should handle duration with seconds that roll over to minutes', () => {
        const result = formatDuration(90, 'en'); // 1m 30s
        expect(result).toBe('1m 30s');
      });

      it('should handle duration with minutes that roll over to hours', () => {
        const result = formatDuration(5400, 'en'); // 1h 30m
        expect(result).toBe('1h 30m');
      });

      it('should handle duration with hours that roll over to days', () => {
        const result = formatDuration(90000, 'en'); // 1d 1h
        expect(result).toBe('1d 1h');
      });

      it('should handle very large duration', () => {
        const result = formatDuration(999999, 'en');
        expect(result).toBeTruthy();
        expect(result).toContain('d');
      });

      it('should handle DurationObject with decimal values (flooring)', () => {
        const result = formatDuration({ hours: 2.5, minutes: 30.8 }, 'en');
        expect(result).toBe('2h 30m');
      });
    });
  });

  describe('formatPhoneNumber', () => {
    describe('US/Canada phone numbers', () => {
      it('should format US phone number with country code (11 digits)', () => {
        const result = formatPhoneNumber('15551234567', 'en');
        expect(result).toBe('+1 (555) 123-4567');
      });

      it('should format US phone number with + prefix', () => {
        const result = formatPhoneNumber('+15551234567', 'en');
        expect(result).toBe('+1 (555) 123-4567');
      });

      it('should format US phone number without country code (10 digits)', () => {
        const result = formatPhoneNumber('5551234567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should format US phone number with dashes', () => {
        const result = formatPhoneNumber('555-123-4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should format US phone number with spaces', () => {
        const result = formatPhoneNumber('555 123 4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should format US phone number with parentheses and dashes', () => {
        const result = formatPhoneNumber('(555) 123-4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should format US phone number with mixed formatting', () => {
        const result = formatPhoneNumber('1 (555) 123-4567', 'en');
        expect(result).toBe('+1 (555) 123-4567');
      });
    });

    describe('Russian phone numbers', () => {
      it('should format Russian phone number with country code', () => {
        const result = formatPhoneNumber('75551234567', 'ru');
        expect(result).toBe('+7 (555) 123-4567');
      });

      it('should format Russian phone number with + prefix', () => {
        const result = formatPhoneNumber('+75551234567', 'ru');
        expect(result).toBe('+7 (555) 123-4567');
      });

      it('should format Russian phone number without country code', () => {
        const result = formatPhoneNumber('5551234567', 'ru');
        expect(result).toBe('(555) 123-4567');
      });

      it('should format Russian phone number in English locale', () => {
        const result = formatPhoneNumber('75551234567', 'en');
        expect(result).toBe('+7 (555) 123-4567');
      });
    });

    describe('UK phone numbers', () => {
      it('should format UK phone number with country code (44)', () => {
        const result = formatPhoneNumber('445551234567', 'en');
        expect(result).toBe('+44 (555) 123-4567');
      });

      it('should format UK phone number with + prefix', () => {
        const result = formatPhoneNumber('+445551234567', 'en');
        expect(result).toBe('+44 (555) 123-4567');
      });

      it('should format UK phone number without country code', () => {
        const result = formatPhoneNumber('5551234567', 'en');
        expect(result).toBe('(555) 123-4567');
      });
    });

    describe('shorter phone numbers', () => {
      it('should format 7-digit number with dashes', () => {
        const result = formatPhoneNumber('5551234', 'en');
        expect(result).toBe('555-1234');
      });

      it('should format 7-digit number with country code', () => {
        const result = formatPhoneNumber('15551234', 'en');
        expect(result).toBe('+1 555-1234');
      });

      it('should format very short number (less than 7 digits)', () => {
        const result = formatPhoneNumber('555123', 'en');
        expect(result).toBe('555123');
      });

      it('should format very short number with country code', () => {
        const result = formatPhoneNumber('1555123', 'en');
        expect(result).toBe('+1 555123');
      });

      it('should format 6-digit number', () => {
        const result = formatPhoneNumber('123456', 'en');
        expect(result).toBe('123456');
      });
    });

    describe('phone numbers with various separators', () => {
      it('should handle phone number with dots', () => {
        const result = formatPhoneNumber('555.123.4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should handle phone number with mixed separators', () => {
        const result = formatPhoneNumber('555-123.4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should handle phone number with multiple spaces', () => {
        const result = formatPhoneNumber('555  123  4567', 'en');
        expect(result).toBe('(555) 123-4567');
      });
    });

    describe('edge cases', () => {
      it('should handle phone number with extension digits (>10)', () => {
        const result = formatPhoneNumber('1555123456789', 'en');
        // Should only format first 10 digits of national number
        expect(result).toBe('+1 (555) 123-4567');
      });

      it('should handle phone number with leading zeros', () => {
        const result = formatPhoneNumber('05551234567', 'en');
        expect(result).toBe('(555) 123-4567');
      });

      it('should handle single digit', () => {
        const result = formatPhoneNumber('1', 'en');
        expect(result).toBe('1');
      });

      it('should handle two digits', () => {
        const result = formatPhoneNumber('12', 'en');
        expect(result).toBe('12');
      });

      it('should handle three digits', () => {
        const result = formatPhoneNumber('123', 'en');
        expect(result).toBe('123');
      });
    });

    describe('error handling', () => {
      it('should throw error for empty string', () => {
        expect(() => formatPhoneNumber('', 'en')).toThrow();
      });

      it('should throw error for string with no digits', () => {
        expect(() => formatPhoneNumber('abc', 'en')).toThrow();
      });

      it('should throw error for string with only separators', () => {
        expect(() => formatPhoneNumber('()- ', 'en')).toThrow();
      });

      it('should throw error for invalid locale', () => {
        expect(() => formatPhoneNumber('5551234567', 'de' as SupportedLanguage)).toThrow();
      });

      it('should throw error for whitespace only', () => {
        expect(() => formatPhoneNumber('   ', 'en')).toThrow();
      });
    });

    describe('locale independence', () => {
      it('should produce same format for same number in different locales', () => {
        const resultEn = formatPhoneNumber('15551234567', 'en');
        const resultRu = formatPhoneNumber('15551234567', 'ru');
        // Phone format should be the same regardless of locale
        expect(resultEn).toBe(resultRu);
      });

      it('should handle Russian number in English locale', () => {
        const result = formatPhoneNumber('75551234567', 'en');
        expect(result).toBe('+7 (555) 123-4567');
      });

      it('should handle US number in Russian locale', () => {
        const result = formatPhoneNumber('15551234567', 'ru');
        expect(result).toBe('+1 (555) 123-4567');
      });
    });
  });

  describe('formatAddress', () => {
    describe('English locale formatting', () => {
      it('should format complete address in English', () => {
        const address = {
          street: '123 Main Street',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/123 Main Street/);
        expect(result).toMatch(/Springfield, IL 62701/);
        expect(result).toMatch(/USA/);
      });

      it('should format address with street2 line in English', () => {
        const address = {
          street: '123 Main Street',
          street2: 'Apt 4B',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/123 Main Street/);
        expect(result).toMatch(/Apt 4B/);
        expect(result).toMatch(/Springfield/);
      });

      it('should format partial address (street and city only) in English', () => {
        const address = {
          street: '456 Oak Avenue',
          city: 'Moscow',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/456 Oak Avenue/);
        expect(result).toMatch(/Moscow/);
      });

      it('should format address without street in English', () => {
        const address = {
          city: 'Chicago',
          state: 'IL',
          postalCode: '60601',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/Chicago, IL 60601/);
      });

      it('should format address with only street and country in English', () => {
        const address = {
          street: '789 Pine Road',
          country: 'Canada',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/789 Pine Road/);
        expect(result).toMatch(/Canada/);
      });

      it('should handle address with only city in English', () => {
        const address = {
          city: 'Boston',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('Boston');
      });

      it('should handle address with postal code and city but no state in English', () => {
        const address = {
          city: 'Seattle',
          postalCode: '98101',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBeTruthy();
        expect(result).toMatch(/Seattle/);
        expect(result).toMatch(/98101/);
      });
    });

    describe('Russian locale formatting', () => {
      it('should format complete address in Russian', () => {
        const address = {
          street: '123 Main Street',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'ru');
        // Russian format: country, postal code, city/state, street
        const lines = result.split('\n');
        expect(lines[0]).toBe('USA');
        expect(lines[1]).toBe('62701');
        expect(result).toMatch(/Springfield, IL/);
        expect(result).toMatch(/123 Main Street/);
      });

      it('should format address with street2 in Russian', () => {
        const address = {
          street: '123 Main Street',
          street2: 'Apt 4B',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toMatch(/USA/);
        expect(result).toMatch(/62701/);
        expect(result).toMatch(/Springfield, IL/);
        expect(result).toMatch(/123 Main Street/);
        expect(result).toMatch(/Apt 4B/);
      });

      it('should format partial address in Russian', () => {
        const address = {
          street: '456 Oak Avenue',
          city: 'Moscow',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toMatch(/Moscow/);
        expect(result).toMatch(/456 Oak Avenue/);
      });

      it('should format address without country in Russian', () => {
        const address = {
          postalCode: '101000',
          city: 'Moscow',
          street: 'Red Square',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toMatch(/101000/);
        expect(result).toMatch(/Moscow/);
        expect(result).toMatch(/Red Square/);
      });

      it('should format address with only city in Russian', () => {
        const address = {
          city: 'Saint Petersburg',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toBe('Saint Petersburg');
      });

      it('should handle address with postal code and city but no state in Russian', () => {
        const address = {
          city: 'Sochi',
          postalCode: '354000',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toBeTruthy();
        expect(result).toMatch(/Sochi/);
        expect(result).toMatch(/354000/);
      });
    });

    describe('field ordering and separators', () => {
      it('should use proper line breaks in English format', () => {
        const address = {
          street: '123 Main Street',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'en');
        const lines = result.split('\n');
        expect(lines.length).toBeGreaterThanOrEqual(2);
        expect(lines[0]).toContain('123 Main Street');
        expect(lines.some(line => line.includes('Springfield'))).toBe(true);
      });

      it('should use proper line breaks in Russian format', () => {
        const address = {
          street: '123 Main Street',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const result = formatAddress(address, 'ru');
        const lines = result.split('\n');
        expect(lines.length).toBeGreaterThanOrEqual(2);
        expect(lines[0]).toBe('USA');
        expect(lines[1]).toBe('62701');
      });

      it('should handle comma separator between city and state in English', () => {
        const address = {
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/Springfield, IL/);
      });

      it('should handle comma separator between city and state in Russian', () => {
        const address = {
          city: 'Springfield',
          state: 'IL',
        };
        const result = formatAddress(address, 'ru');
        expect(result).toMatch(/Springfield, IL/);
      });
    });

    describe('whitespace handling', () => {
      it('should trim whitespace from address fields in English', () => {
        const address = {
          street: '  123 Main Street  ',
          city: '  Springfield  ',
          state: 'IL',
          postalCode: '62701',
        };
        const result = formatAddress(address, 'en');
        expect(result).not.toMatch(/  123 Main Street  /);
        expect(result).toMatch(/123 Main Street/);
      });

      it('should trim whitespace from address fields in Russian', () => {
        const address = {
          street: '  123 Main Street  ',
          city: '  Springfield  ',
          state: 'IL',
        };
        const result = formatAddress(address, 'ru');
        expect(result).not.toMatch(/  123 Main Street  /);
        expect(result).toMatch(/123 Main Street/);
      });

      it('should handle empty string values in address', () => {
        const address = {
          street: '123 Main Street',
          city: '',
          state: 'IL',
          postalCode: '62701',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBeTruthy();
        expect(result).toMatch(/123 Main Street/);
        expect(result).toMatch(/IL/);
      });
    });

    describe('minimal and edge case addresses', () => {
      it('should handle address with only street', () => {
        const address = {
          street: '123 Main Street',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('123 Main Street');
      });

      it('should handle address with only city', () => {
        const address = {
          city: 'Boston',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('Boston');
      });

      it('should handle address with only state', () => {
        const address = {
          state: 'CA',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('CA');
      });

      it('should handle address with only postal code', () => {
        const address = {
          postalCode: '90210',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('90210');
      });

      it('should handle address with only country', () => {
        const address = {
          country: 'France',
        };
        const result = formatAddress(address, 'en');
        expect(result).toBe('France');
      });

      it('should handle address with street and street2 only', () => {
        const address = {
          street: '123 Main Street',
          street2: 'Apt 4B',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/123 Main Street/);
        expect(result).toMatch(/Apt 4B/);
      });

      it('should handle address with city and state only', () => {
        const address = {
          city: 'Denver',
          state: 'CO',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/Denver, CO/);
      });
    });

    describe('error handling', () => {
      it('should throw error for null address', () => {
        expect(() => formatAddress(null as any, 'en')).toThrow();
      });

      it('should throw error for undefined address', () => {
        expect(() => formatAddress(undefined as any, 'en')).toThrow();
      });

      it('should throw error for empty object', () => {
        expect(() => formatAddress({}, 'en')).toThrow();
      });

      it('should throw error for address with only empty strings', () => {
        const address = {
          street: '',
          city: '',
          state: '',
          postalCode: '',
          country: '',
        };
        expect(() => formatAddress(address, 'en')).toThrow();
      });

      it('should throw error for address with only whitespace', () => {
        const address = {
          street: '   ',
          city: '   ',
        };
        expect(() => formatAddress(address, 'en')).toThrow();
      });

      it('should throw error for invalid locale', () => {
        const address = {
          street: '123 Main Street',
        };
        expect(() => formatAddress(address, 'de' as SupportedLanguage)).toThrow();
      });

      it('should throw error for non-object address', () => {
        expect(() => formatAddress('invalid' as any, 'en')).toThrow();
      });

      it('should throw error for number address', () => {
        expect(() => formatAddress(12345 as any, 'en')).toThrow();
      });

      it('should throw error for array address', () => {
        expect(() => formatAddress([] as any, 'en')).toThrow();
      });

      it('should throw error for boolean address', () => {
        expect(() => formatAddress(true as any, 'en')).toThrow();
      });
    });

    describe('special characters and international addresses', () => {
      it('should handle address with special characters', () => {
        const address = {
          street: "O'Connor Street",
          city: "Saint-Jérôme",
          state: 'QC',
          postalCode: 'J7Z 0A1',
          country: 'Canada',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/O'Connor/);
        expect(result).toMatch(/Saint-Jérôme/);
      });

      it('should handle address with numbers and letters', () => {
        const address = {
          street: '12345A Main Street Suite 100',
          city: 'New York',
          state: 'NY',
          postalCode: '10001',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/12345A Main Street Suite 100/);
      });

      it('should handle address with hyphens', () => {
        const address = {
          street: 'A-1 Main Street',
          city: 'Niceville',
          state: 'FL',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/A-1 Main Street/);
      });

      it('should handle address with apostrophes in both locales', () => {
        const address = {
          street: "St. John's Avenue",
          city: "St. Paul's",
        };
        const resultEn = formatAddress(address, 'en');
        const resultRu = formatAddress(address, 'ru');
        expect(resultEn).toMatch(/St. John's/);
        expect(resultRu).toMatch(/St. John's/);
      });
    });

    describe('real-world address examples', () => {
      it('should format US residential address in English', () => {
        const address = {
          street: '742 Evergreen Terrace',
          city: 'Springfield',
          state: 'OR',
          postalCode: '97477',
          country: 'USA',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/742 Evergreen Terrace/);
        expect(result).toMatch(/Springfield, OR 97477/);
      });

      it('should format business address in English', () => {
        const address = {
          street: '350 Fifth Avenue, Suite 5100',
          street2: 'Empire State Building',
          city: 'New York',
          state: 'NY',
          postalCode: '10118',
          country: 'USA',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/350 Fifth Avenue, Suite 5100/);
        expect(result).toMatch(/Empire State Building/);
        expect(result).toMatch(/New York, NY 10118/);
      });

      it('should format PO Box address in English', () => {
        const address = {
          street: 'PO Box 12345',
          city: 'Los Angeles',
          state: 'CA',
          postalCode: '90001',
        };
        const result = formatAddress(address, 'en');
        expect(result).toMatch(/PO Box 12345/);
        expect(result).toMatch(/Los Angeles, CA 90001/);
      });
    });

    describe('comparison between locales', () => {
      it('should produce different field order for English vs Russian', () => {
        const address = {
          street: '123 Main Street',
          city: 'Springfield',
          state: 'IL',
          postalCode: '62701',
          country: 'USA',
        };
        const resultEn = formatAddress(address, 'en');
        const resultRu = formatAddress(address, 'ru');

        // English should have street first
        expect(resultEn.split('\n')[0]).toContain('123 Main Street');

        // Russian should have country first
        expect(resultRu.split('\n')[0]).toBe('USA');

        // Results should not be identical
        expect(resultEn).not.toBe(resultRu);
      });

      it('should handle same partial address in both locales', () => {
        const address = {
          city: 'Moscow',
          street: 'Red Square',
        };
        const resultEn = formatAddress(address, 'en');
        const resultRu = formatAddress(address, 'ru');

        // Both should contain the same information
        expect(resultEn).toMatch(/Moscow/);
        expect(resultEn).toMatch(/Red Square/);
        expect(resultRu).toMatch(/Moscow/);
        expect(resultRu).toMatch(/Red Square/);

        // But order should be different
        expect(resultEn).not.toBe(resultRu);
      });
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
