import React, { useState, createContext, useContext, useCallback } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { Collapse } from './Collapse';

/**
 * Accordion context for managing expanded state
 */
const AccordionContext = createContext<{
  expanded: boolean;
  toggleExpanded: () => void;
  disabled?: boolean;
}>({
  expanded: false,
  toggleExpanded: () => {},
  disabled: false,
});

/**
 * Accordion component props interface
 */
export interface AccordionProps {
  /** Accordion content (AccordionSummary and AccordionDetails) */
  children?: React.ReactNode;
  /** If true, expands the accordion by default */
  defaultExpanded?: boolean;
  /** If true, the accordion is disabled */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  accordionRef?: React.Ref<HTMLDivElement>;
  /** Callback fired when the accordion is expanded */
  onChange?: (event: React.SyntheticEvent, expanded: boolean) => void;
}

/**
 * AccordionSummary props interface
 */
export interface AccordionSummaryProps {
  /** Summary content (typically text) */
  children?: React.ReactNode;
  /** Expand/collapse icon (customizable) */
  expandIcon?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  summaryRef?: React.Ref<HTMLDivElement>;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
}

/**
 * AccordionDetails props interface
 */
export interface AccordionDetailsProps {
  /** Details content */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  detailsRef?: React.Ref<HTMLDivElement>;
}

/**
 * Styled Accordion root
 */
const StyledAccordion = styled('div')<{ theme: EmotionTheme; disabled?: boolean }>`
  border: 1px solid ${({ theme }) => theme.divider};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  background-color: ${({ theme }) => theme.background.paper};
  overflow: hidden;

  ${({ disabled }) =>
    disabled
      ? `
    opacity: 0.5;
    pointer-events: none;
  `
      : ''}
`;

/**
 * Styled AccordionSummary
 */
const StyledAccordionSummary = styled('div')<{
  theme: EmotionTheme;
  expanded: boolean;
  disabled?: boolean;
}>`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${({ theme }) => theme.spacing.md} ${({ theme }) => theme.spacing.lg};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  user-select: none;
  transition: background-color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  min-height: 48px;

  &:hover {
    background-color: ${({ theme, disabled }) =>
      disabled ? 'transparent' : theme.palette.action.hover};
  }

  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: -2px;
  }

  ${({ expanded, theme }) =>
    expanded
      ? `
    margin-bottom: ${theme.spacing.sm};
  `
      : ''}
`;

/**
 * AccordionSummary content
 */
const SummaryContent = styled('div')<{ theme: EmotionTheme }>`
  flex: 1;
  display: flex;
  align-items: center;
`;

/**
 * Expand icon wrapper
 */
const ExpandIconWrapper = styled('div')<{ theme: EmotionTheme; expanded: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: ${({ theme }) => theme.spacing.md};
  transition: transform ${({ theme }) => theme.transitions.duration.shorter}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  transform: rotate(${({ expanded }) => (expanded ? 180 : 0)}deg);

  svg {
    width: 24px;
    height: 24px;
  }
`;

/**
 * Styled AccordionDetails
 */
const StyledAccordionDetails = styled('div')<{ theme: EmotionTheme }>`
  padding: 0 ${({ theme }) => theme.spacing.lg} ${({ theme }) => theme.spacing.lg};
  padding-top: 0;
`;

/**
 * Default expand icon
 */
const DefaultExpandIcon: React.FC<{ expanded: boolean }> = ({ expanded }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
    <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z" />
  </svg>
);

/**
 * Accordion Component
 *
 * Accordions allow users to expand and collapse sections of content.
 *
 * @example
 * ```tsx
 * // Basic accordion
 * <Accordion defaultExpanded>
 *   <AccordionSummary>Accordion 1</AccordionSummary>
 *   <AccordionDetails>
 *     Content for accordion 1
 *   </AccordionDetails>
 * </Accordion>
 *
 * // Controlled accordion
 * const [expanded, setExpanded] = useState(false);
 *
 * <Accordion expanded={expanded} onChange={(e, exp) => setExpanded(exp)}>
 *   <AccordionSummary>Controlled Accordion</AccordionSummary>
 *   <AccordionDetails>
 *     Controlled content
 *   </AccordionDetails>
 * </Accordion>
 *
 * // Disabled accordion
 * <Accordion disabled>
 *   <AccordionSummary>Disabled Accordion</AccordionSummary>
 *   <AccordionDetails>
 *     Cannot be expanded
 *   </AccordionDetails>
 * </Accordion>
 *
 * // Custom expand icon
 * <Accordion>
 *   <AccordionSummary expandIcon={<Icon name="Plus" />}>
 *     Custom Icon
 *   </AccordionSummary>
 *   <AccordionDetails>
 *     Content with custom expand icon
 *   </AccordionDetails>
 * </Accordion>
 * ```
 */
export const Accordion = React.forwardRef<HTMLDivElement, AccordionProps>(
  (
    {
      children,
      defaultExpanded = false,
      disabled = false,
      className,
      style,
      accordionRef,
      onChange,
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const [expanded, setExpanded] = useState(defaultExpanded);

    const toggleExpanded = useCallback(
      (event: React.SyntheticEvent) => {
        if (disabled) return;
        const newExpanded = !expanded;
        setExpanded(newExpanded);
        onChange?.(event, newExpanded);
      },
      [expanded, disabled, onChange]
    );

    const contextValue = React.useMemo(
      () => ({
        expanded,
        toggleExpanded: () => {
          const event = new SyntheticEvent('click', {
            bubbles: true,
            cancelable: true,
          });
          toggleExpanded(event);
        },
        disabled,
      }),
      [expanded, toggleExpanded, disabled]
    );

    return (
      <AccordionContext.Provider value={contextValue}>
        <StyledAccordion
          ref={ref || accordionRef}
          theme={theme}
          disabled={disabled}
          className={className}
          style={style}
        >
          {children}
        </StyledAccordion>
      </AccordionContext.Provider>
    );
  }
);

Accordion.displayName = 'Accordion';

/**
 * AccordionSummary Component
 *
 * The summary element of the accordion. Contains the title and expand icon.
 *
 * @example
 * ```tsx
 * <AccordionSummary>
 *   <Typography>Accordion Title</Typography>
 * </AccordionSummary>
 *
 * // With custom icon
 * <AccordionSummary expandIcon={<Icon name="ArrowDown" />}>
 *   <Typography>Custom Icon</Typography>
 * </AccordionSummary>
 * ```
 */
export const AccordionSummary = React.forwardRef<HTMLDivElement, AccordionSummaryProps>(
  ({ children, expandIcon, className, style, summaryRef, onClick, ...rest }, ref) => {
    const { theme } = useEmotionTheme();
    const { expanded, toggleExpanded, disabled } = useContext(AccordionContext);

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
      onClick?.(event);
      toggleExpanded();
    };

    return (
      <StyledAccordionSummary
        ref={ref || summaryRef}
        theme={theme}
        expanded={expanded}
        disabled={disabled}
        className={className}
        style={style}
        onClick={handleClick}
        role="button"
        aria-expanded={expanded}
        tabIndex={disabled ? -1 : 0}
        onKeyPress={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleExpanded();
          }
        }}
        {...(rest as React.HTMLAttributes<HTMLDivElement>)}
      >
        <SummaryContent theme={theme}>{children}</SummaryContent>
        <ExpandIconWrapper theme={theme} expanded={expanded}>
          {expandIcon || <DefaultExpandIcon expanded={expanded} />}
        </ExpandIconWrapper>
      </StyledAccordionSummary>
    );
  }
);

AccordionSummary.displayName = 'AccordionSummary';

/**
 * AccordionDetails Component
 *
 * The details/content element of the accordion. Only visible when expanded.
 *
 * @example
 * ```tsx
 * <AccordionDetails>
 *   <Typography>
 *     This is the content that is shown when the accordion is expanded.
 *   </Typography>
 * </AccordionDetails>
 * ```
 */
export const AccordionDetails = React.forwardRef<HTMLDivElement, AccordionDetailsProps>(
  ({ children, className, style, detailsRef }, ref) => {
    const { theme } = useEmotionTheme();
    const { expanded } = useContext(AccordionContext);

    return (
      <Collapse in={expanded}>
        <StyledAccordionDetails
          ref={ref || detailsRef}
          theme={theme}
          className={className}
          style={style}
        >
          {children}
        </StyledAccordionDetails>
      </Collapse>
    );
  }
);

AccordionDetails.displayName = 'AccordionDetails';

export default Accordion;
