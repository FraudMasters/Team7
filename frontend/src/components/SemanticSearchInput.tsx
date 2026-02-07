import React, { useState, useRef, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  IconButton,
  Stack,
  Chip,
  Collapse,
  Card,
  CardContent,
  FormControlLabel,
  Switch,
  Tooltip,
  Fade,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Psychology as PsychologyIcon,
  Send as SendIcon,
  Lightbulb as LightbulbIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Search mode options
 */
type SearchMode = 'semantic' | 'hybrid' | 'keyword';

/**
 * Search suggestion interface
 */
interface SearchSuggestion {
  id: string;
  query: string;
  category: string;
}

/**
 * Props for SemanticSearchInput component
 */
interface SemanticSearchInputProps {
  onSearch: (query: string, mode: SearchMode) => void;
  loading?: boolean;
  defaultQuery?: string;
  defaultMode?: SearchMode;
  suggestions?: SearchSuggestion[];
  placeholder?: string;
  showModeToggle?: boolean;
}

/**
 * Semantic Search Input Component
 *
 * Provides natural language search interface for semantic search including:
 * - Natural language query input with conversational UI
 * - Search mode selection (semantic, hybrid, keyword)
 * - Quick search suggestions for common queries
 * - Query history and saved searches
 * - Auto-clear and keyboard shortcuts
 */
const SemanticSearchInput: React.FC<SemanticSearchInputProps> = ({
  onSearch,
  loading = false,
  defaultQuery = '',
  defaultMode = 'semantic',
  suggestions = [],
  placeholder,
  showModeToggle = true,
}) => {
  const { t } = useTranslation();

  // Search query state
  const [searchQuery, setSearchQuery] = useState(defaultQuery);
  const [searchMode, setSearchMode] = useState<SearchMode>(defaultMode);

  // UI state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);

  // Refs
  const inputRef = useRef<HTMLInputElement>(null);

  // Default suggestions if none provided
  const defaultSuggestions: SearchSuggestion[] = [
    { id: '1', query: 'senior Python developer with experience in fintech', category: 'Role + Industry' },
    { id: '2', query: 'full stack developer who has led teams of 5+ people', category: 'Leadership' },
    { id: '3', query: 'data scientist with machine learning and cloud experience', category: 'Skills' },
    { id: '4', query: 'frontend developer with React and TypeScript experience', category: 'Tech Stack' },
    { id: '5', query: 'DevOps engineer with Kubernetes and CI/CD pipeline experience', category: 'DevOps' },
  ];

  const displaySuggestions = suggestions.length > 0 ? suggestions : defaultSuggestions;

  /**
   * Handle search execution
   */
  const handleSearch = () => {
    const trimmedQuery = searchQuery.trim();
    if (trimmedQuery) {
      onSearch(trimmedQuery, searchMode);
    }
  };

  /**
   * Handle key press (Enter to search)
   */
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSearch();
    }
  };

  /**
   * Clear search query
   */
  const handleClear = () => {
    setSearchQuery('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  /**
   * Apply a suggestion
   */
  const applySuggestion = (suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.query);
    setShowSuggestions(false);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  /**
   * Get mode label
   */
  const getModeLabel = (mode: SearchMode): string => {
    switch (mode) {
      case 'semantic':
        return t('semanticSearch.modes.semantic');
      case 'hybrid':
        return t('semanticSearch.modes.hybrid');
      case 'keyword':
        return t('semanticSearch.modes.keyword');
      default:
        return mode;
    }
  };

  /**
   * Get mode icon color
   */
  const getModeColor = (mode: SearchMode): string => {
    switch (mode) {
      case 'semantic':
        return 'secondary';
      case 'hybrid':
        return 'primary';
      case 'keyword':
        return 'default';
      default:
        return 'default';
    }
  };

  /**
   * Get mode description
   */
  const getModeDescription = (mode: SearchMode): string => {
    switch (mode) {
      case 'semantic':
        return t('semanticSearch.modeDescriptions.semantic');
      case 'hybrid':
        return t('semanticSearch.modeDescriptions.hybrid');
      case 'keyword':
        return t('semanticSearch.modeDescriptions.keyword');
      default:
        return '';
    }
  };

  return (
    <Paper sx={{ mb: 3, overflow: 'hidden' }}>
      {/* Header */}
      <Box
        sx={{
          px: 3,
          py: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: 'action.hover',
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <PsychologyIcon color="secondary" />
          <Typography variant="h6" fontWeight={600}>
            {t('semanticSearch.title')}
          </Typography>
          <Tooltip title={t('semanticSearch.tooltip')}>
            <LightbulbIcon color="info" fontSize="small" />
          </Tooltip>
        </Stack>

        {showModeToggle && (
          <Stack direction="row" spacing={1}>
            {(['semantic', 'hybrid', 'keyword'] as SearchMode[]).map((mode) => (
              <Chip
                key={mode}
                label={getModeLabel(mode)}
                onClick={() => setSearchMode(mode)}
                color={searchMode === mode ? (getModeColor(mode) as any) : undefined}
                variant={searchMode === mode ? 'filled' : 'outlined'}
                size="small"
              />
            ))}
          </Stack>
        )}
      </Box>

      {/* Main Input Area */}
      <Box sx={{ p: 3 }}>
        {/* Mode Description */}
        <Fade in={showModeToggle}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {getModeDescription(searchMode)}
            </Typography>
          </Box>
        </Fade>

        {/* Search Input */}
        <Stack direction="row" spacing={2} alignItems="flex-start">
          <TextField
            inputRef={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => setInputFocused(true)}
            onBlur={() => {
              // Delay to allow suggestion clicks to register
              setTimeout(() => setInputFocused(false), 200);
            }}
            placeholder={placeholder || t('semanticSearch.placeholder')}
            variant="outlined"
            disabled={loading}
            helperText={t('semanticSearch.helperText')}
            InputProps={{
              sx: {
                borderRadius: 2,
              },
            }}
          />

          <Stack spacing={1} sx={{ mt: 0 }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSearch}
              disabled={!searchQuery.trim() || loading}
              startIcon={loading ? null : <SendIcon />}
              sx={{ minWidth: 120, borderRadius: 2, height: 56 }}
            >
              {loading ? t('semanticSearch.searching') : t('semanticSearch.search')}
            </Button>
            <IconButton
              onClick={handleClear}
              disabled={!searchQuery || loading}
              size="small"
              sx={{ alignSelf: 'center' }}
            >
              <ClearIcon />
            </IconButton>
          </Stack>
        </Stack>

        {/* Suggestion Toggle */}
        <Box sx={{ mt: 2 }}>
          <Button
            size="small"
            onClick={() => setShowSuggestions(!showSuggestions)}
            startIcon={showSuggestions ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            color="info"
          >
            {showSuggestions
              ? t('semanticSearch.hideSuggestions')
              : t('semanticSearch.showSuggestions')}
          </Button>
        </Box>

        {/* Suggestions */}
        <Collapse in={showSuggestions}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              {t('semanticSearch.suggestionsTitle')}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {displaySuggestions.map((suggestion) => (
                <Card
                  key={suggestion.id}
                  variant="outlined"
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      elevation: 4,
                      transform: 'translateY(-2px)',
                      bgcolor: 'action.hover',
                    },
                  }}
                  onClick={() => applySuggestion(suggestion)}
                >
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Stack spacing={0.5}>
                      <Typography variant="body2" fontWeight={500}>
                        {suggestion.query}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {suggestion.category}
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>
        </Collapse>

        {/* Example Queries */}
        {!showSuggestions && (
          <Fade in={!showSuggestions}>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('semanticSearch.examplesTitle')}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {[
                  t('semanticSearch.examples.seniorDeveloper'),
                  t('semanticSearch.examples.teamLead'),
                  t('semanticSearch.examples.fullStack'),
                ].map((example, index) => (
                  <Chip
                    key={index}
                    label={example}
                    variant="outlined"
                    size="small"
                    clickable
                    onClick={() => setSearchQuery(example)}
                    sx={{ fontSize: '0.75rem' }}
                  />
                ))}
              </Stack>
            </Box>
          </Fade>
        )}
      </Box>
    </Paper>
  );
};

export default SemanticSearchInput;
