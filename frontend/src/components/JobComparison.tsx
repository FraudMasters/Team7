import React, { useState, useEffect } from 'react';
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
  apiUrl = 'http://localhost:8000/api/matching',
}) => {
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
      const response = await fetch(`${apiUrl}/${resumeId}/${vacancyId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result: JobComparisonData = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load comparison data';
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
        color: 'success' as const;
        label: 'Excellent Match',
        bgColor: 'success.main',
        textColor: 'success.contrastText',
      };
    }
    if (percentage >= 40) {
      return {
        color: 'warning' as const,
        label: 'Moderate Match',
        bgColor: 'warning.main',
        textColor: 'warning.contrastText',
      };
    }
    return {
      color: 'error' as const,
      label: 'Poor Match',
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
      return `${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
    }
    if (remainingMonths === 0) {
      return `${years} year${years !== 1 ? 's' : ''}`;
    }
    return `${years}y ${remainingMonths}m`;
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
          Comparing resume with vacancy...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing skills and experience
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
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Comparison Failed
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
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No comparison data found for resume ID: <strong>{resumeId}</strong> and vacancy
          ID: <strong>{vacancyId}</strong>
        </Typography>
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
              Job Comparison Results
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Resume: <strong>{resumeId}</strong> • Vacancy: <strong>{vacancyId}</strong>
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            Refresh
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
            {data.match_percentage.toFixed(0)}%
          </Typography>
          <Typography variant="h6" fontWeight={600} sx={{ mt: 1 }}>
            {matchConfig.label}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5, opacity: 0.9 }}>
            {matched_skills.length} of {matched_skills.length + missing_skills.length} skills matched
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
                Matched Skills
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary" paragraph>
              Candidate has {matched_skills.length} skill{matched_skills.length !== 1 ? 's' : ''} that match
              the vacancy requirements.
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
                <Typography variant="body2" color="text.secondary" italic>
                  No matched skills found
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
                Missing Skills
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary" paragraph>
              Candidate is missing {missing_skills.length} skill
              {missing_skills.length !== 1 ? 's' : ''} from the vacancy requirements.
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
                  All required skills are matched!
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
              Experience Verification
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
                        <Chip label="Meets Req" color="success" size="small" />
                      ) : (
                        <Chip label="Below Req" color="warning" size="small" />
                      )}
                    </Box>
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Candidate Experience:
                        </Typography>
                        <Typography variant="body2" fontWeight={600} color="primary.main">
                          {formatExperience(exp.total_months)}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Required:
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {formatExperience(exp.required_months)}
                        </Typography>
                      </Box>
                      {exp.projects && exp.projects.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            Verified from {exp.projects.length} project
                            {exp.projects.length !== 1 ? 's' : ''}:
                          </Typography>
                          {exp.projects.slice(0, 3).map((project, pIndex) => (
                            <Typography
                              key={pIndex}
                              variant="caption"
                              display="block"
                              sx={{ ml: 1, color: 'text.secondary' }}
                            >
                              • {project.company} ({formatExperience(project.months)})
                            </Typography>
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
          Overall Assessment
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Alert
          severity={data.match_percentage >= 70 ? 'success' : data.match_percentage >= 40 ? 'warning' : 'error'}
          sx={{ mt: 1 }}
        >
          <Typography variant="subtitle1" fontWeight={600}>
            {data.match_percentage >= 70
              ? 'Strong Candidate'
              : data.match_percentage >= 40
                ? 'Potential Candidate'
                : 'Weak Match'}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {data.match_percentage >= 70
              ? `This candidate matches ${data.match_percentage.toFixed(0)}% of the required skills and has strong potential for the role. Consider proceeding with interviews.`
              : data.match_percentage >= 40
                ? `This candidate matches ${data.match_percentage.toFixed(0)}% of requirements. Review missing skills and experience gaps before proceeding.`
                : `This candidate only matches ${data.match_percentage.toFixed(0)}% of requirements. Significant skill gaps exist. Consider other candidates.`}
          </Typography>
        </Alert>
      </Paper>

      {/* Processing Time */}
      {data.processing_time && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Comparison completed in {data.processing_time.toFixed(2)} seconds
        </Typography>
      )}
    </Stack>
  );
};

export default JobComparison;
