import React, { forwardRef, useState, useCallback, useRef, useEffect } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Slider size variants
 */
export type SliderSize = 'small' | 'medium' | 'large';

/**
 * Slider color variants
 */
export type SliderColor = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';

/**
 * Slider mark interface
 */
export interface SliderMark {
  /** Mark value */
  value: number;
  /** Mark label */
  label?: string | number;
}

/**
 * Base Slider props interface
 */
export interface BaseSliderProps {
  /** Slider value (or values for range) */
  value?: number | number[];
  /** Default value (uncontrolled) */
  defaultValue?: number | number[];
  /** Minimum value */
  min?: number;
  /** Maximum value */
  max?: number;
  /** Step value */
  step?: number | null;
  /** Disabled state */
  disabled?: boolean;
  /** Slider size */
  size?: SliderSize;
  /** Color variant */
  color?: SliderColor;
  /** Show error state */
  error?: boolean;
  /** Marks to show on the slider */
  marks?: boolean | SliderMark[];
  /** Show value label */
  valueLabelDisplay?: 'on' | 'auto' | 'off';
  /** Format value for display */
  valueLabelFormat?: (value: number) => string | number;
  /** Range mode (two handles) */
  range?: boolean;
  /** Read-only */
  readOnly?: boolean;
  /** Change handler */
  onChange?: (event: React.ChangeEvent<HTMLInputElement>, value: number | number[]) => void;
  /** Change committed handler (after drag ends) */
  onChangeCommitted?: (event: React.ChangeEvent<HTMLInputElement>, value: number | number[]) => void;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Slider track container reference */
  trackRef?: React.Ref<HTMLDivElement>;
  /** ARIA label for accessibility */
  'aria-label'?: string;
  /** ARIA labelledby */
  'aria-labelledby'?: string;
  /** Reference to container element */
  ref?: React.Ref<HTMLDivElement>;
  /** Input name */
  name?: string;
  /** Input ID */
  id?: string;
}

/**
 * Props for Slider component
 * Extends standard HTML input attributes where applicable
 */
export interface SliderProps extends BaseSliderProps {}

/**
 * Get color styles based on color
 */
const getColorStyles = (color: SliderColor, theme: EmotionTheme) => {
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
    '--slider-color': colors.main,
    '--slider-color-light': colors.light,
    '--slider-color-dark': colors.dark,
  } as React.CSSProperties;
};

/**
 * Get size styles
 */
const getSizeStyles = (size: SliderSize) => {
  const sizeMap = {
    small: {
      trackHeight: '4px',
      thumbSize: '12px',
      thumbBorder: '2px',
      markSize: '2px',
    },
    medium: {
      trackHeight: '6px',
      thumbSize: '16px',
      thumbBorder: '2px',
      markSize: '2px',
    },
    large: {
      trackHeight: '8px',
      thumbSize: '20px',
      thumbBorder: '3px',
      markSize: '3px',
    },
  };

  return sizeMap[size];
};

/**
 * Styled container for Slider
 */
const StyledContainer = styled.div<{ className?: string }>`
  position: relative;
  width: 100%;
  padding: 8px 0;
  ${props => props.className};
`;

/**
 * Slider track container
 */
const TrackContainer = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
`;

/**
 * Slider track (background)
 */
const Track = styled.div<{ size: SliderSize; disabled?: boolean; error?: boolean }>`
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  height: ${props => getSizeStyles(props.size).trackHeight};
  background-color: ${props => props.error ? props.theme.error.main : props.theme.divider};
  border-radius: ${props => props.theme.borderRadius.pill};
  opacity: ${props => props.disabled ? 0.5 : 1};
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
`;

/**
 * Slider track (filled portion)
 */
const TrackFill = styled.div<{ size: SliderSize; disabled?: boolean; left?: string; width?: string }>`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  height: ${props => getSizeStyles(props.size).trackHeight};
  background-color: var(--slider-color);
  border-radius: ${props => props.theme.borderRadius.pill};
  opacity: ${props => props.disabled ? 0.5 : 1};
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  left: ${props => props.left || '0'};
  width: ${props => props.width || '0%'};
`;

/**
 * Slider thumb (handle)
 */
const Thumb = styled.div<{
  size: SliderSize;
  disabled?: boolean;
  focused: boolean;
  error?: boolean;
  position: string;
}>`
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: ${props => getSizeStyles(props.size).thumbSize};
  height: ${props => getSizeStyles(props.size).thumbSize};
  border: ${props => getSizeStyles(props.size).thumbBorder} solid white;
  background-color: ${props => {
    if (props.error) return props.theme.error.main;
    return 'var(--slider-color)';
  }};
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  cursor: ${props => props.disabled ? 'not-allowed' : 'grab'};
  opacity: ${props => props.disabled ? 0.5 : 1};
  transition: all ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  left: ${props => props.position};

  &:hover {
    transform: translate(-50%, -50%) scale(1.1);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  }

  ${props => props.focused && `
    outline: 2px solid var(--slider-color);
    outline-offset: 2px;
    transform: translate(-50%, -50%) scale(1.15);
  `}

  &:active {
    cursor: grabbing;
    transform: translate(-50%, -50%) scale(0.95);
  }
`;

/**
 * Hidden range input
 */
const HiddenInput = styled.input`
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  pointer-events: none;

  &:focus {
    outline: none;
  }
`;

/**
 * Mark label
 */
const MarkLabel = styled.span<{ active?: boolean; disabled?: boolean }>`
  position: absolute;
  top: 100%;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: ${props => {
    if (props.disabled) return props.theme.text.disabled;
    if (props.active) return 'var(--slider-color)';
    return props.theme.text.hint;
  }};
  margin-top: 4px;
  white-space: nowrap;
  pointer-events: none;
  transition: color ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
`;

/**
 * Mark indicator
 */
const Mark = styled.div<{ active?: boolean; disabled?: boolean; error?: boolean }>`
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 8px;
  background-color: ${props => {
    if (props.error) return props.theme.error.main;
    if (props.active) return 'var(--slider-color)';
    if (props.disabled) return props.theme.text.disabled;
    return props.theme.text.hint;
  }};
  border-radius: ${props => props.theme.borderRadius.xs};
  pointer-events: none;
`;

/**
 * Value label tooltip
 */
const ValueLabel = styled.div<{ size: SliderSize; visible: boolean }>`
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  background-color: ${props => props.theme.text.primary};
  color: ${props => props.theme.background.paper};
  padding: 4px 8px;
  border-radius: ${props => props.theme.borderRadius.sm};
  font-size: ${props => {
    const sizeMap = { small: '0.75rem', medium: '0.875rem', large: '1rem' };
    return sizeMap[props.size];
  }};
  font-weight: 500;
  white-space: nowrap;
  opacity: ${props => props.visible ? 1 : 0};
  pointer-events: none;
  transition: opacity ${props => props.theme.transitions.duration.shorter}ms ${props => props.theme.transitions.easing.easeInOut};
  box-shadow: ${props => props.theme.shadows.sm};
  z-index: 1;

  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid ${props => props.theme.text.primary};
  }
`;

/**
 * Convert value to percentage
 */
const valueToPercent = (value: number, min: number, max: number) => {
  return ((value - min) / (max - min)) * 100;
};

/**
 * Convert percentage to value
 */
const percentToValue = (percent: number, min: number, max: number) => {
  return min + (percent / 100) * (max - min);
};

/**
 * Clamp value between min and max
 */
const clampValue = (value: number, min: number, max: number) => {
  return Math.min(Math.max(value, min), max);
};

/**
 * Round value to step
 */
const roundToStep = (value: number, step: number) => {
  return Math.round(value / step) * step;
};

/**
 * Slider Component
 *
 * A customizable slider component with range support, marks, and value labels.
 * Built with Emotion to replace Material-UI Slider component.
 *
 * @example
 * ```tsx
 * // Basic slider
 * <Slider value={value} onChange={(e, newValue) => setValue(newValue)} />
 *
 * // With min, max, and step
 * <Slider
 *   value={volume}
 *   onChange={(e, newValue) => setVolume(newValue)}
 *   min={0}
 *   max={100}
 *   step={5}
 * />
 *
 * // Range slider (two handles)
 * <Slider
 *   range
 *   value={[minPrice, maxPrice]}
 *   onChange={(e, newValue) => setPriceRange(newValue as number[])}
 *   min={0}
 *   max={1000}
 *   step={10}
 * />
 *
 * // With marks
 * <Slider
 *   value={rating}
 *   onChange={(e, newValue) => setRating(newValue)}
 *   min={1}
 *   max={5}
 *   step={1}
 *   marks={[
 *     { value: 1, label: '1' },
 *     { value: 2, label: '2' },
 *     { value: 3, label: '3' },
 *     { value: 4, label: '4' },
 *     { value: 5, label: '5' },
 *   ]}
 *   valueLabelDisplay="on"
 * />
 *
 * // With custom value format
 * <Slider
 *   value={temperature}
 *   onChange={(e, newValue) => setTemperature(newValue)}
 *   min={-20}
 *   max={40}
 *   valueLabelFormat={(value) => `${value}°C`}
 *   valueLabelDisplay="on"
 * />
 *
 * // Disabled
 * <Slider disabled value={50} />
 *
 * // Different colors and sizes
 * <Slider color="secondary" size="large" value={75} />
 * ```
 */
export const Slider = forwardRef<HTMLDivElement, SliderProps>(
  ({
    value: controlledValue,
    defaultValue,
    min = 0,
    max = 100,
    step = 1,
    disabled = false,
    size = 'medium',
    color = 'primary',
    error = false,
    marks = false,
    valueLabelDisplay = 'off',
    valueLabelFormat,
    range = false,
    readOnly = false,
    onChange,
    onChangeCommitted,
    className,
    style,
    trackRef,
    'aria-label': ariaLabel,
    'aria-labelledby': ariaLabelledBy,
    name,
    id,
    ...rest
  }, ref) => {
    const { theme } = useEmotionTheme();
    const containerRef = useRef<HTMLDivElement>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [draggingIndex, setDraggingIndex] = useState<number>(0);
    const [focusedIndex, setFocusedIndex] = useState<number>(-1);

    // Determine if controlled
    const isControlled = controlledValue !== undefined;
    const initialValue = range ? [min, max] : min;
    const internalValue = useState(defaultValue !== undefined ? defaultValue : initialValue)[0];
    const value = isControlled ? controlledValue : internalValue;

    // Ensure value is an array for range
    const values = range ? (Array.isArray(value) ? value : [min, value]) : [value as number];

    // Handle value change
    const handleChange = useCallback((newValue: number | number[], index: number) => {
      if (readOnly || disabled) return;

      let finalValue = newValue;

      // Apply step if not null
      if (step !== null) {
        if (Array.isArray(newValue)) {
          finalValue = newValue.map(v => roundToStep(v, step));
        } else {
          finalValue = roundToStep(newValue, step);
        }
      }

      if (!isControlled) {
        // For uncontrolled, we'd need a setter - not implementing for now
        // In a real scenario, you'd use setState here
      }

      if (onChange) {
        const event = {
          target: { value: finalValue },
        } as React.ChangeEvent<HTMLInputElement>;
        onChange(event, finalValue);
      }
    }, [disabled, readOnly, step, isControlled, onChange]);

    // Handle drag start
    const handleDragStart = useCallback((index: number) => {
      if (disabled || readOnly) return;
      setIsDragging(true);
      setDraggingIndex(index);
    }, [disabled, readOnly]);

    // Handle drag end
    const handleDragEnd = useCallback(() => {
      if (isDragging && onChangeCommitted) {
        const event = {
          target: { value: range ? values : values[0] },
        } as React.ChangeEvent<HTMLInputElement>;
        onChangeCommitted(event, range ? values : values[0]);
      }
      setIsDragging(false);
      setFocusedIndex(-1);
    }, [isDragging, onChangeCommitted, range, values]);

    // Handle track click
    const handleTrackClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
      if (disabled || readOnly) return;

      const track = containerRef.current;
      if (!track) return;

      const rect = track.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const percent = (clickX / rect.width) * 100;
      const newValue = percentToValue(percent, min, max);

      if (range) {
        // Find closest thumb
        const distances = values.map(v => Math.abs(v - newValue));
        const closestIndex = distances.indexOf(Math.min(...distances));
        const newValues = [...values] as number[];
        newValues[closestIndex] = clampValue(newValue, min, max);

        // Ensure min doesn't cross max
        if (closestIndex === 0) {
          newValues[0] = Math.min(newValues[0], newValues[1] - (step || 1));
        } else {
          newValues[1] = Math.max(newValues[1], newValues[0] + (step || 1));
        }

        handleChange(newValues, closestIndex);
      } else {
        handleChange(clampValue(newValue, min, max), 0);
      }
    }, [disabled, readOnly, range, values, min, max, step, handleChange]);

    // Handle mouse move during drag
    useEffect(() => {
      if (!isDragging || disabled || readOnly) return;

      const handleMouseMove = (event: MouseEvent) => {
        const track = containerRef.current;
        if (!track) return;

        const rect = track.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const percent = Math.max(0, Math.min(100, (mouseX / rect.width) * 100));
        const newValue = percentToValue(percent, min, max);

        if (range) {
          const newValues = [...values] as number[];
          newValues[draggingIndex] = clampValue(newValue, min, max);

          // Ensure min doesn't cross max
          if (draggingIndex === 0) {
            newValues[0] = Math.min(newValues[0], newValues[1] - (step || 1));
          } else {
            newValues[1] = Math.max(newValues[1], newValues[0] + (step || 1));
          }

          handleChange(newValues, draggingIndex);
        } else {
          handleChange(clampValue(newValue, min, max), 0);
        }
      };

      const handleMouseUp = () => {
        handleDragEnd();
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }, [isDragging, draggingIndex, disabled, readOnly, range, values, min, max, step, handleChange, handleDragEnd]);

    // Format value for display
    const formatValue = (val: number) => {
      if (valueLabelFormat) {
        return valueLabelFormat(val);
      }
      return val.toString();
    };

    // Calculate track fill
    const getTrackFill = () => {
      if (range) {
        const leftPercent = valueToPercent(values[0], min, max);
        const rightPercent = valueToPercent(values[1], min, max);
        return {
          left: `${leftPercent}%`,
          width: `${rightPercent - leftPercent}%`,
        };
      } else {
        return {
          left: '0',
          width: `${valueToPercent(values[0], min, max)}%`,
        };
      }
    };

    // Render marks
    const renderMarks = () => {
      if (!marks) return null;

      let markArray: SliderMark[] = [];

      if (marks === true) {
        // Auto-generate marks at step intervals
        const stepValue = step || 1;
        for (let i = min; i <= max; i += stepValue) {
          markArray.push({ value: i });
        }
      } else {
        markArray = marks;
      }

      return markArray.map((mark, index) => {
        const percent = valueToPercent(mark.value, min, max);
        const isActive = range
          ? values[0] <= mark.value && values[1] >= mark.value
          : values[0] >= mark.value;

        return (
          <React.Fragment key={`mark-${index}`}>
            <Mark
              active={isActive}
              disabled={disabled}
              error={error}
              style={{ left: `${percent}%` }}
            />
            {mark.label && (
              <MarkLabel
                active={isActive}
                disabled={disabled}
                style={{ left: `${percent}%` }}
              >
                {mark.label}
              </MarkLabel>
            )}
          </React.Fragment>
        );
      });
    };

    // Render thumbs
    const renderThumbs = () => {
      return values.map((val, index) => {
        const percent = valueToPercent(val, min, max);
        const showLabel = valueLabelDisplay === 'on' || (valueLabelDisplay === 'auto' && (isDragging || focusedIndex === index));

        return (
          <React.Fragment key={`thumb-${index}`}>
            <HiddenInput
              type="range"
              value={val}
              min={min}
              max={max}
              step={step || 1}
              disabled={disabled}
              name={name}
              id={id}
              aria-label={ariaLabel}
              aria-labelledby={ariaLabelledBy}
              aria-valuenow={val}
              aria-valuemin={min}
              aria-valuemax={max}
              onFocus={() => setFocusedIndex(index)}
              onBlur={() => setFocusedIndex(-1)}
            />
            {showLabel && (
              <ValueLabel size={size} visible>
                {formatValue(val)}
              </ValueLabel>
            )}
            <Thumb
              size={size}
              disabled={disabled}
              focused={focusedIndex === index || isDragging}
              error={error}
              position={`${percent}%`}
              onMouseDown={() => handleDragStart(index)}
              role="slider"
              aria-valuenow={val}
              aria-valuemin={min}
              aria-valuemax={max}
              tabIndex={0}
            />
          </React.Fragment>
        );
      });
    };

    const trackFillStyles = getTrackFill();

    const containerProps = {
      ref: (ref as any) || containerRef,
      className,
      style: {
        ...getColorStyles(color, theme),
        ...style,
      },
      ...rest,
    };

    return (
      <StyledContainer {...containerProps}>
        <TrackContainer
          ref={trackRef}
          onMouseDown={handleTrackClick}
        >
          <Track size={size} disabled={disabled} error={error} />
          <TrackFill
            size={size}
            disabled={disabled}
            left={trackFillStyles.left}
            width={trackFillStyles.width}
          />
          {renderMarks()}
          {renderThumbs()}
        </TrackContainer>
      </StyledContainer>
    );
  }
);

Slider.displayName = 'Slider';

export default Slider;
