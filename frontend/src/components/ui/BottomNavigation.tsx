import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * BottomNavigation props interface
 */
export interface BottomNavigationProps {
  /** Current selected value */
  value: number;
  /** Callback when selection changes */
  onChange: (event: React.SyntheticEvent, newValue: number) => void;
  /** Navigation items */
  children?: React.ReactNode;
  /** If true, show labels */
  showLabels?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  navRef?: React.Ref<HTMLNavElement>;
  /** ARIA label */
  'aria-label'?: string;
}

/**
 * Styled BottomNavigation container
 */
const StyledBottomNav = styled.nav<{ theme: EmotionTheme }>`
  /* Base styles */
  box-sizing: border-box;
  display: flex;
  flex-direction: row;
  justify-content: space-around;
  align-items: center;
  width: 100%;
  height: 56px;
  background-color: ${({ theme }) => theme.background.paper};
  border-top: 1px solid ${({ theme }) => theme.divider};
  font-family: ${({ theme }) => theme.typography.fontFamily};
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: ${({ theme }) => theme.zIndex.appBar - 1};
  box-shadow: ${({ theme }) => theme.shadows.md};
`;

/**
 * Styled action item
 */
const StyledAction = styled.button<{ theme: EmotionTheme; selected: boolean }>`
  /* Reset and base styles */
  appearance: none;
  border: none;
  background: none;
  box-sizing: border-box;
  cursor: pointer;
  outline: none;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-width: 80px;
  max-width: 168px;
  height: 100%;
  padding: ${({ theme }) => theme.spacing.xs};
  color: ${({ theme, selected }) => (selected ? theme.primary.main : theme.text.secondary)};
  transition: color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  text-decoration: none;
  border-radius: ${({ theme }) => theme.borderRadius.sm};

  /* Selected state */
  ${({ selected, theme }) =>
    selected
      ? `
    font-weight: ${theme.typography.fontWeight.medium};
  `
      : ''}

  /* Hover state */
  &:hover {
    background-color: ${({ theme }) => theme.action.hover};
  }

  /* Focus visible state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: -2px;
  }

  /* Active state */
  &:active {
    transform: scale(0.98);
  }

  /* Icon styling */
  & > svg {
    margin-bottom: ${({ theme, showLabels }) => (showLabels ? theme.spacing.xs : '0')};
    width: 24px;
    height: 24px;
  }

  /* Label styling */
  & > span {
    font-size: 0.75rem;
    margin-top: ${({ theme }) => theme.spacing.xs};
  }
`;

/**
 * BottomNavigationAction props interface
 */
export interface BottomNavigationActionProps {
  /** Label for the action */
  label: string;
  /** Icon to display */
  icon: React.ReactElement;
  /** If true, the component is selected */
  value?: number;
  /** ARIA label */
  'aria-label'?: string;
  /** ARIA current */
  'aria-current'?: 'page' | undefined;
}

/**
 * BottomNavigationAction Component
 *
 * Individual action item for BottomNavigation.
 *
 * @example
 * ```tsx
 * <BottomNavigationAction
 *   label="Home"
 *   icon={<Icon name="home" />}
 *   aria-current={selected ? 'page' : undefined}
 * />
 * ```
 */
export const BottomNavigationAction: React.FC<BottomNavigationActionProps> = ({
  label,
  icon,
  'aria-label': ariaLabel,
  'aria-current': ariaCurrent,
}) => {
  const { theme } = useEmotionTheme();

  return (
    <StyledAction
      theme={theme}
      selected={ariaCurrent === 'page'}
      aria-label={ariaLabel || label}
      aria-current={ariaCurrent}
      showLabels={true}
      type="button"
    >
      {icon}
      <span>{label}</span>
    </StyledAction>
  );
};

/**
 * BottomNavigation Component
 *
 * A mobile-first bottom navigation bar that allows navigation between
 * top-level views with a simple icon and label.
 *
 * @example
 * ```tsx
 * const [value, setValue] = useState(0);
 *
 * const navItems = [
 *   { label: 'Home', icon: <Icon name="home" />, path: '/' },
 *   { label: 'Search', icon: <Icon name="search" />, path: '/search' },
 *   { label: 'Profile', icon: <Icon name="user" />, path: '/profile' },
 * ];
 *
 * <BottomNavigation
 *   value={value}
 *   onChange={(event, newValue) => setValue(newValue)}
 *   aria-label="Mobile navigation"
 *   showLabels
 * >
 *   {navItems.map((item, index) => (
 *     <BottomNavigationAction
 *       key={item.path}
 *       label={item.label}
 *       icon={item.icon}
 *       aria-current={value === index ? 'page' : undefined}
 *     />
 *   ))}
 * </BottomNavigation>
 * ```
 */
export const BottomNavigation = React.forwardRef<HTMLNavElement, BottomNavigationProps>(
  (
    {
      value,
      onChange,
      children,
      showLabels = false,
      className,
      style,
      navRef,
      'aria-label': ariaLabel = 'Navigation',
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Clone children to inject onClick handlers
    const childrenWithProps = React.Children.map(children, (child, index) => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, {
          onClick: (event: React.SyntheticEvent) => {
            onChange(event, index);
          },
          'aria-current': value === index ? 'page' : undefined,
        } as React.HTMLAttributes<HTMLElement>);
      }
      return child;
    });

    return (
      <StyledBottomNav
        ref={ref || navRef}
        theme={theme}
        className={className}
        style={style}
        aria-label={ariaLabel}
        {...(rest as React.HTMLAttributes<HTMLElement>)}
      >
        {childrenWithProps}
      </StyledBottomNav>
    );
  }
);

BottomNavigation.displayName = 'BottomNavigation';

export default BottomNavigation;
