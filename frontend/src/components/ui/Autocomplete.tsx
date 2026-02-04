import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../contexts/EmotionThemeContext';
import { TextField } from './TextField';
import { Chip } from './Chip';
import { Icon } from './primitives/Icon';

/**
 * Autocomplete option type
 */
export interface AutocompleteOption {
  label: string;
  value: string;
}

/**
 * Props for Autocomplete component
 */
export interface AutocompleteProps<T = string> {
  /** Current value(s) */
  value: T[];
  /** Options to suggest from */
  options: T[];
  /** Callback when value changes */
  onChange: (event: React.SyntheticEvent, value: T[]) => void;
  /** Render the input element */
  renderInput: (params: AutocompleteRenderInputParams) => React.ReactNode;
  /** Render the tags (chips) */
  renderTags?: (value: T[], getTagProps: (index: number) => AutocompleteTagProps) => React.ReactNode;
  /** Allow free-form text input */
  freeSolo?: boolean;
  /** Allow multiple selections */
  multiple?: boolean;
  /** Disable the component */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** CSS class name */
  className?: string;
}

/**
 * Parameters passed to renderInput
 */
export interface AutocompleteRenderInputParams {
  id: string;
  disabled: boolean;
  InputProps: {
    ref: React.RefObject<HTMLInputElement>;
    startAdornment?: React.ReactNode;
    endAdornment?: React.ReactNode;
  };
}

/**
 * Props for individual tag
 */
export interface AutocompleteTagProps {
  key: string;
  label: string;
  onDelete: () => void;
  disabled?: boolean;
}

/**
 * Container for the autocomplete
 */
const AutocompleteContainer = styled('div')<{ disabled: boolean }>((props) => {
  const theme = useEmotionTheme().theme;

  return {
    position: 'relative',
    width: '100%',
    opacity: props.disabled ? 0.6 : 1,
    pointerEvents: props.disabled ? 'none' : 'auto',
  };
});

/**
 * Input wrapper that displays tags
 */
const InputWrapper = styled('div')(() => {
  return {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    alignItems: 'center',
    minHeight: '56px',
    padding: '8px 0',
  };
});

/**
 * Autocomplete Component
 *
 * A flexible autocomplete component that supports both single and multiple selections,
 * with freeSolo mode for custom values.
 *
 * @example
 * ```tsx
 * <Autocomplete
 *   multiple
 *   freeSolo
 *   options={['React', 'Vue', 'Angular']}
 *   value={skills}
 *   onChange={(_, value) => setSkills(value)}
 *   renderInput={(params) => (
 *     <TextField
 *       {...params}
 *       label="Skills"
 *       placeholder="Add skills..."
 *     />
 *   )}
 * />
 * ```
 */
export function Autocomplete<T = string>(props: AutocompleteProps<T>) {
  const {
    value = [],
    options = [],
    onChange,
    renderInput,
    renderTags,
    freeSolo = false,
    multiple = false,
    disabled = false,
    placeholder,
    className,
  } = props;

  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const uniqueId = React.useId();

  /**
   * Handle input change
   */
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);
  };

  /**
   * Handle key down (Enter to add value)
   */
  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && inputValue.trim() && freeSolo) {
      event.preventDefault();
      const newValue = multiple ? [...value, inputValue.trim() as T] : [inputValue.trim() as T];
      onChange(event as unknown as React.SyntheticEvent, newValue);
      setInputValue('');
    }
  };

  /**
   * Remove tag by index
   */
  const handleDeleteTag = (index: number) => {
    const newValue = value.filter((_, i) => i !== index);
    onChange({} as React.SyntheticEvent, newValue);
  };

  /**
   * Get tag props for rendering
   */
  const getTagProps = (index: number): AutocompleteTagProps => ({
    key: `tag-${index}`,
    label: String(value[index]),
    onDelete: () => handleDeleteTag(index),
    disabled,
  });

  /**
   * Default render tags implementation
   */
  const defaultRenderTags = (valueToRender: T[], getTagPropsFn: (index: number) => AutocompleteTagProps) => {
    return (
      <>
        {valueToRender.map((option, index) => {
          const tagProps = getTagPropsFn(index);
          return <Chip key={tagProps.key} label={tagProps.label} onDelete={tagProps.onDelete} disabled={tagProps.disabled} />;
        })}
      </>
    );
  };

  const tagsRender = renderTags || defaultRenderTags;

  return (
    <AutocompleteContainer className={className} disabled={disabled}>
      <InputWrapper>
        {multiple && tagsRender(value, getTagProps)}
      </InputWrapper>
      {renderInput({
        id: uniqueId,
        disabled,
        InputProps: {
          ref: inputRef,
          startAdornment: undefined,
          endAdornment: undefined,
        },
      })}
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={!multiple || value.length === 0 ? placeholder : ''}
        style={{
          position: 'absolute',
          top: multiple && value.length > 0 ? '32px' : '16px',
          left: '14px',
          right: '14px',
          border: 'none',
          outline: 'none',
          background: 'transparent',
          fontSize: '16px',
          fontFamily: 'inherit',
          color: 'inherit',
        }}
      />
    </AutocompleteContainer>
  );
}

export default Autocomplete;
