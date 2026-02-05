import React from 'react';
import { Link } from 'react-router-dom';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Breadcrumb item interface
 */
export interface BreadcrumbItem {
  /** Label text */
  label: string;
  /** URL path (if not provided, item is not clickable) */
  path?: string;
  /** Icon to display before label */
  icon?: React.ReactNode;
  /** If true, the item is disabled */
  disabled?: boolean;
}

/**
 * Base Breadcrumbs props interface
 */
export interface BaseBreadcrumbsProps {
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  breadcrumbsRef?: React.Ref<HTMLElement>;
}

/**
 * Props for Breadcrumbs component
 */
export interface BreadcrumbsProps extends BaseBreadcrumbsProps {
  /** Breadcrumb items to display */
  items: BreadcrumbItem[];
  /** Custom separator between items */
  separator?: React.ReactNode;
  /** Maximum number of items to display before collapsing */
  maxItems?: number;
  /** If true, the items are collapsed before the last item */
  itemsBeforeCollapse?: number;
  /** If true, the items are collapsed after the first item */
  itemsAfterCollapse?: number;
  /** Component to use for the root node */
  component?: React.ElementType;
}

/**
 * Styled Breadcrumbs container
 */
const StyledBreadcrumbs = styled.nav<{ theme: EmotionTheme }>`
  /* Layout */
  display: flex;
  align-items: center;
  flex-wrap: wrap;

  /* Typography */
  font-family: ${({ theme }) => theme.typography.fontFamily};
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  line-height: 1.5;

  /* Spacing */
  gap: 8px;
`;

/**
 * Styled breadcrumb item (link)
 */
const StyledBreadcrumbLink = styled(Link)<{ theme: EmotionTheme; disabled: boolean }>`
  /* Typography */
  color: ${({ theme, disabled }) => (disabled ? theme.text.disabled : theme.primary.main)};
  text-decoration: none;
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};

  /* Transition */
  transition: color 150ms ease-in-out;

  /* Cursor */
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};

  /* Hover state */
  &:hover {
    color: ${({ theme, disabled }) => (disabled ? theme.text.disabled : theme.primary.dark)};
    text-decoration: ${({ disabled }) => (disabled ? 'none' : 'underline')};
  }

  /* Focus state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: 2px;
    border-radius: 4px;
  }

  /* Display */
  display: flex;
  align-items: center;
  gap: 8px;
`;

/**
 * Styled current page (last item)
 */
const StyledCurrentPage = styled.span<{ theme: EmotionTheme }>`
  /* Typography */
  color: ${({ theme }) => theme.text.primary};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};

  /* Display */
  display: flex;
  align-items: center;
  gap: 8px;
`;

/**
 * Styled separator
 */
const StyledSeparator = styled.span<{ theme: EmotionTheme }>`
  /* Typography */
  color: ${({ theme }) => theme.text.disabled};
  font-size: ${({ theme }) => theme.typography.fontSize.sm};

  /* Display */
  display: flex;
  align-items: center;
  user-select: none;
`;

/**
 * Styled icon container
 */
const StyledIconContainer = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
`;

/**
 * Breadcrumbs Component
 *
 * Navigation component that shows the current location in the application hierarchy.
 * Automatically handles the last item as the current page (non-link).
 *
 * @example
 * ```tsx
 * // Basic breadcrumbs
 * <Breadcrumbs
 *   items={[
 *     { label: 'Home', path: '/' },
 *     { label: 'Products', path: '/products' },
 *     { label: 'Category', path: '/products/category' },
 *     { label: 'Product Name' }, // Current page, no path
 *   ]}
 * />
 *
 * // With icons
 * <Breadcrumbs
 *   items={[
 *     { label: 'Home', path: '/', icon: <Icon name="Home" size="small" /> },
 *     { label: 'Settings', path: '/settings', icon: <Icon name="Settings" size="small" /> },
 *     { label: 'Profile' },
 *   ]}
 * />
 *
 * // Custom separator
 * <Breadcrumbs
 *   items={items}
 *   separator={<Icon name="ArrowRight" size="small" />}
 * />
 * ```
 */
export const Breadcrumbs = React.forwardRef<HTMLElement, BreadcrumbsProps>(
  (
    {
      items,
      separator = '/',
      maxItems,
      itemsBeforeCollapse = 1,
      itemsAfterCollapse = 1,
      component = 'nav',
      className,
      style,
      breadcrumbsRef,
      ref,
      ...rest
    }
  ) => {
    const { theme } = useEmotionTheme();

    if (!items || items.length === 0) {
      return null;
    }

    // Determine if we need to collapse items
    const shouldCollapse = maxItems && items.length > maxItems;

    // Get visible items based on collapse settings
    let visibleItems: typeof items = items;
    if (shouldCollapse) {
      const firstItems = items.slice(0, itemsBeforeCollapse);
      const lastItems = items.slice(-itemsAfterCollapse);
      visibleItems = [...firstItems, { label: '...' }, ...lastItems] as typeof items;
    }

    const lastIndex = visibleItems.length - 1;

    return (
      <StyledBreadcrumbs
        ref={ref || breadcrumbsRef}
        theme={theme}
        className={className}
        style={style}
        aria-label="Breadcrumb"
        {...rest}
      >
        {visibleItems.map((item, index) => {
          const isLast = index === lastIndex;
          const isClickable = item.path && !item.disabled && !isLast;

          return (
            <React.Fragment key={index}>
              {index > 0 && (
                <StyledSeparator theme={theme} aria-hidden="true">
                  {separator}
                </StyledSeparator>
              )}

              {item.icon && <StyledIconContainer>{item.icon}</StyledIconContainer>}

              {isLast || !isClickable ? (
                <StyledCurrentPage
                  theme={theme}
                  aria-current="page"
                  {...(item.path ? { 'data-path': item.path } : {})}
                >
                  {item.label}
                </StyledCurrentPage>
              ) : (
                <StyledBreadcrumbLink
                  theme={theme}
                  href={item.path!}
                  disabled={item.disabled || false}
                  aria-disabled={item.disabled}
                >
                  {item.label}
                </StyledBreadcrumbLink>
              )}
            </React.Fragment>
          );
        })}
      </StyledBreadcrumbs>
    );
  }
);

Breadcrumbs.displayName = 'Breadcrumbs';

export default Breadcrumbs;
