import React, { useState, useCallback, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  useTheme,
  useMediaQuery,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  Keyboard as KeyboardIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Keyboard shortcut definition
 */
export interface KeyboardShortcut {
  /**
   * Unique identifier for the shortcut
   */
  id: string;

  /**
   * Keyboard keys (e.g., "Ctrl+S", "Escape", "Enter")
   */
  keys: string[];

  /**
   * Human-readable description of what the shortcut does
   */
  description: string;

  /**
   * Which workflow this shortcut belongs to
   */
  category: ShortcutCategory;
}

/**
 * Shortcut category for organizing shortcuts by workflow
 */
export type ShortcutCategory =
  | 'global'
  | 'upload'
  | 'vacancy'
  | 'candidate'
  | 'navigation'
  | 'forms';

/**
 * Category metadata for display
 */
interface ShortcutCategoryMeta {
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

/**
 * Keyboard shortcut categories with metadata
 */
const SHORTCUT_CATEGORIES: Record<ShortcutCategory, ShortcutCategoryMeta> = {
  global: {
    label: 'Global Shortcuts',
    description: 'Available everywhere in the application',
    icon: <KeyboardIcon />,
    color: '#1976d2',
  },
  upload: {
    label: 'Resume Upload',
    description: 'Upload and batch upload pages',
    icon: '📤',
    color: '#388e3c',
  },
  vacancy: {
    label: 'Vacancy Management',
    description: 'Vacancy list and form pages',
    icon: '💼',
    color: '#f57c00',
  },
  candidate: {
    label: 'Candidate Review',
    description: 'Candidate kanban and detail views',
    icon: '👥',
    color: '#7b1fa2',
  },
  navigation: {
    label: 'Navigation',
    description: 'Navigate through lists and cards',
    icon: '🧭',
    color: '#0097a7',
  },
  forms: {
    label: 'Forms',
    description: 'Common form shortcuts',
    icon: '📝',
    color: '#c2185b',
  },
};

/**
 * All keyboard shortcuts documented for the application
 *
 * This is the central registry of keyboard shortcuts that should be
 * kept in sync with the actual implementations in useKeyboardNavigation hook
 * and individual components.
 */
export const KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  // Global shortcuts
  {
    id: 'global.search',
    keys: ['Ctrl', 'K'],
    description: 'Open global search',
    category: 'global',
  },
  {
    id: 'global.showShortcuts',
    keys: ['Ctrl', '/'],
    description: 'Show this keyboard shortcuts help',
    category: 'global',
  },
  {
    id: 'global.closeModal',
    keys: ['Escape'],
    description: 'Close modal or dialog',
    category: 'global',
  },

  // Resume upload shortcuts
  {
    id: 'upload.focusZone',
    keys: ['Ctrl', 'U'],
    description: 'Focus upload zone',
    category: 'upload',
  },
  {
    id: 'upload.cancel',
    keys: ['Escape'],
    description: 'Cancel upload',
    category: 'upload',
  },

  // Vacancy management shortcuts
  {
    id: 'vacancy.new',
    keys: ['Ctrl', 'N'],
    description: 'Create new vacancy',
    category: 'vacancy',
  },
  {
    id: 'vacancy.search',
    keys: ['Ctrl', 'F'],
    description: 'Focus search field',
    category: 'vacancy',
  },
  {
    id: 'vacancy.edit',
    keys: ['Enter'],
    description: 'Edit selected vacancy',
    category: 'vacancy',
  },

  // Candidate review shortcuts
  {
    id: 'candidate.openDetails',
    keys: ['Enter'],
    description: 'Open candidate details',
    category: 'candidate',
  },
  {
    id: 'candidate.closeDetails',
    keys: ['Escape'],
    description: 'Close candidate details',
    category: 'candidate',
  },
  {
    id: 'candidate.nextStage',
    keys: ['Ctrl', '→'],
    description: 'Move to next stage',
    category: 'candidate',
  },
  {
    id: 'candidate.prevStage',
    keys: ['Ctrl', '←'],
    description: 'Move to previous stage',
    category: 'candidate',
  },

  // Navigation shortcuts
  {
    id: 'nav.next',
    keys: ['Arrow Down', '→'],
    description: 'Next item/card',
    category: 'navigation',
  },
  {
    id: 'nav.previous',
    keys: ['Arrow Up', '←'],
    description: 'Previous item/card',
    category: 'navigation',
  },
  {
    id: 'nav.first',
    keys: ['Home'],
    description: 'First item in list',
    category: 'navigation',
  },
  {
    id: 'nav.last',
    keys: ['End'],
    description: 'Last item in list',
    category: 'navigation',
  },

  // Form shortcuts
  {
    id: 'form.save',
    keys: ['Ctrl', 'S'],
    description: 'Save form',
    category: 'forms',
  },
  {
    id: 'form.nextField',
    keys: ['Tab'],
    description: 'Next field',
    category: 'forms',
  },
  {
    id: 'form.prevField',
    keys: ['Shift', 'Tab'],
    description: 'Previous field',
    category: 'forms',
  },
  {
    id: 'form.submit',
    keys: ['Ctrl', 'Enter'],
    description: 'Submit form',
    category: 'forms',
  },
];

export interface KeyboardShortcutsHelpProps {
  /**
   * Whether the dialog is open
   */
  open?: boolean;

  /**
   * Callback when dialog is closed
   */
  onClose?: () => void;

  /**
   * Optional title for the dialog
   * @default 'Keyboard Shortcuts'
   */
  title?: string;
}

/**
 * KeyboardShortcutsHelp Component
 *
 * Displays a comprehensive keyboard shortcuts reference organized by workflow.
 * The dialog can be triggered with Ctrl+/ and provides an at-a-glance reference
 * for all available keyboard shortcuts in the application.
 *
 * @example
 * ```tsx
 * // Controlled component
 * const [open, setOpen] = useState(false);
 * <KeyboardShortcutsHelp open={open} onClose={() => setOpen(false)} />
 *
 * // Or trigger with button
 * <Button onClick={() => setOpen(true)}>
 *   <KeyboardIcon /> Keyboard Shortcuts
 * </Button>
 * ```
 *
 * @example
 * ```tsx
 * // Register Ctrl+/ to open dialog globally
 * useEffect(() => {
 *   const handleKeyDown = (e: KeyboardEvent) => {
 *     if (e.ctrlKey && e.key === '/') {
 *       e.preventDefault();
 *       setOpen(true);
 *     }
 *   };
 *   window.addEventListener('keydown', handleKeyDown);
 *   return () => window.removeEventListener('keydown', handleKeyDown);
 * }, []);
 * ```
 */
const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  open = false,
  onClose,
  title = 'Keyboard Shortcuts',
}) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));

  const handleClose = useCallback(() => {
    onClose?.();
  }, [onClose]);

  // Handle Escape key to close dialog
  useEffect(() => {
    if (!open) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [open, handleClose]);

  // Group shortcuts by category
  const shortcutsByCategory = KEYBOARD_SHORTCUTS.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<ShortcutCategory, KeyboardShortcut[]>);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullScreen={fullScreen}
      maxWidth="md"
      scroll="paper"
      PaperProps={{
        sx: {
          borderRadius: fullScreen ? 0 : 2,
          maxHeight: '80vh',
        },
      }}
      aria-labelledby="keyboard-shortcuts-title"
    >
      <DialogTitle id="keyboard-shortcuts-title">
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <KeyboardIcon color="primary" />
            <Typography variant="h6" component="span">
              {title}
            </Typography>
          </Box>
          <IconButton
            edge="end"
            onClick={handleClose}
            aria-label="Close keyboard shortcuts"
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1,
              mb: 2,
              p: 2,
              bgcolor: 'info.main',
              color: 'info.contrastText',
              borderRadius: 1,
            }}
          >
            <InfoIcon fontSize="small" />
            <Typography variant="body2">
              Press <strong>Ctrl+/</strong> anywhere in the application to open this
              help dialog. Keyboard shortcuts help you navigate and work more
              efficiently without using the mouse.
            </Typography>
          </Box>
        </Box>

        {Object.entries(SHORTCUT_CATEGORIES).map(
          ([category, meta], categoryIndex) => {
            const shortcuts = shortcutsByCategory[category as ShortcutCategory];
            if (!shortcuts || shortcuts.length === 0) return null;

            return (
              <Box
                key={category}
                sx={{ mb: categoryIndex < Object.keys(SHORTCUT_CATEGORIES).length - 1 ? 3 : 0 }}
              >
                {/* Category header */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1.5,
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 32,
                      height: 32,
                      bgcolor: `${meta.color}20`,
                      borderRadius: 1,
                      color: meta.color,
                    }}
                  >
                    {meta.icon}
                  </Box>
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {meta.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {meta.description}
                    </Typography>
                  </Box>
                </Box>

                {/* Shortcuts table */}
                <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ width: '40%', fontWeight: 600 }}>
                          Shortcut
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {shortcuts.map((shortcut, index) => (
                        <TableRow
                          key={shortcut.id}
                          sx={{
                            '&:last-child td': { border: 0 },
                            bgcolor: index % 2 === 0 ? 'action.hover' : 'inherit',
                          }}
                        >
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {shortcut.keys.map((key, keyIndex) => (
                                <React.Fragment key={keyIndex}>
                                  {keyIndex > 0 && (
                                    <Typography
                                      variant="body2"
                                      color="text.secondary"
                                      sx={{ mx: 0.5 }}
                                    >
                                      +
                                    </Typography>
                                  )}
                                  <Chip
                                    label={key}
                                    variant="outlined"
                                    size="small"
                                    sx={{
                                      fontFamily: 'monospace',
                                      fontSize: '0.75rem',
                                      fontWeight: 600,
                                      bgcolor: 'background.paper',
                                    }}
                                  />
                                </React.Fragment>
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{shortcut.description}</Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            );
          }
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 'auto', px: 1 }}>
          Total: {KEYBOARD_SHORTCUTS.length} shortcuts across{' '}
          {Object.keys(SHORTCUT_CATEGORIES).length} categories
        </Typography>
        <Button onClick={handleClose} variant="contained" autoFocus>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default KeyboardShortcutsHelp;
