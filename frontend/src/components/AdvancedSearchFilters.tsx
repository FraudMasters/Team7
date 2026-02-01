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
  Slider,
  Checkbox,
  FormControlLabel,
  Stack,
  Collapse,
  IconButton,
  Divider,
  Autocomplete,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Clear as ClearIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

/**
 * Boolean operator types for search queries
 */
type BooleanOperator = 'AND' | 'OR' | 'NOT';

/**
 * Education level options
 */
type EducationLevel = 'high_school' | 'bachelor' | 'master' | 'phd' | 'any';

/**
 * Sort options for search results
 */
type SortOption = 'relevance' | 'date' | 'experience';

/**
 * Filter group for building complex boolean queries
 */
interface FilterGroup {
  id: string;
  operator: BooleanOperator;
  field: string;
  value: string;
}

/**
 * Search filters interface
 */
interface SearchFilters {
  skills: string[];
  minExperienceYears: number;
  maxExperienceYears: number;
  location: string;
  educationLevel: EducationLevel;
  languages: string[];
  minMatchScore: number;
  maxMatchScore: number;
  minSalaryExpectation?: number;
  maxSalaryExpectation?: number;
  dateFrom?: Date | null;
  dateTo?: Date | null;
  vacancyId?: string;
  stageId?: string;
}

/**
 * Props for AdvancedSearchFilters component
 */
interface AdvancedSearchFiltersProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  loading?: boolean;
  vacancies?: Array<{ id: string; title: string }>;
  stages?: Array<{ id: string; name: string }>;
  defaultFilters?: Partial<SearchFilters>;
}

/**
 * Advanced Search Filters Component
 *
 * Provides comprehensive filtering capabilities for candidate search including:
 * - Multi-field filters (skills, experience, education, location, languages, match score)
 * - Range filters (experience years, match score %, salary expectations, date ranges)
 * - Boolean operators (AND, OR, NOT) for complex queries
 * - Saved filter combinations
 */
const AdvancedSearchFilters: React.FC<AdvancedSearchFiltersProps> = ({
  onSearch,
  loading = false,
  vacancies = [],
  stages = [],
  defaultFilters = {},
}) => {
  const { t } = useTranslation();

  // Search query state
  const [searchQuery, setSearchQuery] = useState('');

  // Filter groups for boolean queries
  const [filterGroups, setFilterGroups] = useState<FilterGroup[]>([]);

  // Range filters state
  const [minExperience, setMinExperience] = useState<number>(defaultFilters.minExperienceYears || 0);
  const [maxExperience, setMaxExperience] = useState<number>(defaultFilters.maxExperienceYears || 20);
  const [minMatchScore, setMinMatchScore] = useState<number>(defaultFilters.minMatchScore || 0);
  const [maxMatchScore, setMaxMatchScore] = useState<number>(defaultFilters.maxMatchScore || 100);

  // Select filters state
  const [location, setLocation] = useState<string>(defaultFilters.location || '');
  const [educationLevel, setEducationLevel] = useState<EducationLevel>(
    defaultFilters.educationLevel || 'any'
  );
  const [selectedSkills, setSelectedSkills] = useState<string[]>(defaultFilters.skills || []);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(defaultFilters.languages || []);

  // Date range filters
  const [dateFrom, setDateFrom] = useState<Date | null>(defaultFilters.dateFrom || null);
  const [dateTo, setDateTo] = useState<Date | null>(defaultFilters.dateTo || null);

  // Salary range filters
  const [minSalary, setMinSalary] = useState<number | undefined>(defaultFilters.minSalaryExpectation);
  const [maxSalary, setMaxSalary] = useState<number | undefined>(defaultFilters.maxSalaryExpectation);

  // Additional filters
  const [selectedVacancy, setSelectedVacancy] = useState<string>(defaultFilters.vacancyId || '');
  const [selectedStage, setSelectedStage] = useState<string>(defaultFilters.stageId || '');

  // UI state
  const [expanded, setExpanded] = useState(true);

  // Available options (these could come from API in the future)
  const skillOptions = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
    'Node.js', 'Django', 'Flask', 'Spring', 'AWS', 'Azure', 'Docker', 'Kubernetes',
    'SQL', 'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST', 'Git', 'CI/CD',
  ];

  const languageOptions = [
    'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Portuguese',
    'Russian', 'Arabic', 'Hindi', 'Italian', 'Dutch', 'Polish', 'Korean',
  ];

  const locationOptions = [
    'Remote', 'New York', 'San Francisco', 'London', 'Berlin', 'Paris',
    'Tokyo', 'Singapore', 'Sydney', 'Toronto', 'Chicago', 'Boston',
  ];

  /**
   * Add a new filter group for boolean query
   */
  const addFilterGroup = () => {
    const newGroup: FilterGroup = {
      id: `filter-${Date.now()}`,
      operator: 'AND',
      field: 'skills',
      value: '',
    };
    setFilterGroups([...filterGroups, newGroup]);
  };

  /**
   * Remove a filter group
   */
  const removeFilterGroup = (id: string) => {
    setFilterGroups(filterGroups.filter((group) => group.id !== id));
  };

  /**
   * Update a filter group
   */
  const updateFilterGroup = (id: string, updates: Partial<FilterGroup>) => {
    setFilterGroups(
      filterGroups.map((group) =>
        group.id === id ? { ...group, ...updates } : group
      )
    );
  };

  /**
   * Build boolean query string from filter groups
   */
  const buildBooleanQuery = (): string => {
    if (filterGroups.length === 0) return searchQuery;

    const queryParts = filterGroups.map((group) => {
      const prefix = group.operator === 'NOT' ? 'NOT ' : '';
      return `${prefix}${group.field}:${group.value}`;
    });

    const baseQuery = searchQuery.trim();
    const booleanQuery = queryParts.join(' ');

    return baseQuery ? `${baseQuery} ${booleanQuery}` : booleanQuery;
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setSearchQuery('');
    setFilterGroups([]);
    setMinExperience(0);
    setMaxExperience(20);
    setMinMatchScore(0);
    setMaxMatchScore(100);
    setLocation('');
    setEducationLevel('any');
    setSelectedSkills([]);
    setSelectedLanguages([]);
    setDateFrom(null);
    setDateTo(null);
    setMinSalary(undefined);
    setMaxSalary(undefined);
    setSelectedVacancy('');
    setSelectedStage('');
  };

  /**
   * Handle search execution
   */
  const handleSearch = () => {
    const query = buildBooleanQuery();
    const filters: SearchFilters = {
      skills: selectedSkills,
      minExperienceYears: minExperience,
      maxExperienceYears: maxExperience,
      location,
      educationLevel,
      languages: selectedLanguages,
      minMatchScore,
      maxMatchScore,
      minSalaryExpectation: minSalary,
      maxSalaryExpectation: maxSalary,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      vacancyId: selectedVacancy || undefined,
      stageId: selectedStage || undefined,
    };

    onSearch(query, filters);
  };

  /**
   * Render a single filter group row
   */
  const renderFilterGroup = (group: FilterGroup) => (
    <Grid item xs={12} key={group.id}>
      <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>Operator</InputLabel>
            <Select
              value={group.operator}
              label="Operator"
              onChange={(e) => updateFilterGroup(group.id, { operator: e.target.value as BooleanOperator })}
            >
              <MenuItem value="AND">AND</MenuItem>
              <MenuItem value="OR">OR</MenuItem>
              <MenuItem value="NOT">NOT</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Field</InputLabel>
            <Select
              value={group.field}
              label="Field"
              onChange={(e) => updateFilterGroup(group.id, { field: e.target.value })}
            >
              <MenuItem value="skills">Skills</MenuItem>
              <MenuItem value="location">Location</MenuItem>
              <MenuItem value="education">Education</MenuItem>
              <MenuItem value="languages">Languages</MenuItem>
            </Select>
          </FormControl>

          <TextField
            size="small"
            label="Value"
            value={group.value}
            onChange={(e) => updateFilterGroup(group.id, { value: e.target.value })}
            sx={{ flex: 1 }}
          />

          <IconButton
            size="small"
            color="error"
            onClick={() => removeFilterGroup(group.id)}
          >
            <DeleteIcon />
          </IconButton>
        </Stack>
      </Paper>
    </Grid>
  );

  return (
    <Paper sx={{ mb: 3 }}>
        {/* Header */}
        <Box
          sx={{
            px: 3,
            py: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
          }}
          onClick={() => setExpanded(!expanded)}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            <FilterIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              {t('advancedSearch.title')}
            </Typography>
            {filterGroups.length > 0 && (
              <Chip
                label={`${filterGroups.length} ${t('advancedSearch.filters')}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Stack>
          <IconButton size="small">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Divider />

        {/* Filters Content */}
        <Collapse in={expanded}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* Main Search Query */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('advancedSearch.searchQuery')}
                  placeholder={t('advancedSearch.searchPlaceholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                  InputProps={{
                    endAdornment: (
                      <IconButton
                        size="small"
                        onClick={clearFilters}
                        disabled={!searchQuery && filterGroups.length === 0}
                      >
                        <ClearIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Grid>

              {/* Boolean Query Builder */}
              {filterGroups.map(renderFilterGroup)}

              <Grid item xs={12}>
                <Button
                  startIcon={<AddIcon />}
                  onClick={addFilterGroup}
                  variant="outlined"
                  size="small"
                >
                  {t('advancedSearch.addFilter')}
                </Button>
              </Grid>

              {/* Skills Filter */}
              <Grid item xs={12} md={6}>
                <Autocomplete
                  multiple
                  options={skillOptions}
                  value={selectedSkills}
                  onChange={(_, newValue) => setSelectedSkills(newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option}
                        {...getTagProps({ index })}
                        key={option}
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('advancedSearch.skills')}
                      placeholder={t('advancedSearch.selectSkills')}
                    />
                  )}
                />
              </Grid>

              {/* Location Filter */}
              <Grid item xs={12} md={6}>
                <Autocomplete
                  options={locationOptions}
                  value={location}
                  onChange={(_, newValue) => setLocation(newValue || '')}
                  renderInput={(params) => (
                    <TextField {...params} label={t('advancedSearch.location')} />
                  )}
                  freeSolo
                />
              </Grid>

              {/* Languages Filter */}
              <Grid item xs={12} md={6}>
                <Autocomplete
                  multiple
                  options={languageOptions}
                  value={selectedLanguages}
                  onChange={(_, newValue) => setSelectedLanguages(newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option}
                        {...getTagProps({ index })}
                        key={option}
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('advancedSearch.languages')}
                      placeholder={t('advancedSearch.selectLanguages')}
                    />
                  )}
                />
              </Grid>

              {/* Education Level Filter */}
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('advancedSearch.educationLevel')}</InputLabel>
                  <Select
                    value={educationLevel}
                    label={t('advancedSearch.educationLevel')}
                    onChange={(e) => setEducationLevel(e.target.value as EducationLevel)}
                  >
                    <MenuItem value="any">{t('advancedSearch.any')}</MenuItem>
                    <MenuItem value="high_school">{t('advancedSearch.highSchool')}</MenuItem>
                    <MenuItem value="bachelor">{t('advancedSearch.bachelor')}</MenuItem>
                    <MenuItem value="master">{t('advancedSearch.master')}</MenuItem>
                    <MenuItem value="phd">{t('advancedSearch.phd')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Experience Years Range */}
              <Grid item xs={12} md={6}>
                <Box sx={{ px: 1 }}>
                  <Typography variant="body2" gutterBottom>
                    {t('advancedSearch.experienceYears', {
                      min: minExperience,
                      max: maxExperience,
                    })}
                  </Typography>
                  <Slider
                    value={[minExperience, maxExperience]}
                    onChange={(_, value) => {
                      setMinExperience(value[0]);
                      setMaxExperience(value[1]);
                    }}
                    min={0}
                    max={20}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 5, label: '5' },
                      { value: 10, label: '10' },
                      { value: 15, label: '15' },
                      { value: 20, label: '20+' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>
              </Grid>

              {/* Match Score Range */}
              <Grid item xs={12} md={6}>
                <Box sx={{ px: 1 }}>
                  <Typography variant="body2" gutterBottom>
                    {t('advancedSearch.matchScore', {
                      min: minMatchScore,
                      max: maxMatchScore,
                    })}
                  </Typography>
                  <Slider
                    value={[minMatchScore, maxMatchScore]}
                    onChange={(_, value) => {
                      setMinMatchScore(value[0]);
                      setMaxMatchScore(value[1]);
                    }}
                    min={0}
                    max={100}
                    marks={[
                      { value: 0, label: '0%' },
                      { value: 50, label: '50%' },
                      { value: 100, label: '100%' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>
              </Grid>

              {/* Date Range */}
              <Grid item xs={12} md={6}>
                <Stack direction="row" spacing={2}>
                  <TextField
                    fullWidth
                    label={t('advancedSearch.dateFrom')}
                    type="date"
                    value={dateFrom ? dateFrom.toISOString().split('T')[0] : ''}
                    onChange={(e) => setDateFrom(e.target.value ? new Date(e.target.value) : null)}
                    InputLabelProps={{ shrink: true }}
                  />
                  <TextField
                    fullWidth
                    label={t('advancedSearch.dateTo')}
                    type="date"
                    value={dateTo ? dateTo.toISOString().split('T')[0] : ''}
                    onChange={(e) => setDateTo(e.target.value ? new Date(e.target.value) : null)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Stack>
              </Grid>

              {/* Salary Range */}
              <Grid item xs={12} md={6}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <TextField
                    fullWidth
                    label={t('advancedSearch.minSalary')}
                    type="number"
                    value={minSalary || ''}
                    onChange={(e) => setMinSalary(e.target.value ? parseInt(e.target.value) : undefined)}
                    InputProps={{
                      startAdornment: <Typography variant="body2">$</Typography>,
                    }}
                  />
                  <Typography variant="body2">-</Typography>
                  <TextField
                    fullWidth
                    label={t('advancedSearch.maxSalary')}
                    type="number"
                    value={maxSalary || ''}
                    onChange={(e) => setMaxSalary(e.target.value ? parseInt(e.target.value) : undefined)}
                    InputProps={{
                      startAdornment: <Typography variant="body2">$</Typography>,
                    }}
                  />
                </Stack>
              </Grid>

              {/* Vacancy Filter */}
              {vacancies.length > 0 && (
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>{t('advancedSearch.vacancy')}</InputLabel>
                    <Select
                      value={selectedVacancy}
                      label={t('advancedSearch.vacancy')}
                      onChange={(e) => setSelectedVacancy(e.target.value)}
                    >
                      <MenuItem value="">{t('advancedSearch.allVacancies')}</MenuItem>
                      {vacancies.map((vacancy) => (
                        <MenuItem key={vacancy.id} value={vacancy.id}>
                          {vacancy.title}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              )}

              {/* Stage Filter */}
              {stages.length > 0 && (
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>{t('advancedSearch.stage')}</InputLabel>
                    <Select
                      value={selectedStage}
                      label={t('advancedSearch.stage')}
                      onChange={(e) => setSelectedStage(e.target.value)}
                    >
                      <MenuItem value="">{t('advancedSearch.allStages')}</MenuItem>
                      {stages.map((stage) => (
                        <MenuItem key={stage.id} value={stage.id}>
                          {stage.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              )}

              {/* Action Buttons */}
              <Grid item xs={12}>
                <Stack direction="row" spacing={2} justifyContent="flex-end">
                  <Button
                    variant="outlined"
                    onClick={clearFilters}
                    startIcon={<ClearIcon />}
                  >
                    {t('advancedSearch.clear')}
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleSearch}
                    startIcon={<SearchIcon />}
                    disabled={loading}
                  >
                    {loading ? t('advancedSearch.searching') : t('advancedSearch.search')}
                  </Button>
                </Stack>
              </Grid>
            </Grid>
          </Box>
        </Collapse>
      </Paper>
    );
  };

export default AdvancedSearchFilters;
