import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLanguageContext } from '@/contexts/LanguageContext';
import { formatNumber, formatDate } from '@/utils/localeFormatters';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CrossIcon,
  Refresh as RefreshIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';

/**
 * Skill match interface for comparison display
 */
interface SkillMatch {
  skill: string;
  matched: boolean;
  highlight: 'green' | 'red';
}

/**
 * Experience verification interface
 */
interface ExperienceVerification {
  skill: string;
  total_months: number;
  required_months: number;
  meets_requirement: boolean;
  projects: Array<{
    company: string;
    position: string;
    start_date: string;
    end_date: string | null;
    months: number;
  }>;
}

/**
 * Job comparison data structure from backend
 */
interface JobComparisonData {
  resume_id: string;
  vacancy_id: string;
  match_percentage: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillMatch[];
  experience_verification?: ExperienceVerification[];
  overall_match: boolean;
  processing_time?: number;
}

/**
 * JobComparison Component Props
 */
interface JobComparisonProps {
  /** Resume ID from URL parameter */
  resumeId: string;
  /** Vacancy ID from URL parameter */
  vacancyId: string;
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
}

/**
 * JobComparison Component
 *
 * Displays side-by-side comparison of resume and job vacancy with:
 * - Match percentage with color-coded threshold display
 * - Matched skills (green highlighting)
 * - Missing skills (red highlighting)
 * - Experience verification by skill
 * - Overall assessment
 *
 * @example
 * ```tsx
 * <JobComparison resumeId="test-id" vacancyId="vacancy-123" />
 * ```
 */
const JobComparison: React.FC<JobComparisonProps> = ({
  resumeId,
  vacancyId,
  apiUrl = '/api/vacancies',
}) => {
  const { t } = useTranslation();
  const { language } = useLanguageContext();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<JobComparisonData | null>(null);

  /**
   * Fetch job comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/match/${vacancyId}?resume_id=${resumeId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result = await response.json();

      // Transform API response to match our interface
      const comparisonData: JobComparisonData = {
        resume_id: result.resume_id,
        vacancy_id: result.vacancy_id,
        match_percentage: result.match_percentage,
        matched_skills: result.matched_skills || [],
        missing_skills: result.missing_skills || [],
        overall_match: result.overall_match,
        processing_time: result.processing_time,
      };
      setData(comparisonData);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('compare.errors.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId && vacancyId) {
      fetchComparison();
    }
  }, [resumeId, vacancyId]);

  /**
   * Get match percentage color and label
   */
  const getMatchConfig = (percentage: number) => {
    if (percentage >= 70) {
      return {
        color: 'success' as const,
        label: t('compare.excellent'),
        bgColor: 'success.main',
        textColor: 'success.contrastText',
      };
    }
    if (percentage >= 40) {
      return {
        color: 'warning' as const,
        label: t('compare.moderate'),
        bgColor: 'warning.main',
        textColor: 'warning.contrastText',
      };
    }
    return {
      color: 'error' as const,
      label: t('compare.poor'),
      bgColor: 'error.main',
      textColor: 'error.contrastText',
    };
  };

  /**
   * Format experience to human-readable string
   */
  const formatExperience = (months: number): string => {
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (years === 0) {
      return `${remainingMonths} ${t('compare.month', { count: remainingMonths })}`;
    }
    if (remainingMonths === 0) {
      return `${years} ${t('compare.year', { count: years })}`;
    }
    return `${years} ${t('compare.year', { count: years })} ${remainingMonths} ${t('compare.month', { count: remainingMonths })}`;
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
          {t('compare.loading')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('compare.loadingSubtitle')}
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
          <Button color="inherit" onClick={fetchComparison} startIcon={<RefreshIcon />}>
            {t('common.tryAgain')}
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          {t('compare.errorTitle')}
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          {t('compare.noDataTitle')}
        </Typography>
        <Typography variant="body2"
          dangerouslySetInnerHTML={{
            __html: t('compare.noDataMessage', {
              resumeId,
              vacancyId,
              interpolation: { escapeValue: false }
            })
          }}
        />
      </Alert>
    );
  }

  const matchConfig = getMatchConfig(data.match_percentage);
  const { matched_skills, missing_skills, experience_verification } = data;

  return (
    <Stack spacing={3}>
      {/* Header Section with Match Percentage */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              {t('compare.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {t('compare.resumeLabel')}: <strong>{resumeId}</strong> • {t('compare.vacancyLabel')}: <strong>{vacancyId}</strong>
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            {t('compare.refreshButton')}
          </Button>
        </Box>

        {/* Match Percentage Display */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            py: 3,
            bgcolor: `${matchConfig.color}.main`,
            borderRadius: 2,
            color: `${matchConfig.color}.contrastText`,
          }}
        >
          <Typography variant="h2" fontWeight={700} sx={{ fontSize: { xs: '3rem', md: '4rem' } }}>
            {formatNumber(data.match_percentage, language)}%
          </Typography>
          <Typography variant="h6" fontWeight={600} sx={{ mt: 1 }}>
            {matchConfig.label}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.9 }}>
            {t('compare.skillsMatched', {
              matched: matched_skills.length,
              total: matched_skills.length + missing_skills.length
            })}
          </Typography>
        </Box>
      </Paper>

      {/* Skills Comparison Section */}
      <Grid container spacing={2}>
        {/* Matched Skills */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CheckIcon color="success" sx={{ mr: 1, fontSize: 28 }} />
              <Typography variant="h6" fontWeight={600} color="success.main">
                {t('compare.matchedSkills')}
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('compare.matchedSkillsDescription', {
                count: matched_skills.length,
                plural: matched_skills.length !== 1 ? 's' : ''
              })}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {matched_skills.length > 0 ? (
                matched_skills.map((item, index) => (
                  <Chip
                    key={index}
                    label={item.skill}
                    size="medium"
                    sx={{
                      bgcolor: 'success.main',
                      color: 'success.contrastText',
                      fontWeight: 500,
                      '&:hover': {
                        bgcolor: 'success.dark',
                      },
                    }}
                  />
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {t('compare.noMatchedSkills')}
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Missing Skills */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CrossIcon color="error" sx={{ mr: 1, fontSize: 28 }} />
              <Typography variant="h6" fontWeight={600} color="error.main">
                {t('compare.missingSkills')}
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('compare.missingSkillsDescription', {
                count: missing_skills.length,
                plural: missing_skills.length !== 1 ? 's' : ''
              })}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {missing_skills.length > 0 ? (
                missing_skills.map((item, index) => (
                  <Chip
                    key={index}
                    label={item.skill}
                    size="medium"
                    sx={{
                      bgcolor: 'error.main',
                      color: 'error.contrastText',
                      fontWeight: 500,
                      '&:hover': {
                        bgcolor: 'error.dark',
                      },
                    }}
                  />
                ))
              ) : (
                <Typography variant="body2" color="success.main" fontWeight={500}>
                  {t('compare.allSkillsMatched')}
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Experience Verification Section */}
      {experience_verification && experience_verification.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WorkIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />
            <Typography variant="h6" fontWeight={600}>
              {t('compare.experienceVerification')}
            </Typography>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            {experience_verification.map((exp, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card
                  variant="outlined"
                  sx={{
                    borderColor: exp.meets_requirement ? 'success.main' : 'warning.main',
                    bgcolor: exp.meets_requirement ? 'success.50' : 'warning.50',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {exp.skill}
                      </Typography>
                      {exp.meets_requirement ? (
                        <Chip label={t('compare.meetsRequirement')} color="success" size="small" />
                      ) : (
                        <Chip label={t('compare.belowRequirement')} color="warning" size="small" />
                      )}
                    </Box>
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          {t('compare.candidateExperience')}
                        </Typography>
                        <Typography variant="body2" fontWeight={600} color="primary.main">
                          {formatExperience(exp.total_months)}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          {t('compare.required')}:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {formatExperience(exp.required_months)}
                        </Typography>
                      </Box>
                      {exp.projects && exp.projects.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {t('compare.verifiedFrom', {
                              count: exp.projects.length,
                              plural: exp.projects.length !== 1 ? 's' : ''
                            })}
                          </Typography>
                          {exp.projects.slice(0, 3).map((project, pIndex) => (
                            <Box key={pIndex} sx={{ ml: 1, mt: 0.5 }}>
                              <Typography variant="caption" display="block" color="text.secondary">
                                • {project.company} - {project.position}
                              </Typography>
                              <Typography variant="caption" display="block" sx={{ ml: 2 }}>
                                {formatDate(project.start_date, language)}
                                {project.end_date ? ` - ${formatDate(project.end_date, language)}` : ` - ${t('compare.present')}`}
                              </Typography>
                              <Typography variant="caption" display="block" sx={{ ml: 2 }} color="text.secondary">
                                ({formatExperience(project.months)})
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Overall Assessment */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          {t('compare.overallAssessment')}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Alert
          severity={data.match_percentage >= 70 ? 'success' : data.match_percentage >= 40 ? 'warning' : 'error'}
          sx={{ mt: 1 }}
        >
          <Typography variant="subtitle1" fontWeight={600}>
            {data.match_percentage >= 70
              ? t('compare.strongCandidate')
              : data.match_percentage >= 40
                ? t('compare.potentialCandidate')
                : t('compare.weakMatch')}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {data.match_percentage >= 70
              ? t('compare.strongCandidateMessage', { percentage: formatNumber(data.match_percentage, language) })
              : data.match_percentage >= 40
                ? t('compare.potentialCandidateMessage', { percentage: formatNumber(data.match_percentage, language) })
                : t('compare.weakMatchMessage', { percentage: formatNumber(data.match_percentage, language) })}
          </Typography>
        </Alert>
      </Paper>

      {/* Processing Time */}
      {data.processing_time && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          {t('compare.processingTime', { seconds: formatNumber(data.processing_time, language, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) })}
        </Typography>
      )}
    </Stack>
  );
};

export default JobComparison;
