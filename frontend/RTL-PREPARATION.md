# RTL (Right-to-Left) Preparation

## Overview

This application has been prepared for future RTL language support (Arabic, Hebrew, etc.) by implementing CSS logical properties and HTML direction management.

## What Has Been Implemented

### 1. Language Direction Support

**File:** `frontend/src/contexts/LanguageContext.tsx`

- Added `TextDirection` type: `'ltr' | 'rtl'`
- Added `direction` field to `LanguageConfig` interface
- Updated `SUPPORTED_LANGUAGES` to include `direction: 'ltr'` for English and Russian
- Added `useEffect` hook to set HTML `dir` and `lang` attributes when language changes

```typescript
export const SUPPORTED_LANGUAGES: Record<SupportedLanguage, LanguageConfig> = {
  en: {
    code: 'en',
    name: 'English',
    nameEn: 'English',
    locale: 'en-US',
    direction: 'ltr', // ← Text direction
  },
  ru: {
    code: 'ru',
    name: 'Русский',
    nameEn: 'Russian',
    locale: 'ru-RU',
    direction: 'ltr',
  },
};
```

### 2. HTML Direction Management

**File:** `frontend/src/contexts/LanguageContext.tsx`

The `LanguageProvider` automatically manages the HTML `dir` attribute:

```typescript
useEffect(() => {
  const direction = SUPPORTED_LANGUAGES[language].direction;
  document.documentElement.setAttribute('dir', direction);
  document.documentElement.setAttribute('lang', language);
}, [language]);
```

This ensures the browser knows the text direction and can:
- Flip text alignment automatically
- Adjust cursor movement direction
- Apply proper Unicode bidirectional algorithm
- Flip scrollbar position (in some browsers)

### 3. CSS Logical Properties

**File:** `frontend/src/index.css`

Added comprehensive documentation for RTL support with CSS logical properties:

```css
/* RTL Support */

/* Use logical properties instead of physical properties */
.element {
  margin-inline-start: 1rem;  /* left in LTR, right in RTL */
  margin-inline-end: 1rem;    /* right in LTR, left in RTL */
  padding-inline-start: 0.5rem;
  text-align: start;          /* left in LTR, right in RTL */
}

/* RTL-specific overrides when needed */
[dir="rtl"] .special-element {
  transform: scaleX(-1);  /* Mirror icons/images for RTL */
}
```

### 4. LanguageProvider Integration

**File:** `frontend/src/main.tsx`

Wrapped the application with `LanguageProvider` to ensure direction management:

```typescript
<LanguageProvider>
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <App />
  </ThemeProvider>
</LanguageProvider>
```

## Verification

### Manual Verification

Run the verification script:

```bash
cd frontend
./verify-rtl-preparation.sh
```

This will guide you through:
1. Checking HTML `dir` and `lang` attributes
2. Switching languages and verifying attribute updates
3. Reviewing CSS RTL documentation
4. Testing via browser console

### Console Verification

You can verify in the browser DevTools Console:

```javascript
// Check current direction
document.documentElement.getAttribute('dir'); // Expected: 'ltr'

// Check current language
document.documentElement.getAttribute('lang'); // Expected: 'en' or 'ru'

// Switch language via UI, then check again
document.documentElement.getAttribute('lang'); // Should update
```

## Adding Future RTL Languages

When adding RTL languages (Arabic, Hebrew, etc.), follow these steps:

### Step 1: Add Language to LanguageContext

**File:** `frontend/src/contexts/LanguageContext.tsx`

```typescript
export type SupportedLanguage = 'en' | 'ru' | 'ar' | 'he';

export const SUPPORTED_LANGUAGES: Record<SupportedLanguage, LanguageConfig> = {
  // ... existing languages
  ar: {
    code: 'ar',
    name: 'العربية',
    nameEn: 'Arabic',
    locale: 'ar-SA',
    direction: 'rtl', // ← Right-to-left
  },
  he: {
    code: 'he',
    name: 'עברית',
    nameEn: 'Hebrew',
    locale: 'he-IL',
    direction: 'rtl', // ← Right-to-left
  },
};
```

### Step 2: Add Translation Files

**Files:**
- `frontend/src/i18n/locales/ar.json`
- `frontend/src/i18n/locales/he.json`

Create translation files following the same structure as `en.json` and `ru.json`.

### Step 3: Add Language to i18n Config

**File:** `frontend/src/i18n/index.ts`

```typescript
import arTranslations from './locales/ar.json';
import heTranslations from './locales/he.json';

i18n.init({
  resources: {
    en: { translation: enTranslations },
    ru: { translation: ruTranslations },
    ar: { translation: arTranslations }, // ← Add Arabic
    he: { translation: heTranslations }, // ← Add Hebrew
  },
});
```

### Step 4: Update LanguageSwitcher (Optional)

**File:** `frontend/src/components/LanguageSwitcher.tsx`

Add flag emojis for new languages:

```typescript
const getFlagEmoji = (langCode: string): string => {
  const flags: Record<string, string> = {
    en: '🇺🇸',
    ru: '🇷🇺',
    ar: '🇸🇦', // ← Saudi Arabia flag
    he: '🇮🇱', // ← Israel flag
  };
  return flags[langCode] || '🌐';
};
```

## CSS Guidelines for RTL

### Use Logical Properties

Instead of physical properties (left, right), use logical properties:

| Physical Property | Logical Property | LTR Effect | RTL Effect |
|-----------------|------------------|------------|------------|
| `margin-left` | `margin-inline-start` | Left margin | Right margin |
| `margin-right` | `margin-inline-end` | Right margin | Left margin |
| `padding-left` | `padding-inline-start` | Left padding | Right padding |
| `padding-right` | `padding-inline-end` | Right padding | Left padding |
| `text-align: left` | `text-align: start` | Left align | Right align |
| `text-align: right` | `text-align: end` | Right align | Left align |
| `border-left` | `border-inline-start` | Left border | Right border |
| `border-right` | `border-inline-end` | Right border | Left border |

### RTL-Specific Overrides

For elements that need special handling in RTL:

```css
/* Flip icons for RTL */
[dir="rtl"] .icon-arrow {
  transform: scaleX(-1);
}

/* Adjust font for better Arabic readability */
[dir="rtl"] body {
  font-family: 'Tahoma', 'Arial', sans-serif;
}

/* Change layout order in RTL */
[dir="rtl"] .flex-row {
  flex-direction: row-reverse;
}
```

### Material-UI RTL Support

Material-UI has built-in RTL support. To enable it:

```typescript
import { createTheme, CacheProvider } from '@mui/material';
import createCache from '@emotion/cache';
import { prefixer } from 'stylis';
import rtlPlugin from 'stylis-plugin-rtl';

// Create RTL cache
const cacheRtl = createCache({
  key: 'muirtl',
  stylisPlugins: [prefixer, rtlPlugin],
});

// Use in component
<CacheProvider value={cacheRtl}>
  <ThemeProvider theme={theme}>
    <App />
  </ThemeProvider>
</CacheProvider>
```

## Testing Checklist

- [ ] HTML `dir` attribute is set to `'ltr'` on initial load
- [ ] HTML `lang` attribute is set to `'en'` or `'ru'` on initial load
- [ ] `dir` attribute updates when language is changed
- [ ] `lang` attribute updates when language is changed
- [ ] CSS has RTL support documentation in `index.css`
- [ ] `LanguageContext` includes `direction` field
- [ ] Both English and Russian have `direction: 'ltr'`
- [ ] `useEffect` in `LanguageProvider` sets dir attribute
- [ ] `LanguageProvider` wraps the app in `main.tsx`

## Benefits of This Implementation

1. **Automatic Layout Flipping**: CSS logical properties automatically flip layout for RTL
2. **No Separate CSS Files**: Same CSS works for both LTR and RTL
3. **Easy to Add RTL Languages**: Only need to set `direction: 'rtl'` in language config
4. **Browser Native Support**: Uses standard HTML `dir` attribute
5. **Material-UI Ready**: Can easily integrate MUI's RTL support when needed
6. **Accessibility**: Proper direction attributes improve screen reader experience

## References

- [MDN: CSS Logical Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Logical_Properties)
- [W3C: Writing Modes](https://www.w3.org/TR/css-writing-modes-3/)
- [Material-UI: Right-to-Left](https://mui.com/material-ui/customization/right-to-left/)
- [i18next: RTL Languages](https://www.i18next.com/principles/translation#rtl-languages)
