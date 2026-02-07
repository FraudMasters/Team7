import React, { forwardRef } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Switch size variants
 */
export type SwitchSize = 'small' | 'medium' | 'large';

/**
 * Switch color variants
 */
export type SwitchColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Base Switch props interface
 */
export interface BaseSwitchProps {
  /** Checked state */
  checked?: boolean;
  /** Default checked state (uncontrolled) */
  defaultChecked?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Switch label */
  label?: string;
  /** Label placement */
  labelPlacement?: 'end' | 'start' | 'top' | 'bottom';
  /** Required indicator */
  required?: boolean;
  /** Switch size */
  size?: SwitchSize;
  /** Color variant */
  color?: SwitchColor;
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
  /** Icon to show when unchecked */
  icon?: React.ReactNode;
  /** Icon to show when checked */
  checkedIcon?: React.ReactNode;
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
 * Props for Switch component
 * Extends standard HTML input attributes
 */
export interface SwitchProps extends BaseSwitchProps, Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'onChange' | 'checked' | 'ref'> {}

/**
 * Get color styles based on color
 */
const getColorStyles = (color: SwitchColor, theme: EmotionTheme) => {
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
    '--switch-color': colors.main,
    '--switch-color-light': colors.light,
    '--switch-color-dark': colors.dark,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: SwitchSize) => {
  const sizeMap = {
    small: {
      width: '32px',
      height: '20px',
      thumbSize: '14px',
      thumbOffset: '14px',
      fontSize: '0.875rem',
      gap: '8px',
    },
    medium: {
      width: '40px',
      height: '24px',
      thumbSize: '18px',
      thumbOffset: '18px',
      fontSize: '1rem',
      gap: '10px',
    },
    large: {
      width: '48px',
      height: '28px',
      thumbSize: '22px',
      thumbOffset: '22px',
      fontSize: '1.125rem',
      gap: '12px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled label for switch container
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
 * Hidden switch input
 */
const HiddenSwitch = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  pointer-events: none;

  &:focus-visible + .switch-track {
    outline: 2px solid var(--switch-color);
    outline-offset: 2px;
  }
`;

/**
 * Switch track (background)
 */
const SwitchTrack = styled.span<{
  checked: boolean;
  disabled?: boolean;
  error?: boolean;
  size: SwitchSize;
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  width: ${props => getSizeStyles(props.size).width};
  height: ${props => getSizeStyles(props.size).height};
  border-radius: 9999px;
  background-color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.error) return props.checked ? props.theme.error.main : props.theme.grey[300];
    if (props.checked) return 'var(--switch-color)';
    return props.theme.grey[400];
  }};
  transition: background-color ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  flex-shrink: 0;

  /* Hover state */
  ${StyledLabel}:hover:not([data-disabled='true']) & {
    background-color: ${props => {
      if (props.error) return props.checked ? props.theme.error.dark : props.theme.grey[400];
      if (props.checked) return 'var(--switch-color-dark)';
      return props.theme.grey[500];
    }};
  }
`;

/**
 * Switch thumb (circle that slides)
 */
const SwitchThumb = styled.span<{
  checked: boolean;
  disabled?: boolean;
  size: SwitchSize;
}>`
  position: absolute;
  width: ${props => getSizeStyles(props.size).thumbSize};
  height: ${props => getSizeStyles(props.size).thumbSize};
  border-radius: 50%;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transform: translateX(${props => props.checked ? getSizeStyles(props.size).thumbOffset : '2px'});
  transition: transform ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  left: 0;

  ${props => props.disabled && `
    background-color: ${props.theme.grey[400]};
    box-shadow: none;
  `}
`;

/**
 * Icon container within thumb
 */
const IconContainer = styled.span`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  color: ${props => props.theme.text.secondary};
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
 * Switch Component
 *
 * A customizable switch component (toggle) with label placement options and validation states.
 * Built with Emotion to replace Material-UI Switch component.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic switch
 * <Switch label="Enable notifications" />
 *
 * // Controlled switch
 * <Switch
 *   checked={enabled}
 *   onChange={(e, checked) => setEnabled(checked)}
 *   label="Dark mode"
 * />
 *
 * // With error state
 * <Switch
 *   checked={agreed}
 *   onChange={(e, checked) => setAgreed(checked)}
 *   error
 *   label="You must agree to continue"
 *   required
 * />
 *
 * // Different sizes
 * <Switch size="small" label="Small" />
 * <Switch size="medium" label="Medium" />
 * <Switch size="large" label="Large" />
 *
 * // Different colors
 * <Switch color="primary" label="Primary" />
 * <Switch color="secondary" label="Secondary" />
 * <Switch color="success" label="Success" />
 * <Switch color="error" label="Error" />
 *
 * // Label placement
 * <Switch labelPlacement="start" label="Label on left" />
 * <Switch labelPlacement="top" label="Label on top" />
 *
 * // With icons
 * <Switch
 *   icon={<Icon name="X" />}
 *   checkedIcon={<Icon name="Check" />}
 *   label="With icons"
 * />
 *
 * // Disabled
 * <Switch disabled checked label="Disabled checked" />
 * <Switch disabled label="Disabled unchecked" />
 *
 * // With react-hook-form
 * <Controller
 *   name="marketingEmails"
 *   control={control}
 *   render={({ field }) => (
 *     <Switch
 *       {...field}
 *       checked={field.value}
 *       onChange={(e, checked) => field.onChange(checked)}
 *       label="Subscribe to marketing emails"
 *     />
 *   )}
 * />
 * ```
 */
export const Switch = forwardRef<HTMLLabelElement, SwitchProps>(
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
    icon,
    checkedIcon,
    name,
    id,
    value,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const [internalChecked, setInternalChecked] = React.useState(defaultChecked);

    // Determine if controlled
    const isControlled = controlledChecked !== undefined;
    const isChecked = isControlled ? controlledChecked : internalChecked;

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (readOnly) return;

      const newChecked = event.target.checked;

      if (!isControlled) {
        setInternalChecked(newChecked);
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
        <HiddenSwitch
          {...rest}
          ref={inputRef}
          type="checkbox"
          role="switch"
          name={name}
          id={id}
          value={value}
          checked={isChecked}
          defaultChecked={isControlled ? undefined : defaultChecked}
          disabled={disabled}
          onChange={handleChange}
        />
        <SwitchTrack
          className="switch-track"
          checked={isChecked}
          disabled={disabled}
          error={error}
          size={size}
        >
          <SwitchThumb
            checked={isChecked}
            disabled={disabled}
            size={size}
          >
            {isChecked ? (
              checkedIcon ? <IconContainer>{checkedIcon}</IconContainer> : null
            ) : (
              icon ? <IconContainer>{icon}</IconContainer> : null
            )}
          </SwitchThumb>
        </SwitchTrack>
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

Switch.displayName = 'Switch';

/**
 * FormControlLabel component for Switch
 * This is simply a re-export of Switch for consistency with MUI
 */
export const FormControlLabelSwitch = Switch;

export default Switch;
