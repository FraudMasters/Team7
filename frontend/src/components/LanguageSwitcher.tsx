import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  FormControl,
  Select,
  MenuItem,
  Typography,
  SelectChangeEvent,
} from '@mui/material';
import { useLanguageContext, SUPPORTED_LANGUAGES } from '@/contexts/LanguageContext';

/**
 * LanguageSwitcher Component
 *
 * Provides a dropdown selector for switching between supported languages.
 * Displays language name with flag emoji icon for visual identification.
 *
 * Features:
 * - Shows current language in dropdown
 * - Displays flag emoji (🇺🇸 for English, 🇷🇺 for Russian)
 * - Changes language on selection
 * - Integrates with LanguageContext for state management
 * - Uses i18next for translation persistence
 *
 * @example
 * ```tsx
 * // In Layout component header
 * <LanguageSwitcher />
 * ```
 */
const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const { language, setLanguage } = useLanguageContext();

  /**
   * Handle language selection change
   *
   * Updates the application language when user selects a different language
   * from the dropdown.
   *
   * @param event - Select change event
   */
  const handleLanguageChange = async (event: SelectChangeEvent<string>) => {
    const newLanguage = event.target.value as 'en' | 'ru';
    await setLanguage(newLanguage);
  };

  /**
   * Get flag emoji for language
   *
   * Returns the appropriate flag emoji for each supported language.
   *
   * @param langCode - Language code ('en' or 'ru')
   * @returns Flag emoji string
   */
  const getFlagEmoji = (langCode: string): string => {
    const flags: Record<string, string> = {
      en: '🇺🇸',
      ru: '🇷🇺',
    };
    return flags[langCode] || '🌐';
  };

  return (
    <Box sx={{ minWidth: 120 }}>
      <FormControl size="small" variant="outlined">
        <Select
          value={language}
          onChange={handleLanguageChange}
          displayEmpty
          inputProps={{
            'aria-label': i18n.t('language.switcher.ariaLabel') || 'Select language',
          }}
          sx={{
            color: 'inherit',
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 1,
            '& .MuiSelect-select': {
              color: 'inherit',
              py: 0.75,
              px: 1.5,
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255, 255, 255, 0.3)',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255, 255, 255, 0.5)',
            },
            '& .MuiSvgIcon-root': {
              color: 'inherit',
            },
          }}
        >
          {Object.values(SUPPORTED_LANGUAGES).map((lang) => (
            <MenuItem
              key={lang.code}
              value={lang.code}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Box
                component="span"
                sx={{
                  fontSize: '1.2rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                }}
              >
                {getFlagEmoji(lang.code)}
              </Box>
              <Typography
                variant="body2"
                sx={{
                  fontWeight: language === lang.code ? 600 : 400,
                }}
              >
                {lang.nameEn}
              </Typography>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default LanguageSwitcher;
