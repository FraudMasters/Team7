import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import i18n from '@i18n';
import { apiClient } from '@/api/client';

/**
 * Supported languages for the application
 */
export type SupportedLanguage = 'en' | 'ru';

/**
 * Text direction for language
 */
export type TextDirection = 'ltr' | 'rtl';

/**
 * Language display configuration
 */
export interface LanguageConfig {
  /** Language code (ISO 639-1) */
  code: SupportedLanguage;
  /** Native language name */
  name: string;
  /** English language name */
  nameEn: string;
  /** Locale code for formatting */
  locale: string;
  /** Text direction (ltr or rtl) */
  direction: TextDirection;
}

/**
 * Supported languages configuration
 */
export const SUPPORTED_LANGUAGES: Record<SupportedLanguage, LanguageConfig> = {
  en: {
    code: 'en',
    name: 'English',
    nameEn: 'English',
    locale: 'en-US',
    direction: 'ltr',
  },
  ru: {
    code: 'ru',
    name: 'Русский',
    nameEn: 'Russian',
    locale: 'ru-RU',
    direction: 'ltr',
  },
} as const;

/**
 * Language Context State Interface
 */
interface LanguageState {
  /** Current language code */
  language: SupportedLanguage;
  /** Change language function */
  setLanguage: (language: SupportedLanguage) => Promise<void>;
  /** Get language configuration */
  getLanguageConfig: (language: SupportedLanguage) => LanguageConfig;
  /** Check if language is supported */
  isLanguageSupported: (language: string) => language is SupportedLanguage;
}

/**
 * Language Context Props
 */
interface LanguageProviderProps {
  /** Children components */
  children: ReactNode;
  /** Initial language (optional, defaults to i18n language) */
  initialLanguage?: SupportedLanguage;
}

/**
 * Language Context
 *
 * Provides language state and management for the application.
 * Integrates with i18next for translation and language persistence.
 *
 * @example
 * ```tsx
 * // Wrap your app with LanguageProvider
 * <LanguageProvider>
 *   <App />
 * </LanguageProvider>
 *
 * // Use in components
 * const { language, setLanguage } = useLanguageContext();
 *
 * // Change language
 * await setLanguage('ru');
 * ```
 */
const LanguageContext = createContext<LanguageState | undefined>(undefined);

/**
 * Language Provider Component
 *
 * Manages application language state and integrates with i18next.
 * Handles language changes and persists language preference.
 *
 * @param props - Provider props
 * @returns Language context provider
 */
export const LanguageProvider: React.FC<LanguageProviderProps> = ({
  children,
  initialLanguage,
}) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    // Use initialLanguage if provided, otherwise get from i18n
    if (initialLanguage) {
      return initialLanguage;
    }
    // Get current language from i18n, default to 'en'
    const currentLang = i18n.language as SupportedLanguage;
    return SUPPORTED_LANGUAGES[currentLang] ? currentLang : 'en';
  });

  /**
   * Update local state when i18n language changes
   */
  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      const newLanguage = SUPPORTED_LANGUAGES[lng as SupportedLanguage]
        ? (lng as SupportedLanguage)
        : 'en';
      setLanguageState(newLanguage);
    };

    // Listen for i18n language changes
    i18n.on('languageChanged', handleLanguageChange);

    // Cleanup listener
    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, []);

  /**
   * Update HTML dir attribute when language changes
   * This ensures proper text direction for LTR and RTL languages
   */
  useEffect(() => {
    const direction = SUPPORTED_LANGUAGES[language].direction;
    document.documentElement.setAttribute('dir', direction);
    document.documentElement.setAttribute('lang', language);
  }, [language]);

  /**
   * Change application language
   *
   * Updates i18n language and triggers re-render of all translated components.
   * Language change is persisted to localStorage by i18next detector
   * and synchronized with backend preferences API.
   *
   * @param newLanguage - Language code to switch to
   * @returns Promise that resolves when language change is complete
   */
  const setLanguage = useCallback(async (newLanguage: SupportedLanguage): Promise<void> => {
    if (!SUPPORTED_LANGUAGES[newLanguage]) {
      console.warn(`Unsupported language: ${newLanguage}. Falling back to 'en'.`);
      newLanguage = 'en';
    }

    // Update i18n language (triggers languageChanged event)
    await i18n.changeLanguage(newLanguage);
    // Local state will be updated by the languageChanged event listener

    // Synchronize language preference with backend
    // Don't let backend failures block the UI update
    try {
      await apiClient.updateLanguagePreference(newLanguage);
    } catch (error) {
      // Log error but don't throw - UI already updated locally
      console.warn('Failed to sync language preference to backend:', error);
    }
  }, []);

  /**
   * Get language configuration object
   *
   * @param languageCode - Language code
   * @returns Language configuration object
   */
  const getLanguageConfig = useCallback(
    (languageCode: SupportedLanguage): LanguageConfig => {
      return SUPPORTED_LANGUAGES[languageCode] || SUPPORTED_LANGUAGES.en;
    },
    []
  );

  /**
   * Check if a language code is supported
   *
   * @param languageCode - Language code to check
   * @returns True if language is supported
   */
  const isLanguageSupported = useCallback(
    (languageCode: string): languageCode is SupportedLanguage => {
      return languageCode in SUPPORTED_LANGUAGES;
    },
    []
  );

  const contextValue: LanguageState = {
    language,
    setLanguage,
    getLanguageConfig,
    isLanguageSupported,
  };

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
};

/**
 * useLanguageContext Hook
 *
 * Access language context state and functions.
 * Must be used within a LanguageProvider.
 *
 * @throws Error if used outside of LanguageProvider
 * @returns Language context state
 *
 * @example
 * ```tsx
 * const { language, setLanguage } = useLanguageContext();
 *
 * // Display current language
 * <p>Current language: {language}</p>
 *
 * // Change language on button click
 * <button onClick={() => setLanguage('ru')}>
 *   Switch to Russian
 * </button>
 * ```
 */
export const useLanguageContext = (): LanguageState => {
  const context = useContext(LanguageContext);

  if (context === undefined) {
    throw new Error(
      'useLanguageContext must be used within a LanguageProvider. ' +
        'Wrap your component tree with <LanguageProvider>.'
    );
  }

  return context;
};

export default LanguageContext;
