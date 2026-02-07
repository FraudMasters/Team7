import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLanguageContext } from '@/contexts/LanguageContext';
import { formatNumber } from '@/utils/localeFormatters';
import { semanticSearchClient } from '@/api/semanticSearch';
import type {
  SemanticSearchResponse,
  SemanticCandidateResult,
  SemanticMatchExplanation,
  SemanticSearchRequest,
  MatchExplanationResponse,
} from '@/types/api';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Psychology as SemanticIcon,
  Description as KeywordIcon,
  CheckCircle as CheckIcon,
  Cancel as CrossIcon,
  Lightbulb as InferredIcon,
  SwapHoriz as TransferableIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * SemanticSearchResults Component Props
 */
interface SemanticSearchResultsProps {
  /** Search request that generated these results */
  searchRequest: SemanticSearchRequest;
  /** Pre-loaded search results (optional, will fetch if not provided) */
  results?: SemanticSearchResponse;
  /** Called when results are loaded */
  onResultsLoaded?: (results: SemanticSearchResponse) => void;
  /** Called when an error occurs */
  onError?: (error: string) => void;
}

/**
 * Get score color based on value
 */
const getScoreColor = (score: number): 'error' | 'warning' | 'success' => {
  if (score >= 0.7) return 'success';
  if (score >= 0.4) return 'warning';
  return 'error';
};

/**
 * Format score as percentage
 */
const formatScore = (score: number): string => {
  return Math.round(score * 100);
};

/**
 * Format score as percentage with locale
 */
const formatScoreLocale = (score: number, language: string): string => {
  return formatNumber(Math.round(score * 100), language);
};

/**
 * SemanticSearchResults Component
 *
 * Displays semantic search results including:
 * - Search summary with query and execution time
 * - Candidate cards with semantic and keyword scores
 * - Detailed match explanations with matched/inferred/transferable skills
 * - Visual distinction between semantic and keyword matches
 * - Expandable explanations for each candidate
 *
 * @example
 * ```tsx
 * <SemanticSearchResults
 *   searchRequest={{ query: 'Senior Python developer with team leadership', limit: 10 }}
 *   onResultsLoaded={(results) => console.log('Found', results.total, 'candidates')}
 * />
 * ```
 */
const SemanticSearchResults: React.FC<SemanticSearchResultsProps> = ({
  searchRequest,
  results: initialResults,
  onResultsLoaded,
  onError,
}) => {
  const { t } = useTranslation();
  const { language } = useLanguageContext();
  const [loading, setLoading] = useState(!initialResults);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SemanticSearchResponse | null>(initialResults || null);
  const [explaining, setExplaining] = useState<Set<string>>(new Set());
  const [explanations, setExplanations] = useState<Map<string, MatchExplanationResponse>>(new Map());

  /**
   * Fetch semantic search results
   */
  const fetchResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await semanticSearchClient.semanticSearch(searchRequest);
      setResults(response);
      onResultsLoaded?.(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('semanticSearch.results.error.failedToLoad');
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch detailed explanation for a specific candidate
   */
  const fetchExplanation = async (resumeId: string) => {
    setExplaining((prev) => new Set(prev).add(resumeId));

    try {
      const explanation = await semanticSearchClient.explainMatch({
        query: searchRequest.query,
        resume_id: resumeId,
        vacancy_id: searchRequest.vacancy_id,
      });
      setExplanations((prev) => new Map(prev).set(resumeId, explanation));
    } catch (err) {
      console.error('Failed to fetch explanation:', err);
    } finally {
      setExplaining((prev) => {
        const next = new Set(prev);
        next.delete(resumeId);
        return next;
      });
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          {t('semanticSearch.results.searching')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('semanticSearch.results.understandingQuery')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchResults} startIcon={<RefreshIcon />}>
            {t('common.tryAgain')}
          </Button>
        }
      >
        <AlertTitle>{t('semanticSearch.results.error.title')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render no results state
   */
  if (!results || results.candidates.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('semanticSearch.results.noResults.title')}</AlertTitle>
        {t('semanticSearch.results.noResults.message')}
      </Alert>
    );
  }

  const { candidates, query, execution_time_seconds, semantic_scores_used, fallback_used, total } = results;

  /**
   * Render skill chips for a skill list
   */
  const renderSkillChips = (skills: string[], color: 'success' | 'warning' | 'error', icon?: React.ReactNode) => {
    if (!skills || skills.length === 0) return null;
    return (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {skills.slice(0, 10).map((skill) => (
          <Tooltip key={skill} title={skill}>
            <Chip
              label={skill}
              size="small"
              color={color}
              variant="filled"
              icon={icon}
              sx={{ fontSize: '0.75rem' }}
            />
          </Tooltip>
        ))}
        {skills.length > 10 && (
          <Chip
            label={`+${skills.length - 10}`}
            size="small"
            variant="outlined"
          />
        )}
      </Box>
    );
  };

  /**
   * Render match explanation for a candidate
   */
  const renderMatchExplanation = (explanation: MatchExplanationResponse) => {
    return (
      <Stack spacing={2}>
        {/* Score Breakdown */}
        <Grid container spacing={1}>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {t('semanticSearch.results.explanation.semanticScore')}
              </Typography>
              <Typography variant="h6" color="primary.main" fontWeight={700}>
                {formatScoreLocale(explanation.semantic_score, language)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {t('semanticSearch.results.explanation.skillMatch')}
              </Typography>
              <Typography variant="h6" color="success.main" fontWeight={700}>
                {formatScoreLocale(explanation.skill_match_score, language)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {t('semanticSearch.results.explanation.experienceRelevance')}
              </Typography>
              <Typography variant="h6" color="info.main" fontWeight={700}>
                {formatScoreLocale(explanation.experience_relevance_score, language)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {t('semanticSearch.results.explanation.contextFit')}
              </Typography>
              <Typography variant="h6" color="warning.main" fontWeight={700}>
                {formatScoreLocale(explanation.context_fit_score, language)}%
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <Divider />

        {/* Matched Skills */}
        {explanation.matched_skills && explanation.matched_skills.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="success.main" gutterBottom fontWeight={600}>
              <CheckIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              {t('semanticSearch.results.explanation.matchedSkills', { count: explanation.matched_skills.length })}
            </Typography>
            {renderSkillChips(explanation.matched_skills, 'success', <CheckIcon style={{ fontSize: 16 }} />)}
          </Box>
        )}

        {/* Inferred Skills */}
        {explanation.inferred_skills && explanation.inferred_skills.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="info.main" gutterBottom fontWeight={600}>
              <InferredIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              {t('semanticSearch.results.explanation.inferredSkills', { count: explanation.inferred_skills.length })}
              <Tooltip title={t('semanticSearch.results.explanation.inferredTooltip')}>
                <InfoIcon fontSize="small" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
              </Tooltip>
            </Typography>
            {renderSkillChips(explanation.inferred_skills, 'info', <InferredIcon style={{ fontSize: 16 }} />)}
          </Box>
        )}

        {/* Transferable Skills */}
        {explanation.transferable_skills && explanation.transferable_skills.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="warning.main" gutterBottom fontWeight={600}>
              <TransferableIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              {t('semanticSearch.results.explanation.transferableSkills', { count: explanation.transferable_skills.length })}
              <Tooltip title={t('semanticSearch.results.explanation.transferableTooltip')}>
                <InfoIcon fontSize="small" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
              </Tooltip>
            </Typography>
            {renderSkillChips(explanation.transferable_skills, 'warning', <TransferableIcon style={{ fontSize: 16 }} />)}
          </Box>
        )}

        {/* Missing Skills */}
        {explanation.missing_skills && explanation.missing_skills.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="error.main" gutterBottom fontWeight={600}>
              <CrossIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
              {t('semanticSearch.results.explanation.missingSkills', { count: explanation.missing_skills.length })}
            </Typography>
            {renderSkillChips(explanation.missing_skills, 'error', <CrossIcon style={{ fontSize: 16 }} />)}
          </Box>
        )}

        {/* Human-readable explanation */}
        {explanation.explanation && (
          <>
            <Divider />
            <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                {t('semanticSearch.results.explanation.whyMatched')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {explanation.explanation}
              </Typography>
            </Box>
          </>
        )}
      </Stack>
    );
  };

  /**
   * Render a single candidate card
   */
  const renderCandidateCard = (candidate: SemanticCandidateResult, index: number) => {
    const explanation = explanations.get(candidate.id);
    const isExplaining = explaining.has(candidate.id);

    return (
      <Card key={candidate.id} elevation={2} sx={{ mb: 2 }}>
        <CardContent>
          {/* Header with name and scores */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 2 }}>
            <Box sx={{ flex: 1, minWidth: 250 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {candidate.filename || `${t('semanticSearch.results.candidate')} #${index + 1}`}
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                {/* Language badge */}
                {candidate.language && (
                  <Chip label={candidate.language.toUpperCase()} size="small" variant="outlined" />
                )}
                {/* Experience badge */}
                {candidate.experience_years !== null && (
                  <Chip
                    label={`${candidate.experience_years} ${t('semanticSearch.results.yearsExperience')}`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>

            {/* Score badges */}
            <Stack direction="row" spacing={1}>
              {/* Semantic score */}
              <Tooltip title={t('semanticSearch.results.semanticScoreTooltip')}>
                <Chip
                  icon={<SemanticIcon />}
                  label={`${formatScore(candidate.semantic_score)}%`}
                  size="medium"
                  color={getScoreColor(candidate.semantic_score)}
                  sx={{ fontWeight: 600 }}
                />
              </Tooltip>
              {/* Keyword score */}
              <Tooltip title={t('semanticSearch.results.keywordScoreTooltip')}>
                <Chip
                  icon={<KeywordIcon />}
                  label={`${formatScore(candidate.keyword_score)}%`}
                  size="medium"
                  color={getScoreColor(candidate.keyword_score)}
                  variant="outlined"
                  sx={{ fontWeight: 600 }}
                />
              </Tooltip>
              {/* Final score */}
              <Tooltip title={t('semanticSearch.results.finalScoreTooltip')}>
                <Chip
                  label={`${formatScore(candidate.final_score)}%`}
                  size="medium"
                  color={getScoreColor(candidate.final_score)}
                  sx={{ fontWeight: 700, minWidth: 80 }}
                />
              </Tooltip>
            </Stack>
          </Box>

          {/* Skills preview */}
          {candidate.skills && candidate.skills.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                {t('semanticSearch.results.skills', { count: candidate.skills.length })}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {candidate.skills.slice(0, 8).map((skill) => (
                  <Chip key={skill} label={skill} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                ))}
                {candidate.skills.length > 8 && (
                  <Chip label={`+${candidate.skills.length - 8}`} size="small" variant="outlined" />
                )}
              </Box>
            </Box>
          )}

          {/* Explanation accordion */}
          <Accordion
            expanded={!!explanation}
            onChange={(_, expanded) => {
              if (expanded && !explanation) {
                fetchExplanation(candidate.id);
              }
            }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" fontWeight={500}>
                  {t('semanticSearch.results.seeExplanation')}
                </Typography>
                {isExplaining && <CircularProgress size={16} />}
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {explanation ? renderMatchExplanation(explanation) : <CircularProgress size={24} />}
            </AccordionDetails>
          </Accordion>

          {/* Inline match explanation (if available in result) */}
          {candidate.match_explanation && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                {t('semanticSearch.results.quickMatch')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {candidate.match_explanation.explanation}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('semanticSearch.results.title')}
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchResults} size="small">
            {t('common.refresh')}
          </Button>
        </Box>

        {/* Query display */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            {t('semanticSearch.results.searchQuery')}
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="body1" fontStyle="italic">
              "{query}"
            </Typography>
          </Paper>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {total}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('semanticSearch.results.stats.candidatesFound')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {candidates.filter((c) => c.final_score >= 0.7).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('semanticSearch.results.stats.highMatch')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {candidates.filter((c) => c.semantic_score >= 0.5).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('semanticSearch.results.stats.semanticMatches')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {execution_time_seconds.toFixed(1)}s
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('semanticSearch.results.stats.executionTime')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Status badges */}
        <Stack direction="row" spacing={1} sx={{ mt: 2 }} flexWrap="wrap">
          {semantic_scores_used && (
            <Chip
              icon={<SemanticIcon />}
              label={t('semanticSearch.results.semanticUsed')}
              color="primary"
              size="small"
            />
          )}
          {fallback_used && (
            <Chip
              label={t('semanticSearch.results.fallbackUsed')}
              color="warning"
              size="small"
            />
          )}
          {!semantic_scores_used && !fallback_used && (
            <Chip
              icon={<KeywordIcon />}
              label={t('semanticSearch.results.keywordOnly')}
              color="default"
              size="small"
            />
          )}
        </Stack>
      </Paper>

      {/* Candidates List */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          {t('semanticSearch.results.candidates', { count: candidates.length })}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {candidates.map((candidate, index) => renderCandidateCard(candidate, index))}
      </Paper>

      {/* No candidates message */}
      {candidates.length === 0 && (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom fontWeight={600}>
            {t('semanticSearch.results.noCandidates.title')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('semanticSearch.results.noCandidates.message')}
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default SemanticSearchResults;
