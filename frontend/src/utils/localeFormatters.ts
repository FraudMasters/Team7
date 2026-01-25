/**
 * Locale Formatters
 *
 * Provides locale-aware formatting utilities for dates, numbers, and currency.
 * Uses the browser's Intl API for standardized internationalization.
 *
 * @module utils/localeFormatters
 */

import type { SupportedLanguage } from '@/contexts/LanguageContext';

/**
 * Locale code mapping
 * Maps supported language codes to full locale strings for Intl API
 */
const LOCALE_MAP: Record<SupportedLanguage, string> = {
  en: 'en-US',
  ru: 'ru-RU',
} as const;

/**
 * Date format options for each locale
 */
const DATE_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.DateTimeFormatOptions> = {
  en: {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  },
  ru: {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  },
} as const;

/**
 * Short date format options (e.g., Jan 15, 2024)
 */
const SHORT_DATE_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.DateTimeFormatOptions> = {
  en: {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  },
  ru: {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  },
} as const;

/**
 * Time format options for each locale
 */
const TIME_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.DateTimeFormatOptions> = {
  en: {
    hour: '2-digit',
    minute: '2-digit',
  },
  ru: {
    hour: '2-digit',
    minute: '2-digit',
  },
} as const;

/**
 * Number format options for each locale
 */
const NUMBER_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.NumberFormatOptions> = {
  en: {
    style: 'decimal',
  },
  ru: {
    style: 'decimal',
  },
} as const;

/**
 * Percent format options for each locale
 */
const PERCENT_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.NumberFormatOptions> = {
  en: {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  },
  ru: {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  },
} as const;

/**
 * Currency symbols for common currencies
 */
const CURRENCY_SYMBOLS: Record<string, Record<SupportedLanguage, string>> = {
  USD: { en: '$', ru: '$' },
  EUR: { en: '€', ru: '€' },
  RUB: { en: '₽', ru: '₽' },
  GBP: { en: '£', ru: '£' },
} as const;

/**
 * Format a date according to locale conventions
 *
 * Formats a date, Date object, or timestamp into a locale-specific string.
 *
 * @param date - Date to format (Date object, ISO string, or timestamp)
 * @param locale - Locale code ('en' or 'ru')
 * @param options - Optional formatting options
 * @returns Formatted date string
 *
 * @throws {Error} If date cannot be parsed or locale is invalid
 *
 * @example
 * ```ts
 * formatDate(new Date('2024-01-15'), 'en')  // 'January 15, 2024'
 * formatDate(new Date('2024-01-15'), 'ru')  // '15 января 2024 г.'
 * formatDate('2024-01-15', 'en')           // 'January 15, 2024'
 * formatDate(1705305600000, 'ru')          // '15 января 2024 г.'
 * ```
 */
export function formatDate(
  date: Date | string | number,
  locale: SupportedLanguage = 'en',
  options?: Partial<Intl.DateTimeFormatOptions>
): string {
  try {
    // Normalize locale
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];

    // Parse date input
    const dateObj = _parseDate(date);

    // Merge custom options with defaults
    const formatOptions = {
      ...DATE_FORMAT_OPTIONS[normalizedLocale],
      ...options,
    };

    // Format date
    return new Intl.DateTimeFormat(localeString, formatOptions).format(dateObj);
  } catch (error) {
    throw new Error(
      `Failed to format date: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a date with short month name (e.g., Jan 15, 2024)
 *
 * @param date - Date to format
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted date string with short month
 *
 * @example
 * ```ts
 * formatDateShort(new Date('2024-01-15'), 'en')  // 'Jan 15, 2024'
 * formatDateShort(new Date('2024-01-15'), 'ru')  // '15 янв. 2024 г.'
 * ```
 */
export function formatDateShort(
  date: Date | string | number,
  locale: SupportedLanguage = 'en'
): string {
  return formatDate(date, locale, SHORT_DATE_FORMAT_OPTIONS[locale]);
}

/**
 * Format a date and time according to locale conventions
 *
 * @param date - Date to format
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted date and time string
 *
 * @example
 * ```ts
 * formatDateTime(new Date('2024-01-15T14:30:00'), 'en')  // 'January 15, 2024, 02:30 PM'
 * formatDateTime(new Date('2024-01-15T14:30:00'), 'ru')  // '15 января 2024 г., 14:30'
 * ```
 */
export function formatDateTime(
  date: Date | string | number,
  locale: SupportedLanguage = 'en'
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];
    const dateObj = _parseDate(date);

    const formatOptions: Intl.DateTimeFormatOptions = {
      ...DATE_FORMAT_OPTIONS[normalizedLocale],
      ...TIME_FORMAT_OPTIONS[normalizedLocale],
    };

    return new Intl.DateTimeFormat(localeString, formatOptions).format(dateObj);
  } catch (error) {
    throw new Error(
      `Failed to format date/time: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a time according to locale conventions
 *
 * @param date - Date containing time to format
 * @param locale - Locale code ('en' or 'ru')
 * @param options - Optional formatting options
 * @returns Formatted time string
 *
 * @example
 * ```ts
 * formatTime(new Date('2024-01-15T14:30:00'), 'en')  // '02:30 PM'
 * formatTime(new Date('2024-01-15T14:30:00'), 'ru')  // '14:30'
 * ```
 */
export function formatTime(
  date: Date | string | number,
  locale: SupportedLanguage = 'en',
  options?: Partial<Intl.DateTimeFormatOptions>
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];
    const dateObj = _parseDate(date);

    const formatOptions: Intl.DateTimeFormatOptions = {
      ...TIME_FORMAT_OPTIONS[normalizedLocale],
      ...options,
    };

    return new Intl.DateTimeFormat(localeString, formatOptions).format(dateObj);
  } catch (error) {
    throw new Error(
      `Failed to format time: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a number according to locale conventions
 *
 * Formats a number with proper thousand separators and decimal separators
 * for the specified locale.
 *
 * @param number - Number to format
 * @param locale - Locale code ('en' or 'ru')
 * @param options - Optional formatting options
 * @returns Formatted number string
 *
 * @throws {Error} If number is invalid or locale is invalid
 *
 * @example
 * ```ts
 * formatNumber(1234.56, 'en')  // '1,234.56'
 * formatNumber(1234.56, 'ru')  // '1 234,56'
 * formatNumber(1000000, 'en')  // '1,000,000'
 * formatNumber(1000000, 'ru')  // '1 000 000'
 * ```
 */
export function formatNumber(
  number: number,
  locale: SupportedLanguage = 'en',
  options?: Partial<Intl.NumberFormatOptions>
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];

    if (typeof number !== 'number' || isNaN(number)) {
      throw new Error(`Invalid number: ${number}`);
    }

    const formatOptions: Intl.NumberFormatOptions = {
      ...NUMBER_FORMAT_OPTIONS[normalizedLocale],
      ...options,
    };

    return new Intl.NumberFormat(localeString, formatOptions).format(number);
  } catch (error) {
    throw new Error(
      `Failed to format number: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a number as a percentage according to locale conventions
 *
 * @param number - Number to format as percentage (0.5 = 50%)
 * @param locale - Locale code ('en' or 'ru')
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string
 *
 * @example
 * ```ts
 * formatPercent(0.75, 'en')  // '75.0%'
 * formatPercent(0.75, 'ru')  // '75,0%'
 * formatPercent(1, 'en')     // '100.0%'
 * ```
 */
export function formatPercent(
  number: number,
  locale: SupportedLanguage = 'en',
  decimals: number = 1
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];

    if (typeof number !== 'number' || isNaN(number)) {
      throw new Error(`Invalid number: ${number}`);
    }

    const formatOptions: Intl.NumberFormatOptions = {
      ...PERCENT_FORMAT_OPTIONS[normalizedLocale],
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    };

    return new Intl.NumberFormat(localeString, formatOptions).format(number);
  } catch (error) {
    throw new Error(
      `Failed to format percentage: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a currency amount according to locale conventions
 *
 * Formats a number as currency with the appropriate symbol and formatting
 * for the specified locale.
 *
 * @param amount - Currency amount to format
 * @param locale - Locale code ('en' or 'ru')
 * @param currency - Currency code (default: 'USD')
 * @param options - Optional formatting options
 * @returns Formatted currency string
 *
 * @throws {Error} If amount is invalid or locale is invalid
 *
 * @example
 * ```ts
 * formatCurrency(1234.56, 'en', 'USD')  // '$1,234.56'
 * formatCurrency(1234.56, 'ru', 'RUB')  // '1 234,56 ₽'
 * formatCurrency(1000, 'en', 'EUR')     // '€1,000.00'
 * ```
 */
export function formatCurrency(
  amount: number,
  locale: SupportedLanguage = 'en',
  currency: string = 'USD',
  options?: Partial<Intl.NumberFormatOptions>
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];

    if (typeof amount !== 'number' || isNaN(amount)) {
      throw new Error(`Invalid amount: ${amount}`);
    }

    const formatOptions: Intl.NumberFormatOptions = {
      style: 'currency',
      currency: currency,
      currencyDisplay: 'symbol',
      ...options,
    };

    return new Intl.NumberFormat(localeString, formatOptions).format(amount);
  } catch (error) {
    throw new Error(
      `Failed to format currency: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format file size in human-readable format
 *
 * Converts byte count to appropriate unit (B, KB, MB, GB) with localization.
 *
 * @param bytes - File size in bytes
 * @param locale - Locale code ('en' or 'ru')
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted file size string
 *
 * @example
 * ```ts
 * formatFileSize(1024, 'en')      // '1.0 KB'
 * formatFileSize(1048576, 'ru')   // '1,0 MB'
 * formatFileSize(1500, 'en', 2)   // '1.46 KB'
 * ```
 */
export function formatFileSize(
  bytes: number,
  locale: SupportedLanguage = 'en',
  decimals: number = 1
): string {
  if (typeof bytes !== 'number' || bytes < 0) {
    throw new Error(`Invalid file size: ${bytes}`);
  }

  const normalizedLocale = _validateLocale(locale);

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const threshold = 1024;

  if (bytes < threshold) {
    return `${bytes} B`;
  }

  const unitIndex = Math.floor(Math.log(bytes) / Math.log(threshold));
  const size = bytes / Math.pow(threshold, unitIndex);
  const unit = units[unitIndex];

  return `${formatNumber(size, normalizedLocale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} ${unit}`;
}

/**
 * Format a relative time (e.g., "2 days ago", "in 3 hours")
 *
 * Uses Intl.RelativeTimeFormat for locale-specific relative time formatting.
 *
 * @param value - Numeric value
 * @param unit - Time unit (second, minute, hour, day, week, month, year)
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted relative time string
 *
 * @example
 * ```ts
 * formatRelativeTime(-2, 'day', 'en')   // '2 days ago'
 * formatRelativeTime(-2, 'day', 'ru')   // '2 дня назад'
 * formatRelativeTime(3, 'hour', 'en')   // 'in 3 hours'
 * formatRelativeTime(3, 'hour', 'ru')   // 'через 3 часа'
 * ```
 */
export function formatRelativeTime(
  value: number,
  unit: Intl.RelativeTimeFormatUnit,
  locale: SupportedLanguage = 'en'
): string {
  try {
    const normalizedLocale = _validateLocale(locale);
    const localeString = LOCALE_MAP[normalizedLocale];

    const rtf = new Intl.RelativeTimeFormat(localeString, { numeric: 'auto' });
    return rtf.format(value, unit);
  } catch (error) {
    throw new Error(
      `Failed to format relative time: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Validate and normalize locale code
 *
 * @private
 * @param locale - Locale code to validate
 * @returns Normalized locale code
 * @throws {Error} If locale is not supported
 */
function _validateLocale(locale: string): SupportedLanguage {
  if (locale === 'en' || locale === 'ru') {
    return locale;
  }
  throw new Error(`Unsupported locale: ${locale}. Supported locales are: en, ru`);
}

/**
 * Parse various date inputs into a Date object
 *
 * @private
 * @param date - Date input (Date, string, or number)
 * @returns Date object
 * @throws {Error} If date cannot be parsed
 */
function _parseDate(date: Date | string | number): Date {
  if (date instanceof Date) {
    if (isNaN(date.getTime())) {
      throw new Error('Invalid Date object');
    }
    return date;
  }

  if (typeof date === 'string') {
    const parsed = new Date(date);
    if (isNaN(parsed.getTime())) {
      throw new Error(`Invalid date string: ${date}`);
    }
    return parsed;
  }

  if (typeof date === 'number') {
    const parsed = new Date(date);
    if (isNaN(parsed.getTime())) {
      throw new Error(`Invalid timestamp: ${date}`);
    }
    return parsed;
  }

  throw new Error(`Unsupported date type: ${typeof date}`);
}

/**
 * Get list of supported locales
 *
 * @returns Array of supported locale codes
 *
 * @example
 * ```ts
 * getSupportedLocales()  // ['en', 'ru']
 * ```
 */
export function getSupportedLocales(): SupportedLanguage[] {
  return ['en', 'ru'];
}
