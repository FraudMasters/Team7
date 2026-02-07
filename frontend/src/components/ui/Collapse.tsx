import React, { useRef, useEffect } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Collapse component props interface
 */
export interface CollapseProps {
  /** Collapse content */
  children?: React.ReactNode;
  /** If true, the component is visible */
  in?: boolean;
  /** Animation duration in milliseconds */
  timeout?: number | { appear?: number; enter?: number; exit?: number };
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  collapseRef?: React.Ref<HTMLDivElement>;
  /** Callback fired when the component has entered */
  onEntered?: () => void;
  /** Callback fired when the component is entering */
  onEntering?: () => void;
  /** Callback fired when the component has exited */
  onExited?: () => void;
  /** Callback fired when the component is exiting */
  onExiting?: () => void;
}

/**
 * Default timeout
 */
const DEFAULT_TIMEOUT = 300;

/**
 * Styled Collapse wrapper
 */
const CollapseWrapper = styled('div')<{
  theme: EmotionTheme;
  entered: boolean;
  timeout: number;
}>`
  overflow: hidden;
  height: 0;
  opacity: 0;
  transition: height ${({ timeout }) => timeout}ms cubic-bezier(0.4, 0, 0.2, 1),
    opacity ${({ timeout }) => timeout}ms cubic-bezier(0.4, 0, 0.2, 1);

  ${({ entered }) =>
    entered
      ? `
    height: auto;
    opacity: 1;
  `
      : ''}
`;

/**
 * Get height of an element
 */
const getHeight = (element: HTMLElement): number => {
  return element.scrollHeight;
};

/**
 * Collapse Component
 *
 * Collapse transitions the height of a component from 0 to auto.
 * Wraps any content and smoothly animates its height.
 *
 * @example
 * ```tsx
 * // Basic usage
 * const [open, setOpen] = useState(false);
 *
 * <Button onClick={() => setOpen(!open)}>Toggle</Button>
 * <Collapse in={open}>
 *   <div>
 *     Content that collapses and expands
 *   </div>
 * </Collapse>
 *
 * // With custom timeout
 * <Collapse in={open} timeout={500}>
 *   <div>Slower animation</div>
 * </Collapse>
 *
 * // With callbacks
 * <Collapse
 *   in={open}
 *   onEntered={() => console.log('Expanded')}
 *   onExited={() => console.log('Collapsed')}
 * >
 *   <div>Content with callbacks</div>
 * </Collapse>
 *
 * // In accordion
 * <Accordion>
 *   <AccordionSummary>Expand me</AccordionSummary>
 *   <Collapse in={expanded}>
 *     <AccordionDetails>
 *       Accordion content
 *     </AccordionDetails>
 *   </Collapse>
 * </Accordion>
 * ```
 */
export const Collapse = React.forwardRef<HTMLDivElement, CollapseProps>(
  (
    {
      children,
      in: inProp = false,
      timeout = DEFAULT_TIMEOUT,
      className,
      style,
      collapseRef,
      onEntered,
      onEntering,
      onExited,
      onExiting,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const nodeRef = useRef<HTMLDivElement>(null);
    const wrapperRef = (ref || collapseRef || nodeRef) as React.RefObject<HTMLDivElement>;
    const timeoutNumber = typeof timeout === 'number' ? timeout : timeout.enter || DEFAULT_TIMEOUT;
    const [isTransitioning, setIsTransitioning] = React.useState(false);
    const [height, setHeight] = React.useState<number | 'auto'>(0);

    useEffect(() => {
      const node = wrapperRef.current;
      if (!node) return;

      if (inProp) {
        // Entering
        onEntering?.();
        setIsTransitioning(true);

        // Set to height of content
        const contentHeight = getHeight(node);
        setHeight(contentHeight);

        // After animation, set to auto
        const timer = setTimeout(() => {
          setHeight('auto');
          setIsTransitioning(false);
          onEntered?.();
        }, timeoutNumber);

        return () => clearTimeout(timer);
      } else {
        // Exiting
        onExiting?.();
        setIsTransitioning(true);

        // Set from auto to specific height
        if (height === 'auto') {
          const contentHeight = getHeight(node);
          setHeight(contentHeight);

          // Force reflow
          node.offsetHeight;

          // Then to 0
          requestAnimationFrame(() => {
            setHeight(0);
          });
        } else {
          setHeight(0);
        }

        const timer = setTimeout(() => {
          setIsTransitioning(false);
          onExited?.();
        }, timeoutNumber);

        return () => clearTimeout(timer);
      }
    }, [inProp]);

    const timeoutValue = typeof timeout === 'number' ? timeout : timeout.enter || DEFAULT_TIMEOUT;

    return (
      <div
        ref={wrapperRef}
        className={className}
        style={{
          ...style,
          height: inProp || isTransitioning ? height : 0,
          opacity: inProp ? 1 : 0,
          overflow: 'hidden',
          transition: `height ${timeoutValue}ms cubic-bezier(0.4, 0, 0.2, 1), opacity ${timeoutValue}ms cubic-bezier(0.4, 0, 0.2, 1)`,
        }}
      >
        {children}
      </div>
    );
  }
);

Collapse.displayName = 'Collapse';

export default Collapse;
