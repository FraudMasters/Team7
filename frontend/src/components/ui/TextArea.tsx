import React, { forwardRef, useEffect, useRef } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { TextFieldProps } from './TextField';

/**
 * TextArea size variants
 */
export type TextAreaSize = 'small' | 'medium';

/**
 * TextArea color variants
 */
export type TextAreaColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Base TextArea props interface
 */
export interface BaseTextAreaProps {
  /** Textarea value */
  value?: string;
  /** Placeholder text */
  placeholder?: string;
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
  /** Disabled state */
  disabled?: boolean;
  /** Read-only state */
  readOnly?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Input size */
  size?: TextAreaSize;
  /** Color variant (for focus/border) */
  color?: TextAreaColor;
  /** Minimum number of rows */
  minRows?: number;
  /** Maximum number of rows */
  maxRows?: number;
  /** Initial number of rows */
  rows?: number;
  /** Maximum length */
  maxLength?: number;
  /** Minimum length */
  minLength?: number;
  /** Auto-resize textarea to fit content */
  autoResize?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  /** Focus handler */
  onFocus?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** Blur handler */
  onBlur?: (event: React.FocusEvent<HTMLTextAreaElement>) => void;
  /** Reference to textarea element */
  textareaRef?: React.Ref<HTMLTextAreaElement>;
  /** Input name */
  name?: string;
  /** Input ID */
  id?: string;
}

/**
 * Props for TextArea component
 * Extends standard HTML textarea attributes
 */
export interface TextAreaProps extends BaseTextAreaProps, Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size' | 'onChange'> {}

/**
 * Get color styles based on color
 */
const getColorStyles = (color: TextAreaColor, theme: EmotionTheme) => {
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
    '--textarea-color': colors.main,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: TextAreaSize) => {
  const sizeMap = {
    small: {
      fontSize: '0.875rem',
      padding: '8px 12px',
      minHeight: '32px',
    },
    medium: {
      fontSize: '1rem',
      padding: '10px 14px',
      minHeight: '40px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled container for TextArea
 */
const StyledContainer = styled.div<{ fullWidth?: boolean; className?: string }>`
  position: relative;
  width: ${props => props.fullWidth ? '100%' : 'auto'};
  ${props => props.className};
`;

/**
 * Styled label for TextArea
 */
const StyledLabel = styled.label<{ isFocused: boolean; hasValue: boolean; hasError: boolean; disabled?: boolean; size: TextAreaSize; required?: boolean }>`
  display: block;
  margin-bottom: 6px;
  color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.hasError) return props.theme.error.main;
    if (props.isFocused) return `var(--textarea-color)`;
    return props.theme.text.primary;
  }};
  font-size: ${props => getSizeStyles(props.size).fontSize};
  font-weight: 500;
  transition: color ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};

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
 * Styled textarea element
 */
const StyledTextarea = styled.textarea<{
  error?: boolean;
  size: TextAreaSize;
  disabled?: boolean;
  autoResize?: boolean;
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
  resize: ${props => props.autoResize ? 'none' : 'vertical'};
  overflow-y: ${props => props.autoResize ? 'hidden' : 'auto'};

  /* Focus state */
  &:focus {
    border-color: ${props => props.error ? props.theme.error.main : 'var(--textarea-color)'};
    box-shadow: 0 0 0 2px ${props => props.error ? 'rgba(211, 47, 47, 0.2)' : 'rgba(25, 118, 210, 0.2)'};
  }

  /* Disabled state */
  &:disabled {
    background-color: ${props => props.theme.action.disabledBackground};
    color: ${props => props.theme.text.disabled};
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Read-only state */
  &:read-only {
    background-color: ${props => props.theme.background.default};
    cursor: default;
  }

  /* Placeholder styles */
  &::placeholder {
    color: ${props => props.theme.text.hint};
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
 * Character count display
 */
const CharCount = styled.span<{ error?: boolean }>`
  font-size: 0.75rem;
  color: ${props => props.error ? props.theme.error.main : props.theme.text.hint};
  text-align: right;
  margin-top: 2px;
`;

/**
 * TextArea Component
 *
 * A multiline text input component with auto-resize, character counting, and validation states.
 * Built with Emotion to replace Material-UI TextField with multiline prop.
 * Compatible with react-hook-form.
 *
 * @example
 * ```tsx
 * // Basic textarea
 * <TextArea
 *   label="Description"
 *   placeholder="Enter description"
 *   rows={4}
 * />
 *
 * // With auto-resize
 * <TextArea
 *   label="Bio"
 *   autoResize
 *   minRows={2}
 *   maxRows={6}
 *   value={bio}
 *   onChange={(e) => setBio(e.target.value)}
 * />
 *
 * // With character limit
 * <TextArea
 *   label="Comment"
 *   rows={3}
 *   maxLength={500}
 *   value={comment}
 *   onChange={(e) => setComment(e.target.value)}
 * />
 *
 * // With error state
 * <TextArea
 *   label="Message"
 *   error
 *   errorMessage="Message is required"
 *   required
 *   rows={4}
 * />
 *
 * // Full width
 * <TextArea
 *   label="Notes"
 *   rows={6}
 *   fullWidth
 *   placeholder="Add your notes here..."
 * />
 *
 * // With react-hook-form
 * <Controller
 *   name="description"
 *   control={control}
 *   render={({ field }) => (
 *     <TextArea
 *       {...field}
 *       label="Description"
 *       rows={4}
 *       error={!!errors.description}
 *       errorMessage={errors.description?.message}
 *     />
 *   )}
 * />
 * ```
 */
export const TextArea = forwardRef<HTMLDivElement, TextAreaProps>(
  ({
    label,
    helperText,
    error = false,
    errorMessage,
    required = false,
    disabled = false,
    readOnly = false,
    fullWidth = false,
    size = 'medium',
    color = 'primary',
    minRows,
    maxRows,
    rows = 4,
    maxLength,
    minLength,
    autoResize = false,
    className,
    style,
    textareaRef,
    value: controlledValue,
    onChange,
    onFocus,
    onBlur,
    name,
    id,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const [focused, setFocused] = React.useState(false);
    const internalRef = useRef<HTMLTextAreaElement>(null);
    const [internalValue, setInternalValue] = React.useState(controlledValue || '');

    // Use external ref if provided, otherwise use internal ref
    const textareaElementRef = (textareaRef as any) || internalRef;

    // Determine if field has a value
    const hasValue = internalValue !== undefined && internalValue !== '';

    // Handle focus
    const handleFocus = (event: React.FocusEvent<HTMLTextAreaElement>) => {
      setFocused(true);
      if (onFocus) {
        onFocus(event);
      }
    };

    // Handle blur
    const handleBlur = (event: React.FocusEvent<HTMLTextAreaElement>) => {
      setFocused(false);
      if (onBlur) {
        onBlur(event);
      }
    };

    // Handle change
    const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInternalValue(event.target.value);
      if (onChange) {
        onChange(event);
      }
    };

    // Auto-resize functionality
    useEffect(() => {
      if (autoResize && textareaElementRef.current) {
        const textarea = textareaElementRef.current;
        textarea.style.height = 'auto';

        let newHeight: string;
        if (minRows !== undefined && maxRows !== undefined) {
          // Both min and max rows specified
          const minHeight = parseFloat(getSizeStyles(size).minHeight) * minRows;
          const maxHeight = parseFloat(getSizeStyles(size).minHeight) * maxRows;
          const scrollHeight = textarea.scrollHeight;

          if (scrollHeight < minHeight) {
            newHeight = `${minHeight}px`;
          } else if (scrollHeight > maxHeight) {
            newHeight = `${maxHeight}px`;
            textarea.style.overflowY = 'auto';
          } else {
            newHeight = `${scrollHeight}px`;
            textarea.style.overflowY = 'hidden';
          }
        } else if (minRows !== undefined) {
          // Only min rows specified
          const minHeight = parseFloat(getSizeStyles(size).minHeight) * minRows;
          newHeight = `${Math.max(textarea.scrollHeight, minHeight)}px`;
        } else if (maxRows !== undefined) {
          // Only max rows specified
          const maxHeight = parseFloat(getSizeStyles(size).minHeight) * maxRows;
          const scrollHeight = textarea.scrollHeight;
          newHeight = `${Math.min(scrollHeight, maxHeight)}px`;
          textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
        } else {
          // No limits, grow with content
          newHeight = `${textarea.scrollHeight}px`;
        }

        textarea.style.height = newHeight;
      }
    }, [internalValue, autoResize, minRows, maxRows, size, textareaElementRef]);

    // Get error message
    const displayHelperText = error && errorMessage ? errorMessage : helperText;

    // Character count
    const showCharCount = maxLength !== undefined;
    const charCount = internalValue ? internalValue.length : 0;
    const charCountError = maxLength !== undefined && charCount > maxLength;

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
            isFocused={focused}
            hasValue={hasValue}
            hasError={error}
            disabled={disabled}
            size={size}
            required={required}
          >
            {label}
          </StyledLabel>
        )}
        <StyledTextarea
          {...rest}
          ref={textareaElementRef}
          id={id}
          name={name}
          value={controlledValue !== undefined ? controlledValue : internalValue}
          placeholder={rest.placeholder}
          error={error}
          size={size}
          disabled={disabled}
          readOnly={readOnly}
          rows={autoResize ? undefined : rows}
          minLength={minLength}
          maxLength={maxLength}
          autoResize={autoResize}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onChange={handleChange}
        />
        {displayHelperText && (
          <HelperText error={error && !!errorMessage}>
            {displayHelperText}
          </HelperText>
        )}
        {showCharCount && (
          <CharCount error={charCountError}>
            {charCount}{maxLength !== undefined && ` / ${maxLength}`}
          </CharCount>
        )}
      </StyledContainer>
    );
  }
);

TextArea.displayName = 'TextArea';

export default TextArea;
