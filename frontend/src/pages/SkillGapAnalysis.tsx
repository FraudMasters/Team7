/**
 * Skill Gap Analysis Page
 *
 * Allows analyzing skill gaps between a candidate and job requirements,
 * with personalized learning recommendations.
 */

import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Autocomplete,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Search as SearchIcon,
  AutoAwesome as AnalyzeIcon,
  School as LearningIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { skillGap } from '@/api/skillGap';
import type { SkillGapAnalysisResponse, LearningRecommendationsResponse } from '@/types/api';
import SkillGapVisualization from '@components/SkillGapVisualization';
import LearningRecommendationsCard from '@components/LearningRecommendationsCard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Vacancy Form State
 */
interface VacancyFormData {
  id: string;
  title: string;
  description: string;
  requiredSkills: string[];
  skillLevels: Record<string, string>;
  experienceYears: number;
}

/**
 * Initial vacancy form state
 */
const initialVacancyState: VacancyFormData = {
  id: '',
  title: '',
  description: '',
  requiredSkills: [],
  skillLevels: {},
  experienceYears: 0,
};

/**
 * Skill Gap Analysis Page
 */
export default function SkillGapAnalysisPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Form state
  const [resumeId, setResumeId] = useState('');
  const [vacancy, setVacancy] = useState<VacancyFormData>(initialVacancyState);

  // Analysis state
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<SkillGapAnalysisResponse | null>(null);
  const [recommendations, setRecommendations] = useState<LearningRecommendationsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // Available skill levels
  const skillLevels = ['beginner', 'intermediate', 'advanced', 'expert'];

  /**
   * Handle skill selection
   */
  const handleSkillsChange = useCallback((_: unknown, value: string[]) => {
    setVacancy((prev) => ({
      ...prev,
      requiredSkills: value,
    }));
  }, []);

  /**
   * Handle skill level change for a specific skill
   */
  const handleSkillLevelChange = useCallback((skill: string, level: string) => {
    setVacancy((prev) => ({
      ...prev,
      skillLevels: {
        ...prev.skillLevels,
        [skill]: level,
      },
    }));
  }, []);

  /**
   * Analyze skill gaps
   */
  const handleAnalyze = useCallback(async () => {
    if (!resumeId.trim() || !vacancy.title.trim() || vacancy.requiredSkills.length === 0) {
      setError(t('skillGap.errors.incomplete', { defaultValue: 'Please fill in all required fields.' }));
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysis(null);
    setRecommendations(null);
    setTabValue(0);

    try {
      // Generate vacancy ID from title if not provided
      const vacancyId = vacancy.id || `vacancy-${Date.now()}`;

      const result = await skillGap.analyzeWithRecommendations(
        {
          resume_id: resumeId.trim(),
          vacancy_data: {
            id: vacancyId,
            title: vacancy.title,
            description: vacancy.description || undefined,
            required_skills: vacancy.requiredSkills,
            required_skill_levels: Object.keys(vacancy.skillLevels).length > 0 ? vacancy.skillLevels : undefined,
            required_experience_years: vacancy.experienceYears > 0 ? vacancy.experienceYears : undefined,
          },
        },
        {
          max_recommendations_per_skill: 3,
          include_free_resources: true,
          min_rating: 4.0,
        }
      );

      setAnalysis(result.analysis);
      setRecommendations(result.recommendations);
    } catch (err) {
      const message = err instanceof Error ? err.message : t('skillGap.errors.analysisFailed', { defaultValue: 'Analysis failed. Please try again.' });
      setError(message);
    } finally {
      setAnalyzing(false);
    }
  }, [resumeId, vacancy, t]);

  /**
   * Reset form
   */
  const handleReset = useCallback(() => {
    setResumeId('');
    setVacancy(initialVacancyState);
    setAnalysis(null);
    setRecommendations(null);
    setError(null);
    setTabValue(0);
  }, []);

  /**
   * Load sample data for testing
   */
  const loadSampleData = useCallback(() => {
    setResumeId('faecba4a-5a01-41fb-b135-cbe7d6e30d67');
    setVacancy({
      id: 'sample-react-vacancy',
      title: 'Senior React Developer',
      description: 'Looking for an experienced React developer with TypeScript skills for building modern web applications.',
      requiredSkills: ['React', 'TypeScript', 'JavaScript', 'AWS', 'Docker', 'GraphQL'],
      skillLevels: {
        React: 'advanced',
        TypeScript: 'intermediate',
        JavaScript: 'advanced',
        AWS: 'beginner',
        Docker: 'intermediate',
        GraphQL: 'intermediate',
      },
      experienceYears: 5,
    });
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box>
          <Typography variant="h4" gutterBottom>
            {t('skillGap.title', { defaultValue: 'Skill Gap Analysis' })}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('skillGap.subtitle', {
              defaultValue: 'Analyze skill gaps between a candidate and job requirements, and get personalized learning recommendations.',
            })}
          </Typography>
        </Box>

        {/* Input Form */}
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={3}>
            {/* Resume ID */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('skillGap.resumeId', { defaultValue: 'Resume ID' })}
                placeholder="e.g., faecba4a-5a01-41fb-b135-cbe7d6e30d67"
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
                disabled={analyzing}
              />
            </Grid>

            {/* Vacancy Title */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('skillGap.vacancyTitle', { defaultValue: 'Job Title' })}
                placeholder="e.g., Senior React Developer"
                value={vacancy.title}
                onChange={(e) => setVacancy((prev) => ({ ...prev, title: e.target.value }))}
                disabled={analyzing}
              />
            </Grid>

            {/* Description */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label={t('skillGap.description', { defaultValue: 'Job Description' })}
                placeholder={t('skillGap.descriptionPlaceholder', {
                  defaultValue: 'Describe the role, responsibilities, and requirements...',
                })}
                value={vacancy.description}
                onChange={(e) => setVacancy((prev) => ({ ...prev, description: e.target.value }))}
                disabled={analyzing}
              />
            </Grid>

            {/* Required Skills */}
            <Grid item xs={12}>
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={vacancy.requiredSkills}
                onChange={handleSkillsChange}
                disabled={analyzing}
                renderTags={(value: readonly string[], getTagProps) =>
                  value.map((option: string, index: number) => {
                    const { key, ...tagProps } = getTagProps({ index });
                    return (
                      <Chip
                        key={key}
                        variant="outlined"
                        label={option}
                        {...tagProps}
                      />
                    );
                  })
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('skillGap.requiredSkills', { defaultValue: 'Required Skills' })}
                    placeholder={t('skillGap.skillsPlaceholder', {
                      defaultValue: 'Type a skill and press Enter...',
                    })}
                  />
                )}
              />
            </Grid>

            {/* Skill Levels */}
            {vacancy.requiredSkills.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  {t('skillGap.skillLevels', { defaultValue: 'Required Skill Levels (optional)' })}
                </Typography>
                <Grid container spacing={2}>
                  {vacancy.requiredSkills.map((skill) => (
                    <Grid item xs={12} sm={6} md={4} key={skill}>
                      <FormControl size="small" fullWidth>
                        <InputLabel>{skill}</InputLabel>
                        <Select
                          value={vacancy.skillLevels[skill] || ''}
                          label={skill}
                          onChange={(e) => handleSkillLevelChange(skill, e.target.value)}
                          disabled={analyzing}
                        >
                          {skillLevels.map((level) => (
                            <MenuItem key={level} value={level}>
                              {t(`skillGap.level.${level}`, { defaultValue: level })}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  ))}
                </Grid>
              </Grid>
            )}

            {/* Required Experience */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label={t('skillGap.experienceYears', { defaultValue: 'Required Experience (Years)' })}
                value={vacancy.experienceYears || ''}
                onChange={(e) =>
                  setVacancy((prev) => ({
                    ...prev,
                    experienceYears: parseInt(e.target.value) || 0,
                  }))
                }
                disabled={analyzing}
                inputProps={{ min: 0, max: 50 }}
              />
            </Grid>

            {/* Actions */}
            <Grid item xs={12}>
              <Stack direction="row" spacing={2} justifyContent="flex-end">
                <Button onClick={loadSampleData} disabled={analyzing}>
                  {t('skillGap.loadSample', { defaultValue: 'Load Sample Data' })}
                </Button>
                <Button onClick={handleReset} disabled={analyzing}>
                  {t('skillGap.reset', { defaultValue: 'Reset' })}
                </Button>
                <Button
                  variant="contained"
                  startIcon={analyzing ? <CircularProgress size={20} /> : <AnalyzeIcon />}
                  onClick={handleAnalyze}
                  disabled={analyzing}
                >
                  {analyzing
                    ? t('skillGap.analyzing', { defaultValue: 'Analyzing...' })
                    : t('skillGap.analyze', { defaultValue: 'Analyze Skill Gaps' })}
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Results */}
        {analysis && (
          <Paper sx={{ p: 0 }}>
            <Tabs
              value={tabValue}
              onChange={(_, newValue) => setTabValue(newValue)}
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab
                icon={<AnalyzeIcon />}
                label={t('skillGap.tabs.analysis', { defaultValue: 'Analysis' })}
              />
              <Tab
                icon={<LearningIcon />}
                label={t('skillGap.tabs.recommendations', { defaultValue: 'Recommendations' })}
                disabled={!recommendations}
              />
            </Tabs>

            <Box sx={{ p: 3 }}>
              <TabPanel value={tabValue} index={0}>
                <SkillGapVisualization analysis={analysis} />
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                {recommendations && (
                  <LearningRecommendationsCard recommendations={recommendations} />
                )}
              </TabPanel>
            </Box>
          </Paper>
        )}
      </Stack>
    </Container>
  );
}
