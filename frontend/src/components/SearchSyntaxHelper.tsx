import React, { useState, useRef, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  Popper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Stack,
  Tooltip,
  IconButton,
  Collapse,
  Divider,
  ClickAwayListener,
} from '@mui/material';
import {
  Code as CodeIcon,
  Help as HelpIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Functions as FunctionsIcon,
  Label as LabelIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Auto-complete suggestion interface
 */
interface SyntaxSuggestion {
  value: string;
  label: string;
  description: string;
  category: 'field' | 'operator' | 'modifier';
  example?: string;
}

/**
 * Props for SearchSyntaxHelper component
 */
interface SearchSyntaxHelperProps {
  inputValue: string;
  cursorPosition: number;
  anchorEl: HTMLElement | null;
  onSelectSuggestion: (suggestion: string) => void;
  open?: boolean;
}

/**
 * Search Syntax Helper Component
 *
 * Provides auto-complete and syntax help for advanced search queries including:
 * - Field name suggestions (skills:, location:, experience:, etc.)
 * - Boolean operator suggestions (AND, OR, NOT)
 * - Syntax help tooltip with examples
 * - Smart context-aware suggestions based on current input
 */
const SearchSyntaxHelper: React.FC<SearchSyntaxHelperProps> = ({
  inputValue,
  cursorPosition,
  anchorEl,
  onSelectSuggestion,
  open = false,
}) => {
  const { t } = useTranslation();

  // UI state
  const [showHelp, setShowHelp] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  /**
   * Field name suggestions
   */
  const fieldSuggestions: SyntaxSuggestion[] = [
    {
      value: 'skills:',
      label: 'skills:',
      description: 'Search by technical skills',
      category: 'field',
      example: 'skills:Python AND skills:React',
    },
    {
      value: 'location:',
      label: 'location:',
      description: 'Filter by location',
      category: 'field',
      example: 'location:"New York"',
    },
    {
      value: 'experience:',
      label: 'experience:',
      description: 'Filter by years of experience',
      category: 'field',
      example: 'experience:>5',
    },
    {
      value: 'education:',
      label: 'education:',
      description: 'Filter by education level',
      category: 'field',
      example: 'education:Masters',
    },
    {
      value: 'title:',
      label: 'title:',
      description: 'Search by job title',
      category: 'field',
      example: 'title:"Senior Developer"',
    },
    {
      value: 'company:',
      label: 'company:',
      description: 'Filter by previous company',
      category: 'field',
      example: 'company:Google OR company:Amazon',
    },
    {
      value: 'salary:',
      label: 'salary:',
      description: 'Filter by expected salary',
      category: 'field',
      example: 'salary:>100000',
    },
  ];

  /**
   * Boolean operator suggestions
   */
  const operatorSuggestions: SyntaxSuggestion[] = [
    {
      value: ' AND ',
      label: 'AND',
      description: 'Both conditions must match',
      category: 'operator',
      example: 'Python AND Django',
    },
    {
      value: ' OR ',
      label: 'OR',
      description: 'Either condition must match',
      category: 'operator',
      example: 'React OR Vue',
    },
    {
      value: ' NOT ',
      label: 'NOT',
      description: 'Exclude matches',
      category: 'operator',
      example: 'Python NOT Junior',
    },
  ];

  /**
   * Modifier suggestions (quotes, parentheses)
   */
  const modifierSuggestions: SyntaxSuggestion[] = [
    {
      value: '""',
      label: '" "',
      description: 'Exact phrase match',
      category: 'modifier',
      example: '"Senior Developer"',
    },
    {
      value: '()',
      label: '( )',
      description: 'Group conditions',
      category: 'modifier',
      example: '(React OR Vue) AND TypeScript',
    },
  ];

  /**
   * Get all available suggestions
   */
  const allSuggestions = [
    ...fieldSuggestions,
    ...operatorSuggestions,
    ...modifierSuggestions,
  ];

  /**
   * Get context-aware suggestions based on current input
   */
  const getContextSuggestions = (): SyntaxSuggestion[] => {
    if (!inputValue) {
      return fieldSuggestions;
    }

    const textBeforeCursor = inputValue.substring(0, cursorPosition);
    const lastWord = textBeforeCursor.split(/\s+/).pop() || '';

    // If typing a field name, show field suggestions
    if (lastWord && !lastWord.includes(':')) {
      return allSuggestions.filter((s) =>
        s.value.toLowerCase().includes(lastWord.toLowerCase())
      );
    }

    // If just typed a field or phrase, show operators
    if (textBeforeCursor.trim() && !textBeforeCursor.trim().match(/(AND|OR|NOT)\s*$/i)) {
      return operatorSuggestions;
    }

    // Default to all suggestions
    return allSuggestions;
  };

  const suggestions = getContextSuggestions();

  /**
   * Handle suggestion selection
   */
  const handleSelectSuggestion = (suggestion: SyntaxSuggestion) => {
    onSelectSuggestion(suggestion.value);
    setSelectedIndex(0);
  };

  /**
   * Handle keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!open || suggestions.length === 0) return;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % suggestions.length);
          break;
        case 'ArrowUp':
          event.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
          break;
        case 'Enter':
          if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
            event.preventDefault();
            handleSelectSuggestion(suggestions[selectedIndex]);
          }
          break;
        case 'Escape':
          event.preventDefault();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, suggestions, selectedIndex]);

  /**
   * Reset selected index when suggestions change
   */
  useEffect(() => {
    setSelectedIndex(0);
  }, [inputValue]);

  /**
   * Get category icon
   */
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'field':
        return <LabelIcon fontSize="small" />;
      case 'operator':
        return <FunctionsIcon fontSize="small" />;
      case 'modifier':
        return <CodeIcon fontSize="small" />;
      default:
        return <CodeIcon fontSize="small" />;
    }
  };

  /**
   * Get category color
   */
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'field':
        return 'primary';
      case 'operator':
        return 'secondary';
      case 'modifier':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <>
      {/* Auto-complete Popper */}
      <Popper
        open={open && suggestions.length > 0}
        anchorEl={anchorEl}
        placement="bottom-start"
        style={{ zIndex: 1300 }}
        modifiers={[
          {
            name: 'offset',
            options: {
              offset: [0, 8],
            },
          },
        ]}
      >
        <Paper
          elevation={8}
          sx={{
            maxHeight: 300,
            overflowY: 'auto',
            minWidth: 400,
            maxWidth: 500,
          }}
        >
          <Box
            sx={{
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              bgcolor: 'action.hover',
            }}
          >
            <Typography variant="caption" color="text.secondary" fontWeight={600}>
              Syntax Suggestions
            </Typography>
            <Tooltip title="Show syntax help">
              <IconButton size="small" onClick={() => setShowHelp(!showHelp)}>
                {showHelp ? <ExpandLessIcon fontSize="small" /> : <HelpIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          </Box>

          <Collapse in={showHelp}>
            <Box sx={{ p: 2, bgcolor: 'info.lighter' }}>
              <Typography variant="body2" gutterBottom fontWeight={600}>
                Search Syntax Guide
              </Typography>
              <Stack spacing={1} sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  <strong>Fields:</strong> Use field: to search specific attributes
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Operators:</strong> Combine with AND, OR, NOT
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Quotes:</strong> Use "quotes" for exact phrases
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Grouping:</strong> Use (parentheses) to group conditions
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Ranges:</strong> Use &gt;, &lt;, &gt;=, &lt;= for numeric fields
                </Typography>
              </Stack>
            </Box>
            <Divider />
          </Collapse>

          <List dense>
            {suggestions.map((suggestion, index) => (
              <ListItem
                key={`${suggestion.category}-${suggestion.value}`}
                button
                selected={index === selectedIndex}
                onClick={() => handleSelectSuggestion(suggestion)}
                sx={{
                  '&.Mui-selected': {
                    bgcolor: 'action.selected',
                  },
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {getCategoryIcon(suggestion.category)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        fontFamily="monospace"
                        sx={{ color: 'primary.main' }}
                      >
                        {suggestion.label}
                      </Typography>
                      <Chip
                        label={suggestion.category}
                        size="small"
                        color={getCategoryColor(suggestion.category) as any}
                        sx={{ height: 18, fontSize: '0.65rem' }}
                      />
                    </Stack>
                  }
                  secondary={
                    <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {suggestion.description}
                      </Typography>
                      {suggestion.example && (
                        <Typography
                          variant="caption"
                          fontFamily="monospace"
                          sx={{
                            bgcolor: 'action.hover',
                            px: 0.5,
                            py: 0.25,
                            borderRadius: 0.5,
                            display: 'inline-block',
                          }}
                        >
                          {suggestion.example}
                        </Typography>
                      )}
                    </Stack>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Box
            sx={{
              p: 1,
              bgcolor: 'action.hover',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant="caption" color="text.secondary">
              Use ↑↓ to navigate, Enter to select
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {suggestions.length} {suggestions.length === 1 ? 'suggestion' : 'suggestions'}
            </Typography>
          </Box>
        </Paper>
      </Popper>
    </>
  );
};

export default SearchSyntaxHelper;
