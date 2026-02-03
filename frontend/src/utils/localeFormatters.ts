/**
 * Locale Formatters
 *
 * Provides locale-aware formatting utilities for dates, numbers, currency, addresses, and more.
 * Uses the browser's Intl API for standardized internationalization.
 *
 * @module utils/localeFormatters
 */

import type { SupportedLanguage } from '@/contexts/LanguageContext';

/**
 * Duration object for explicit time units
 */
export interface DurationObject {
  days?: number;
  hours?: number;
  minutes?: number;
  seconds?: number;
}

/**
 * Address object for postal addresses
 */
export interface Address {
  street?: string;
  street2?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

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
 * Duration unit labels for each locale
 * Includes singular, plural forms for proper pluralization
 */
const DURATION_UNIT_LABELS: Record<
  SupportedLanguage,
  Record<'day' | 'hour' | 'minute' | 'second', string[]>
> = {
  en: {
    day: ['day', 'days'],
    hour: ['h', 'h'],
    minute: ['m', 'm'],
    second: ['s', 's'],
  },
  ru: {
    day: ['д', 'д'],
    hour: ['ч', 'ч'],
    minute: ['мин', 'мин'],
    second: ['с', 'с'],
  },
} as const;

/**
 * Address field order and formatting for each locale
 */
const ADDRESS_FORMAT_CONFIG: Record<
  SupportedLanguage,
  {
    fieldOrder: (keyof Address)[];
    separators: Record<string, string>;
  }
> = {
  en: {
    fieldOrder: ['street', 'street2', 'city', 'state', 'postalCode', 'country'],
    separators: {
      cityState: ', ',
      statePostal: ' ',
      postalCountry: '\n',
    },
  },
  ru: {
    fieldOrder: ['country', 'postalCode', 'city', 'state', 'street', 'street2'],
    separators: {
      cityState: ', ',
      statePostal: ' ',
      postalCountry: '\n',
    },
  },
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
 * Format a duration in a locale-aware compact format
 *
 * Formats a duration as seconds or a duration object into a compact string like '2h 30m', '1d 4h', or '45m'.
 * This is ideal for displaying time durations in UI elements where space is limited.
 *
 * @param duration - Duration in seconds, or a DurationObject with explicit units
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted duration string
 *
 * @throws {Error} If duration is invalid or locale is invalid
 *
 * @example
 * ```ts
 * // Using seconds
 * formatDuration(9000, 'en')   // '2h 30m'
 * formatDuration(9000, 'ru')   // '2 ч 30 мин'
 * formatDuration(2700, 'en')   // '45m'
 * formatDuration(2700, 'ru')   // '45 мин'
 * formatDuration(30, 'en')     // '30s'
 * formatDuration(30, 'ru')     // '30 с'
 *
 * // Using duration object
 * formatDuration({ days: 1, hours: 4 }, 'en')  // '1d 4h'
 * formatDuration({ days: 1, hours: 4 }, 'ru')  // '1 д 4 ч'
 * formatDuration({ hours: 2, minutes: 30 }, 'en')  // '2h 30m'
 * formatDuration({ hours: 2, minutes: 30 }, 'ru')  // '2 ч 30 мин'
 * formatDuration({ minutes: 45 }, 'en')  // '45m'
 * formatDuration({ minutes: 45 }, 'ru')  // '45 мин'
 * ```
 */
export function formatDuration(
  duration: number | DurationObject,
  locale: SupportedLanguage = 'en'
): string {
  try {
    const normalizedLocale = _validateLocale(locale);

    // Parse duration into seconds and breakdown
    let totalSeconds = 0;
    let days = 0;
    let hours = 0;
    let minutes = 0;
    let seconds = 0;

    if (typeof duration === 'number') {
      if (duration < 0) {
        throw new Error(`Duration cannot be negative: ${duration}`);
      }
      if (!isFinite(duration)) {
        throw new Error(`Duration must be finite: ${duration}`);
      }
      totalSeconds = Math.floor(duration);
    } else if (typeof duration === 'object' && duration !== null) {
      // Handle DurationObject
      days = duration.days ?? 0;
      hours = duration.hours ?? 0;
      minutes = duration.minutes ?? 0;
      seconds = duration.seconds ?? 0;

      if (days < 0 || hours < 0 || minutes < 0 || seconds < 0) {
        throw new Error('Duration values cannot be negative');
      }

      totalSeconds = days * 86400 + hours * 3600 + minutes * 60 + seconds;
    } else {
      throw new Error(`Invalid duration type: ${typeof duration}`);
    }

    // Break down total seconds into units
    if (typeof duration === 'number') {
      days = Math.floor(totalSeconds / 86400);
      hours = Math.floor((totalSeconds % 86400) / 3600);
      minutes = Math.floor((totalSeconds % 3600) / 60);
      seconds = totalSeconds % 60;
    }

    // Build the formatted string
    const labels = DURATION_UNIT_LABELS[normalizedLocale];
    const parts: string[] = [];

    if (days > 0) {
      parts.push(`${days}${labels.day[0]}`);
    }
    if (hours > 0) {
      parts.push(`${hours}${labels.hour[0]}`);
    }
    if (minutes > 0) {
      parts.push(`${minutes}${labels.minute[0]}`);
    }
    if (seconds > 0 || parts.length === 0) {
      // Show seconds if present, or if duration is zero
      parts.push(`${seconds}${labels.second[0]}`);
    }

    return parts.join(' ');
  } catch (error) {
    throw new Error(
      `Failed to format duration: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a phone number with country code and proper grouping
 *
 * Formats a phone number into a standardized format with country code.
 * The format is: +[countryCode] [areaCode] [prefix]-[lineNumber]
 * Example: +1 (555) 123-4567
 *
 * @param phoneNumber - Phone number to format (can include various formats)
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted phone number string
 *
 * @throws {Error} If phone number is invalid or locale is invalid
 *
 * @example
 * ```ts
 * formatPhoneNumber('15551234567', 'en')  // '+1 (555) 123-4567'
 * formatPhoneNumber('+15551234567', 'en')  // '+1 (555) 123-4567'
 * formatPhoneNumber('5551234567', 'en')    // '(555) 123-4567'
 * formatPhoneNumber('15551234567', 'ru')  // '+1 (555) 123-4567'
 * ```
 */
export function formatPhoneNumber(
  phoneNumber: string,
  locale: SupportedLanguage = 'en'
): string {
  try {
    const normalizedLocale = _validateLocale(locale);

    // Remove all non-digit characters
    const cleaned = phoneNumber.replace(/\D/g, '');

    if (cleaned.length === 0) {
      throw new Error(`Invalid phone number: ${phoneNumber}`);
    }

    // Check if the number includes a country code (starts with 1-3 digits)
    let countryCode = '';
    let nationalNumber = cleaned;

    // If number starts with country code format (e.g., 1 for US/Canada)
    if (cleaned.length >= 11 && cleaned[0] === '1') {
      countryCode = '1';
      nationalNumber = cleaned.slice(1);
    } else if (cleaned.length >= 11 && cleaned.startsWith('7')) {
      // Russian country code
      countryCode = '7';
      nationalNumber = cleaned.slice(1);
    } else if (cleaned.length >= 11 && cleaned.startsWith('44')) {
      // UK country code
      countryCode = '44';
      nationalNumber = cleaned.slice(2);
    }

    // Format the national number
    // US/Canada format: (555) 123-4567 (10 digits)
    // Russian format: (555) 123-45-67 (10 digits)
    // If number is too short, just return with minimal formatting
    if (nationalNumber.length >= 10) {
      const areaCode = nationalNumber.slice(0, 3);
      const prefix = nationalNumber.slice(3, 6);
      const lineNumber = nationalNumber.slice(6, 10);

      if (countryCode) {
        return `+${countryCode} (${areaCode}) ${prefix}-${lineNumber}`;
      }
      return `(${areaCode}) ${prefix}-${lineNumber}`;
    } else if (nationalNumber.length >= 7) {
      // Shorter numbers: 123-4567
      const prefix = nationalNumber.slice(0, 3);
      const lineNumber = nationalNumber.slice(3);

      if (countryCode) {
        return `+${countryCode} ${prefix}-${lineNumber}`;
      }
      return `${prefix}-${lineNumber}`;
    } else {
      // Very short numbers, just return with country code if present
      if (countryCode) {
        return `+${countryCode} ${nationalNumber}`;
      }
      return nationalNumber;
    }
  } catch (error) {
    throw new Error(
      `Failed to format phone number: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Format a mailing address with locale-specific field ordering and line breaks
 *
 * Formats an address object into a properly formatted string with locale-specific
 * field ordering and line breaks. English addresses use the standard Western format
 * (street first, then city/state/postal), while Russian addresses use the Eastern
 * European format (country and postal code first, then city, then street).
 *
 * @param address - Address object containing address components
 * @param locale - Locale code ('en' or 'ru')
 * @returns Formatted address string with proper line breaks
 *
 * @throws {Error} If address is invalid or locale is invalid
 *
 * @example
 * ```ts
 * // English format
 * const address = {
 *   street: '123 Main Street',
 *   city: 'Springfield',
 *   state: 'IL',
 *   postalCode: '62701',
 *   country: 'USA',
 * };
 * formatAddress(address, 'en');
 * // '123 Main Street\nSpringfield, IL 62701\nUSA'
 *
 * // Russian format
 * formatAddress(address, 'ru');
 * // 'USA\n62701\nSpringfield, IL\n123 Main Street'
 *
 * // Partial address
 * const partialAddress = {
 *   street: '456 Oak Avenue',
 *   city: 'Moscow',
 * };
 * formatAddress(partialAddress, 'en');
 * // '456 Oak Avenue\nMoscow'
 * ```
 */
export function formatAddress(
  address: Address,
  locale: SupportedLanguage = 'en'
): string {
  try {
    const normalizedLocale = _validateLocale(locale);

    if (!address || typeof address !== 'object') {
      throw new Error(`Invalid address: ${address}`);
    }

    const config = ADDRESS_FORMAT_CONFIG[normalizedLocale];
    const lines: string[] = [];
    const currentLine: string[] = [];

    for (const field of config.fieldOrder) {
      const value = address[field];
      if (!value || typeof value !== 'string' || value.trim() === '') {
        continue;
      }

      const trimmedValue = value.trim();

      // English format: street lines together, city/state/postal together, country separate
      if (normalizedLocale === 'en') {
        if (field === 'street' || field === 'street2') {
          if (currentLine.length > 0 && currentLine[0]?.startsWith(trimmedValue[0] || '')) {
            // Start new line for street fields
            if (currentLine.length > 0) {
              lines.push(currentLine.join(' '));
              currentLine.length = 0;
            }
          }
          currentLine.push(trimmedValue);
        } else if (field === 'city') {
          if (currentLine.length > 0) {
            lines.push(currentLine.join(' '));
            currentLine.length = 0;
          }
          currentLine.push(trimmedValue);
        } else if (field === 'state') {
          currentLine.push(trimmedValue);
        } else if (field === 'postalCode') {
          currentLine.push(trimmedValue);
        } else if (field === 'country') {
          if (currentLine.length > 0) {
            lines.push(currentLine.join(', '));
            currentLine.length = 0;
          }
          lines.push(trimmedValue);
        }
      }
      // Russian format: country first, then postal code, then city/state, then street lines
      else if (normalizedLocale === 'ru') {
        if (field === 'country' || field === 'postalCode') {
          lines.push(trimmedValue);
        } else if (field === 'city') {
          currentLine.push(trimmedValue);
        } else if (field === 'state') {
          currentLine.push(trimmedValue);
        } else if (field === 'street' || field === 'street2') {
          if (currentLine.length > 0) {
            lines.push(currentLine.join(', '));
            currentLine.length = 0;
          }
          lines.push(trimmedValue);
        }
      }
    }

    // Add remaining current line
    if (currentLine.length > 0) {
      if (normalizedLocale === 'en' && currentLine.length >= 2) {
        // Join city/state/postal with appropriate separators
        const cityIdx = config.fieldOrder.indexOf('city');
        const stateIdx = config.fieldOrder.indexOf('state');
        const postalIdx = config.fieldOrder.indexOf('postalCode');

        // Check if we have city and state
        if (
          currentLine.length >= 2 &&
          address.city &&
          address.state &&
          cityIdx < stateIdx
        ) {
          lines.push(`${currentLine[0]}, ${currentLine[1]}${currentLine[2] ? ' ' + currentLine[2] : ''}`);
        } else {
          lines.push(currentLine.join(', '));
        }
      } else {
        lines.push(currentLine.join(', '));
      }
    }

    const result = lines.join('\n').trim();

    if (!result) {
      throw new Error('Address is empty');
    }

    return result;
  } catch (error) {
    throw new Error(
      `Failed to format address: ${error instanceof Error ? error.message : 'Unknown error'}`
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
