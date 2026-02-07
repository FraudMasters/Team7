import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * FormControl margin variant
 */
export type FormControlMargin = 'none' | 'normal' | 'dense';

/**
 * FormControl size
 */
export type FormControlSize = 'small' | 'medium';

/**
 * Props for FormLabel component
 */
export interface FormLabelProps {
  /** Label content */
  children?: React.ReactNode;
  /** If true, the label will indicate that the input is required */
  required?: boolean;
  /** If true, the label will be displayed in an error state */
  error?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  labelRef?: React.Ref<HTMLLabelElement>;
  /** For attribute to associate with input */
  htmlFor?: string;
  /** ARIA label for accessibility */
  'aria-label'?: string;
  /** ARIA described by */
  'aria-describedby'?: string;
}

/**
 * Props for FormHelperText component
 */
export interface FormHelperTextProps {
  /** Helper text content */
  children?: React.ReactNode;
  /** If true, the helper text will be displayed in an error state */
  error?: boolean;
  /** If true, the helper text will be disabled */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  helperRef?: React.Ref<HTMLParagraphElement>;
  /** ID for associating with input */
  id?: string;
}

/**
 * Base FormControl props interface
 */
export interface BaseFormControlProps {
  /** Form content */
  children?: React.ReactNode;
  /** If true, the component will be displayed in a disabled state */
  disabled?: boolean;
  /** If true, the component will be displayed in an error state */
  error?: boolean;
  /** If true, the label will be displayed with a required indicator */
  required?: boolean;
  /** If true, the form control will take up the full width of its container */
  fullWidth?: boolean;
  /** Margin to apply to the form control */
  margin?: FormControlMargin;
  /** Size of the form control */
  size?: FormControlSize;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  controlRef?: React.Ref<HTMLDivElement>;
  /** Variant to use */
  variant?: 'standard' | 'filled' | 'outlined';
}

/**
 * Props for FormControl component
 */
export interface FormControlProps extends BaseFormControlProps {}

/**
 * Styled container for FormControl
 */
const StyledFormControl = styled.div<{
  fullWidth?: boolean;
  margin?: FormControlMargin;
  size?: FormControlSize;
}>`
  position: relative;
  width: ${({ fullWidth }) => (fullWidth ? '100%' : 'auto')};

  /* Margin styles */
  ${({ margin }) => {
    if (margin === 'normal') {
      return 'margin-top: 16px; margin-bottom: 8px;';
    }
    if (margin === 'dense') {
      return 'margin-top: 8px; margin-bottom: 4px;';
    }
    return '';
  }}
`;

/**
 * Styled label for FormLabel
 */
const StyledFormLabel = styled.label<{
  error?: boolean;
  disabled?: boolean;
  required?: boolean;
  size?: FormControlSize;
}>`
  display: block;
  margin-bottom: ${({ size }) => (size === 'small' ? '4px' : '8px')};
  color: ${({ theme, error, disabled }) => {
    if (disabled) return theme.text.disabled;
    if (error) return theme.error.main;
    return theme.text.primary;
  }};
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-size: ${({ size }) => (size === 'small' ? '0.875rem' : '1rem')};
  font-weight: 500;
  line-height: 1.5;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'default')};

  /* Required indicator */
  ${({ required, theme }) =>
    required
      ? `
    &::after {
      content: ' *';
      color: ${theme.error.main};
    }
  `
      : ''}
`;

/**
 * Styled helper text for FormHelperText
 */
const StyledFormHelperText = styled.p<{
  error?: boolean;
  disabled?: boolean;
  size?: FormControlSize;
}>`
  margin: ${({ size }) => (size === 'small' ? '3px' : '4px')} 0 0 0;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-size: 0.75rem;
  line-height: 1.5;
  min-height: 1rem;
  color: ${({ theme, error, disabled }) => {
    if (disabled) return theme.text.disabled;
    if (error) return theme.error.main;
    return theme.text.hint;
  }};
`;

/**
 * FormLabel Component
 *
 * A label component for form controls with optional required indicator.
 *
 * @example
 * ```tsx
 * <FormLabel htmlFor="email">Email Address</FormLabel>
 * <FormLabel required>Required Field</FormLabel>
 * <FormLabel error>Email Address</FormLabel>
 * ```
 */
export const FormLabel = React.forwardRef<HTMLLabelElement, FormLabelProps>(
  ({ children, required = false, error = false, className, style, labelRef, htmlFor, 'aria-label': ariaLabel, 'aria-describedby': ariaDescribedby }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledFormLabel
        ref={ref || labelRef}
        theme={theme}
        required={required}
        error={error}
        className={className}
        style={style}
        htmlFor={htmlFor}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedby}
      >
        {children}
      </StyledFormLabel>
    );
  }
);

FormLabel.displayName = 'FormLabel';

/**
 * FormHelperText Component
 *
 * A helper text component for form controls that displays additional information.
 *
 * @example
 * ```tsx
 * <FormHelperText>We'll never share your email.</FormHelperText>
 * <FormHelperText error>Email is required</FormHelperText>
 * <FormHelperText disabled>Helper text</FormHelperText>
 * ```
 */
export const FormHelperText = React.forwardRef<HTMLParagraphElement, FormHelperTextProps>(
  ({ children, error = false, disabled = false, className, style, helperRef, id }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledFormHelperText
        ref={ref || helperRef}
        theme={theme}
        error={error}
        disabled={disabled}
        className={className}
        style={style}
        id={id}
      >
        {children}
      </StyledFormHelperText>
    );
  }
);

FormHelperText.displayName = 'FormHelperText';

/**
 * FormControl Component
 *
 * A container component that provides context for form controls.
 * Wraps form inputs with labels, helper text, and error states.
 * Built with Emotion to replace Material-UI FormControl component.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <FormControl>
 *   <FormLabel htmlFor="name">Name</FormLabel>
 *   <TextField id="name" placeholder="Enter your name" />
 * </FormControl>
 *
 * // With error state
 * <FormControl error>
 *   <FormLabel htmlFor="email">Email</FormLabel>
 *   <TextField id="email" error />
 *   <FormHelperText>Please enter a valid email address</FormHelperText>
 * </FormControl>
 *
 * // With required field
 * <FormControl required>
 *   <FormLabel htmlFor="password">Password</FormLabel>
 *   <TextField id="password" type="password" />
 *   <FormHelperText>Must be at least 8 characters</FormHelperText>
 * </FormControl>
 *
 * // With margin
 * <FormControl margin="normal">
 *   <FormLabel>Address</FormLabel>
 *   <TextField placeholder="Enter your address" />
 * </FormControl>
 *
 * // Full width
 * <FormControl fullWidth>
 *   <FormLabel>Message</FormLabel>
 *   <TextArea placeholder="Type your message" rows={4} />
 * </FormControl>
 *
 * // With select
 * <FormControl fullWidth margin="normal">
 *   <FormLabel htmlFor="country">Country</FormLabel>
 *   <Select id="country" options={countries} />
 *   <FormHelperText>Select your country</FormHelperText>
 * </FormControl>
 *
 * // Disabled
 * <FormControl disabled>
 *   <FormLabel>Disabled Field</FormLabel>
 *   <TextField disabled placeholder="This is disabled" />
 * </FormControl>
 *
 * // Dense spacing
 * <FormControl margin="dense">
 *   <FormLabel>City</FormLabel>
 *   <TextField placeholder="Enter city" />
 * </FormControl>
 * ```
 */
export const FormControl = React.forwardRef<HTMLDivElement, FormControlProps>(
  (
    {
      children,
      disabled = false,
      error = false,
      required = false,
      fullWidth = false,
      margin = 'none',
      size = 'medium',
      className,
      style,
      controlRef,
      variant,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Clone children and pass down context props
    const enhancedChildren = React.Children.map(children, (child) => {
      if (!React.isValidElement(child)) {
        return child;
      }

      // Don't override if child already has the prop
      const childProps: any = {};

      // For FormLabel, pass required if not already set
      const componentName = (child.type as any).displayName || (child.type as any).name;
      if (componentName === 'FormLabel' && required && !child.props.required) {
        childProps.required = required;
      }

      // For input-like components, pass error and disabled if not already set
      if (['TextField', 'TextArea', 'Select', 'Checkbox', 'Radio', 'Switch'].includes(componentName)) {
        if (error && !child.props.error) {
          childProps.error = error;
        }
        if (disabled && !child.props.disabled) {
          childProps.disabled = disabled;
        }
      }

      // For FormHelperText, pass error if not already set
      if (componentName === 'FormHelperText' && error && !child.props.error) {
        childProps.error = error;
      }

      // If there are props to apply, clone the element
      if (Object.keys(childProps).length > 0) {
        return React.cloneElement(child, childProps);
      }

      return child;
    });

    return (
      <StyledFormControl
        ref={ref || controlRef}
        theme={theme}
        fullWidth={fullWidth}
        margin={margin}
        size={size}
        className={className}
        style={style}
      >
        {enhancedChildren}
      </StyledFormControl>
    );
  }
);

FormControl.displayName = 'FormControl';

export default FormControl;
