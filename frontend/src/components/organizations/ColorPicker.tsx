import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Stack,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Colorize as ColorIcon,
  RestartAlt as ResetIcon,
} from '@mui/icons-material';

/**
 * Color picker state interface
 */
interface ColorPickerState {
  value: string;
  error: string | null;
}

/**
 * Color preset interface
 */
interface ColorPreset {
  name: string;
  color: string;
}

/**
 * ColorPicker Component Props
 */
interface ColorPickerProps {
  /** Current color value (hex format) */
  value: string;
  /** Label for the color picker */
  label: string;
  /** Callback when color changes */
  onChange: (color: string) => void;
  /** Helper text to display */
  helperText?: string;
  /** Whether the field is required */
  required?: boolean;
  /** Whether the field is disabled */
  disabled?: boolean;
  /** Default color to reset to */
  defaultColor?: string;
  /** Preset colors to display */
  presetColors?: ColorPreset[];
  /** Unique ID for the input */
  id?: string;
}

/**
 * Common preset color palettes for branding
 */
const COMMON_PRESETS: ColorPreset[] = [
  { name: 'Blue', color: '#3B82F6' },
  { name: 'Green', color: '#10B981' },
  { name: 'Purple', color: '#8B5CF6' },
  { name: 'Red', color: '#EF4444' },
  { name: 'Orange', color: '#F59E0B' },
  { name: 'Pink', color: '#EC4899' },
  { name: 'Teal', color: '#14B8A6' },
  { name: 'Indigo', color: '#6366F1' },
];

/**
 * Validates hex color format
 *
 * @param color - Color string to validate
 * @returns True if valid hex color, false otherwise
 */
const isValidHexColor = (color: string): boolean => {
  return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(color);
};

/**
 * ColorPicker Component
 *
 * Provides a comprehensive color picker interface for branding customization with:
 * - Visual color preview
 * - Native color picker (HTML5 color input)
 * - Hex color input for precise color entry
 * - Preset color palette for quick selection
 * - Color validation
 * - Reset to default color
 * - Accessibility support
 *
 * @example
 * ```tsx
 * <ColorPicker
 *   label="Primary Color"
 *   value="#3B82F6"
 *   onChange={(color) => console.log('Color changed:', color)}
 *   helperText="Main brand color for buttons and links"
 *   defaultColor="#3B82F6"
 * />
 * ```
 */
const ColorPicker: React.FC<ColorPickerProps> = ({
  value,
  label,
  onChange,
  helperText,
  required = false,
  disabled = false,
  defaultColor = '#3B82F6',
  presetColors = COMMON_PRESETS,
  id,
}) => {
  const { t } = useTranslation();

  const [state, setState] = useState<ColorPickerState>({
    value,
    error: null,
  });

  /**
   * Validate hex color
   */
  const validateColor = useCallback((color: string): string | null => {
    if (!color && !required) {
      return null;
    }
    if (!color && required) {
      return t('validation.colorRequired') || 'Color is required';
    }
    if (!isValidHexColor(color)) {
      return t('validation.invalidHexColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }
    return null;
  }, [required, t]);

  /**
   * Handle color change from native picker
   */
  const handleColorChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newColor = event.target.value;
      const error = validateColor(newColor);

      setState({ value: newColor, error });

      if (!error) {
        onChange(newColor);
      }
    },
    [onChange, validateColor]
  );

  /**
   * Handle hex input change
   */
  const handleHexInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      let hexValue = event.target.value;

      // Add # if missing
      if (hexValue && !hexValue.startsWith('#')) {
        hexValue = '#' + hexValue;
      }

      // Allow empty value if not required
      if (!hexValue && !required) {
        setState({ value: '', error: null });
        onChange('');
        return;
      }

      const error = validateColor(hexValue);
      setState({ value: hexValue, error });

      if (!error) {
        onChange(hexValue);
      }
    },
    [onChange, required, validateColor]
  );

  /**
   * Handle preset color selection
   */
  const handlePresetClick = useCallback(
    (presetColor: string) => {
      setState({ value: presetColor, error: null });
      onChange(presetColor);
    },
    [onChange]
  );

  /**
   * Handle reset to default color
   */
  const handleReset = useCallback(() => {
    setState({ value: defaultColor, error: null });
    onChange(defaultColor);
  }, [defaultColor, onChange]);

  /**
   * Handle blur to validate final value
   */
  const handleBlur = useCallback(() => {
    const error = validateColor(state.value);
    setState((prev) => ({ ...prev, error }));
  }, [state.value, validateColor]);

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        elevation={1}
        sx={{
          p: 3,
          border: '1px solid',
          borderColor: state.error ? 'error.main' : 'divider',
          bgcolor: disabled ? 'action.disabledBackground' : 'background.paper',
        }}
      >
        {/* Label and Reset Button */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            {label}
            {required && <span style={{ color: 'red' }}> *</span>}
          </Typography>
          {state.value !== defaultColor && !disabled && (
            <Tooltip title={t('common.reset') || 'Reset to default'}>
              <IconButton size="small" onClick={handleReset} disabled={disabled}>
                <ResetIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Color Preview and Input */}
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
          {/* Native Color Input */}
          <Box
            sx={{
              position: 'relative',
              width: 56,
              height: 56,
              flexShrink: 0,
            }}
          >
            <Box
              sx={{
                width: '100%',
                height: '100%',
                borderRadius: 2,
                bgcolor: state.value || '#cccccc',
                border: '2px solid',
                borderColor: 'divider',
                overflow: 'hidden',
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease-in-out',
                '&:hover': !disabled
                  ? {
                      borderColor: 'primary.main',
                      transform: 'scale(1.05)',
                    }
                  : {},
              }}
            >
              <ColorIcon
                sx={{
                  fontSize: 32,
                  color: (theme) => {
                    const hexColor = state.value || '#cccccc';
                    // Calculate luminance to determine text color
                    const r = parseInt(hexColor.slice(1, 3), 16);
                    const g = parseInt(hexColor.slice(3, 5), 16);
                    const b = parseInt(hexColor.slice(5, 7), 16);
                    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                    return luminance > 0.5 ? '#000000' : '#FFFFFF';
                  },
                }}
              />
            </Box>
            <Box
              component="input"
              type="color"
              value={state.value || '#cccccc'}
              onChange={handleColorChange}
              disabled={disabled}
              id={id}
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                opacity: 0,
                cursor: disabled ? 'not-allowed' : 'pointer',
              }}
            />
          </Box>

          {/* Hex Input */}
          <Box sx={{ flex: 1 }}>
            <TextField
              fullWidth
              label={t('branding.color.hexValue') || 'Hex Color'}
              value={state.value}
              onChange={handleHexInputChange}
              onBlur={handleBlur}
              error={!!state.error}
              helperText={state.error || helperText}
              disabled={disabled}
              placeholder="#3B82F6"
              inputProps={{
                maxLength: 7,
                style: { textTransform: 'uppercase' },
              }}
            />
          </Box>
        </Stack>

        {/* Preset Colors */}
        {!disabled && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {t('branding.color.presets') || 'Quick presets'}
            </Typography>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              {presetColors.map((preset) => (
                <Chip
                  key={preset.name}
                  label={preset.name}
                  onClick={() => handlePresetClick(preset.color)}
                  sx={{
                    bgcolor: preset.color,
                    color: (theme) => {
                      // Calculate luminance for text color
                      const r = parseInt(preset.color.slice(1, 3), 16);
                      const g = parseInt(preset.color.slice(3, 5), 16);
                      const b = parseInt(preset.color.slice(5, 7), 16);
                      const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                      return luminance > 0.5 ? '#000000' : '#FFFFFF';
                    },
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: state.value === preset.color ? 'primary.main' : 'divider',
                    '&:hover': {
                      opacity: 0.9,
                      transform: 'scale(1.05)',
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default ColorPicker;
