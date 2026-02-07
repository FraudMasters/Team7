import React, { forwardRef, useRef, useState } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Select size variants
 */
export type SelectSize = 'small' | 'medium';

/**
 * Select color variants
 */
export type SelectColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Select option interface
 */
export interface SelectOption {
  /** Option value */
  value: string | number;
  /** Option label */
  label: string;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Select option group interface
 */
export interface SelectOptionGroup {
  /** Group label */
  label: string;
  /** Group options */
  options: SelectOption[];
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Base Select props interface
 */
export interface BaseSelectProps {
  /** Select value */
  value?: string | number | string[] | number[];
  /** Label text */
  label?: string;
  /** Helper text to display below select */
  helperText?: string;
  /** Error state */
  error?: boolean;
  /** Error message to display */
  errorMessage?: string;
  /** Required indicator */
  required?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Select size */
  size?: SelectSize;
  /** Color variant (for focus/border) */
  color?: SelectColor;
  /** Placeholder text (when no value selected) */
  placeholder?: string;
  /** Multiple selection mode */
  multiple?: boolean;
  /** Native select */
  native?: boolean;
  /** Options array */
  options?: (SelectOption | SelectOptionGroup)[];
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  /** Focus handler */
  onFocus?: (event: React.FocusEvent<HTMLSelectElement>) => void;
  /** Blur handler */
  onBlur?: (event: React.FocusEvent<HTMLSelectElement>) => void;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Select element reference */
  selectRef?: React.Ref<HTMLSelectElement>;
  /** Label props */
  LabelProps?: {
    className?: string;
    style?: React.CSSProperties;
  };
  /** Reference to container element */
  ref?: React.Ref<HTMLDivElement>;
  /** Input name */
  name?: string;
  /** Input ID */
  id?: string;
  /** Display empty option */
  displayEmpty?: boolean;
}

/**
 * Props for Select component
 * Extends standard HTML select attributes
 */
export interface SelectProps extends BaseSelectProps, Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size' | 'onChange' | 'value'> {}

/**
 * Get color styles based on color
 */
const getColorStyles = (color: SelectColor, theme: EmotionTheme) => {
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
    '--select-color': colors.main,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: SelectSize) => {
  const sizeMap = {
    small: {
      minHeight: '32px',
      fontSize: '0.875rem',
      padding: '4px 32px 4px 12px',
    },
    medium: {
      minHeight: '40px',
      fontSize: '1rem',
      padding: '8px 32px 8px 14px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled container for Select
 */
const StyledContainer = styled.div<{ fullWidth?: boolean; className?: string }>`
  position: relative;
  width: ${props => props.fullWidth ? '100%' : 'auto'};
  ${props => props.className};
`;

/**
 * Styled label for Select
 */
const StyledLabel = styled.label<{ hasValue: boolean; isFocused: boolean; hasError: boolean; disabled?: boolean; size: SelectSize; required?: boolean }>`
  display: block;
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.hasError) return props.theme.error.main;
    if (props.isFocused) return `var(--select-color)`;
    return props.theme.text.secondary;
  }};
  font-size: ${props => getSizeStyles(props.size).fontSize};
  pointer-events: none;
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  background-color: ${props => props.theme.background.paper};
  padding: 0 4px;
  transition-property: font-size, top, color, transform;
  z-index: 1;

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
 * Styled select element
 */
const StyledSelect = styled.select<{
  error?: boolean;
  size: SelectSize;
  disabled?: boolean;
}>`
  width: 100%;
  border: 1px solid ${props => props.error ? props.theme.error.main : props.theme.divider};
  border-radius: ${props => props.theme.borderRadius.md};
  background-color: ${props => props.theme.background.paper};
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23616161' d='M6 8.825L1.175 4 2.238 2.938 6 6.7l3.763-3.762L10.825 4z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  color: ${props => props.theme.text.primary};
  font-family: ${props => props.theme.typography.fontFamily};
  ${props => getSizeStyles(props.size)};
  outline: none;
  transition: border-color ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut},
              box-shadow ${props => props.theme.transitions.duration.shorter}ms ${props => props.transitions.easing.easeInOut};
  box-sizing: border-box;
  appearance: none;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};

  /* Focus state */
  &:focus {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--select-color)'};
    box-shadow: 0 0 0 2px ${props => props.error ? 'rgba(211, 47, 47, 0.2)' : 'rgba(25, 118, 210, 0.2)'};

    & + label {
      color: ${props => props.error ? props.theme.error.main : 'var(--select-color)'};
    }
  }

  /* Disabled state */
  &:disabled {
    background-color: ${props => props.theme.action.disabledBackground};
    color: ${props => props.theme.text.disabled};
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Reset browser styles */
  &::-ms-expand {
    display: none;
  }

  /* Option styles */
  & option {
    background-color: ${props => props.theme.background.paper};
    color: ${props => props.theme.text.primary};
    padding: 8px 12px;

    &:disabled {
      color: ${props => props.theme.text.disabled};
      background-color: ${props => props.action.disabledBackground};
    }

    &:hover {
      background-color: ${props => props.theme.action.hover};
    }
  }

  & optgroup {
    font-weight: 600;
    color: ${props => props.theme.text.secondary};
    background-color: ${props => props.theme.background.default};
  }
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
 * Select Component
 *
 * A dropdown select component with floating label, variants, sizes, and validation states.
 * Built with Emotion to replace Material-UI Select component.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic select
 * <Select
 *   label="Country"
 *   options={[
 *     { value: 'us', label: 'United States' },
 *     { value: 'uk', label: 'United Kingdom' },
 *     { value: 'ca', label: 'Canada' },
 *   ]}
 * />
 *
 * // With value and change handler
 * <Select
 *   label="Status"
 *   value={status}
 *   onChange={(e) => setStatus(e.target.value)}
 *   options={[
 *     { value: 'active', label: 'Active' },
 *     { value: 'inactive', label: 'Inactive' },
 *     { value: 'pending', label: 'Pending' },
 *   ]}
 *   fullWidth
 * />
 *
 * // With error state
 * <Select
 *   label="Role"
 *   error
 *   errorMessage="Role is required"
 *   required
 *   options={[
 *     { value: 'admin', label: 'Admin' },
 *     { value: 'user', label: 'User' },
 *   ]}
 * />
 *
 * // With option groups
 * <Select
 *   label="Category"
 *   options={[
 *     {
 *       label: 'Fruits',
 *       options: [
 *         { value: 'apple', label: 'Apple' },
 *         { value: 'banana', label: 'Banana' },
 *       ],
 *     },
 *     {
 *       label: 'Vegetables',
 *       options: [
 *         { value: 'carrot', label: 'Carrot' },
 *         { value: 'broccoli', label: 'Broccoli' },
 *       ],
 *     },
 *   ]}
 * />
 *
 * // With disabled options
 * <Select
 *   label="Plan"
 *   options={[
 *     { value: 'free', label: 'Free' },
 *     { value: 'pro', label: 'Pro', disabled: true },
 *     { value: 'enterprise', label: 'Enterprise' },
 *   ]}
 * />
 *
 * // With placeholder
 * <Select
 *   label="Select an option"
 *   placeholder="Choose..."
 *   displayEmpty
 *   options={[
 *     { value: 'option1', label: 'Option 1' },
 *     { value: 'option2', label: 'Option 2' },
 *   ]}
 * />
 *
 * // Multiple select
 * <Select
 *   label="Tags"
 *   multiple
 *   value={selectedTags}
 *   onChange={(e) => {
 *     const values = Array.from(e.target.selectedOptions, option => option.value);
 *     setSelectedTags(values);
 *   }}
 *   options={[
 *     { value: 'react', label: 'React' },
 *     { value: 'vue', label: 'Vue' },
 *     { value: 'angular', label: 'Angular' },
 *   ]}
 * />
 *
 * // With react-hook-form
 * <Controller
 *   name="country"
 *   control={control}
 *   render={({ field }) => (
 *     <Select
 *       {...field}
 *       label="Country"
 *       options={countryOptions}
 *       error={!!errors.country}
 *       errorMessage={errors.country?.message}
 *     />
 *   )}
 * />
 * ```
 */
export const Select = forwardRef<HTMLDivElement, SelectProps>(
  ({
    label,
    helperText,
    error = false,
    errorMessage,
    required = false,
    disabled = false,
    fullWidth = false,
    size = 'medium',
    color = 'primary',
    placeholder,
    multiple = false,
    native = true,
    options = [],
    displayEmpty = false,
    onChange,
    onFocus,
    onBlur,
    selectRef,
    LabelProps,
    className,
    style,
    name,
    id,
    value: controlledValue,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const [focused, setFocused] = useState(false);
    const internalRef = useRef<HTMLSelectElement>(null);

    // Use external ref if provided, otherwise use internal ref
    const selectElementRef = (selectRef as any) || internalRef;

    // Determine if field has a value
    const hasValue = controlledValue !== undefined && controlledValue !== '';

    // Handle focus
    const handleFocus = (event: React.FocusEvent<HTMLSelectElement>) => {
      setFocused(true);
      if (onFocus) {
        onFocus(event);
      }
    };

    // Handle blur
    const handleBlur = (event: React.FocusEvent<HTMLSelectElement>) => {
      setFocused(false);
      if (onBlur) {
        onBlur(event);
      }
    };

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
      if (onChange) {
        onChange(event);
      }
    };

    // Get error message
    const displayHelperText = error && errorMessage ? errorMessage : helperText;

    // Render options
    const renderOptions = () => {
      return options.map((optionOrGroup, index) => {
        // Check if it's an option group
        if ('options' in optionOrGroup) {
          const group = optionOrGroup as SelectOptionGroup;
          return (
            <optgroup key={`group-${index}`} label={group.label} disabled={group.disabled}>
              {group.options.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                >
                  {option.label}
                </option>
              ))}
            </optgroup>
          );
        }

        // It's a single option
        const option = optionOrGroup as SelectOption;
        return (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        );
      });
    };

    const containerProps = {
      ref,
      fullWidth,
      className,
      style: {
        ...getColorStyles(color, theme),
        ...style,
      },
    };

    return (
      <StyledContainer {...containerProps}>
        {label && (
          <StyledLabel
            as="label"
            htmlFor={id}
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
        <StyledSelect
          {...rest}
          ref={selectElementRef}
          id={id}
          name={name}
          value={controlledValue !== undefined ? controlledValue : ''}
          error={error}
          size={size}
          disabled={disabled}
          multiple={multiple}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onChange={handleChange}
        >
          {displayEmpty && <option value="">{placeholder || label}</option>}
          {renderOptions()}
        </StyledSelect>
        {displayHelperText && (
          <HelperText error={error && !!errorMessage}>
            {displayHelperText}
          </HelperText>
        )}
      </StyledContainer>
    );
  }
);

Select.displayName = 'Select';

export default Select;
