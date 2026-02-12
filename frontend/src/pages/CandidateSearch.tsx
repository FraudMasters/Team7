import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Slider,
  FormControlLabel,
  Checkbox,
  ToggleButtonGroup,
  ToggleButton,
  Stack,
  LinearProgress,
  Tooltip,
  Tabs,
  Tab,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Work as WorkIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as AIIcon,
  PsychologyAlt,
  Star as StarIcon,
  FilterList as FilterIcon,
  BookmarkBorder as SavedSearchIcon,
  History as HistoryIcon,
  Download as DownloadIcon,
  AutoAwesome as AISuggestionsIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { RankedCandidate } from '../types/api';
import AdvancedSearchFilters from '../components/AdvancedSearchFilters';
import SavedSearchManager from '../components/SavedSearchManager';
import SearchHistory from '../components/SearchHistory';
import AIFilterSuggestions from '../components/AIFilterSuggestions';
import type { SavedSearchResponse } from '../types/api';

interface Resume {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  skills: string[];
}

interface Vacancy {
  id: string;
  title: string;
  required_skills: string[];
  location?: string;
}

interface CandidateWithMatch extends Resume {
  matchPercentage: number;
  matchedSkills: string[];
  missingSkills: string[];
  vacancyTitle: string;
  rankingScore?: number;
  hireProbability?: number;
  isTopRecommendation?: boolean;
  modelVersion?: string;
  semanticScore?: number;
  semanticSimilarity?: number;
  semanticPassed?: boolean;
}

/**
 * Tab panel type
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * Tab panel component
 */
const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

/**
 * Candidate Search Page (Recruiter Module)
 *
 * Allows recruiters to search for candidates by skills and find the best matches for their vacancies.
 * Now with advanced search filters, saved searches, and search history.
 */
type SortBy = 'match' | 'ranking';
type SearchTab = 'search' | 'saved' | 'history' | 'ai';

const CandidateSearchPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [minMatchPercentage, setMinMatchPercentage] = useState<number>(30);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [candidates, setCandidates] = useState<CandidateWithMatch[]>([]);
  const [selectedVacancy, setSelectedVacancy] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [sortBy, setSortBy] = useState<SortBy>('ranking');
  const [usingAIRanking, setUsingAIRanking] = useState(true);
  const [rankingData, setRankingData] = useState<Record<string, RankedCandidate>>({});

  // Advanced search state
  const [currentTab, setCurrentTab] = useState<SearchTab>('search');
  const [advancedSearchEnabled, setAdvancedSearchEnabled] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Store last search parameters for export
  const [lastSearchParams, setLastSearchParams] = useState<{
    query: string;
    filters: any;
    useSemanticSearch: boolean;
  } | null>(null);

  // Load vacancies on mount
  useEffect(() => {
    const fetchVacancies = async () => {
      try {
        const response = await axios.get('/api/vacancies/?limit=50');
        setVacancies(response.data);
        if (response.data.length > 0) {
          setSelectedVacancy(response.data[0].id);
        }
      } catch (error) {
        console.error('Error fetching vacancies:', error);
      }
    };
    fetchVacancies();
  }, []);

  // Load resumes for search
  useEffect(() => {
    const fetchResumes = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/resumes/?limit=100');
        setResumes(response.data);
      } catch (error) {
        console.error('Error fetching resumes:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchResumes();
  }, []);

  /**
   * Handle advanced search from AdvancedSearchFilters component
   */
  const handleAdvancedSearch = async (query: string, filters: any) => {
    setSearching(true);
    setSearched(true);
    setSearchError(null);
    setCurrentTab('search');

    try {
      // Call the advanced search API (microservice endpoint)
      const useSemanticSearch = filters.semanticSearch || false;
      const response = await axios.post('/api/candidates/search', {
        query,
        filters: {
          ...filters,
          vacancy_id: filters.vacancyId || selectedVacancy,
        },
        use_semantic_search: useSemanticSearch,
        limit: 100,
      });

      // Store search parameters for export
      setLastSearchParams({
        query,
        filters: {
          ...filters,
          vacancy_id: filters.vacancyId || selectedVacancy,
        },
        useSemanticSearch,
      });

      // Transform results to match our candidate format
      const results: CandidateWithMatch[] = response.data.results.map((result: any) => ({
        ...result,
        matchPercentage: result.match_score || result.match_percentage || 0,
        matchedSkills: result.matched_skills || [],
        missingSkills: result.missing_skills || [],
        vacancyTitle: result.vacancy_title || vacancies.find((v) => v.id === selectedVacancy)?.title || '',
        semanticScore: result.semantic_score,
        semanticSimilarity: result.semantic_similarity,
        semanticPassed: result.semantic_passed,
      }));

      setCandidates(results);
    } catch (error: any) {
      console.error('Error in advanced search:', error);
      setSearchError(error.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  /**
   * Handle saved search selection
   */
  const handleSavedSearchSelect = (search: SavedSearchResponse) => {
    setAdvancedSearchEnabled(true);
    handleAdvancedSearch(search.query, search.filters || {});
  };

  /**
   * Handle search history repeat
   */
  const handleHistoryRepeat = (query: string | null, filters: Record<string, unknown>) => {
    setAdvancedSearchEnabled(true);
    handleAdvancedSearch(query || '', filters);
  };

  /**
   * Handle AI filter suggestions - apply filters from AI analysis
   */
  const handleAIFilterApply = (filters: Record<string, unknown>) => {
    setAdvancedSearchEnabled(true);
    setCurrentTab('search');
    // Use the filters directly with an empty query since the filters contain all the search criteria
    handleAdvancedSearch('', filters);
  };

  const handleSearch = async () => {
    if (!selectedVacancy) {
      alert(t('candidateSearch.selectVacancyFirst'));
      return;
    }

    setSearching(true);
    setSearched(true);
    setRankingData({});
    setSearchError(null);

    try {
      // Get match results for the selected vacancy
      const vacancy = vacancies.find((v) => v.id === selectedVacancy);
      if (!vacancy) return;

      const results: CandidateWithMatch[] = [];

      // Fetch AI ranking if enabled
      let aiRankings: Record<string, RankedCandidate> = {};
      if (usingAIRanking) {
        try {
          const rankingResponse = await axios.post<{
            ranked_candidates: RankedCandidate[];
          }>('/api/ranking/rank', {
            vacancy_id: selectedVacancy,
            limit: 100,
          });
          rankingResponse.data.ranked_candidates.forEach((candidate) => {
            aiRankings[candidate.resume_id] = candidate;
          });
          setRankingData(aiRankings);
        } catch (rankingError) {
          console.warn('AI ranking not available, falling back to match percentage:', rankingError);
          setUsingAIRanking(false);
        }
      }

      for (const resume of resumes) {
        try {
          const response = await axios.get(
            `/api/vacancies/match/${selectedVacancy}?resume_id=${resume.id}`
          );

          if (response.data && response.data.match_percentage >= minMatchPercentage) {
            const aiRanking = aiRankings[resume.id];
            results.push({
              ...resume,
              matchPercentage: response.data.match_percentage,
              matchedSkills: response.data.matched_skills?.map((s: any) =>
                typeof s === 'string' ? s : s.skill
              ) || [],
              missingSkills: response.data.missing_skills?.map((s: any) =>
                typeof s === 'string' ? s : s.skill
              ) || [],
              vacancyTitle: response.data.vacancy_title || vacancy.title,
              rankingScore: aiRanking?.ranking_score,
              hireProbability: aiRanking?.hire_probability,
              isTopRecommendation: aiRanking?.is_top_recommendation,
              modelVersion: aiRanking ? 'AI' : undefined,
            });
          }
        } catch (e) {
          // Skip failed matches
        }
      }

      // Sort by selected criteria
      const sortedResults = [...results].sort((a, b) => {
        if (sortBy === 'ranking') {
          // Sort by AI ranking score if available, otherwise fall back to match percentage
          const aScore = a.rankingScore ?? a.matchPercentage;
          const bScore = b.rankingScore ?? b.matchPercentage;
          return bScore - aScore;
        } else {
          return b.matchPercentage - a.matchPercentage;
        }
      });

      setCandidates(sortedResults);

      // Store search parameters for export (basic search doesn't use the /search endpoint,
      // but we can construct equivalent parameters)
      setLastSearchParams({
        query: '',
        filters: {
          vacancy_id: selectedVacancy,
          min_match_score: minMatchPercentage,
        },
        useSemanticSearch: false,
      });
    } catch (error) {
      console.error('Error searching:', error);
      setSearchError('Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const filterBySkills = (candidates: CandidateWithMatch[]) => {
    if (!searchQuery.trim()) return candidates;

    const query = searchQuery.toLowerCase();
    return candidates.filter(
      (c) =>
        c.matchedSkills.some((s) => s.toLowerCase().includes(query)) ||
        c.vacancyTitle.toLowerCase().includes(query)
    );
  };

  const displayedCandidates = filterBySkills(candidates);

  const getMatchColor = (percentage: number) => {
    if (percentage >= 70) return 'success';
    if (percentage >= 50) return 'warning';
    return 'error';
  };

  /**
   * Export candidates to CSV (client-side generation)
   */
  const handleExportCSV = () => {
    if (candidates.length === 0) {
      setSearchError('No search results to export. Please perform a search first.');
      return;
    }

    try {
      // CSV headers
      const headers = [
        'Rank',
        'Filename',
        'Vacancy',
        'Match Percentage',
        'Matched Skills',
        'Missing Skills',
        'AI Ranking Score',
        'Hire Probability',
        'Semantic Score',
      ];

      // Convert candidates to CSV rows
      const rows = candidates.map((candidate, index) => [
        index + 1,
        `"${candidate.filename.replace(/"/g, '""')}"`,
        `"${candidate.vacancyTitle.replace(/"/g, '""')}"`,
        candidate.matchPercentage,
        `"${candidate.matchedSkills.join(', ').replace(/"/g, '""')}"`,
        `"${candidate.missingSkills.join(', ').replace(/"/g, '""')}"`,
        candidate.rankingScore ?? 'N/A',
        candidate.hireProbability ? `${Math.round(candidate.hireProbability * 100)}%` : 'N/A',
        candidate.semanticScore ? `${Math.round(candidate.semanticScore * 100)}%` : 'N/A',
      ]);

      // Combine headers and rows
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(',')),
      ].join('\n');

      // Add BOM for Excel compatibility
      const bom = '\uFEFF';
      const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);

      // Generate filename based on query or vacancy
      const sanitizedName = (lastSearchParams?.query || selectedVacancy || 'search')
        .replace(/[^a-zA-Z0-9\s\-_]/g, '')
        .trim()
        .substring(0, 50);
      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `candidates_${sanitizedName}_${timestamp}.csv`);

      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      setSearchError('Export failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('candidateSearch.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          {t('candidateSearch.subtitle')}
        </Typography>

        {/* Search Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={currentTab === 'search' ? 0 : currentTab === 'saved' ? 1 : currentTab === 'history' ? 2 : 3}
            onChange={(_, newValue) => {
              setCurrentTab(newValue === 0 ? 'search' : newValue === 1 ? 'saved' : newValue === 2 ? 'history' : 'ai');
            }}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab
              icon={<SearchIcon />}
              label="Search"
              sx={{ textTransform: 'none' }}
            />
            <Tab
              icon={<SavedSearchIcon />}
              label="Saved Searches"
              sx={{ textTransform: 'none' }}
            />
            <Tab
              icon={<HistoryIcon />}
              label="Search History"
              sx={{ textTransform: 'none' }}
            />
            <Tab
              icon={<AISuggestionsIcon />}
              label="AI Suggestions"
              sx={{ textTransform: 'none' }}
            />
          </Tabs>

          {/* Search Tab */}
          <TabPanel value={0} index={currentTab === 'search' ? 0 : -1}>
            <Box sx={{ px: 2 }}>
              {/* Toggle Advanced Search */}
              <Box sx={{ mb: 2 }}>
                <Button
                  variant={advancedSearchEnabled ? 'contained' : 'outlined'}
                  startIcon={<FilterIcon />}
                  onClick={() => setAdvancedSearchEnabled(!advancedSearchEnabled)}
                  size="small"
                >
                  {advancedSearchEnabled ? 'Advanced Filters Enabled' : 'Enable Advanced Filters'}
                </Button>
              </Box>

              {/* Advanced Search Filters */}
              {advancedSearchEnabled && (
                <AdvancedSearchFilters
                  onSearch={handleAdvancedSearch}
                  loading={searching}
                  vacancies={vacancies.map((v) => ({ id: v.id, title: v.title }))}
                  defaultFilters={{
                    vacancyId: selectedVacancy,
                    minMatchScore: minMatchPercentage,
                  }}
                />
              )}

              {/* Error Display */}
              {searchError && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setSearchError(null)}>
                  {searchError}
                </Alert>
              )}
            </Box>
          </TabPanel>

          {/* Saved Searches Tab */}
          <TabPanel value={1} index={currentTab === 'saved' ? 1 : -1}>
            <SavedSearchManager
              onSearchSelect={handleSavedSearchSelect}
            />
          </TabPanel>

          {/* Search History Tab */}
          <TabPanel value={2} index={currentTab === 'history' ? 2 : -1}>
            <SearchHistory
              onRepeatSearch={handleHistoryRepeat}
              limit={20}
            />
          </TabPanel>

          {/* AI Suggestions Tab */}
          <TabPanel value={3} index={currentTab === 'ai' ? 3 : -1}>
            <Box sx={{ px: 2 }}>
              <AIFilterSuggestions
                onApplyFilters={handleAIFilterApply}
                vacancyId={selectedVacancy}
                disabled={searching}
              />
            </Box>
          </TabPanel>
        </Paper>

        {/* Search Panel */}
        <Paper sx={{ p: 3, mb: 4 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label={t('candidateSearch.selectVacancy')}
                value={selectedVacancy}
                onChange={(e) => setSelectedVacancy(e.target.value)}
                SelectProps={{ native: true }}
              >
                {vacancies.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.title} {v.location ? `(${v.location})` : ''}
                  </option>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('candidateSearch.filterBySkills')}
                placeholder={t('candidateSearch.filterPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ px: 1 }}>
                <Typography variant="body2" gutterBottom>
                  {t('candidateSearch.minMatchPercentage', { percentage: minMatchPercentage })}
                </Typography>
                <Slider
                  value={minMatchPercentage}
                  onChange={(_, value) => setMinMatchPercentage(value as number)}
                  min={0}
                  max={100}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </Grid>
            <Grid item xs={12}>
              <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                <ToggleButtonGroup
                  value={sortBy}
                  exclusive
                  onChange={(_, value) => value && setSortBy(value)}
                  size="small"
                >
                  <ToggleButton value="ranking" aria-label="sort by AI ranking">
                    <Tooltip title={t('candidateSearch.sortByRanking')}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <AIIcon fontSize="small" />
                        <Typography variant="body2">{t('candidateSearch.aiRanking')}</Typography>
                      </Box>
                    </Tooltip>
                  </ToggleButton>
                  <ToggleButton value="match" aria-label="sort by match percentage">
                    <Tooltip title={t('candidateSearch.sortByMatch')}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <TrendingUpIcon fontSize="small" />
                        <Typography variant="body2">{t('candidateSearch.matchPercent')}</Typography>
                      </Box>
                    </Tooltip>
                  </ToggleButton>
                </ToggleButtonGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={usingAIRanking}
                      onChange={(e) => setUsingAIRanking(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <AIIcon fontSize="small" />
                      <Typography variant="body2">{t('candidateSearch.useAIRanking')}</Typography>
                    </Box>
                  }
                />
              </Stack>
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                size="large"
                startIcon={searching ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleSearch}
                disabled={searching || !selectedVacancy}
                fullWidth
              >
                {searching ? t('candidateSearch.searching') : t('candidateSearch.findCandidates')}
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Results */}
        {!searched ? (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <WorkIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              {t('candidateSearch.startMessage')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('candidateSearch.resumesAvailable', { count: resumes.length })}
            </Typography>
          </Paper>
        ) : displayedCandidates.length === 0 ? (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              {t('candidateSearch.noCandidates')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('candidateSearch.tryDifferent')}
            </Typography>
          </Paper>
        ) : (
          <>
            {/* Summary Stats */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary.main" fontWeight={700}>
                      {displayedCandidates.length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.candidatesFound')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main" fontWeight={700}>
                      {displayedCandidates.filter((c) => c.matchPercentage >= 70).length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.highMatch')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main" fontWeight={700}>
                      {displayedCandidates.filter((c) => c.matchPercentage >= 50 && c.matchPercentage < 70).length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.mediumMatch')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main" fontWeight={700}>
                      {Math.round(displayedCandidates.reduce((sum, c) => sum + c.matchPercentage, 0) / displayedCandidates.length)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.avgMatch')}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Export Button */}
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleExportCSV}
                  size="small"
                >
                  Export to CSV
                </Button>
              </Box>
            </Paper>

            {/* Candidate List */}
            <Grid container spacing={3}>
              {displayedCandidates.map((candidate, index) => (
                <Grid item xs={12} md={6} key={candidate.id}>
                  <Card
                    sx={{
                      height: '100%',
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                      borderLeft: 4,
                      borderColor: candidate.rankingScore
                        ? `${candidate.rankingScore >= 70 ? 'success' : candidate.rankingScore >= 40 ? 'warning' : 'error'}.main`
                        : `${getMatchColor(candidate.matchPercentage)}.main`,
                      position: 'relative',
                    }}
                    onClick={() => (window.location.href = `/results/${candidate.id}`)}
                  >
                    {/* Top Recommendation Badge */}
                    {candidate.isTopRecommendation && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: -8,
                          right: -8,
                          bgcolor: 'warning.main',
                          color: 'warning.contrastText',
                          px: 1.5,
                          py: 0.5,
                          borderRadius: '0 12px 0 12px',
                          zIndex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5,
                          boxShadow: 2,
                        }}
                      >
                        <StarIcon sx={{ fontSize: 14 }} />
                        <Typography variant="caption" fontWeight={700}>
                          TOP
                        </Typography>
                      </Box>
                    )}

                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              #{index + 1}
                            </Typography>
                            {candidate.modelVersion === 'AI' && (
                              <Chip
                                icon={<AIIcon sx={{ fontSize: 12 }} />}
                                label="AI"
                                size="small"
                                color="primary"
                                variant="outlined"
                                sx={{ height: 20, fontSize: '0.65rem', fontWeight: 600 }}
                              />
                            )}
                            <Typography variant="caption" color="text.secondary">
                              • {candidate.filename}
                            </Typography>
                          </Box>
                          <Typography variant="h6" fontWeight={600}>
                            {candidate.vacancyTitle}
                          </Typography>
                        </Box>
                        <Stack direction="row" spacing={1} alignItems="center">
                          {/* AI Ranking Score */}
                          {candidate.rankingScore !== undefined && (
                            <Tooltip title={t('candidateSearch.aiRankingScore')}>
                              <Box sx={{ textAlign: 'center' }}>
                                <Chip
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <AIIcon sx={{ fontSize: 14 }} />
                                  <Typography variant="body2" fontWeight={700}>
                                    {Math.round(candidate.rankingScore)}
                                  </Typography>
                                </Box>
                              }
                              color={
                                candidate.rankingScore >= 70
                                  ? 'success'
                                  : candidate.rankingScore >= 40
                                    ? 'warning'
                                    : 'error'
                              }
                              sx={{ fontWeight: 700, fontSize: '1rem' }}
                            />
                            {candidate.hireProbability !== undefined && (
                              <LinearProgress
                                variant="determinate"
                                value={candidate.hireProbability * 100}
                                sx={{
                                  height: 3,
                                  borderRadius: 1.5,
                                  mt: 0.5,
                                  width: 40,
                                  mx: 'auto',
                                }}
                                color={candidate.rankingScore >= 70 ? 'success' : 'warning'}
                              />
                            )}
                          </Box>
                        </Tooltip>
                      )}
                      {/* Semantic Similarity Score */}
                      {candidate.semanticScore !== undefined && candidate.semanticScore !== null && (
                        <Tooltip title={`Semantic Similarity: ${Math.round(candidate.semanticScore * 100)}%`}>
                          <Box sx={{ textAlign: 'center' }}>
                            <Chip
                              label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <PsychologyAlt sx={{ fontSize: 14 }} />
                                  <Typography variant="body2" fontWeight={700}>
                                    {Math.round(candidate.semanticScore * 100)}%
                                  </Typography>
                                </Box>
                              }
                              color={
                                candidate.semanticScore >= 0.7
                                  ? 'success'
                                  : candidate.semanticScore >= 0.4
                                    ? 'warning'
                                    : 'error'
                              }
                              sx={{ fontWeight: 700, fontSize: '1rem' }}
                            />
                          </Box>
                        </Tooltip>
                      )}
                      {/* Match Percentage */}
                      <Chip
                        label={`${candidate.matchPercentage}%`}
                        color={getMatchColor(candidate.matchPercentage) as any}
                        sx={{ fontWeight: 700, fontSize: '1rem' }}
                      />
                    </Stack>
                  </Box>

                  {/* Matched Skills */}
                  {candidate.matchedSkills.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="success.main" fontWeight={600}>
                        ✓ {t('candidateSearch.matched', { count: candidate.matchedSkills.length })}
                      </Typography>
                      <Box sx={{ mt: 0.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {candidate.matchedSkills.slice(0, 6).map((skill) => (
                          <Chip key={skill} label={skill} size="small" color="success" variant="outlined" />
                        ))}
                        {candidate.matchedSkills.length > 6 && (
                          <Chip
                            label={t('vacancyList.more', { count: candidate.matchedSkills.length - 6 })}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}

                  {/* Missing Skills */}
                  {candidate.missingSkills.length > 0 && (
                    <Box>
                      <Typography variant="caption" color="error.main" fontWeight={600}>
                        ✗ {t('candidateSearch.missing', { count: candidate.missingSkills.length })}
                      </Typography>
                      <Box sx={{ mt: 0.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {candidate.missingSkills.slice(0, 4).map((skill) => (
                          <Chip key={skill} label={skill} size="small" color="error" variant="outlined" />
                        ))}
                        {candidate.missingSkills.length > 4 && (
                          <Chip
                            label={t('vacancyList.more', { count: candidate.missingSkills.length - 4 })}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
          </>
        )}
      </Box>
    </Container>
  );
};

export default CandidateSearchPage;
