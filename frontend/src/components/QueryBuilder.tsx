import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  IconButton,
  Divider,
  Autocomplete,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Boolean operator types for query building
 */
type BooleanOperator = 'AND' | 'OR' | 'NOT';

/**
 * Field types available for querying
 */
type QueryField = 'skills' | 'location' | 'education' | 'experience' | 'language' | 'title' | 'company';

/**
 * Filter row in the query builder
 */
interface FilterRow {
  id: string;
  operator: BooleanOperator;
  field: QueryField;
  value: string;
}

/**
 * Props for QueryBuilder component
 */
interface QueryBuilderProps {
  onQueryChange?: (query: string) => void;
  initialQuery?: string;
  disabled?: boolean;
}

/**
 * Query Builder Component
 *
 * Visual query builder for non-technical users to construct complex boolean search queries.
 * Provides an intuitive interface for building AND/OR/NOT queries without knowing the syntax.
 *
 * Features:
 * - Add/remove filter rows dynamically
 * - Select boolean operators (AND, OR, NOT) for each filter
 * - Choose from predefined fields (skills, location, education, etc.)
 * - Auto-generate query string from visual representation
 * - Copy query to clipboard
 * - Reset to default state
 *
 * @example
 * ```tsx
 * <QueryBuilder
 *   onQueryChange={(query) => console.log('Generated query:', query)}
 *   disabled={false}
 * />
 * ```
 */
const QueryBuilder: React.FC<QueryBuilderProps> = ({
  onQueryChange,
  initialQuery = '',
  disabled = false,
}) => {
  const { t } = useTranslation();

  // Filter rows state
  const [filterRows, setFilterRows] = useState<FilterRow[]>([
    {
      id: `filter-${Date.now()}`,
      operator: 'AND',
      field: 'skills',
      value: '',
    },
  ]);

  // Generated query string
  const [generatedQuery, setGeneratedQuery] = useState<string>('');

  // Copy notification
  const [showCopyNotification, setShowCopyNotification] = useState(false);

  // Field options with display names
  const fieldOptions: { value: QueryField; label: string }[] = [
    { value: 'skills', label: t('search.fields.skills', 'Skills') },
    { value: 'location', label: t('search.fields.location', 'Location') },
    { value: 'education', label: t('search.fields.education', 'Education') },
    { value: 'experience', label: t('search.fields.experience', 'Experience') },
    { value: 'language', label: t('search.fields.language', 'Language') },
    { value: 'title', label: t('search.fields.title', 'Job Title') },
    { value: 'company', label: t('search.fields.company', 'Company') },
  ];

  // Operator options with display names
  const operatorOptions: { value: BooleanOperator; label: string; color: string }[] = [
    { value: 'AND', label: 'AND', color: '#1976d2' },
    { value: 'OR', label: 'OR', color: '#2e7d32' },
    { value: 'NOT', label: 'NOT', color: '#d32f2f' },
  ];

  /**
   * Add a new filter row
   */
  const addFilterRow = () => {
    const newRow: FilterRow = {
      id: `filter-${Date.now()}`,
      operator: 'AND',
      field: 'skills',
      value: '',
    };
    setFilterRows([...filterRows, newRow]);
  };

  /**
   * Remove a filter row by ID
   */
  const removeFilterRow = (id: string) => {
    if (filterRows.length > 1) {
      setFilterRows(filterRows.filter((row) => row.id !== id));
    }
  };

  /**
   * Update a filter row
   */
  const updateFilterRow = (id: string, updates: Partial<FilterRow>) => {
    setFilterRows(
      filterRows.map((row) =>
        row.id === id ? { ...row, ...updates } : row
      )
    );
  };

  /**
   * Generate query string from filter rows
   */
  const generateQueryString = (): string => {
    const validRows = filterRows.filter((row) => row.value.trim() !== '');

    if (validRows.length === 0) {
      return '';
    }

    const queryParts: string[] = [];

    validRows.forEach((row, index) => {
      const fieldPrefix = `${row.field}:`;
      const value = row.value.includes(' ') ? `"${row.value}"` : row.value;
      const term = `${fieldPrefix}${value}`;

      if (index === 0) {
        // First row - no operator prefix needed unless it's NOT
        if (row.operator === 'NOT') {
          queryParts.push(`NOT ${term}`);
        } else {
          queryParts.push(term);
        }
      } else {
        // Subsequent rows - add operator
        if (row.operator === 'NOT') {
          queryParts.push(`AND NOT ${term}`);
        } else {
          queryParts.push(`${row.operator} ${term}`);
        }
      }
    });

    return queryParts.join(' ');
  };

  /**
   * Reset query builder to default state
   */
  const resetQueryBuilder = () => {
    setFilterRows([
      {
        id: `filter-${Date.now()}`,
        operator: 'AND',
        field: 'skills',
        value: '',
      },
    ]);
    setGeneratedQuery('');
  };

  /**
   * Copy query to clipboard
   */
  const copyQueryToClipboard = async () => {
    if (generatedQuery) {
      try {
        await navigator.clipboard.writeText(generatedQuery);
        setShowCopyNotification(true);
        setTimeout(() => setShowCopyNotification(false), 3000);
      } catch (err) {
        console.error('Failed to copy query:', err);
      }
    }
  };

  /**
   * Update generated query when filter rows change
   */
  useEffect(() => {
    const query = generateQueryString();
    setGeneratedQuery(query);
    if (onQueryChange) {
      onQueryChange(query);
    }
  }, [filterRows]);

  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        backgroundColor: 'background.paper',
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t('search.queryBuilder.title', 'Visual Query Builder')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t(
            'search.queryBuilder.description',
            'Build complex search queries visually without knowing boolean syntax'
          )}
        </Typography>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Filter Rows */}
      <Stack spacing={2} sx={{ mb: 3 }}>
        {filterRows.map((row, index) => (
          <Box key={row.id}>
            <Grid container spacing={2} alignItems="center">
              {/* Operator (hidden for first row if not NOT) */}
              <Grid item xs={12} sm={2}>
                {index === 0 && row.operator !== 'NOT' ? (
                  <Box sx={{ height: 56 }} />
                ) : (
                  <FormControl fullWidth size="small" disabled={disabled}>
                    <InputLabel>{t('search.queryBuilder.operator', 'Operator')}</InputLabel>
                    <Select
                      value={row.operator}
                      label={t('search.queryBuilder.operator', 'Operator')}
                      onChange={(e) =>
                        updateFilterRow(row.id, { operator: e.target.value as BooleanOperator })
                      }
                    >
                      {operatorOptions.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          <Chip
                            label={option.label}
                            size="small"
                            sx={{
                              backgroundColor: option.color,
                              color: 'white',
                              fontWeight: 'bold',
                            }}
                          />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              </Grid>

              {/* Field */}
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth size="small" disabled={disabled}>
                  <InputLabel>{t('search.queryBuilder.field', 'Field')}</InputLabel>
                  <Select
                    value={row.field}
                    label={t('search.queryBuilder.field', 'Field')}
                    onChange={(e) =>
                      updateFilterRow(row.id, { field: e.target.value as QueryField })
                    }
                  >
                    {fieldOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Value */}
              <Grid item xs={12} sm={5}>
                <TextField
                  fullWidth
                  size="small"
                  label={t('search.queryBuilder.value', 'Value')}
                  value={row.value}
                  onChange={(e) => updateFilterRow(row.id, { value: e.target.value })}
                  placeholder={t(
                    'search.queryBuilder.valuePlaceholder',
                    'Enter search value...'
                  )}
                  disabled={disabled}
                />
              </Grid>

              {/* Actions */}
              <Grid item xs={12} sm={2}>
                <Stack direction="row" spacing={1}>
                  <Tooltip title={t('search.queryBuilder.removeRow', 'Remove row')}>
                    <span>
                      <IconButton
                        color="error"
                        size="small"
                        onClick={() => removeFilterRow(row.id)}
                        disabled={disabled || filterRows.length === 1}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                  {index === filterRows.length - 1 && (
                    <Tooltip title={t('search.queryBuilder.addRow', 'Add row')}>
                      <IconButton
                        color="primary"
                        size="small"
                        onClick={addFilterRow}
                        disabled={disabled}
                      >
                        <AddIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </Stack>
              </Grid>
            </Grid>
          </Box>
        ))}
      </Stack>

      {/* Action Buttons */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={addFilterRow}
          disabled={disabled}
        >
          {t('search.queryBuilder.addFilter', 'Add Filter')}
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={resetQueryBuilder}
          disabled={disabled}
        >
          {t('search.queryBuilder.reset', 'Reset')}
        </Button>
      </Stack>

      <Divider sx={{ mb: 3 }} />

      {/* Generated Query Preview */}
      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {t('search.queryBuilder.generatedQuery', 'Generated Query')}
          </Typography>
          {generatedQuery && (
            <Tooltip title={t('search.queryBuilder.copyQuery', 'Copy query')}>
              <IconButton size="small" onClick={copyQueryToClipboard}>
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Stack>

        <Paper
          variant="outlined"
          sx={{
            p: 2,
            backgroundColor: 'grey.50',
            minHeight: 60,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            wordBreak: 'break-all',
          }}
        >
          {generatedQuery || (
            <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
              {t('search.queryBuilder.noQuery', 'No query generated yet. Add filters above.')}
            </Typography>
          )}
        </Paper>

        {/* Copy notification */}
        {showCopyNotification && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {t('search.queryBuilder.copiedToClipboard', 'Query copied to clipboard!')}
          </Alert>
        )}
      </Box>

      {/* Help Text */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          {t(
            'search.queryBuilder.helpText',
            'Tip: Use AND to require all conditions, OR for any condition, and NOT to exclude. Values with spaces will be automatically quoted.'
          )}
        </Typography>
      </Box>
    </Paper>
  );
};

export default QueryBuilder;
