import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Table component props interface
 */
export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  /** Table content */
  children?: React.ReactNode;
  /** If true, the table will have sticky header */
  stickyHeader?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  tableRef?: React.Ref<HTMLTableElement>;
}

/**
 * TableHead props interface
 */
export interface TableHeadProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  /** Table head content (typically TableRow elements) */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  headRef?: React.Ref<HTMLTableSectionElement>;
}

/**
 * TableBody props interface
 */
export interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  /** Table body content (typically TableRow elements) */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  bodyRef?: React.Ref<HTMLTableSectionElement>;
}

/**
 * TableFooter props interface
 */
export interface TableFooterProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  /** Table footer content (typically TableRow elements) */
  children?: React.ReactNode;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  footerRef?: React.Ref<HTMLTableSectionElement>;
}

/**
 * TableRow props interface
 */
export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  /** Row content (typically TableCell elements) */
  children?: React.ReactNode;
  /** If true, the row will have hover effect */
  hover?: boolean;
  /** If true, the row is selected */
  selected?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  rowRef?: React.Ref<HTMLTableRowElement>;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLTableRowElement>) => void;
}

/**
 * TableCell props interface
 */
export interface TableCellProps extends React.HTMLAttributes<HTMLTableCellElement> {
  /** Cell content */
  children?: React.ReactNode;
  /** Cell alignment */
  align?: 'left' | 'center' | 'right' | 'justify';
  /** Cell padding */
  padding?: 'none' | 'normal' | 'checkbox';
  /** Cell scope (for header cells) */
  scope?: 'col' | 'row' | 'colgroup' | 'rowgroup';
  /** Cell variant */
  variant?: 'head' | 'body' | 'footer';
  /** If true, the cell will have numeric sorting */
  sortDirection?: 'asc' | 'desc' | false;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  cellRef?: React.Ref<HTMLTableCellElement>;
  /** Component to use (td or th) */
  component?: React.ElementType;
}

/**
 * Styled Table root
 */
const StyledTable = styled('table')<{ theme: EmotionTheme; stickyHeader?: boolean }>`
  border-collapse: collapse;
  width: 100%;
  border-spacing: 0;
  display: table;
  font-family: ${({ theme }) => theme.typography.fontFamily};

  ${({ stickyHeader }) =>
    stickyHeader
      ? `
    & thead {
      position: sticky;
      top: 0;
      z-index: 1;
    }
  `
      : ''}
`;

/**
 * Styled Table section (thead, tbody, tfoot)
 */
const StyledTableSection = styled('tbody')<{ theme: EmotionTheme; component: string }>`
  display: ${({ component }) => (component === 'thead' || component === 'tfoot' ? 'table-header-group' : 'table-row-group')};
`;

/**
 * Styled TableRow
 */
const StyledTableRow = styled('tr')<{
  theme: EmotionTheme;
  hover?: boolean;
  selected?: boolean;
  clickable?: boolean;
}>`
  transition: background-color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};

  /* Hover effect */
  ${({ hover, theme, clickable }) =>
    (hover || clickable) &&
    `
    &:hover {
      background-color: ${theme.palette.action.hover};
    }
  `}

  /* Selected state */
  ${({ selected, theme }) =>
    selected
      ? `
    background-color: ${theme.palette.action.selected};
  `
      : ''}

  /* Clickable cursor */
  ${({ clickable }) =>
    clickable
      ? `
    cursor: pointer;
  `
      : ''}
`;

/**
 * Styled TableCell
 */
const StyledTableCell = styled('td')<{
  theme: EmotionTheme;
  align: string;
  padding: string;
  variant: string;
}>`
  text-align: ${({ align }) => align};
  padding: ${({ padding }) => padding};
  border-bottom: 1px solid ${({ theme }) => theme.divider};
  font-size: ${({ theme, variant }) =>
    variant === 'head' ? theme.typography.fontSize.sm : theme.typography.fontSize.md};
  font-weight: ${({ theme, variant }) =>
    variant === 'head' ? theme.typography.fontWeight.medium : theme.typography.fontWeight.regular};
  color: ${({ theme, variant }) =>
    variant === 'head' ? theme.text.secondary : theme.text.primary};
  vertical-align: inherit;

  /* Head cell styles */
  ${({ variant, theme }) =>
    variant === 'head'
      ? `
    background-color: ${theme.background.paper};
    font-weight: ${theme.typography.fontWeight.medium};
  `
      : ''}
`;

/**
 * Get padding value based on padding prop
 */
const getPaddingValue = (
  padding: 'none' | 'normal' | 'checkbox',
  theme: EmotionTheme
): string => {
  const paddingMap = {
    none: '0',
    normal: `${theme.spacing.md}px`,
    checkbox: `0 ${theme.spacing.md}px`,
  };
  return paddingMap[padding];
};

/**
 * Table Component
 *
 * Tables display sets of data. They can be fully customized.
 *
 * @example
 * ```tsx
 * // Basic table
 * <Table>
 *   <TableHead>
 *     <TableRow>
 *       <TableCell>Name</TableCell>
 *       <TableCell>Email</TableCell>
 *       <TableCell>Role</TableCell>
 *     </TableRow>
 *   </TableHead>
 *   <TableBody>
 *     <TableRow>
 *       <TableCell>John Doe</TableCell>
 *       <TableCell>john@example.com</TableCell>
 *       <TableCell>Admin</TableCell>
 *     </TableRow>
 *   </TableBody>
 * </Table>
 *
 * // With sticky header
 * <Table stickyHeader>
 *   <TableHead>
 *     <TableRow>
 *       <TableCell>Column 1</TableCell>
 *       <TableCell>Column 2</TableCell>
 *     </TableRow>
 *   </TableHead>
 *   <TableBody>
 *     {/* rows *\/}
 *   </TableBody>
 * </Table>
 *
 * // With hover and selection
 * <Table>
 *   <TableBody>
 *     <TableRow hover selected>
 *       <TableCell>Selected row</TableCell>
 *     </TableRow>
 *     <TableRow hover onClick={() => console.log('clicked')}>
 *       <TableCell>Clickable row</TableCell>
 *     </TableRow>
 *   </TableBody>
 * </Table>
 * ```
 */
export const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ children, stickyHeader = false, className, style, tableRef, ...rest }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledTable
        ref={ref || tableRef}
        theme={theme}
        stickyHeader={stickyHeader}
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableElement>)}
      >
        {children}
      </StyledTable>
    );
  }
);

Table.displayName = 'Table';

/**
 * TableHead Component
 *
 * Table header section.
 *
 * @example
 * ```tsx
 * <TableHead>
 *   <TableRow>
 *     <TableCell>Name</TableCell>
 *     <TableCell align="right">Amount</TableCell>
 *   </TableRow>
 * </TableHead>
 * ```
 */
export const TableHead = React.forwardRef<HTMLTableSectionElement, TableHeadProps>(
  ({ children, className, style, headRef, ...rest }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledTableSection
        ref={ref || headRef}
        theme={theme}
        component="thead"
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableSectionElement>)}
      >
        {children}
      </StyledTableSection>
    );
  }
);

TableHead.displayName = 'TableHead';

/**
 * TableBody Component
 *
 * Table body section.
 *
 * @example
 * ```tsx
 * <TableBody>
 *   <TableRow>
 *     <TableCell>Data 1</TableCell>
 *   </TableRow>
 *   <TableRow>
 *     <TableCell>Data 2</TableCell>
 *   </TableRow>
 * </TableBody>
 * ```
 */
export const TableBody = React.forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ children, className, style, bodyRef, ...rest }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledTableSection
        ref={ref || bodyRef}
        theme={theme}
        component="tbody"
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableSectionElement>)}
      >
        {children}
      </StyledTableSection>
    );
  }
);

TableBody.displayName = 'TableBody';

/**
 * TableFooter Component
 *
 * Table footer section.
 *
 * @example
 * ```tsx
 * <TableFooter>
 *   <TableRow>
 *     <TableCell>Total</TableCell>
 *     <TableCell align="right">$100</TableCell>
 *   </TableRow>
 * </TableFooter>
 * ```
 */
export const TableFooter = React.forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ children, className, style, footerRef, ...rest }, ref) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledTableSection
        ref={ref || footerRef}
        theme={theme}
        component="tfoot"
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableSectionElement>)}
      >
        {children}
      </StyledTableSection>
    );
  }
);

TableFooter.displayName = 'TableFooter';

/**
 * TableRow Component
 *
 * Table row container.
 *
 * @example
 * ```tsx
 * // Basic row
 * <TableRow>
 *   <TableCell>Cell 1</TableCell>
 *   <TableCell>Cell 2</TableCell>
 * </TableRow>
 *
 * // Hoverable row
 * <TableRow hover>
 *   <TableCell>Hover me</TableCell>
 * </TableRow>
 *
 * // Selected row
 * <TableRow selected>
 *   <TableCell>Selected</TableCell>
 * </TableRow>
 *
 * // Clickable row
 * <TableRow onClick={() => console.log('clicked')}>
 *   <TableCell>Click me</TableCell>
 * </TableRow>
 * ```
 */
export const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ children, hover = false, selected = false, className, style, rowRef, onClick, ...rest }, ref) => {
    const { theme } = useEmotionTheme();
    const clickable = Boolean(onClick);

    return (
      <StyledTableRow
        ref={ref || rowRef}
        theme={theme}
        hover={hover}
        selected={selected}
        clickable={clickable}
        onClick={onClick}
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableRowElement>)}
      >
        {children}
      </StyledTableRow>
    );
  }
);

TableRow.displayName = 'TableRow';

/**
 * TableCell Component
 *
 * Table cell. Can be used as header cell (th) or data cell (td).
 *
 * @example
 * ```tsx
 * // Basic cell
 * <TableCell>Content</TableCell>
 *
 * // Aligned cell
 * <TableCell align="right">$100</TableCell>
 * <TableCell align="center">Centered</TableCell>
 *
 * // Header cell
 * <TableCell component="th" scope="col">
 *   Name
 * </TableCell>
 *
 * // Custom padding
 * <TableCell padding="none">No padding</TableCell>
 * <TableCell padding="checkbox">
 *   <Checkbox />
 * </TableCell>
 *
 * // Variant
 * <TableCell variant="head">Header</TableCell>
 * <TableCell variant="body">Body</TableCell>
 * ```
 */
export const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(
  (
    {
      children,
      align = 'left',
      padding = 'normal',
      scope,
      variant = 'body',
      sortDirection = false,
      className,
      style,
      cellRef,
      component: Component = 'td',
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const paddingValue = getPaddingValue(padding, theme);

    // Use th if scope is provided or component is explicitly 'th'
    const CellComponent = Component || (scope ? 'th' : 'td');

    return (
      <StyledTableCell
        ref={ref || cellRef}
        as={CellComponent}
        theme={theme}
        align={align}
        padding={paddingValue}
        variant={variant}
        scope={scope}
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLTableCellElement>)}
      >
        {children}
      </StyledTableCell>
    );
  }
);

TableCell.displayName = 'TableCell';

export default Table;
