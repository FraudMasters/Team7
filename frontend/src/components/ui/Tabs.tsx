import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Tab item interface
 */
export interface TabItem {
  /** Unique identifier */
  id: string;
  /** Label text */
  label: string;
  /** Icon to display */
  icon?: React.ReactNode;
  /** If true, the tab is disabled */
  disabled?: boolean;
  /** Additional content to display */
  content?: React.ReactNode;
}

/**
 * Tabs orientation types
 */
export type TabsOrientation = 'horizontal' | 'vertical';

/**
 * Tabs variant types
 */
export type TabsVariant = 'standard' | 'fullWidth' | 'scrollable';

/**
 * Base Tabs props interface
 */
export interface BaseTabsProps {
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  tabsRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Tabs component
 */
export interface TabsProps extends BaseTabsProps {
  /** Tab items to display */
  items: TabItem[];
  /** Currently active tab ID */
  value: string;
  /** Callback fired when the tab changes */
  onChange: (event: React.MouseEvent, newValue: string) => void;
  /** Orientation of the tabs */
  orientation?: TabsOrientation;
  /** Variant of the tabs */
  variant?: TabsVariant;
  /** If true, the Tab indicator is centered */
  centered?: boolean;
  /** If true, the tabs are centered */
  centeredTabs?: boolean;
  /** If true, the text will not wrap (only for horizontal) */
  textColor?: 'inherit' | 'primary' | 'secondary';
}

/**
 * Styled Tabs container
 */
const StyledTabs = styled.div<{
  theme: EmotionTheme;
  orientation: TabsOrientation;
  variant: TabsVariant;
}>`
  /* Layout */
  display: flex;
  flex-direction: ${({ orientation }) => (orientation === 'vertical' ? 'column' : 'row')};
  overflow-x: ${({ variant, orientation }) =>
    variant === 'scrollable' && orientation === 'horizontal' ? 'auto' : 'visible'};
  overflow-y: auto;

  /* Spacing */
  gap: ${({ orientation }) => (orientation === 'vertical' ? '0' : '4px')};

  /* Width */
  width: 100%;

  /* Hide scrollbar for scrollable tabs */
  ${({ variant, orientation }) =>
    variant === 'scrollable' && orientation === 'horizontal'
      ? `
    &::-webkit-scrollbar {
      display: none;
    }
    -ms-overflow-style: none;
    scrollbar-width: none;
  `
      : ''}
`;

/**
 * Styled Tab button
 */
const StyledTab = styled.button<{
  theme: EmotionTheme;
  active: boolean;
  disabled: boolean;
  orientation: TabsOrientation;
  centered: boolean;
  variant: TabsVariant;
  textColor: 'inherit' | 'primary' | 'secondary';
}>`
  /* Reset */
  appearance: none;
  border: none;
  background: none;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  user-select: none;
  outline: none;

  /* Layout */
  display: flex;
  flex-direction: ${({ orientation }) => (orientation === 'vertical' ? 'column' : 'row')};
  align-items: center;
  justify-content: centered;
  gap: 8px;

  /* Spacing */
  padding: ${({ orientation }) => (orientation === 'vertical' ? '12px 16px' : '12px 16px')};
  min-width: ${({ variant, orientation }) => {
    if (orientation === 'vertical') return '120px';
    if (variant === 'fullWidth') return '0';
    return '160px';
  }};
  min-height: 48px;

  /* Flex */
  flex: ${({ variant, centered }) => {
    if (variant === 'fullWidth') return '1';
    if (centered) return '1';
    return '0 1 auto';
  }};

  /* Typography */
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  font-weight: ${({ theme, active }) =>
    active ? theme.typography.fontWeight.semibold : theme.typography.fontWeight.medium};
  text-transform: uppercase;
  letter-spacing: 0.02857em;
  line-height: 1.25;
  white-space: nowrap;

  /* Color */
  color: ${({ theme, active, disabled, textColor }) => {
    if (disabled) return theme.text.disabled;
    if (active) {
      if (textColor === 'primary') return theme.primary.main;
      if (textColor === 'secondary') return theme.secondary.main;
      return theme.primary.main;
    }
    if (textColor === 'primary') return theme.primary.main;
    if (textColor === 'secondary') return theme.secondary.main;
    return theme.text.secondary;
  }};

  /* Transition */
  transition: color 150ms ease-in-out, background-color 150ms ease-in-out;

  /* Border */
  border-bottom: 2px solid
    ${({ theme, active, disabled }) => {
      if (disabled) return 'transparent';
      if (active) return theme.primary.main;
      return 'transparent';
    }};

  /* Border radius for vertical tabs */
  ${({ orientation }) =>
    orientation === 'vertical'
      ? `
    border-bottom: none;
    border-right: 2px solid transparent;
    border-right-color: ${({ theme, active }) => (active ? theme.primary.main : 'transparent')};
  `
      : ''}

  /* Hover state */
  &:hover:not(:disabled) {
    background-color: ${({ theme }) => theme.action.hover};
  }

  /* Focus state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: -2px;
    border-radius: ${({ orientation }) => (orientation === 'vertical' ? '4px' : '4px 4px 0 0')};
  }
`;

/**
 * Styled icon container
 */
const StyledIconContainer = styled.span<{ orientation: TabsOrientation }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: ${({ orientation }) => (orientation === 'vertical' ? '4px' : '0')};
`;

/**
 * Tabs Component
 *
 * Tab navigation component for organizing content into separate panels.
 * Supports horizontal and vertical orientations.
 *
 * @example
 * ```tsx
 * const [value, setValue] = useState('tab1');
 *
 * const tabs = [
 *   { id: 'tab1', label: 'Tab 1' },
 *   { id: 'tab2', label: 'Tab 2' },
 *   { id: 'tab3', label: 'Tab 3', disabled: true },
 * ];
 *
 * <Tabs value={value} onChange={(e, newVal) => setValue(newVal)} items={tabs} />
 *
 * // With icons
 * const tabsWithIcons = [
 *   { id: 'home', label: 'Home', icon: <Icon name="Home" size="small" /> },
 *   { id: 'profile', label: 'Profile', icon: <Icon name="User" size="small" /> },
 *   { id: 'settings', label: 'Settings', icon: <Icon name="Settings" size="small" /> },
 * ];
 *
 * <Tabs value={value} onChange={setValue} items={tabsWithIcons} />
 *
 * // Vertical tabs
 * <Tabs
 *   value={value}
 *   onChange={setValue}
 *   items={tabs}
 *   orientation="vertical"
 * />
 *
 * // Full width tabs
 * <Tabs
 *   value={value}
 *   onChange={setValue}
 *   items={tabs}
 *   variant="fullWidth"
 * />
 * ```
 */
export const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  (
    {
      items,
      value,
      onChange,
      orientation = 'horizontal',
      variant = 'standard',
      centered = false,
      centeredTabs = false,
      textColor = 'primary',
      className,
      style,
      tabsRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    const handleTabClick = (event: React.MouseEvent, tabId: string) => {
      const tab = items.find((t) => t.id === tabId);
      if (tab && !tab.disabled) {
        onChange(event, tabId);
      }
    };

    return (
      <StyledTabs
        ref={ref || tabsRef}
        theme={theme}
        orientation={orientation}
        variant={variant}
        className={className}
        style={style}
        role="tablist"
        aria-orientation={orientation}
        {...rest}
      >
        {items.map((tab) => (
          <StyledTab
            key={tab.id}
            theme={theme}
            active={value === tab.id}
            disabled={tab.disabled || false}
            orientation={orientation}
            centered={centered}
            variant={variant}
            textColor={textColor}
            onClick={(e) => handleTabClick(e, tab.id)}
            role="tab"
            aria-selected={value === tab.id}
            aria-disabled={tab.disabled}
            tabIndex={value === tab.id ? 0 : -1}
          >
            {tab.icon && <StyledIconContainer orientation={orientation}>{tab.icon}</StyledIconContainer>}
            {tab.label}
          </StyledTab>
        ))}
      </StyledTabs>
    );
  }
);

Tabs.displayName = 'Tabs';

/**
 * TabPanel Component
 *
 * Content panel for a specific tab.
 * Should be used to show content corresponding to the active tab.
 *
 * @example
 * ```tsx
 * <Tabs value={value} onChange={setValue} items={tabs} />
 * <TabPanel value={value} index="tab1">
 *   Content for Tab 1
 * </TabPanel>
 * <TabPanel value={value} index="tab2">
 *   Content for Tab 2
 * </TabPanel>
 * ```
 */
export interface TabPanelProps {
  /** Currently active tab value */
  value: string;
  /** Tab panel index (should match tab id) */
  index: string;
  /** Panel content */
  children: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
}

export const TabPanel: React.FC<TabPanelProps> = ({ value, index, children, className, style }) => {
  if (value !== index) {
    return null;
  }

  return (
    <div
      role="tabpanel"
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      className={className}
      style={style}
    >
      {children}
    </div>
  );
};

TabPanel.displayName = 'TabPanel';

export default Tabs;
