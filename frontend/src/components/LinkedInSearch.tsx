import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
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
  Autocomplete,
  Typography,
  Card,
  CardContent,
  CardActions,
  CircularProgress,
  Alert,
  Stack,
  Pagination,
  Divider,
  IconButton,
  Checkbox,
} from '@mui/material';
import {
  Search as SearchIcon,
  LinkedIn as LinkedInIcon,
  PersonAdd as ImportIcon,
  Clear as ClearIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api';
import type {
  LinkedInProfileSummary,
  LinkedInSearchResponse,
  LinkedInProfileImportResponse,
} from '@/types/api';

/**
 * Experience level options for LinkedIn search
 */
type ExperienceLevel = 'entry' | 'associate' | 'mid' | 'senior' | 'director' | 'executive' | '';

/**
 * Search filters interface
 */
interface SearchFilters {
  keywords: string;
  skills: string[];
  location: string;
  industry: string;
  experienceLevel: ExperienceLevel;
}

/**
 * LinkedIn search state interface
 */
interface SearchState {
  loading: boolean;
  error: string | null;
  results: LinkedInProfileSummary[];
  totalResults: number;
  page: number;
  importing: Set<string>;
  importSuccess: string[];
  importErrors: Map<string, string>;
}

/**
 * Props for LinkedInSearch component
 */
interface LinkedInSearchProps {
  /** Callback when a profile is imported successfully */
  onProfileImported?: (profileId: string, resumeId: string) => void;
  /** Callback when search completes */
  onSearchComplete?: (resultCount: number) => void;
  /** Default search filters */
  defaultFilters?: Partial<SearchFilters>;
  /** Maximum results per page (default: 10, max: 50) */
  resultsPerPage?: number;
}

/**
 * LinkedInSearch Component
 *
 * Provides comprehensive LinkedIn candidate search functionality including:
 * - Multi-field filters (keywords, skills, location, industry, experience)
 * - Search results with profile summaries
 * - Individual and bulk profile import
 * - Pagination support
 * - Error handling and success states
 *
 * @example
 * ```tsx
 * <LinkedInSearch
 *   onProfileImported={(profileId, resumeId) => {
 *     console.log('Imported:', profileId, resumeId);
 *   }}
 *   onSearchComplete={(count) => {
 *     console.log('Found:', count, 'candidates');
 *   }}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // With default filters
 * <LinkedInSearch
 *   defaultFilters={{
 *     keywords: 'software engineer',
 *     skills: ['Python', 'React'],
 *     location: 'San Francisco',
 *   }}
 *   resultsPerPage={20}
 * />
 * ```
 */
const LinkedInSearch: React.FC<LinkedInSearchProps> = ({
  onProfileImported,
  onSearchComplete,
  defaultFilters = {},
  resultsPerPage = 10,
}) => {
  const { t } = useTranslation();

  // Search filters state
  const [filters, setFilters] = useState<SearchFilters>({
    keywords: defaultFilters.keywords || '',
    skills: defaultFilters.skills || [],
    location: defaultFilters.location || '',
    industry: defaultFilters.industry || '',
    experienceLevel: defaultFilters.experienceLevel || '',
  });

  // Search state
  const [searchState, setSearchState] = useState<SearchState>({
    loading: false,
    error: null,
    results: [],
    totalResults: 0,
    page: 1,
    importing: new Set<string>(),
    importSuccess: [],
    importErrors: new Map<string, string>(),
  });

  // Selected profiles for bulk import
  const [selectedProfiles, setSelectedProfiles] = useState<Set<string>>(new Set());

  // Available options
  const skillOptions = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue.js',
    'Node.js', 'Django', 'Flask', 'Spring', 'AWS', 'Azure', 'Docker', 'Kubernetes',
    'SQL', 'PostgreSQL', 'MongoDB', 'Redis', 'GraphQL', 'REST', 'Git', 'CI/CD',
  ];

  const locationOptions = [
    'Remote', 'New York', 'San Francisco', 'London', 'Berlin', 'Paris',
    'Tokyo', 'Singapore', 'Sydney', 'Toronto', 'Chicago', 'Boston',
  ];

  const industryOptions = [
    'Technology', 'Finance', 'Healthcare', 'Education', 'Manufacturing',
    'Retail', 'Consulting', 'Telecommunications', 'Energy', 'Transportation',
  ];

  const experienceLevelOptions: Array<{ value: ExperienceLevel; label: string }> = [
    { value: '', label: t('linkedin.search.any') },
    { value: 'entry', label: t('linkedin.search.experience.entry') },
    { value: 'associate', label: t('linkedin.search.experience.associate') },
    { value: 'mid', label: t('linkedin.search.experience.mid') },
    { value: 'senior', label: t('linkedin.search.experience.senior') },
    { value: 'director', label: t('linkedin.search.experience.director') },
    { value: 'executive', label: t('linkedin.search.experience.executive') },
  ];

  /**
   * Update a single filter
   */
  const updateFilter = useCallback(<K extends keyof SearchFilters>(
    key: K,
    value: SearchFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    // Clear errors when filters change
    if (searchState.error) {
      setSearchState((prev) => ({ ...prev, error: null }));
    }
  }, [searchState.error]);

  /**
   * Clear all filters
   */
  const clearFilters = useCallback(() => {
    setFilters({
      keywords: '',
      skills: [],
      location: '',
      industry: '',
      experienceLevel: '',
    });
    setSelectedProfiles(new Set());
    setSearchState((prev) => ({
      ...prev,
      results: [],
      totalResults: 0,
      error: null,
      page: 1,
    }));
  }, []);

  /**
   * Execute LinkedIn search
   */
  const handleSearch = useCallback(async () => {
    setSearchState((prev) => ({
      ...prev,
      loading: true,
      error: null,
      results: [],
      page: 1,
    }));

    try {
      const response: LinkedInSearchResponse = await apiClient.searchLinkedInProfiles(
        filters.keywords || undefined,
        filters.skills.length > 0 ? filters.skills : undefined,
        filters.location || undefined,
        filters.industry || undefined,
        filters.experienceLevel || undefined,
        resultsPerPage
      );

      setSearchState((prev) => ({
        ...prev,
        loading: false,
        results: response.results,
        totalResults: response.total_results,
      }));

      setSelectedProfiles(new Set());
      onSearchComplete?.(response.total_results);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : t('linkedin.search.errors.searchFailed');

      setSearchState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
        results: [],
        totalResults: 0,
      }));
    }
  }, [filters, resultsPerPage, onSearchComplete, t]);

  /**
   * Import a single LinkedIn profile
   */
  const handleImportProfile = useCallback(async (profile: LinkedInProfileSummary) => {
    // Add to importing set
    setSearchState((prev) => ({
      ...prev,
      importing: new Set(prev.importing).add(profile.profile_id),
      importErrors: new Map(prev.importErrors),
    }));

    try {
      const response: LinkedInProfileImportResponse = await apiClient.importLinkedInProfile({
        linkedin_url: profile.profile_url,
        profile_id: profile.profile_id,
      });

      if (response.success && response.resume_id) {
        // Add to success list
        setSearchState((prev) => ({
          ...prev,
          importSuccess: [...prev.importSuccess, profile.profile_id],
          importing: new Set([...prev.importing].filter(id => id !== profile.profile_id)),
        }));

        onProfileImported?.(profile.profile_id, response.resume_id);
      } else {
        throw new Error(response.message || t('linkedin.search.errors.importFailed'));
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : t('linkedin.search.errors.importFailed');

      setSearchState((prev) => {
        const newErrors = new Map(prev.importErrors);
        newErrors.set(profile.profile_id, errorMessage);
        return {
          ...prev,
          importErrors: newErrors,
          importing: new Set([...prev.importing].filter(id => id !== profile.profile_id)),
        };
      });
    }
  }, [onProfileImported, t]);

  /**
   * Import all selected profiles
   */
  const handleImportSelected = useCallback(async () => {
    if (selectedProfiles.size === 0) return;

    // Import all selected profiles sequentially
    for (const profileId of selectedProfiles) {
      const profile = searchState.results.find(p => p.profile_id === profileId);
      if (profile && !searchState.importing.has(profileId)) {
        await handleImportProfile(profile);
      }
    }
  }, [selectedProfiles, searchState.results, searchState.importing, handleImportProfile]);

  /**
   * Toggle profile selection
   */
  const toggleProfileSelection = useCallback((profileId: string) => {
    setSelectedProfiles((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(profileId)) {
        newSet.delete(profileId);
      } else {
        newSet.add(profileId);
      }
      return newSet;
    });
  }, []);

  /**
   * Toggle select all visible profiles
   */
  const toggleSelectAll = useCallback(() => {
    const visibleIds = searchState.results.map(p => p.profile_id);
    const allSelected = visibleIds.every(id => selectedProfiles.has(id));

    if (allSelected) {
      // Deselect all visible
      setSelectedProfiles((prev) => {
        const newSet = new Set(prev);
        visibleIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    } else {
      // Select all visible
      setSelectedProfiles((prev) => {
        const newSet = new Set(prev);
        visibleIds.forEach(id => newSet.add(id));
        return newSet;
      });
    }
  }, [searchState.results, selectedProfiles]);

  /**
   * Calculate total pages
   */
  const totalPages = Math.ceil(searchState.totalResults / resultsPerPage);

  /**
   * Render a single search result card
   */
  const renderProfileCard = (profile: LinkedInProfileSummary) => {
    const isSelected = selectedProfiles.has(profile.profile_id);
    const isImporting = searchState.importing.has(profile.profile_id);
    const isSuccess = searchState.importSuccess.includes(profile.profile_id);
    const hasError = searchState.importErrors.has(profile.profile_id);

    return (
      <Grid item xs={12} sm={6} md={4} key={profile.profile_id}>
        <Card
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            border: isSelected ? '2px solid' : '1px solid',
            borderColor: isSelected ? 'primary.main' : 'divider',
            position: 'relative',
          }}
        >
          {/* Selection Checkbox */}
          <Checkbox
            checked={isSelected}
            onChange={() => toggleProfileSelection(profile.profile_id)}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              bgcolor: 'background.paper',
              borderRadius: 1,
            }}
          />

          {/* Status Indicator */}
          {isSuccess && (
            <Box
              sx={{
                position: 'absolute',
                top: 8,
                left: 8,
                color: 'success.main',
              }}
            >
              <SuccessIcon />
            </Box>
          )}

          <CardContent sx={{ flexGrow: 1 }}>
            {/* Profile Name */}
            <Typography variant="h6" gutterBottom fontWeight={600}>
              {profile.first_name} {profile.last_name}
            </Typography>

            {/* Headline */}
            {profile.headline && (
              <Typography
                variant="body2"
                color="text.secondary"
                gutterBottom
                sx={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {profile.headline}
              </Typography>
            )}

            {/* Location */}
            {profile.location && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                📍 {profile.location}
              </Typography>
            )}

            {/* Industry */}
            {profile.industry && (
              <Typography variant="body2" color="text.secondary">
                💼 {profile.industry}
              </Typography>
            )}

            {/* Error Message */}
            {hasError && (
              <Alert severity="error" sx={{ mt: 2 }} icon={<ErrorIcon fontSize="inherit" />}>
                {searchState.importErrors.get(profile.profile_id)}
              </Alert>
            )}
          </CardContent>

          <Divider />

          <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1 }}>
            {/* View on LinkedIn Link */}
            <Button
              size="small"
              startIcon={<LinkedInIcon />}
              href={profile.profile_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t('linkedin.search.viewProfile')}
            </Button>

            {/* Import Button */}
            <Button
              size="small"
              variant="contained"
              startIcon={
                isImporting ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <ImportIcon />
                )
              }
              onClick={() => handleImportProfile(profile)}
              disabled={isImporting || isSuccess}
              color={isSuccess ? 'success' : 'primary'}
            >
              {isImporting
                ? t('linkedin.search.importing')
                : isSuccess
                  ? t('linkedin.search.imported')
                  : t('linkedin.search.import')}
            </Button>
          </CardActions>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: 3,
          }}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            <LinkedInIcon color="primary" sx={{ fontSize: 32 }} />
            <Typography variant="h5" fontWeight={600}>
              {t('linkedin.search.title')}
            </Typography>
          </Stack>
          <IconButton
            onClick={clearFilters}
            disabled={searchState.loading}
            title={t('linkedin.search.clearFilters')}
          >
            <ClearIcon />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {/* Search Filters */}
        <Grid container spacing={2}>
          {/* Keywords */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label={t('linkedin.search.keywords')}
              placeholder={t('linkedin.search.keywordsPlaceholder')}
              value={filters.keywords}
              onChange={(e) => updateFilter('keywords', e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
              disabled={searchState.loading}
            />
          </Grid>

          {/* Location */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={locationOptions}
              value={filters.location}
              onChange={(_, newValue) => updateFilter('location', newValue || '')}
              renderInput={(params) => (
                <TextField {...params} label={t('linkedin.search.location')} />
              )}
              freeSolo
              disabled={searchState.loading}
            />
          </Grid>

          {/* Skills */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              options={skillOptions}
              value={filters.skills}
              onChange={(_, newValue) => updateFilter('skills', newValue)}
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
                  label={t('linkedin.search.skills')}
                  placeholder={t('linkedin.search.selectSkills')}
                />
              )}
              disabled={searchState.loading}
            />
          </Grid>

          {/* Industry */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              options={industryOptions}
              value={filters.industry}
              onChange={(_, newValue) => updateFilter('industry', newValue || '')}
              renderInput={(params) => (
                <TextField {...params} label={t('linkedin.search.industry')} />
              )}
              freeSolo
              disabled={searchState.loading}
            />
          </Grid>

          {/* Experience Level */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>{t('linkedin.search.experienceLevel')}</InputLabel>
              <Select
                value={filters.experienceLevel}
                label={t('linkedin.search.experienceLevel')}
                onChange={(e) => updateFilter('experienceLevel', e.target.value as ExperienceLevel)}
                disabled={searchState.loading}
              >
                {experienceLevelOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Search Button */}
          <Grid item xs={12} md={6}>
            <Button
              fullWidth
              variant="contained"
              size="large"
              startIcon={
                searchState.loading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <SearchIcon />
                )
              }
              onClick={handleSearch}
              disabled={searchState.loading}
            >
              {searchState.loading
                ? t('linkedin.search.searching')
                : t('linkedin.search.search')}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Alert */}
      {searchState.error && (
        <Alert
          severity="error"
          icon={<ErrorIcon />}
          sx={{ mb: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => setSearchState((prev) => ({ ...prev, error: null }))}
            >
              {t('common.dismiss')}
            </Button>
          }
        >
          {searchState.error}
        </Alert>
      )}

      {/* Results Section */}
      {searchState.results.length > 0 && (
        <Box>
          {/* Results Header */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              justifyContent="space-between"
            >
              <Typography variant="h6" fontWeight={600}>
                {t('linkedin.search.resultsTitle', {
                  count: searchState.totalResults,
                })}
              </Typography>

              <Stack direction="row" spacing={2}>
                {/* Select All Checkbox */}
                <Button
                  variant="outlined"
                  size="small"
                  onClick={toggleSelectAll}
                  disabled={searchState.loading}
                >
                  {t('linkedin.search.selectAll')}
                </Button>

                {/* Import Selected Button */}
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<ImportIcon />}
                  onClick={handleImportSelected}
                  disabled={selectedProfiles.size === 0 || searchState.loading}
                >
                  {t('linkedin.search.importSelected', {
                    count: selectedProfiles.size,
                  })}
                </Button>
              </Stack>
            </Stack>
          </Paper>

          {/* Results Grid */}
          <Grid container spacing={2}>
            {searchState.results.map(renderProfileCard)}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={searchState.page}
                onChange={(_, page) => setSearchState((prev) => ({ ...prev, page }))}
                color="primary"
                size="large"
                disabled={searchState.loading}
              />
            </Box>
          )}
        </Box>
      )}

      {/* No Results */}
      {!searchState.loading && !searchState.error && searchState.results.length === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <LinkedInIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('linkedin.search.noResults')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('linkedin.search.adjustFilters')}
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default LinkedInSearch;
