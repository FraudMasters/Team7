import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import enTranslations from './locales/en.json';
import ruTranslations from './locales/ru.json';

// Configure i18next
i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources: {
      en: {
        translation: enTranslations,
      },
      ru: {
        translation: ruTranslations,
      },
    },
    fallbackLng: 'en', // Use English if detected language is not available
    debug: false, // Set to true for development debugging

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      // Cache user language in localStorage
      caches: ['localStorage'],
      // Only use languages that are in our resources
      checkWhitelist: true,
    },
  });

export default i18n;
