import React, { useEffect, useRef, useCallback } from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';

/**
 * Menu item interface
 */
export interface MenuItem {
  /** Unique identifier */
  id: string;
  /** Label text */
  label: string;
  /** Icon component */
  icon?: React.ReactNode;
  /** Click handler */
  onClick?: () => void;
  /** If true, the item is disabled */
  disabled?: boolean;
  /** If true, the item is selected */
  selected?: boolean;
}

/**
 * Base Menu props interface
 */
export interface BaseMenuProps {
  /** CSS class name */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Reference to element */
  menuRef?: React.Ref<HTMLDivElement>;
}

/**
 * Props for Menu component
 */
export interface MenuProps extends BaseMenuProps {
  /** If true, the menu is visible */
  open: boolean;
  /** Callback fired when the menu is requested to be closed */
  onClose: (event: React.MouseEvent | React.KeyboardEvent, reason?: string) => void;
  /** Anchor element for positioning */
  anchorEl?: HTMLElement | null;
  /** Menu items to display */
  items: MenuItem[];
  /** Position of the menu relative to anchor */
  anchorOrigin?: {
    vertical: 'top' | 'bottom' | 'center';
    horizontal: 'left' | 'right' | 'center';
  };
  /** Position of the menu content itself */
  transformOrigin?: {
    vertical: 'top' | 'bottom' | 'center';
    horizontal: 'left' | 'right' | 'center';
  };
  /** Elevation shadow depth */
  elevation?: number;
  /** Maximum width of the menu */
  maxWidth?: number | string;
  /** Minimum width of the menu */
  minWidth?: number | string;
}

/**
 * Styled Menu component
 */
const StyledMenu = styled.div<{
  theme: EmotionTheme;
  elevation: number;
  maxWidth: number | string;
  minWidth: number | string;
}>`
  /* Position and display */
  position: fixed;
  z-index: 1300;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  overflow-x: hidden;

  /* Sizing */
  max-width: ${({ maxWidth }) => (typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth)};
  min-width: ${({ minWidth }) => (typeof minWidth === 'number' ? `${minWidth}px` : minWidth)};

  /* Base styles */
  box-sizing: border-box;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  background-color: ${({ theme }) => theme.background.paper};
  color: ${({ theme }) => theme.text.primary};
  border-radius: ${({ theme }) => theme.borderRadius.md};

  /* Elevation shadow */
  box-shadow: ${({ elevation, theme }) =>
    elevation === 0 ? 'none' : elevation <= 4 ? theme.shadows.md : elevation <= 8 ? theme.shadows.lg : theme.shadows.xl};

  /* Border */
  border: 1px solid ${({ theme }) => theme.divider};

  /* Animation */
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 150ms cubic-bezier(0.4, 0, 0.2, 1),
    transform 150ms cubic-bezier(0.4, 0, 0.2, 1);

  &.open {
    opacity: 1;
    transform: scale(1);
  }
`;

/**
 * Styled Menu Item component
 */
const StyledMenuItem = styled.div<{ theme: EmotionTheme; disabled: boolean; selected: boolean }>`
  /* Layout */
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  user-select: none;
  transition: background-color 150ms ease-in-out;

  /* Typography */
  font-size: ${({ theme }) => theme.typography.fontSize.sm};
  font-weight: ${({ theme }) => theme.typography.fontWeight.normal};
  line-height: 1.5;
  color: ${({ theme, disabled }) => (disabled ? theme.text.disabled : theme.text.primary)};

  /* Selected state */
  background-color: ${({ theme, selected }) => (selected ? theme.action.hover : 'transparent')};

  /* Hover state */
  &:hover {
    background-color: ${({ theme, disabled }) => (disabled ? 'transparent' : theme.action.hover)};
  }

  /* Focus state */
  &:focus-visible {
    outline: 2px solid ${({ theme }) => theme.primary.main};
    outline-offset: -2px;
  }

  /* Separator */
  &:not(:last-child) {
    border-bottom: 1px solid ${({ theme }) => theme.divider};
  }
`;

/**
 * Styled Icon container
 */
const StyledIconContainer = styled.span`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

/**
 * Menu Component
 *
 * A dropdown menu that displays a list of options.
 * Positioned relative to an anchor element.
 *
 * @example
 * ```tsx
 * const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
 * const [open, setOpen] = useState(false);
 *
 * const handleClick = (event: React.MouseEvent<HTMLElement>) => {
 *   setAnchorEl(event.currentTarget);
 *   setOpen(true);
 * };
 *
 * const handleClose = () => {
 *   setOpen(false);
 *   setAnchorEl(null);
 * };
 *
 * const menuItems = [
 *   { id: '1', label: 'Option 1', onClick: () => console.log('Option 1') },
 *   { id: '2', label: 'Option 2', onClick: () => console.log('Option 2') },
 *   { id: '3', label: 'Option 3', onClick: () => console.log('Option 3'), disabled: true },
 * ];
 *
 * <Button onClick={handleClick}>Open Menu</Button>
 * <Menu
 *   open={open}
 *   onClose={handleClose}
 *   anchorEl={anchorEl}
 *   items={menuItems}
 * />
 * ```
 */
export const Menu = React.forwardRef<HTMLDivElement, MenuProps>(
  (
    {
      open,
      onClose,
      anchorEl,
      items,
      anchorOrigin = { vertical: 'bottom', horizontal: 'left' },
      transformOrigin = { vertical: 'top', horizontal: 'left' },
      elevation = 8,
      maxWidth = 280,
      minWidth = 200,
      className,
      style,
      menuRef,
      ...rest
    },
    ref
  ) => {
    const { theme } = useEmotionTheme();
    const menuRefInternal = useRef<HTMLDivElement>(null);
    const effectiveMenuRef = (ref || menuRef || menuRefInternal) as React.RefObject<HTMLDivElement>;

    // Calculate menu position
    const getPosition = useCallback(() => {
      if (!anchorEl) {
        return { top: 0, left: 0 };
      }

      const anchorRect = anchorEl.getBoundingClientRect();
      const menuRect = effectiveMenuRef.current?.getBoundingClientRect();

      const menuWidth = menuRect?.width || 280;
      const menuHeight = menuRect?.height || 300;

      let top = 0;
      let left = 0;

      // Vertical positioning
      switch (anchorOrigin.vertical) {
        case 'top':
          top = anchorRect.top - menuHeight;
          break;
        case 'center':
          top = anchorRect.top + anchorRect.height / 2 - menuHeight / 2;
          break;
        case 'bottom':
        default:
          top = anchorRect.bottom;
          break;
      }

      // Horizontal positioning
      switch (anchorOrigin.horizontal) {
        case 'right':
          left = anchorRect.right - menuWidth;
          break;
        case 'center':
          left = anchorRect.left + anchorRect.width / 2 - menuWidth / 2;
          break;
        case 'left':
        default:
          left = anchorRect.left;
          break;
      }

      // Apply transform origin
      // This is handled by CSS transforms

      return { top, left };
    }, [anchorEl, effectiveMenuRef]);

    const position = getPosition();

    // Handle keyboard events
    const handleKeyDown = useCallback(
      (event: React.KeyboardEvent) => {
        if (event.key === 'Escape' && open) {
          onClose(event, 'escapeKeyDown');
        }
      },
      [open, onClose]
    );

    // Close menu when clicking outside
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          open &&
          effectiveMenuRef.current &&
          !effectiveMenuRef.current.contains(event.target as Node) &&
          anchorEl &&
          !anchorEl.contains(event.target as Node)
        ) {
          onClose(event as unknown as React.MouseEvent, 'backdropClick');
        }
      };

      if (open) {
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
          document.removeEventListener('mousedown', handleClickOutside);
        };
      }
    }, [open, onClose, anchorEl, effectiveMenuRef]);

    // Handle menu item click
    const handleItemClick = (item: MenuItem) => {
      if (!item.disabled && item.onClick) {
        item.onClick();
        onClose({} as React.MouseEvent, 'itemClick');
      }
    };

    if (!open && !anchorEl) {
      return null;
    }

    return (
      <StyledMenu
        ref={effectiveMenuRef}
        theme={theme}
        elevation={elevation}
        maxWidth={maxWidth}
        minWidth={minWidth}
        className={`${className || ''} ${open ? 'open' : ''}`}
        style={{
          top: `${position.top}px`,
          left: `${position.left}px`,
          ...style,
        }}
        onKeyDown={handleKeyDown}
        role="menu"
        aria-hidden={!open}
        {...rest}
      >
        {items.map((item, index) => (
          <StyledMenuItem
            key={item.id}
            theme={theme}
            disabled={item.disabled || false}
            selected={item.selected || false}
            onClick={() => handleItemClick(item)}
            role="menuitem"
            tabIndex={item.disabled ? -1 : 0}
            aria-disabled={item.disabled}
          >
            {item.icon && <StyledIconContainer>{item.icon}</StyledIconContainer>}
            <span>{item.label}</span>
          </StyledMenuItem>
        ))}
      </StyledMenu>
    );
  }
);

Menu.displayName = 'Menu';

export default Menu;
