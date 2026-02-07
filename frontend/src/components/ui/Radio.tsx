import React, { forwardRef, createContext, useContext, useState, useCallback } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Radio size variants
 */
export type RadioSize = 'small' | 'medium' | 'large';

/**
 * Radio color variants
 */
export type RadioColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Radio option interface
 */
export interface RadioOption {
  /** Option value */
  value: string | number;
  /** Option label */
  label: string;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Base Radio props interface
 */
export interface BaseRadioProps {
  /** Radio value */
  value?: string | number;
  /** Checked state */
  checked?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Radio label */
  label?: string;
  /** Label placement */
  labelPlacement?: 'end' | 'start' | 'top' | 'bottom';
  /** Radio size */
  size?: RadioSize;
  /** Color variant */
  color?: RadioColor;
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
}

/**
 * Props for Radio component
 * Extends standard HTML input attributes
 */
export interface RadioProps extends BaseRadioProps, Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'onChange' | 'checked' | 'ref'> {}

/**
 * RadioGroup context interface
 */
interface RadioGroupContextValue {
  name?: string;
  value?: string | number;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>, value: string | number) => void;
  size?: RadioSize;
  color?: RadioColor;
  disabled?: boolean;
}

/**
 * RadioGroup context
 */
const RadioGroupContext = createContext<RadioGroupContextValue | undefined>(undefined);

/**
 * Get color styles based on color
 */
const getColorStyles = (color: RadioColor, theme: EmotionTheme) => {
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
    '--radio-color': colors.main,
    '--radio-color-light': colors.light,
    '--radio-color-dark': colors.dark,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: RadioSize) => {
  const sizeMap = {
    small: {
      radioSize: '16px',
      dotSize: '8px',
      fontSize: '0.875rem',
      gap: '8px',
    },
    medium: {
      radioSize: '20px',
      dotSize: '10px',
      fontSize: '1rem',
      gap: '10px',
    },
    large: {
      radioSize: '24px',
      dotSize: '12px',
      fontSize: '1.125rem',
      gap: '12px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled label for radio container
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
 * Hidden radio input
 */
const HiddenRadio = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  pointer-events: none;

  &:focus-visible + .radio-visual {
    outline: 2px solid var(--radio-color);
    outline-offset: 2px;
  }
`;

/**
 * Visual radio element
 */
const RadioVisual = styled.span<{
  checked: boolean;
  disabled?: boolean;
  error?: boolean;
  size: RadioSize;
}>`
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: ${props => getSizeStyles(props.size).radioSize};
  height: ${props => getSizeStyles(props.size).radioSize};
  border: 2px solid ${props => {
    if (props.error) return props.theme.error.main;
    if (props.disabled) return props.theme.text.disabled;
    return props.theme.text.secondary;
  }};
  border-radius: 50%;
  background-color: ${props => props.theme.background.paper};
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  flex-shrink: 0;

  /* Inner dot for checked state */
  &::after {
    content: '';
    position: absolute;
    width: ${props => getSizeStyles(props.size).dotSize};
    height: ${props => getSizeStyles(props.size).dotSize};
    border-radius: 50%;
    background-color: ${props => {
      if (props.error) return props.theme.error.main;
      return 'var(--radio-color)';
    }};
    transform: ${props => props.checked ? 'scale(1)' : 'scale(0)'};
    transition: transform ${props => props.theme.transitions.duration.shortest}ms ${props => props.theme.transitions.easing.easeInOut};
  }

  /* Hover state */
  ${StyledLabel}:hover:not([data-disabled='true']) & {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--radio-color)'};
  }

  /* Disabled state */
  ${props => props.disabled && `
    background-color: ${props.theme.background.paper};
    border-color: ${props.theme.text.disabled};

    &::after {
      background-color: ${props.theme.text.disabled};
    }
  `}
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
 * Radio Component
 *
 * A customizable radio button component with label placement options and validation states.
 * Built with Emotion to replace Material-UI Radio component.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic radio
 * <Radio value="option1" label="Option 1" />
 *
 * // Controlled radio (use with RadioGroup)
 * <RadioGroup
 *   name="category"
 *   value={category}
 *   onChange={(e, value) => setCategory(value)}
 * >
 *   <Radio value="option1" label="Option 1" />
 *   <Radio value="option2" label="Option 2" />
 *   <Radio value="option3" label="Option 3" />
 * </RadioGroup>
 *
 * // Different sizes
 * <Radio size="small" label="Small" />
 * <Radio size="medium" label="Medium" />
 * <Radio size="large" label="Large" />
 *
 * // Different colors
 * <Radio color="primary" label="Primary" />
 * <Radio color="secondary" label="Secondary" />
 * <Radio color="success" label="Success" />
 * <Radio color="error" label="Error" />
 *
 * // Label placement
 * <Radio labelPlacement="start" label="Label on left" />
 * <Radio labelPlacement="top" label="Label on top" />
 *
 * // Disabled
 * <Radio disabled checked label="Disabled checked" />
 * <Radio disabled label="Disabled unchecked" />
 *
 * // With react-hook-form
 * <Controller
 *   name="plan"
 *   control={control}
 *   render={({ field }) => (
 *     <RadioGroup
 *       value={field.value}
 *       onChange={(e, value) => field.onChange(value)}
 *     >
 *       <Radio value="free" label="Free Plan" />
 *       <Radio value="pro" label="Pro Plan" />
 *       <Radio value="enterprise" label="Enterprise Plan" />
 *     </RadioGroup>
 *   )}
 * />
 * ```
 */
export const Radio = forwardRef<HTMLLabelElement, RadioProps>(
  ({
    value: radioValue,
    checked: controlledChecked,
    disabled: propDisabled,
    label,
    labelPlacement = 'end',
    size: propSize,
    color: propColor,
    error = false,
    readOnly = false,
    onChange: propOnChange,
    className,
    style,
    inputRef,
    LabelProps,
    name: propName,
    id,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const context = useContext(RadioGroupContext);

    // Use context values if provided, otherwise use props
    const name = propName || context?.name;
    const groupValue = context?.value;
    const size = propSize || context?.size || 'medium';
    const color = propColor || context?.color || 'primary';
    const disabled = propDisabled || context?.disabled;

    // Determine checked state
    const isChecked = controlledChecked !== undefined
      ? controlledChecked
      : groupValue !== undefined && radioValue !== undefined
      ? groupValue === radioValue
      : false;

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (readOnly) return;

      const checked = event.target.checked;

      if (propOnChange) {
        propOnChange(event, checked);
      }

      if (context?.onChange && radioValue !== undefined) {
        context.onChange(event, radioValue);
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
        <HiddenRadio
          {...rest}
          ref={inputRef}
          type="radio"
          name={name}
          id={id}
          value={radioValue}
          checked={isChecked}
          disabled={disabled}
          onChange={handleChange}
        />
        <RadioVisual
          className="radio-visual"
          checked={isChecked}
          disabled={disabled}
          error={error}
          size={size}
        />
        {label && (
          <LabelText
            disabled={disabled}
            error={error}
            {...LabelProps}
          >
            {label}
          </LabelText>
        )}
      </StyledLabel>
    );
  }
);

Radio.displayName = 'Radio';

/**
 * RadioGroup Component
 *
 * A container for Radio components that provides shared state and context.
 * Simplifies managing radio button groups.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <RadioGroup
 *   name="gender"
 *   value={gender}
 *   onChange={(e, value) => setGender(value)}
 * >
 *   <Radio value="male" label="Male" />
 *   <Radio value="female" label="Female" />
 *   <Radio value="other" label="Other" />
 * </RadioGroup>
 *
 * // With row layout
 * <RadioGroup
 *   name="plan"
 *   value={plan}
 *   onChange={handlePlanChange}
 *   row
 * >
 *   <Radio value="free" label="Free" />
 *   <Radio value="pro" label="Pro" />
 *   <Radio value="enterprise" label="Enterprise" />
 * </RadioGroup>
 *
 * // With error state
 * <RadioGroup
 *   name="option"
 *   value={option}
 *   onChange={handleOptionChange}
 *   error
 *   helperText="Please select an option"
 * >
 *   <Radio value="a" label="Option A" />
 *   <Radio value="b" label="Option B" />
 * </RadioGroup>
 *
 * // Disabled group
 * <RadioGroup
 *   name="disabled-group"
 *   value="option1"
 *   disabled
 * >
 *   <Radio value="option1" label="Option 1" />
 *   <Radio value="option2" label="Option 2" />
 * </RadioGroup>
 * ```
 */
export interface RadioGroupProps {
  /** Group name for all radio buttons */
  name?: string;
  /** Selected value */
  value?: string | number;
  /** Default selected value (uncontrolled) */
  defaultValue?: string | number;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>, value: string | number) => void;
  /** Radio button size */
  size?: RadioSize;
  /** Color variant */
  color?: RadioColor;
  /** Disabled state for all radio buttons */
  disabled?: boolean;
  /** Layout direction */
  row?: boolean;
  /** Error state */
  error?: boolean;
  /** Helper text */
  helperText?: string;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Child radio components */
  children: React.ReactNode;
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  value: controlledValue,
  defaultValue,
  onChange,
  size = 'medium',
  color = 'primary',
  disabled = false,
  row = false,
  error = false,
  helperText,
  className,
  style,
  children,
}) => {
  const { theme } = useEmotionTheme();
  const [internalValue, setInternalValue] = useState<string | number | undefined>(defaultValue);

  // Determine if controlled
  const isControlled = controlledValue !== undefined;
  const currentValue = isControlled ? controlledValue : internalValue;

  // Handle change
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>, newValue: string | number) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }

    if (onChange) {
      onChange(event, newValue);
    }
  }, [isControlled, onChange]);

  const contextValue: RadioGroupContextValue = {
    name,
    value: currentValue,
    onChange: handleChange,
    size,
    color,
    disabled,
  };

  const groupStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: row ? 'row' : 'column',
    gap: row ? '24px' : '8px',
    ...style,
  };

  return (
    <RadioGroupContext.Provider value={contextValue}>
      <div className={className} style={groupStyle}>
        {children}
      </div>
      {helperText && (
        <HelperText error={error}>
          {helperText}
        </HelperText>
      )}
    </RadioGroupContext.Provider>
  );
};

/**
 * Helper text container
 */
const HelperText = styled.p<{ error?: boolean }>`
  margin: 4px 0 0 0;
  font-size: 0.75rem;
  color: ${props => props.error ? props.theme.error.main : props.theme.text.hint};
`;

RadioGroup.displayName = 'RadioGroup';

/**
 * FormControlLabel component for Radio
 * This is simply a re-export of Radio for consistency with MUI
 */
export const FormControlLabelRadio = Radio;

export default Radio;
