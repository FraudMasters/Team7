import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * List component props interface
 */
export interface ListProps extends React.HTMLAttributes<HTMLUListElement> {
  /** List content */
  children?: React.ReactNode;
  /** If true, disables padding for list items */
  disablePadding?: boolean;
  /** Dense mode (reduces padding) */
  dense?: boolean;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  listRef?: React.Ref<HTMLUListElement>;
}

/**
 * List item props interface
 */
export interface ListItemProps extends React.HTMLAttributes<HTMLDivElement> {
  /** List item content */
  children?: React.ReactNode;
  /** If true, the component is disabled */
  disabled?: boolean;
  /** If true, removes padding from the item */
  disablePadding?: boolean;
  /** If true, removes gutters (horizontal padding) */
  disableGutters?: boolean;
  /** If true, divides the item with a divider at the bottom */
  divider?: boolean;
  /** If true, item is selected */
  selected?: boolean;
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  listItemRef?: React.Ref<HTMLDivElement>;
}

/**
 * Styled List component
 */
const StyledList = styled('ul')<{ theme: EmotionTheme; disablePadding?: boolean; dense?: boolean }>`
  list-style: none;
  margin: 0;
  padding: ${({ theme, disablePadding }) => (disablePadding ? 0 : theme.spacing.sm)};

  /* Remove list marker */
  &::-webkit-list-marker {
    display: none;
  }
`;

/**
 * Styled List Item component
 */
const StyledListItem = styled('li')<{ theme: EmotionTheme; disablePadding?: boolean }>`
  list-style: none;

  /* Remove list marker */
  &::-webkit-list-marker {
    display: none;
  }

  /* Padding */
  padding: ${({ theme, disablePadding }) => (disablePadding ? 0 : `0 ${theme.spacing.sm}`)};

  /* Divider */
  &:not(:last-child) {
    border-bottom: 1px solid ${({ theme }) => theme.divider};
  }
`;

/**
 * List Item Content
 */
const ListItemContent = styled('div')<{
  theme: EmotionTheme;
  disabled?: boolean;
  disablePadding?: boolean;
  disableGutters?: boolean;
  selected?: boolean;
  clickable?: boolean;
}>`
  display: flex;
  align-items: flex-start;
  padding: ${({ theme, disablePadding, disableGutters }) =>
    disablePadding
      ? '0'
      : disableGutters
        ? `0 0`
        : `0 ${theme.spacing.md}`};
  padding-top: ${({ theme, disablePadding }) => (disablePadding ? 0 : theme.spacing.sm)};
  padding-bottom: ${({ theme, disablePadding }) => (disablePadding ? 0 : theme.spacing.sm)};
  transition: background-color ${({ theme }) => theme.transitions.duration.shortest}ms
    ${({ theme }) => theme.transitions.easing.easeInOut};
  border-radius: ${({ theme }) => theme.borderRadius.sm};

  /* Disabled state */
  ${({ disabled }) =>
    disabled
      ? `
    opacity: 0.5;
    pointer-events: none;
  `
      : ''}

  /* Selected state */
  ${({ selected, theme }) =>
    selected
      ? `
    background-color: ${theme.palette.action.selected};
  `
      : ''}

  /* Clickable state */
  ${({ clickable, theme, disabled }) =>
    clickable && !disabled
      ? `
    cursor: pointer;
    &:hover {
      background-color: ${theme.palette.action.hover};
    }
    &:focus-visible {
      outline: 2px solid ${theme.primary.main};
      outline-offset: -2px;
    }
  `
      : ''}
`;

/**
 * List Component
 *
 * Lists are continuous, vertical indexes of text and images.
 *
 * @example
 * ```tsx
 * // Basic list
 * <List>
 *   <ListItem><ListItemText primary="Item 1" /></ListItem>
 *   <ListItem><ListItemText primary="Item 2" /></ListItem>
 *   <ListItem><ListItemText primary="Item 3" /></ListItem>
 * </List>
 *
 * // Dense list
 * <List dense>
 *   <ListItem><ListItemText primary="Dense Item 1" /></ListItem>
 *   <ListItem><ListItemText primary="Dense Item 2" /></ListItem>
 * </List>
 *
 * // Disable padding
 * <List disablePadding>
 *   <ListItem divider><ListItemText primary="No padding" /></ListItem>
 *   <ListItem><ListItemText primary="Still no padding" /></ListItem>
 * </List>
 * ```
 */
export const List = React.forwardRef<HTMLUListElement, ListProps>(
  (
    {
      children,
      disablePadding = false,
      dense = false,
      className,
      style,
      listRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();

    return (
      <StyledList
        ref={ref || listRef}
        theme={theme}
        disablePadding={disablePadding}
        dense={dense}
        className={className}
        style={style}
        {...(rest as React.HTMLAttributes<HTMLUListElement>)}
      >
        {children}
      </StyledList>
    );
  }
);

List.displayName = 'List';

/**
 * ListItem Component
 *
 * Items in a List.
 *
 * @example
 * ```tsx
 * // Basic list item
 * <ListItem>
 *   <ListItemText primary="Single line item" />
 * </ListItem>
 *
 * // With icon
 * <ListItem>
 *   <ListItemIcon>
 *     <Icon name="Star" />
 *   </ListItemIcon>
 *   <ListItemText primary="With Icon" />
 * </ListItem>
 *
 * // With avatar
 * <ListItem>
 *   <ListItemAvatar>
 *     <Avatar>JD</Avatar>
 *   </ListItemAvatar>
 *   <ListItemText primary="John Doe" secondary="Software Engineer" />
 * </ListItem>
 *
 * // Clickable
 * <ListItem button onClick={() => console.log('clicked')}>
 *   <ListItemText primary="Clickable Item" />
 * </ListItem>
 *
 * // Selected
 * <ListItem selected>
 *   <ListItemText primary="Selected Item" />
 * </ListItem>
 *
 * // Disabled
 * <ListItem disabled>
 *   <ListItemText primary="Disabled Item" />
 * </ListItem>
 *
 * // With divider
 * <ListItem divider>
 *   <ListItemText primary="Item with divider" />
 * </ListItem>
 * ```
 */
export const ListItem = React.forwardRef<HTMLDivElement, ListItemProps>(
  (
    {
      children,
      disabled = false,
      disablePadding = false,
      disableGutters = false,
      divider = false,
      selected = false,
      onClick,
      className,
      style,
      listItemRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const clickable = Boolean(onClick);

    return (
      <StyledListItem
        theme={theme}
        disablePadding={disablePadding}
        style={{
          borderBottom: divider ? `1px solid ${theme.divider}` : undefined,
        }}
      >
        <ListItemContent
          ref={ref || listItemRef}
          theme={theme}
          disabled={disabled}
          disablePadding={disablePadding}
          disableGutters={disableGutters}
          selected={selected}
          clickable={clickable}
          onClick={onClick}
          className={className}
          style={style}
          {...(rest as React.HTMLAttributes<HTMLDivElement>)}
        >
          {children}
        </ListItemContent>
      </StyledListItem>
    );
  }
);

ListItem.displayName = 'ListItem';

/**
 * ListItemText Component
 *
 * Primary and secondary text for list items.
 *
 * @example
 * ```tsx
 * <ListItemText primary="Primary text" />
 *
 * <ListItemText
 *   primary="Primary text"
 *   secondary="Secondary text"
 * />
 *
 * <ListItemText
 *   primary="Inset secondary text"
 *   secondary="This text is inset from the left"
 *   inset
 * />
 * ```
 */
export interface ListItemTextProps {
  /** Primary text */
  primary?: React.ReactNode;
  /** Secondary text */
  secondary?: React.ReactNode;
  /** If true, the children are indented */
  inset?: boolean;
}

export const ListItemText: React.FC<ListItemTextProps> = ({ primary, secondary, inset }) => {
  const { theme } = useEmotionTheme();

  return (
    <div
      style={{
        flex: '1 1 auto',
        marginLeft: inset ? theme.spacing.lg : 0,
      }}
    >
      {primary && (
        <div
          style={{
            fontSize: theme.typography.fontSize.md,
            fontWeight: theme.typography.fontWeight.medium,
            color: theme.text.primary,
          }}
        >
          {primary}
        </div>
      )}
      {secondary && (
        <div
          style={{
            fontSize: theme.typography.fontSize.sm,
            color: theme.text.secondary,
            marginTop: theme.spacing.xs,
          }}
        >
          {secondary}
        </div>
      )}
    </div>
  );
};

/**
 * ListItemIcon Component
 *
 * Icon container for list items.
 *
 * @example
 * ```tsx
 * <ListItem>
 *   <ListItemIcon>
 *     <Icon name="Folder" />
 *   </ListItemIcon>
 *   <ListItemText primary="Folder" />
 * </ListItem>
 * ```
 */
export interface ListItemIconProps {
  /** Icon content */
  children: React.ReactElement;
}

export const ListItemIcon: React.FC<ListItemIconProps> = ({ children }) => {
  const { theme } = useEmotionTheme();

  return (
    <div
      style={{
        display: 'flex',
        minWidth: '56px',
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: theme.spacing.md,
        color: theme.text.secondary,
      }}
    >
      {React.cloneElement(children, {
        size: 'medium' as const,
      })}
    </div>
  );
};

/**
 * ListItemAvatar Component
 *
 * Avatar container for list items.
 *
 * @example
 * ```tsx
 * <ListItem>
 *   <ListItemAvatar>
 *     <Avatar>JD</Avatar>
 *   </ListItemAvatar>
 *   <ListItemText primary="John Doe" />
 * </ListItem>
 * ```
 */
export interface ListItemAvatarProps {
  /** Avatar content */
  children: React.ReactElement;
}

export const ListItemAvatar: React.FC<ListItemAvatarProps> = ({ children }) => {
  const { theme } = useEmotionTheme();

  return (
    <div
      style={{
        display: 'flex',
        minWidth: '56px',
        alignItems: 'center',
        justifyContent: 'flex-start',
        marginRight: theme.spacing.md,
      }}
    >
      {React.cloneElement(children, {
        size: 'small' as const,
      })}
    </div>
  );
};

export default List;
