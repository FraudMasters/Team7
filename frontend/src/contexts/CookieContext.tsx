import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

/**
 * Cookie consent types
 */
export type CookieConsentType = 'necessary' | 'analytics' | 'marketing';

/**
 * Cookie consent state
 */
export interface CookieConsent {
  /** Necessary cookies (always enabled) */
  necessary: boolean;
  /** Analytics cookies */
  analytics: boolean;
  /** Marketing cookies */
  marketing: boolean;
}

/**
 * Cookie Context State Interface
 */
interface CookieState {
  /** Whether user has made consent decision */
  hasConsented: boolean;
  /** Current consent settings */
  consent: CookieConsent;
  /** Accept all cookies */
  acceptAll: () => void;
  /** Reject all optional cookies */
  rejectAll: () => void;
  /** Save custom consent preferences */
  saveConsent: (consent: CookieConsent) => void;
  /** Reset consent (for testing) */
  resetConsent: () => void;
}

/**
 * Cookie Context Props
 */
interface CookieProviderProps {
  /** Children components */
  children: ReactNode;
}

/**
 * Local storage key for cookie consent
 */
const CONSENT_STORAGE_KEY = 'cookie_consent';

/**
 * Default consent state (all enabled for necessary, disabled for others)
 */
const DEFAULT_CONSENT: CookieConsent = {
  necessary: true,
  analytics: false,
  marketing: false,
};

/**
 * Load consent from localStorage
 */
const loadConsent = (): CookieConsent | null => {
  try {
    const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as CookieConsent;
    }
  } catch (error) {
    console.warn('Failed to load cookie consent from localStorage:', error);
  }
  return null;
};

/**
 * Save consent to localStorage
 */
const saveConsentToStorage = (consent: CookieConsent): void => {
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consent));
  } catch (error) {
    console.warn('Failed to save cookie consent to localStorage:', error);
  }
};

/**
 * Cookie Context
 *
 * Provides GDPR-compliant cookie consent management for the application.
 * Handles user consent decisions and persists preferences to localStorage.
 *
 * @example
 * ```tsx
 * // Wrap your app with CookieProvider
 * <CookieProvider>
 *   <App />
 * </CookieProvider>
 *
 * // Use in components
 * const { hasConsented, consent, acceptAll } = useCookieContext();
 *
 * // Check if user has consented
 * if (!hasConsented) {
 *   // Show cookie banner
 * }
 *
 * // Accept all cookies
 * acceptAll();
 * ```
 */
const CookieContext = createContext<CookieState | undefined>(undefined);

/**
 * Cookie Provider Component
 *
 * Manages GDPR-compliant cookie consent state.
 * Handles user consent decisions and persists preferences.
 *
 * @param props - Provider props
 * @returns Cookie context provider
 */
export const CookieProvider: React.FC<CookieProviderProps> = ({ children }) => {
  const [consent, setConsent] = useState<CookieConsent>(() => {
    // Load consent from localStorage on mount
    const stored = loadConsent();
    return stored || DEFAULT_CONSENT;
  });

  const [hasConsented, setHasConsented] = useState<boolean>(() => {
    // User has consented if there's a stored value
    return loadConsent() !== null;
  });

  /**
   * Accept all cookies
   *
   * Enables all cookie categories and saves consent.
   */
  const acceptAll = useCallback(() => {
    const fullConsent: CookieConsent = {
      necessary: true,
      analytics: true,
      marketing: true,
    };
    setConsent(fullConsent);
    setHasConsented(true);
    saveConsentToStorage(fullConsent);
  }, []);

  /**
   * Reject all optional cookies
   *
   * Keeps only necessary cookies enabled and saves consent.
   */
  const rejectAll = useCallback(() => {
    const minimalConsent: CookieConsent = {
      necessary: true,
      analytics: false,
      marketing: false,
    };
    setConsent(minimalConsent);
    setHasConsented(true);
    saveConsentToStorage(minimalConsent);
  }, []);

  /**
   * Save custom consent preferences
   *
   * @param customConsent - Custom consent settings from user
   */
  const saveConsent = useCallback((customConsent: CookieConsent) => {
    // Ensure necessary cookies are always enabled
    const finalConsent: CookieConsent = {
      ...customConsent,
      necessary: true,
    };
    setConsent(finalConsent);
    setHasConsented(true);
    saveConsentToStorage(finalConsent);
  }, []);

  /**
   * Reset consent (for testing purposes)
   *
   * Clears stored consent and resets to initial state.
   */
  const resetConsent = useCallback(() => {
    try {
      localStorage.removeItem(CONSENT_STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to remove cookie consent from localStorage:', error);
    }
    setConsent(DEFAULT_CONSENT);
    setHasConsented(false);
  }, []);

  const contextValue: CookieState = {
    hasConsented,
    consent,
    acceptAll,
    rejectAll,
    saveConsent,
    resetConsent,
  };

  return (
    <CookieContext.Provider value={contextValue}>
      {children}
    </CookieContext.Provider>
  );
};

/**
 * useCookieContext Hook
 *
 * Access cookie context state and functions.
 * Must be used within a CookieProvider.
 *
 * @throws Error if used outside of CookieProvider
 * @returns Cookie context state
 *
 * @example
 * ```tsx
 * const { hasConsented, consent, acceptAll, rejectAll } = useCookieContext();
 *
 * // Show banner if user hasn't consented
 * {!hasConsented && <CookieBanner />}
 *
 * // Check specific consent
 * {consent.analytics && <AnalyticsTracker />}
 * ```
 */
export const useCookieContext = (): CookieState => {
  const context = useContext(CookieContext);

  if (context === undefined) {
    throw new Error(
      'useCookieContext must be used within a CookieProvider. ' +
        'Wrap your component tree with <CookieProvider>.'
    );
  }

  return context;
};

export default CookieContext;
