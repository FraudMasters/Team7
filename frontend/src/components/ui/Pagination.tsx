import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Pagination size types
 */
export type PaginationSize = 'small' | 'medium' | 'large';

/**
 * Pagination variant types
 */
export type PaginationVariant = 'outlined' | 'text';

/**
 * Base Pagination props interface
 */
export interface BasePaginationProps {
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  paginationRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Pagination component
 */
export interface PaginationProps extends BasePaginationProps {
  /** Total number of pages */
  count: number;
  /** Current page number (1-indexed) */
  page: number;
  /** Callback fired when the page is changed */
  onChange: (event: React.MouseEvent, page: number) => void;
  /** Number of pages to display before and after the current page */
  siblingCount?: number;
  /** Number of pages to display at the beginning and end */
  boundaryCount?: number;
  /** Size of the pagination items */
  size?: PaginationSize;
  /** Variant of the pagination items */
  variant?: PaginationVariant;
  /** Color of the pagination items */
  color?: 'primary' | 'secondary' | 'standard';
  /** If true, the pagination is disabled */
  disabled?: boolean;
  /** If true, show first and last page buttons */
  showFirstButton?: boolean;
  /** If true, show previous and next page buttons */
  showLastButton?: boolean;
}

/**
 * Styled Pagination container
 */
const StyledPagination = styled.nav<{ theme: EmotionTheme }>`
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
`;

/**
 * Styled Pagination item
 */
const StyledPaginationItem = styled.button<{
  theme: EmotionTheme;
  active: boolean;
  disabled: boolean;
  size: PaginationSize;
  variant: PaginationVariant;
  color: 'primary' | 'secondary' | 'standard';
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
  align-items: center;
  justify-content: center;

  /* Sizing */
  width: ${({ size }) => {
    switch (size) {
      case 'small':
        return '28px';
      case 'large':
        return '44px';
      default:
        return '36px';
    }
  }};
  height: ${({ size }) => {
    switch (size) {
      case 'small':
        return '28px';
      case 'large':
        return '44px';
      default:
        return '36px';
    }
  }};
  min-width: ${({ size }) => {
    switch (size) {
      case 'small':
        return '28px';
      case 'large':
        return '44px';
      default:
        return '36px';
    }
  }};

  /* Typography */
  font-size: ${({ size }) => {
    switch (size) {
      case 'small':
        return '0.75rem';
      case 'large':
        return '1rem';
      default:
        return '0.875rem';
    }
  }};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};
  line-height: 1;

  /* Border radius */
  border-radius: ${({ theme }) => theme.borderRadius.sm};

  /* Transition */
  transition: color 150ms ease-in-out, background-color 150ms ease-in-out,
    border-color 150ms ease-in-out;

  /* Variant styles */
  ${({ variant, theme }) => {
    if (variant === 'outlined') {
      return `
        border: 1px solid ${theme.divider};
        background-color: ${theme.background.paper};
      `;
    }
    return `
      border: none;
      background-color: transparent;
    `;
  }}

  /* Color and state styles */
  ${({ theme, active, disabled, color, variant }) => {
    if (disabled) {
      return `
        color: ${theme.text.disabled};
        border-color: ${theme.divider};
        cursor: not-allowed;
        pointer-events: none;
      `;
    }

    if (active) {
      const activeColor = color === 'secondary' ? theme.secondary.main : theme.primary.main;
      const activeContrast = color === 'secondary' ? theme.secondary.contrastText : theme.primary.contrastText;
      return `
        background-color: ${activeColor};
        color: ${activeContrast};
        border-color: ${activeColor};
        font-weight: ${theme.typography.fontWeight.semibold};
      `;
    }

    const textColor = color === 'secondary' ? theme.secondary.main : theme.primary.main;
    return `
      color: ${textColor};
      &:hover:not(:disabled) {
        background-color: ${theme.action.hover};
        border-color: ${color === 'secondary' ? theme.secondary.main : theme.primary.main};
      }
    `;
  }}

  /* Focus state */
  &:focus-visible:not(:disabled) {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: 2px;
  }
`;

/**
 * Styled ellipsis item
 */
const StyledEllipsis = styled.span<{ theme: EmotionTheme; size: PaginationSize }>`
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Sizing */
  width: ${({ size }) => {
    switch (size) {
      case 'small':
        return '28px';
      case 'large':
        return '44px';
      default:
        return '36px';
    }
  }};
  height: ${({ size }) => {
    switch (size) {
      case 'small':
        return '28px';
      case 'large':
        return '44px';
      default:
        return '36px';
    }
  }};

  /* Typography */
  font-size: ${({ size }) => {
    switch (size) {
      case 'small':
        return '0.75rem';
      case 'large':
        return '1rem';
      default:
        return '0.875rem';
    }
  }};
  font-weight: ${({ theme }) => theme.typography.fontWeight.medium};
  color: ${({ theme }) => theme.text.disabled};
  user-select: none;
`;

/**
 * Pagination Component
 *
 * Pagination component for navigating through paged data.
 * Displays page numbers with navigation buttons.
 *
 * @example
 * ```tsx
 * const [page, setPage] = useState(1);
 * const totalPages = 10;
 *
 * <Pagination
 *   count={totalPages}
 *   page={page}
 *   onChange={(e, newPage) => setPage(newPage)}
 * />
 *
 * // With first and last buttons
 * <Pagination
 *   count={totalPages}
 *   page={page}
 *   onChange={handleChange}
 *   showFirstButton
 *   showLastButton
 * />
 *
 * // Large size with outlined variant
 * <Pagination
 *   count={totalPages}
 *   page={page}
 *   onChange={handleChange}
 *   size="large"
 *   variant="outlined"
 *   color="secondary"
 * />
 *
 * // Custom boundary and sibling counts
 * <Pagination
 *   count={100}
 *   page={page}
 *   onChange={handleChange}
 *   boundaryCount={2}
 *   siblingCount={1}
 * />
 * ```
 */
export const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  (
    {
      count,
      page,
      onChange,
      siblingCount = 1,
      boundaryCount = 1,
      size = 'medium',
      variant = 'text',
      color = 'primary',
      disabled = false,
      showFirstButton = false,
      showLastButton = false,
      className,
      style,
      paginationRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    // Generate page range to display
    const getPageRange = (): (number | string)[] => {
      const pages: (number | string)[] = [];
      const rangeStart = 1 + boundaryCount;
      const rangeEnd = count - boundaryCount;

      // Helper to add ellipsis
      const startEllipsis = page > siblingCount + boundaryCount + 2;
      const endEllipsis = page < count - siblingCount - boundaryCount - 1;

      // First button
      if (showFirstButton) {
        pages.push('first');
      }

      // Previous button
      pages.push('previous');

      // Boundary start pages
      for (let i = 1; i <= boundaryCount; i++) {
        if (i <= count) {
          pages.push(i);
        }
      }

      // Start ellipsis
      if (startEllipsis && boundaryCount > 0 && count - boundaryCount > boundaryCount) {
        pages.push('start-ellipsis');
      }

      // Sibling pages around current page
      const startPage = Math.max(boundaryCount + 1, page - siblingCount);
      const endPage = Math.min(count - boundaryCount, page + siblingCount);

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }

      // End ellipsis
      if (endEllipsis && boundaryCount > 0 && count - boundaryCount > boundaryCount) {
        pages.push('end-ellipsis');
      }

      // Boundary end pages
      for (let i = Math.max(count - boundaryCount + 1, boundaryCount + 1); i <= count; i++) {
        pages.push(i);
      }

      // Next button
      pages.push('next');

      // Last button
      if (showLastButton) {
        pages.push('last');
      }

      return pages;
    };

    const pages = getPageRange();

    // Handle page click
    const handlePageClick = (event: React.MouseEvent, clickedPage: number | string) => {
      if (disabled) return;

      let newPage = page;

      if (typeof clickedPage === 'number') {
        newPage = clickedPage;
      } else {
        switch (clickedPage) {
          case 'previous':
            newPage = Math.max(1, page - 1);
            break;
          case 'next':
            newPage = Math.min(count, page + 1);
            break;
          case 'first':
            newPage = 1;
            break;
          case 'last':
            newPage = count;
            break;
          default:
            return;
        }
      }

      if (newPage !== page) {
        onChange(event, newPage);
      }
    };

    const getItemLabel = (item: number | string): string => {
      if (typeof item === 'number') {
        return item.toString();
      }
      switch (item) {
        case 'first':
          return '«';
        case 'previous':
          return '‹';
        case 'next':
          return '›';
        case 'last':
          return '»';
        case 'start-ellipsis':
        case 'end-ellipsis':
          return '…';
        default:
          return '';
      }
    };

    return (
      <StyledPagination
        ref={ref || paginationRef}
        theme={theme}
        className={className}
        style={style}
        aria-label="Pagination navigation"
        {...rest}
      >
        {pages.map((item, index) => {
          const isEllipsis = typeof item === 'string' && item.includes('ellipsis');
          const isNavButton = typeof item === 'string' && !isEllipsis;

          if (isEllipsis) {
            return <StyledEllipsis key={index} theme={theme} size={size} aria-hidden="true">
              {getItemLabel(item)}
            </StyledEllipsis>;
          }

          const isActive = typeof item === 'number' && item === page;
          const isDisabled =
            disabled ||
            (isNavButton &&
              ((item === 'previous' && page === 1) ||
                (item === 'next' && page === count) ||
                (item === 'first' && page === 1) ||
                (item === 'last' && page === count)));

          return (
            <StyledPaginationItem
              key={index}
              theme={theme}
              active={isActive}
              disabled={isDisabled}
              size={size}
              variant={variant}
              color={color}
              onClick={(e) => handlePageClick(e, item)}
              aria-label={typeof item === 'number' ? `Page ${item}` : `${item} page`}
              aria-current={isActive ? 'page' : undefined}
              disabled={isDisabled}
            >
              {getItemLabel(item)}
            </StyledPaginationItem>
          );
        })}
      </StyledPagination>
    );
  }
);

Pagination.displayName = 'Pagination';

export default Pagination;
