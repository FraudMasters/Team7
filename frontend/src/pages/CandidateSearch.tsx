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
} from '@mui/material';
import {
  Search as SearchIcon,
  Work as WorkIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as AIIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { RankedCandidate } from '../types/api';

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
}

/**
 * Candidate Search Page (Recruiter Module)
 *
 * Allows recruiters to search for candidates by skills and find the best matches for their vacancies.
 */
type SortBy = 'match' | 'ranking';

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

  const handleSearch = async () => {
    if (!selectedVacancy) {
      alert(t('candidateSearch.selectVacancyFirst'));
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
              <Grid container spacing={2}>
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
