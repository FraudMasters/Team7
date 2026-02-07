import React, { forwardRef, useEffect, useRef } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Checkbox size variants
 */
export type CheckboxSize = 'small' | 'medium' | 'large';

/**
 * Checkbox color variants
 */
export type CheckboxColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Base Checkbox props interface
 */
export interface BaseCheckboxProps {
  /** Checked state */
  checked?: boolean | 'indeterminate';
  /** Default checked state (uncontrolled) */
  defaultChecked?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Checkbox label */
  label?: string;
  /** Label placement */
  labelPlacement?: 'end' | 'start' | 'top' | 'bottom';
  /** Required indicator */
  required?: boolean;
  /** Checkbox size */
  size?: CheckboxSize;
  /** Color variant */
  color?: CheckboxColor;
  /** Show error state */
  error?: boolean;
  /** Read-only */
  readOnly?: boolean;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => void;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Input reference */
  inputRef?: React.Ref<HTMLInputElement>;
  /** Label props */
  LabelProps?: {
    className?: string;
    style?: React.CSSProperties;
  };
  /** Reference to container element */
  ref?: React.Ref<HTMLLabelElement>;
  /** Input name */
  name?: string;
  /** Input ID */
  id?: string;
  /** Input value */
  value?: string | number;
}

/**
 * Props for Checkbox component
 * Extends standard HTML input attributes
 */
export interface CheckboxProps extends BaseCheckboxProps, Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'onChange' | 'checked' | 'ref'> {}

/**
 * Get color styles based on color
 */
const getColorStyles = (color: CheckboxColor, theme: EmotionTheme) => {
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
    '--checkbox-color': colors.main,
    '--checkbox-color-light': colors.light,
    '--checkbox-color-dark': colors.dark,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: CheckboxSize) => {
  const sizeMap = {
    small: {
      checkboxSize: '16px',
      iconSize: '12px',
      fontSize: '0.875rem',
      gap: '8px',
    },
    medium: {
      checkboxSize: '20px',
      iconSize: '14px',
      fontSize: '1rem',
      gap: '10px',
    },
    large: {
      checkboxSize: '24px',
      iconSize: '16px',
      fontSize: '1.125rem',
      gap: '12px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled label for checkbox container
 */
const StyledLabel = styled.label<{ disabled?: boolean; labelPlacement?: string; gap?: string; flexDirection?: string; alignItems?: string }>`
  display: inline-flex;
  align-items: ${props => props.alignItems || 'center'};
  gap: ${props => props.gap || '10px'};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  user-select: none;
  flex-direction: ${props => props.flexDirection || 'row'};
  width: fit-content;

  &[data-disabled='true'] {
    cursor: not-allowed;
    opacity: 0.6;
  }
`;

/**
 * Hidden checkbox input
 */
const HiddenCheckbox = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  pointer-events: none;

  &:focus-visible + .checkbox-visual {
    outline: 2px solid var(--checkbox-color);
    outline-offset: 2px;
  }
`;

/**
 * Visual checkbox element
 */
const CheckboxVisual = styled.span<{
  checked: boolean;
  indeterminate: boolean;
  disabled?: boolean;
  error?: boolean;
  size: CheckboxSize;
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: ${props => getSizeStyles(props.size).checkboxSize};
  height: ${props => getSizeStyles(props.size).checkboxSize};
  border: 2px solid ${props => {
    if (props.error) return props.theme.error.main;
    if (props.disabled) return props.theme.text.disabled;
    return props.theme.text.secondary;
  }};
  border-radius: ${props => props.theme.borderRadius.xs};
  background-color: ${props => {
    if (props.checked || props.indeterminate) {
      if (props.error) return props.theme.error.main;
      return 'var(--checkbox-color)';
    }
    return props.theme.background.paper;
  }};
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  flex-shrink: 0;

  /* Hover state */
  ${StyledLabel}:hover:not([data-disabled='true']) & {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--checkbox-color)'};
    background-color: ${props => {
      if (props.checked || props.indeterminate) {
        return props.error ? props.theme.error.dark : 'var(--checkbox-color-dark)';
      }
      return 'transparent';
    }};
  }

  /* Disabled state */
  ${props => props.disabled && `
    background-color: ${props.checked || props.indeterminate ? props.theme.action.disabledBackground : 'transparent'};
    border-color: ${props.theme.text.disabled};
  `}
`;

/**
 * Checkbox icon (check mark or indeterminate)
 */
const CheckboxIcon = styled.svg<{ size: CheckboxSize }>`
  width: ${props => getSizeStyles(props.size).iconSize};
  height: ${props => getSizeStyles(props.size).iconSize};
  fill: none;
  stroke: white;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  pointer-events: none;
`;

/**
 * Label text
 */
const LabelText = styled.span<{ disabled?: boolean; error?: boolean }>`
  font-size: inherit;
  color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.error) return props.theme.error.main;
    return props.theme.text.primary;
  }};
`;

/**
 * Checkbox Component
 *
 * A customizable checkbox component with indeterminate state, label placement options, and validation states.
 * Built with Emotion to replace Material-UI Checkbox component.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic checkbox
 * <Checkbox label="Accept terms" />
 *
 * // Controlled checkbox
 * <Checkbox
 *   checked={accepted}
 *   onChange={(e, checked) => setAccepted(checked)}
 *   label="I accept the terms and conditions"
 * />
 *
 * // With error state
 * <Checkbox
 *   checked={agreed}
 *   onChange={(e, checked) => setAgreed(checked)}
 *   error
 *   label="You must agree to continue"
 *   required
 * />
 *
 * // Indeterminate state
 * <Checkbox
 *   checked="indeterminate"
 *   onChange={handleChange}
 *   label="Select all"
 * />
 *
 * // Different sizes
 * <Checkbox size="small" label="Small" />
 * <Checkbox size="medium" label="Medium" />
 * <Checkbox size="large" label="Large" />
 *
 * // Different colors
 * <Checkbox color="primary" label="Primary" />
 * <Checkbox color="secondary" label="Secondary" />
 * <Checkbox color="success" label="Success" />
 * <Checkbox color="error" label="Error" />
 *
 * // Label placement
 * <Checkbox labelPlacement="start" label="Label on left" />
 * <Checkbox labelPlacement="top" label="Label on top" />
 *
 * // Disabled
 * <Checkbox disabled checked label="Disabled checked" />
 * <Checkbox disabled label="Disabled unchecked" />
 *
 * // With react-hook-form
 * <Controller
 *   name="acceptTerms"
 *   control={control}
 *   render={({ field }) => (
 *     <Checkbox
 *       {...field}
 *       checked={field.value}
 *       onChange={(e, checked) => field.onChange(checked)}
 *       label="I accept the terms"
 *       error={!!errors.acceptTerms}
 *     />
 *   )}
 * />
 * ```
 */
export const Checkbox = forwardRef<HTMLLabelElement, CheckboxProps>(
  ({
    checked: controlledChecked,
    defaultChecked = false,
    disabled = false,
    label,
    labelPlacement = 'end',
    required = false,
    size = 'medium',
    color = 'primary',
    error = false,
    readOnly = false,
    onChange,
    className,
    style,
    inputRef,
    LabelProps,
    name,
    id,
    value,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const internalRef = useRef<HTMLInputElement>(null);
    const [internalChecked, setInternalChecked] = React.useState(defaultChecked);
    const [indeterminate, setIndeterminate] = React.useState(controlledChecked === 'indeterminate');

    // Use external ref if provided, otherwise use internal ref
    const checkboxElementRef = (inputRef as any) || internalRef;

    // Determine if controlled
    const isControlled = controlledChecked !== undefined;
    const isChecked = isControlled ? controlledChecked === true : internalChecked;
    const isIndeterminate = isControlled ? controlledChecked === 'indeterminate' : indeterminate;

    // Update indeterminate state
    useEffect(() => {
      if (checkboxElementRef.current) {
        checkboxElementRef.current.indeterminate = isIndeterminate;
      }
    }, [isIndeterminate, checkboxElementRef]);

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (readOnly) return;

      const newChecked = event.target.checked;

      if (!isControlled) {
        setInternalChecked(newChecked);
        setIndeterminate(false);
      }

      if (onChange) {
        onChange(event, newChecked);
      }
    };

    // Get flex direction based on label placement
    const getFlexDirection = () => {
      if (labelPlacement === 'top') return 'column';
      if (labelPlacement === 'bottom') return 'column-reverse';
      return 'row';
    };

    // Get align items based on label placement
    const getAlignItems = () => {
      if (labelPlacement === 'top' || labelPlacement === 'bottom') return 'flex-start';
      return 'center';
    };

    const containerProps = {
      ref,
      className,
      style: {
        ...getColorStyles(color, theme),
        ...style,
      },
      disabled,
      'data-disabled': disabled,
      labelPlacement,
      gap: getSizeStyles(size).gap,
      flexDirection: getFlexDirection(),
      alignItems: getAlignItems(),
    };

    return (
      <StyledLabel {...containerProps}>
        <HiddenCheckbox
          {...rest}
          ref={checkboxElementRef}
          type="checkbox"
          name={name}
          id={id}
          value={value}
          checked={isChecked}
          defaultChecked={isControlled ? undefined : defaultChecked}
          disabled={disabled}
          onChange={handleChange}
        />
        <CheckboxVisual
          className="checkbox-visual"
          checked={isChecked}
          indeterminate={isIndeterminate}
          disabled={disabled}
          error={error}
          size={size}
        >
          {(isChecked || isIndeterminate) && (
            <CheckboxIcon size={size} viewBox="0 0 24 24">
              {isIndeterminate ? (
                <line x1="6" y1="12" x2="18" y2="12" />
              ) : (
                <polyline points="20 6 9 17 4 12" />
              )}
            </CheckboxIcon>
          )}
        </CheckboxVisual>
        {label && (
          <LabelText
            disabled={disabled}
            error={error}
            {...LabelProps}
          >
            {label}
            {required && ' *'}
          </LabelText>
        )}
      </StyledLabel>
    );
  }
);

Checkbox.displayName = 'Checkbox';

/**
 * FormControlLabel component for consistency with MUI
 * This is simply a re-export of Checkbox with a different name
 */
export const FormControlLabel = Checkbox;

export default Checkbox;
