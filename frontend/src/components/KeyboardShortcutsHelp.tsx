import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Table,
  TableBody,
  TableRow,
  TableCell,
  Box,
  Typography,
  DialogProps,
} from '@mui/material';
import {
  Keyboard as KeyboardIcon,
  Search as SearchIcon,
  Home as HomeIcon,
} from '@mui/icons-material';

/**
 * KeyboardShortcutsHelp Component
 *
 * Provides a modal dialog displaying all available keyboard shortcuts
 * in the application. Helps users discover and learn navigation shortcuts.
 *
 * Features:
 * - Displays all keyboard shortcuts in a table format
 * - Shows key combinations and their actions
 * - Includes icons for visual identification
 * - Supports open/close control via props
 * - Integrates with i18next for translations
 * - Closes on Escape key (via Dialog default behavior)
 *
 * @example
 * ```tsx
 * // In Layout component
 * const [shortcutsOpen, setShortcutsOpen] = useState(false);
 *
 * // Keyboard shortcut handler
 * useEffect(() => {
 *   const handleKeyDown = (event: KeyboardEvent) => {
 *     if ((event.ctrlKey || event.metaKey) && event.key === '/') {
 *       event.preventDefault();
 *       setShortcutsOpen(true);
 *     }
 *   };
 *   window.addEventListener('keydown', handleKeyDown);
 *   return () => window.removeEventListener('keydown', handleKeyDown);
 * }, []);
 *
 * <KeyboardShortcutsHelp
 *   open={shortcutsOpen}
 *   onClose={() => setShortcutsOpen(false)}
 * />
 * ```
 */
interface KeyboardShortcutsHelpProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback fired when the dialog requests to be closed */
  onClose: () => void;
}

const KeyboardShortcutsHelp: React.FC<KeyboardShortcutsHelpProps> = ({
  open,
  onClose,
}) => {
  const { t } = useTranslation();

  /**
   * Handle dialog close
   *
   * Calls the onClose callback when user requests to close the dialog.
   */
  const handleClose: DialogProps['onClose'] = (event, reason) => {
    onClose();
  };

  /**
   * Keyboard key styling component
   *
   * Renders a keyboard key with visual styling to represent
   * actual keyboard keys.
   *
   * @param children - Key label to display
   * @returns Styled key component
   */
  const KeyBadge: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <Box
      sx={{
        display: 'inline-block',
        padding: '2px 6px',
        minWidth: '24px',
        textAlign: 'center',
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        fontWeight: 500,
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
      }}
    >
      {children}
    </Box>
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <KeyboardIcon color="primary" />
          <Typography variant="h6" component="span">
            {t('keyboardShortcuts.title')}
          </Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Table>
          <TableBody>
            {/* Ctrl+K - Search */}
            <TableRow>
              <TableCell component="th" scope="row">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <KeyBadge>Ctrl</KeyBadge>
                  <Typography variant="body2">+</Typography>
                  <KeyBadge>K</KeyBadge>
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SearchIcon fontSize="small" color="action" />
                  <Typography variant="body2">
                    {t('keyboardShortcuts.search')}
                  </Typography>
                </Box>
              </TableCell>
            </TableRow>

            {/* Ctrl+/ - Show shortcuts */}
            <TableRow>
              <TableCell component="th" scope="row">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <KeyBadge>Ctrl</KeyBadge>
                  <Typography variant="body2">+</Typography>
                  <KeyBadge>/</KeyBadge>
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <KeyboardIcon fontSize="small" color="action" />
                  <Typography variant="body2">
                    {t('keyboardShortcuts.showShortcuts')}
                  </Typography>
                </Box>
              </TableCell>
            </TableRow>

            {/* Alt+Home - Go home */}
            <TableRow>
              <TableCell component="th" scope="row">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <KeyBadge>Alt</KeyBadge>
                  <Typography variant="body2">+</Typography>
                  <KeyBadge>Home</KeyBadge>
                </Box>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HomeIcon fontSize="small" color="action" />
                  <Typography variant="body2">
                    {t('keyboardShortcuts.goHome')}
                  </Typography>
                </Box>
              </TableCell>
            </TableRow>

            {/* Escape - Close dialog */}
            <TableRow>
              <TableCell component="th" scope="row">
                <KeyBadge>Esc</KeyBadge>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2">
                    {t('keyboardShortcuts.closeDialog')}
                  </Typography>
                </Box>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </DialogContent>
    </Dialog>
  );
};

export default KeyboardShortcutsHelp;
