import React, { useState, useEffect, useRef } from 'react';
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
  CardActions,
  Chip,
  Slider,
  FormControlLabel,
  Checkbox,
  ToggleButtonGroup,
  ToggleButton,
  Stack,
  LinearProgress,
  Tooltip,
  IconButton,
  Collapse,
  useTheme,
  useMediaQuery,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Work as WorkIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as AIIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Email as EmailIcon,
  Event as EventIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { RankedCandidate } from '../types/api';
import ErrorMessage, { ErrorMessageConfig } from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';

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
  starred?: boolean;
}

/**
 * Candidate Search Page (Recruiter Module)
 *
 * Allows recruiters to search for candidates by skills and find the best matches for their vacancies.
 */
type SortBy = 'match' | 'ranking';

const CandidateSearchPage: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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
  const [filtersExpanded, setFiltersExpanded] = useState(true);
  const [errorMessage, setErrorMessage] = useState<ErrorMessageConfig>({
    open: false,
    message: '',
    severity: 'error',
  });
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const candidateListRef = useRef<HTMLDivElement>(null);
  const candidateRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [interviewDialogOpen, setInterviewDialogOpen] = useState(false);
  const [candidateForInterview, setCandidateForInterview] = useState<CandidateWithMatch | null>(null);
  const [interviewDate, setInterviewDate] = useState('');
  const [interviewTime, setInterviewTime] = useState('');
  const [interviewType, setInterviewType] = useState('screening');
  const [interviewNotes, setInterviewNotes] = useState('');
  const [actionFeedback, setActionFeedback] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

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

  // Keyboard navigation for candidate list
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle keyboard navigation when candidates are displayed
      if (displayedCandidates.length === 0) {
        return;
      }

      // Ignore if typing in an input field
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      switch (event.key) {
        case 'ArrowDown':
        case 'j':
          event.preventDefault();
          setFocusedIndex((prev) => {
            const next = prev + 1;
            return next < displayedCandidates.length ? next : prev;
          });
          break;

        case 'ArrowUp':
        case 'k':
          event.preventDefault();
          setFocusedIndex((prev) => {
            if (prev <= 0) {
              return prev;
            }
            return prev - 1;
          });
          break;

        case 'Enter':
          if (focusedIndex >= 0 && focusedIndex < displayedCandidates.length) {
            event.preventDefault();
            const candidate = displayedCandidates[focusedIndex];
            window.location.href = `/results/${candidate.id}`;
          }
          break;

        case 'Escape':
          event.preventDefault();
          setFocusedIndex(-1);
          break;

        case 'Home':
          event.preventDefault();
          setFocusedIndex(0);
          break;

        case 'End':
          event.preventDefault();
          setFocusedIndex(displayedCandidates.length - 1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [displayedCandidates.length, focusedIndex]);

  // Reset focused index when candidates change
  useEffect(() => {
    setFocusedIndex(-1);
  }, [candidates]);

  // Scroll focused candidate into view
  useEffect(() => {
    if (focusedIndex >= 0 && candidateRefs.current[focusedIndex]) {
      candidateRefs.current[focusedIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [focusedIndex]);

  const handleSearch = async () => {
    if (!selectedVacancy) {
      setErrorMessage({
        open: true,
        message: t('candidateSearch.selectVacancyFirst'),
        severity: 'warning',
      });
      return;
    }

    setSearching(true);
    setSearched(true);
    setRankingData({});

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
    } catch (error) {
      console.error('Error searching:', error);
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

  const handleToggleStar = async (candidate: CandidateWithMatch) => {
    try {
      const newStarredValue = !candidate.starred;
      await axios.patch(`/api/resumes/${candidate.id}`, { starred: newStarredValue });
      // Update local state
      setCandidates(candidates.map((c) => (c.id === candidate.id ? { ...c, starred: newStarredValue } : c)));
      setActionFeedback({
        open: true,
        message: newStarredValue ? t('candidateSearch.starredSuccess') : t('candidateSearch.unstarredSuccess'),
        severity: 'success',
      });
    } catch (error) {
      console.error('Error toggling star:', error);
      setActionFeedback({
        open: true,
        message: t('errors.somethingWentWrong'),
        severity: 'error',
      });
    }
  };

  const handleEmail = (candidate: CandidateWithMatch) => {
    const subject = encodeURIComponent(t('candidateSearch.emailSubject', { vacancy: candidate.vacancyTitle }));
    const body = encodeURIComponent(t('candidateSearch.emailBody', { vacancy: candidate.vacancyTitle }));
    const mailtoLink = `mailto:?subject=${subject}&body=${body}`;
    window.location.href = mailtoLink;
    setActionFeedback({
      open: true,
      message: t('candidateSearch.emailSent'),
      severity: 'success',
    });
  };

  const handleOpenInterviewDialog = (candidate: CandidateWithMatch) => {
    setCandidateForInterview(candidate);
    setInterviewDate('');
    setInterviewTime('');
    setInterviewType('screening');
    setInterviewNotes('');
    setInterviewDialogOpen(true);
  };

  const handleCloseInterviewDialog = () => {
    setInterviewDialogOpen(false);
    setCandidateForInterview(null);
  };

  const handleScheduleInterview = async () => {
    if (!candidateForInterview) return;

    // Placeholder for backend integration
    // TODO: Integrate with backend API when available
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      setActionFeedback({
        open: true,
        message: t('candidateSearch.interviewDialog.success', {
          date: interviewDate || 'TBD',
          time: interviewTime || 'TBD',
        }),
        severity: 'success',
      });
      setInterviewDialogOpen(false);
    } catch (error) {
      console.error('Error scheduling interview:', error);
      setActionFeedback({
        open: true,
        message: t('candidateSearch.interviewDialog.error'),
        severity: 'error',
      });
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <LoadingSpinner size={40} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: { xs: 2, md: 4 } }}>
        <Typography variant={{ xs: 'h5', md: 'h4' }} component="h1" gutterBottom fontWeight={600}>
          {t('candidateSearch.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          {t('candidateSearch.subtitle')}
        </Typography>

        {/* Search Panel */}
        <Paper sx={{ mb: 4 }}>
          {/* Mobile Toggle Header */}
          {isMobile && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
                py: 1.5,
                borderBottom: filtersExpanded ? 1 : 0,
                borderColor: 'divider',
              }}
            >
              <Typography variant="subtitle1" fontWeight={600}>
                {t('candidateSearch.filters')}
              </Typography>
              <IconButton
                onClick={() => setFiltersExpanded(!filtersExpanded)}
                size="small"
                aria-label={filtersExpanded ? 'collapse filters' : 'expand filters'}
              >
                {filtersExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
          )}

          <Collapse in={!isMobile || filtersExpanded}>
            <Box sx={{ p: { xs: 2, md: 3 } }}>
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
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    spacing={2}
                    alignItems={{ xs: 'flex-start', sm: 'center' }}
                    justifyContent={{ xs: 'flex-start', sm: 'space-between' }}
                  >
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
                    startIcon={searching ? <LoadingSpinner size={20} /> : <SearchIcon />}
                    onClick={handleSearch}
                    disabled={searching || !selectedVacancy}
                    fullWidth
                  >
                    {searching ? t('candidateSearch.searching') : t('candidateSearch.findCandidates')}
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Collapse>
        </Paper>

        {/* Results */}
        {!searched ? (
          <Paper sx={{ p: { xs: 4, md: 6 }, textAlign: 'center' }}>
            <WorkIcon sx={{ fontSize: { xs: 48, md: 64 }, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              {t('candidateSearch.startMessage')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('candidateSearch.resumesAvailable', { count: resumes.length })}
            </Typography>
          </Paper>
        ) : displayedCandidates.length === 0 ? (
          <Paper sx={{ p: { xs: 4, md: 6 }, textAlign: 'center' }}>
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
            <Paper sx={{ p: { xs: 2, md: 3 }, mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant={{ xs: 'h5', md: 'h4' }} color="primary.main" fontWeight={700}>
                      {displayedCandidates.length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.candidatesFound')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant={{ xs: 'h5', md: 'h4' }} color="success.main" fontWeight={700}>
                      {displayedCandidates.filter((c) => c.matchPercentage >= 70).length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.highMatch')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant={{ xs: 'h5', md: 'h4' }} color="warning.main" fontWeight={700}>
                      {displayedCandidates.filter((c) => c.matchPercentage >= 50 && c.matchPercentage < 70).length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.mediumMatch')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant={{ xs: 'h5', md: 'h4' }} color="info.main" fontWeight={700}>
                      {Math.round(displayedCandidates.reduce((sum, c) => sum + c.matchPercentage, 0) / displayedCandidates.length)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateSearch.stats.avgMatch')}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>

            {/* Candidate List */}
            <Box ref={candidateListRef}>
              {/* Keyboard Navigation Hint */}
              {displayedCandidates.length > 0 && focusedIndex === -1 && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 1,
                    mb: 2,
                    py: 1,
                    px: 2,
                    bgcolor: 'action.hover',
                    borderRadius: 1,
                  }}
                >
                  <KeyboardArrowDownIcon fontSize="small" color="action" />
                  <Typography variant="caption" color="text.secondary">
                    {t('candidateSearch.keyboardHint', 'Use arrow keys to navigate, Enter to view details')}
                  </Typography>
                  <KeyboardArrowUpIcon fontSize="small" color="action" />
                </Box>
              )}

              <Grid container spacing={{ xs: 2, md: 3 }}>
                {displayedCandidates.map((candidate, index) => (
                  <Grid item xs={12} md={6} key={candidate.id}>
                    <Card
                      ref={(el) => (candidateRefs.current[index] = el)}
                      sx={{
                        height: '100%',
                        cursor: 'pointer',
                        transition: 'transform 0.2s, box-shadow 0.2s, outline-color 0.2s',
                        '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                        borderLeft: 4,
                        borderColor: candidate.rankingScore
                          ? `${candidate.rankingScore >= 70 ? 'success' : candidate.rankingScore >= 40 ? 'warning' : 'error'}.main`
                          : `${getMatchColor(candidate.matchPercentage)}.main`,
                        position: 'relative',
                        display: 'flex',
                        flexDirection: 'column',
                        outline: focusedIndex === index ? '3px solid' : 'none',
                        outlineColor: 'primary.main',
                        outlineOffset: '2px',
                        boxShadow: focusedIndex === index ? 8 : 1,
                      }}
                      onClick={() => {
                        setFocusedIndex(index);
                        window.location.href = `/results/${candidate.id}`;
                      }}
                      onMouseEnter={() => setFocusedIndex(index)}
                      tabIndex={0}
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
                          px: { xs: 1, md: 1.5 },
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

                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          mb: 2,
                          flexDirection: { xs: 'column', sm: 'row' },
                          gap: { xs: 1, sm: 0 },
                        }}
                      >
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 0.5,
                              mb: 0.5,
                              flexWrap: 'wrap',
                            }}
                          >
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
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                maxWidth: { xs: 150, sm: 200 },
                              }}
                            >
                              • {candidate.filename}
                            </Typography>
                          </Box>
                          <Typography
                            variant="h6"
                            fontWeight={600}
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
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
                          <Box
                            sx={{
                              mt: 0.5,
                              display: 'flex',
                              flexWrap: 'wrap',
                              gap: 0.5,
                            }}
                          >
                            {candidate.matchedSkills.slice(0, 6).map((skill) => (
                              <Chip
                                key={skill}
                                label={skill}
                                size="small"
                                color="success"
                                variant="outlined"
                                sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                              />
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
                          <Box
                            sx={{
                              mt: 0.5,
                              display: 'flex',
                              flexWrap: 'wrap',
                              gap: 0.5,
                            }}
                          >
                            {candidate.missingSkills.slice(0, 4).map((skill) => (
                              <Chip
                                key={skill}
                                label={skill}
                                size="small"
                                color="error"
                                variant="outlined"
                                sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                              />
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
                    <CardActions sx={{ justifyContent: 'space-between', px: { xs: 1, sm: 2 }, pb: { xs: 1, sm: 2 } }}>
                      {/* Quick Actions */}
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title={candidate.starred ? t('candidateSearch.unstar') : t('candidateSearch.star')}>
                          <IconButton
                            color={candidate.starred ? 'primary' : 'default'}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleStar(candidate);
                            }}
                            size="small"
                            sx={{
                              minWidth: 36,
                              minHeight: 36,
                            }}
                            aria-label={candidate.starred ? t('candidateSearch.unstar') : t('candidateSearch.star')}
                          >
                            {candidate.starred ? <StarIcon /> : <StarBorderIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('candidateSearch.email')}>
                          <IconButton
                            color="primary"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEmail(candidate);
                            }}
                            size="small"
                            sx={{
                              minWidth: 36,
                              minHeight: 36,
                            }}
                            aria-label={t('candidateSearch.email')}
                          >
                            <EmailIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('candidateSearch.scheduleInterview')}>
                          <IconButton
                            color="success"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenInterviewDialog(candidate);
                            }}
                            size="small"
                            sx={{
                              minWidth: 36,
                              minHeight: 36,
                            }}
                            aria-label={t('candidateSearch.scheduleInterview')}
                          >
                            <EventIcon />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
          </>
        )}
      </Box>

      <ErrorMessage
        errorState={errorMessage}
        onErrorStateChange={setErrorMessage}
      />

      {/* Interview Scheduling Dialog */}
      <Dialog
        open={interviewDialogOpen}
        onClose={handleCloseInterviewDialog}
        fullWidth
        maxWidth="sm"
        PaperProps={{
          sx: {
            mx: { xs: 1, sm: 2 },
          }
        }}
      >
        <DialogTitle>{t('candidateSearch.interviewDialog.title')}</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              {t('candidateSearch.interviewDialog.candidate')}: {candidateForInterview?.filename}
            </Typography>
            <Typography variant="subtitle2" color="text.secondary">
              {t('candidateSearch.interviewDialog.vacancy')}: {candidateForInterview?.vacancyTitle}
            </Typography>
          </Box>
          <Stack spacing={2}>
            <TextField
              fullWidth
              type="date"
              label={t('candidateSearch.interviewDialog.date')}
              value={interviewDate}
              onChange={(e) => setInterviewDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size={isMobile ? 'small' : 'medium'}
            />
            <TextField
              fullWidth
              type="time"
              label={t('candidateSearch.interviewDialog.time')}
              value={interviewTime}
              onChange={(e) => setInterviewTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size={isMobile ? 'small' : 'medium'}
            />
            <FormControl fullWidth size={isMobile ? 'small' : 'medium'}>
              <InputLabel id="interview-type-label">{t('candidateSearch.interviewDialog.type')}</InputLabel>
              <Select
                labelId="interview-type-label"
                value={interviewType}
                label={t('candidateSearch.interviewDialog.type')}
                onChange={(e) => setInterviewType(e.target.value)}
              >
                <MenuItem value="screening">{t('candidateSearch.interviewDialog.types.screening')}</MenuItem>
                <MenuItem value="technical">{t('candidateSearch.interviewDialog.types.technical')}</MenuItem>
                <MenuItem value="onsite">{t('candidateSearch.interviewDialog.types.onsite')}</MenuItem>
                <MenuItem value="panel">{t('candidateSearch.interviewDialog.types.panel')}</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              multiline
              rows={3}
              label={t('candidateSearch.interviewDialog.notes')}
              value={interviewNotes}
              onChange={(e) => setInterviewNotes(e.target.value)}
              placeholder={t('candidateSearch.interviewDialog.notes')}
              size={isMobile ? 'small' : 'medium'}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ flexDirection: { xs: 'column', sm: 'row' }, gap: 1, px: 2, pb: 2 }}>
          <Button
            onClick={handleCloseInterviewDialog}
            fullWidth={isMobile}
            sx={{ minWidth: isMobile ? '100%' : 100 }}
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleScheduleInterview}
            color="success"
            variant="contained"
            fullWidth={isMobile}
            sx={{ minWidth: isMobile ? '100%' : 100 }}
          >
            {t('candidateSearch.interviewDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Action Feedback Snackbar */}
      <Snackbar
        open={actionFeedback.open}
        autoHideDuration={4000}
        onClose={() => setActionFeedback({ ...actionFeedback, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setActionFeedback({ ...actionFeedback, open: false })}
          severity={actionFeedback.severity}
          sx={{ width: '100%' }}
        >
          {actionFeedback.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CandidateSearchPage;
