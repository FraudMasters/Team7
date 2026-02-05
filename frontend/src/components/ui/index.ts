// UI Components Index
// Re-exports all MUI-based components

// Icon from primitives
export { Icon, default as IconDefault } from './primitives/Icon';

export { default as Box } from './Box';
export { default as Typography } from './Typography';
export { default as Accordion, AccordionSummary, AccordionDetails } from './Accordion';
export { default as Alert, AlertTitle } from './Alert';
export { default as AppBar } from './AppBar';
export { default as Autocomplete } from './Autocomplete';
export { default as Avatar } from './Avatar';
export { default as Badge } from './Badge';
export { default as BottomNavigation } from './BottomNavigation';
export { default as Breadcrumbs } from './Breadcrumbs';
export { default as Button } from './Button';
export { default as ButtonGroup } from './ButtonGroup';
export { default as Card, CardActions, CardHeader, CardContent } from './Card';
export { default as Checkbox } from './Checkbox';
export { default as Chip } from './Chip';
export { default as CircularProgress } from './CircularProgress';
export { default as Collapse } from './Collapse';
export { default as Container } from './Paper';  // Container doesn't exist, use Paper as fallback
export { default as Dialog, DialogTitle, DialogContent, DialogActions } from './Dialog';
export { default as DialogContentText } from './DialogContentText';
export { default as Divider } from './Divider';
export { default as Drawer } from './Drawer';
export { default as FormControl } from './FormControl';
export { default as FormControlLabel } from './FormControlLabel';
export { default as Grid } from './Grid';
export { default as IconButton } from './IconButton';
export { default as InputLabel } from './InputLabel';
export { default as InputAdornment } from './InputAdornment';
export { default as LinearProgress } from './LinearProgress';
export { default as List, ListItem, ListItemText, ListItemIcon } from './List';
export { default as Menu } from './Menu';
export { default as MenuItem } from './Menu';
export { default as Modal } from './Modal';
export { default as Pagination } from './Pagination';
export { default as Paper } from './Paper';
export { default as Popover } from './Popover';
export { default as Rating } from './Rating';
export { default as Radio } from './Radio';
export { default as Select } from './Select';
export { default as Skeleton } from './Skeleton';
export { default as Slider } from './Slider';
export { default as Snackbar } from './Snackbar';
export { default as Stack } from './Stack';
export { default as Switch } from './Switch';
export { default as Table, TableHead, TableBody, TableFooter, TableRow, TableCell } from './Table';
export { default as ToggleButton } from './ToggleButton';
export { default as ToggleButtonGroup } from './ToggleButtonGroup';
export { default as TableContainer } from './TableContainer';
export { default as Tabs } from './Tabs';
export { default as Tab } from './Tabs';
export { default as TextArea } from './TextArea';
export { default as TextField } from './TextField';
export { default as Toolbar } from './Toolbar';
export { default as Tooltip } from './Tooltip';

// Re-export commonly used hooks
export { useMediaQuery } from '../../hooks/useMediaQuery';

// PullToRefresh and TouchCarousel
export { default as PullToRefresh } from './PullToRefresh';
export type { PullToRefreshProps } from './PullToRefresh';
export { default as TouchCarousel } from './TouchCarousel';
export type { TouchCarouselProps } from './TouchCarousel';

// Note: ErrorState, LoadingState, PageTransition
// are in @components/mui - import from there instead
