import React, { forwardRef } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * TextField size variants
 */
export type TextFieldSize = 'small' | 'medium';

/**
 * TextField color variants
 */
export type TextFieldColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Props for the input element
 */
export interface TextFieldInputProps {
  /** Input value */
  value?: string | number;
  /** Placeholder text */
  placeholder?: string;
  /** Input type */
  type?: 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local';
  /** Disabled state */
  disabled?: boolean;
  /** Read-only state */
  readOnly?: boolean;
  /** Maximum length */
  maxLength?: number;
  /** Minimum length */
  minLength?: number;
  /** Minimum value (for number inputs) */
  min?: number | string;
  /** Maximum value (for number inputs) */
  max?: number | string;
  /** Step value (for number inputs) */
  step?: number | string;
  /** Auto-complete behavior */
  autoComplete?: string;
  /** Input name */
  name?: string;
  /** Input ID */
  id?: string;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  /** Focus handler */
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  /** Blur handler */
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  /** Key press handler */
  onKeyDown?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  /** Key up handler */
  onKeyUp?: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLInputElement>) => void;
  /** Input reference */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Start adornment (icon or text) */
  startAdornment?: React.ReactNode;
  /** End adornment (icon or text) */
  endAdornment?: React.ReactNode;
}

/**
 * Base TextField props interface
 */
export interface BaseTextFieldProps extends TextFieldInputProps {
  /** Label text */
  label?: string;
  /** Helper text to display below input */
  helperText?: string;
  /** Error state */
  error?: boolean;
  /** Error message to display */
  errorMessage?: string;
  /** Required indicator */
  required?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Input size */
  size?: TextFieldSize;
  /** Color variant (for focus/border) */
  color?: TextFieldColor;
  /** Multiline textarea */
  multiline?: boolean;
  /** Number of rows (for multiline) */
  rows?: number;
  /** Minimum number of rows (for multiline) */
  minRows?: number;
  /** Maximum number of rows (for multiline) */
  maxRows?: number;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Additional input props */
  InputProps?: Partial<TextFieldInputProps>;
  /** Label props */
  LabelProps?: {
    className?: string;
    style?: React.CSSProperties;
  };
  /** Reference to container element */
  ref?: React.Ref<HTMLDivElement>;
}

/**
 * Props for TextField component
 * Extends standard HTML input attributes
 */
export interface TextFieldProps extends BaseTextFieldProps, Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'color' | 'onChange'> {}

/**
 * Get color styles based on color and state
 */
const getColorStyles = (color: TextFieldColor, theme: EmotionTheme) => {
  const colorMap = {
    primary: theme.primary,
    secondary: theme.secondary,
    success: theme.success,
    error: theme.error,
    warning: theme.warning,
    info: theme.info,
  };

  const colors = colorMap[color];

  return {
    '--field-color': colors.main,
    '--field-color-light': colors.light,
    '--field-color-dark': colors.dark,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: TextFieldSize) => {
  const sizeMap = {
    small: {
      minHeight: '32px',
      fontSize: '0.875rem',
      padding: '4px 12px',
    },
    medium: {
      minHeight: '40px',
      fontSize: '1rem',
      padding: '8px 14px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled container for TextField
 */
const StyledContainer = styled.div<{ fullWidth?: boolean; className?: string }>`
  position: relative;
  width: ${props => props.fullWidth ? '100%' : 'auto'};
  ${props => props.className};

  & + .helper-text {
    margin-top: 4px;
  }
`;

/**
 * Styled label for TextField
 */
const StyledLabel = styled.label<{ hasValue: boolean; isFocused: boolean; hasError: boolean; disabled?: boolean; size: TextFieldSize; required?: boolean }>`
  display: block;
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.hasError) return props.theme.error.main;
    if (props.isFocused) return `var(--field-color)`;
    return props.theme.text.secondary;
  }};
  font-size: ${props => getSizeStyles(props.size).fontSize};
  pointer-events: none;
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  background-color: ${props => props.theme.background.paper};
  padding: 0 4px;
  transition-property: font-size, top, color, transform;

  /* Floating label state */
  ${props => (props.hasValue || props.isFocused) && `
    font-size: 0.75rem;
    top: 0;
    transform: translateY(-50%);
  `}

  ${props => props.hasError && !props.isFocused && `
    color: ${props.theme.error.main};
  `}

  /* Required indicator */
  ${props => props.required && `
    &::after {
      content: ' *';
      color: ${props.theme.error.main};
    }
  `}
`;

/**
 * Styled input for TextField
 */
const StyledInput = styled.input<{
  error?: boolean;
  size: TextFieldSize;
  disabled?: boolean;
  hasStartAdornment: boolean;
  hasEndAdornment: boolean;
}>`
  width: 100%;
  border: 1px solid ${props => props.error ? props.theme.error.main : props.theme.divider};
  border-radius: ${props => props.theme.borderRadius.md};
  background-color: ${props => props.theme.background.paper};
  color: ${props => props.theme.text.primary};
  font-family: ${props => props.theme.typography.fontFamily};
  ${props => getSizeStyles(props.size)};
  outline: none;
  transition: border-color ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut},
              box-shadow ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut};
  box-sizing: border-box;

  /* Padding adjustments for adornments */
  padding-left: ${props => props.hasStartAdornment ? '40px' : '12px'};
  padding-right: ${props => props.hasEndAdornment ? '40px' : '12px'};

  /* Focus state */
  &:focus {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--field-color)'};
    box-shadow: 0 0 0 2px ${props => props.error ? 'rgba(211, 47, 47, 0.2)' : 'rgba(25, 118, 210, 0.2)'};

    & + label {
      color: ${props => props.error ? props.theme.error.main : 'var(--field-color)'};
    }
  }

  /* Disabled state */
  &:disabled {
    background-color: ${props => props.theme.action.disabledBackground};
    color: ${props => props.theme.text.disabled};
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Placeholder styles */
  &::placeholder {
    color: ${props => props.theme.text.hint};
  }

  /* Remove default number input styles */
  &[type='number'] {
    -moz-appearance: textfield;

    &::-webkit-inner-spin-button,
    &::-webkit-outer-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
  }

  /* Date input styles */
  &[type='date'],
  &[type='time'],
  &[type='datetime-local'] {
    &::-webkit-calendar-picker-indicator {
      cursor: pointer;
      color: ${props => props.theme.text.secondary};
    }
  }

  /* Autocomplete styles */
  &::-webkit-contacts-auto-fill-button,
  &::-webkit-credentials-auto-fill-button {
    background-color: ${props => props.theme.primary.main};
  }

  /* Search input styles */
  &[type='search'] {
    &::-webkit-search-cancel-button {
      cursor: pointer;
    }

    &::-webkit-search-decoration,
    &::-webkit-search-results-button {
      display: none;
    }
  }
`;

/**
 * Styled textarea for multiline TextField
 */
const StyledTextarea = styled.textarea<{
  error?: boolean;
  size: TextFieldSize;
  disabled?: boolean;
}>`
  width: 100%;
  border: 1px solid ${props => props.error ? props.theme.error.main : props.theme.divider};
  border-radius: ${props => props.theme.borderRadius.md};
  background-color: ${props => props.theme.background.paper};
  color: ${props => props.theme.text.primary};
  font-family: ${props => props.theme.typography.fontFamily};
  font-size: ${props => getSizeStyles(props.size).fontSize};
  padding: 8px 12px;
  outline: none;
  transition: border-color ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut},
              box-shadow ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut};
  box-sizing: border-box;
  resize: vertical;

  /* Focus state */
  &:focus {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--field-color)'};
    box-shadow: 0 0 0 2px ${props => props.error ? 'rgba(211, 47, 47, 0.2)' : 'rgba(25, 118, 210, 0.2)'};
  }

  /* Disabled state */
  &:disabled {
    background-color: ${props => props.theme.action.disabledBackground};
    color: ${props => props.theme.text.disabled};
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Placeholder styles */
  &::placeholder {
    color: ${props => props.theme.text.hint};
  }
`;

/**
 * Adornment container
 */
const Adornment = styled.div<{ position: 'start' | 'end' }>`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  ${props => props.position === 'start' ? 'left: 12px;' : 'right: 12px;'}
  display: flex;
  align-items: center;
  pointer-events: none;
  color: ${props => props.theme.text.secondary};
`;

/**
 * Helper text container
 */
const HelperText = styled.p<{ error?: boolean }>`
  margin: 4px 0 0 0;
  font-size: 0.75rem;
  color: ${props => props.error ? props.theme.error.main : props.theme.text.hint};
  min-height: 1rem;
`;

/**
 * TextField Component
 *
 * A customizable text input component with floating label, variants, sizes, and states.
 * Built with Emotion to replace Material-UI TextField component.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic text field
 * <TextField label="Name" placeholder="Enter name" />
 *
 * // With value and change handler
 * <TextField
 *   label="Email"
 *   type="email"
 *   value={email}
 *   onChange={(e) => setEmail(e.target.value)}
 *   fullWidth
 * />
 *
 * // With error state
 * <TextField
 *   label="Password"
 *   type="password"
 *   error
 *   errorMessage="Password is required"
 *   required
 * />
 *
 * // With adornments
 * <TextField
 *   label="Search"
 *   placeholder="Search..."
 *   startAdornment={<SearchIcon />}
 * />
 *
 * // Multiline
 * <TextField
 *   label="Description"
 *   multiline
 *   rows={4}
 *   fullWidth
 * />
 *
 * // Number input
 * <TextField
 *   label="Amount"
 *   type="number"
 *   min={0}
 *   max={100}
 * />
 *
 * // Date input
 * <TextField
 *   label="Birthday"
 *   type="date"
 * />
 *
 * // With react-hook-form
 * <Controller
 *   name="email"
 *   control={control}
 *   render={({ field }) => (
 *     <TextField
 *       {...field}
 *       label="Email"
 *       error={!!errors.email}
 *       errorMessage={errors.email?.message}
 *     />
 *   )}
 * />
 * ```
 */
export const TextField = forwardRef<HTMLDivElement, TextFieldProps>(
  ({
    label,
    helperText,
    error = false,
    errorMessage,
    required = false,
    fullWidth = false,
    size = 'medium',
    color = 'primary',
    multiline = false,
    rows,
    minRows,
    maxRows,
    className,
    style,
    InputProps,
    LabelProps,
    startAdornment,
    endAdornment,
    disabled = false,
    inputRef,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const [focused, setFocused] = React.useState(false);
    const [internalValue, setInternalValue] = React.useState(rest.value || '');

    // Determine if field has a value
    const hasValue = internalValue !== undefined && internalValue !== '';

    // Handle focus
    const handleFocus = (event: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setFocused(true);
      if (rest.onFocus) {
        rest.onFocus(event as React.FocusEvent<HTMLInputElement>);
      }
    };

    // Handle blur
    const handleBlur = (event: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setFocused(false);
      if (rest.onBlur) {
        rest.onBlur(event as React.FocusEvent<HTMLInputElement>);
      }
    };

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setInternalValue(event.target.value);
      if (rest.onChange) {
        rest.onChange(event as React.ChangeEvent<HTMLInputElement>);
      }
    };

    // Merge input props
    const mergedInputProps = { ...rest, ...InputProps };

    // Get error message
    const displayHelperText = error && errorMessage ? errorMessage : helperText;

    const containerProps = {
      ref,
      fullWidth,
      className,
      style: {
        ...getColorStyles(color, theme),
        ...style,
      },
    };

    const inputElement = multiline ? (
      <StyledTextarea
        {...(mergedInputProps as any)}
        ref={inputRef}
        error={error}
        size={size}
        disabled={disabled}
        rows={rows}
        placeholder={label ? undefined : mergedInputProps.placeholder}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onChange={handleChange}
      />
    ) : (
      <>
        <StyledInput
          {...mergedInputProps}
          ref={inputRef}
          error={error}
          size={size}
          disabled={disabled}
          hasStartAdornment={!!startAdornment}
          hasEndAdornment={!!endAdornment}
          placeholder={label ? undefined : mergedInputProps.placeholder}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onChange={handleChange}
        />
        {startAdornment && <Adornment position="start">{startAdornment}</Adornment>}
        {endAdornment && <Adornment position="end">{endAdornment}</Adornment>}
      </>
    );

    return (
      <StyledContainer {...containerProps}>
        {label && !multiline && (
          <StyledLabel
            as="label"
            hasValue={hasValue}
            isFocused={focused}
            hasError={error}
            disabled={disabled}
            size={size}
            required={required}
            {...LabelProps}
          >
            {label}
          </StyledLabel>
        )}
        {inputElement}
        {displayHelperText && (
          <HelperText error={error && !!errorMessage}>
            {displayHelperText}
          </HelperText>
        )}
      </StyledContainer>
    );
  }
);

TextField.displayName = 'TextField';

export default TextField;
