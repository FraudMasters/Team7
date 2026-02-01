import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
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
  List,
  ListItem,
  ListItemText,
  TextField,
  IconButton,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Lightbulb as LightbulbIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  School as TechnicalIcon,
  Psychology as BehavioralIcon,
  Assignment as SituationalIcon,
  Verified as VerificationIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Add as AddIcon,
  PictureAsPdf as PictureAsPdfIcon,
} from '@mui/icons-material';
import type { InterviewPrepResponse, InterviewQuestion, ApiError } from '@/types/api';

/**
 * InterviewPrepSheet Component Props
 */
interface InterviewPrepSheetProps {
  /** Interview Prep ID from URL parameter */
  prepId: string;
  /** API endpoint URL for fetching interview prep data */
  apiUrl?: string;
}

/**
 * Get category icon for display
 */
const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'technical':
      return <TechnicalIcon />;
    case 'behavioral':
      return <BehavioralIcon />;
    case 'situational':
      return <SituationalIcon />;
    case 'skill_verification':
      return <VerificationIcon />;
    default:
      return <InfoIcon />;
  }
};

/**
 * Get category color for display
 */
const getCategoryColor = (category: string): 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' => {
  switch (category) {
    case 'technical':
      return 'primary';
    case 'behavioral':
      return 'secondary';
    case 'situational':
      return 'info';
    case 'skill_verification':
      return 'success';
    default:
      return 'default';
  }
};

/**
 * Get difficulty color for display
 */
const getDifficultyColor = (difficulty: string): 'success' | 'info' | 'warning' | 'error' => {
  switch (difficulty) {
    case 'beginner':
      return 'success';
    case 'intermediate':
      return 'info';
    case 'advanced':
      return 'warning';
    default:
      return 'error';
  }
};

/**
 * InterviewPrepSheet Component
 *
 * Displays comprehensive interview preparation data including:
 * - Technical questions with difficulty ratings
 * - Behavioral questions for soft skills assessment
 * - Situational questions for scenario-based evaluation
 * - Skill verification questions for experience validation
 * - Areas to probe based on skill gaps
 * - Interview tips for conducting effective interviews
 *
 * @example
 * ```tsx
 * <InterviewPrepSheet prepId="test-id" />
 * ```
 */
const InterviewPrepSheet: React.FC<InterviewPrepSheetProps> = ({
  prepId,
  apiUrl = '/api/interview-prep',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [data, setData] = useState<InterviewPrepResponse | null>(null);

  // Custom question input state
  const [newCustomQuestion, setNewCustomQuestion] = useState('');

  /**
   * Fetch interview prep data from backend
   */
  const fetchPrep = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/${prepId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch interview prep: ${response.statusText}`);
      }

      const result: InterviewPrepResponse = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load interview preparation data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (prepId) {
      fetchPrep();
    }
  }, [prepId]);

  /**
   * Update interview prep with custom questions or feedback
   */
  const updatePrep = useCallback(async (updates: { custom_questions?: string[]; question_feedback?: Record<string, unknown> }) => {
    try {
      setSubmitting(true);
      setError(null);

      const response = await fetch(`${apiUrl}/${prepId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.detail || 'Failed to update interview prep');
      }

      const result: InterviewPrepResponse = await response.json();
      setData(result);

      setSuccessMessage('Interview prep updated successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update interview prep';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  }, [prepId, apiUrl]);

  /**
   * Handle adding a custom question
   */
  const handleAddCustomQuestion = useCallback(async () => {
    if (!newCustomQuestion.trim()) {
      setError('Question cannot be empty.');
      return;
    }

    const currentCustomQuestions = data?.custom_questions || [];
    const updatedQuestions = [...currentCustomQuestions, newCustomQuestion.trim()];

    await updatePrep({ custom_questions: updatedQuestions });

    setNewCustomQuestion('');
  }, [newCustomQuestion, data, updatePrep]);

  /**
   * Handle providing feedback on a question
   */
  const handleQuestionFeedback = useCallback(async (
    questionId: string,
    feedback: 'helpful' | 'not_helpful'
  ) => {
    const currentFeedback = data?.question_feedback || {};
    const updatedFeedback = {
      ...currentFeedback,
      [questionId]: feedback,
    };

    await updatePrep({ question_feedback: updatedFeedback });
  }, [data, updatePrep]);

  /**
   * Handle PDF export
   */
  const handleExportPDF = useCallback(async () => {
    try {
      setExporting(true);
      setError(null);

      const response = await fetch(`${apiUrl}/${prepId}/export`);

      if (!response.ok) {
        throw new Error(`Failed to export PDF: ${response.statusText}`);
      }

      // Get the filename from the Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `interview_prep_${prepId}.pdf`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccessMessage('PDF exported successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export PDF';
      setError(errorMessage);
    } finally {
      setExporting(false);
    }
  }, [prepId, apiUrl]);

  /**
   * Render a single question card
   */
  const renderQuestion = (question: InterviewQuestion) => {
    const categoryColor = getCategoryColor(question.category);
    const difficultyColor = getDifficultyColor(question.difficulty);
    const currentFeedback = data?.question_feedback?.[question.id] as string | undefined;
    const feedbackHelpful = currentFeedback === 'helpful';
    const feedbackNotHelpful = currentFeedback === 'not_helpful';

    return (
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 2 }}>
            <Box sx={{ color: `${categoryColor}.main`, mt: 0.5 }}>
              {getCategoryIcon(question.category)}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                <Typography variant="subtitle1" fontWeight={600}>
                  {question.text}
                </Typography>
                <Chip
                  label={question.difficulty}
                  size="small"
                  color={difficultyColor}
                  variant="filled"
                />
              </Box>

              {/* Skills Tags */}
              {question.skills && question.skills.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                  {question.skills.map((skill, idx) => (
                    <Chip
                      key={idx}
                      label={skill}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.75rem' }}
                    />
                  ))}
                </Box>
              )}
            </Box>

            {/* Feedback Buttons */}
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton
                size="small"
                onClick={() => handleQuestionFeedback(question.id, 'helpful')}
                color={feedbackHelpful ? 'success' : 'default'}
                disabled={submitting}
              >
                <ThumbUpIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                onClick={() => handleQuestionFeedback(question.id, 'not_helpful')}
                color={feedbackNotHelpful ? 'error' : 'default'}
                disabled={submitting}
              >
                <ThumbDownIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          {/* Rationale */}
          {question.rationale && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                Rationale
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {question.rationale}
              </Typography>
            </Box>
          )}

          {/* Expected Answers */}
          {question.expected_answers && question.expected_answers.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="success.main" fontWeight={600}>
                <CheckIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                Expected Answers
              </Typography>
              <List dense sx={{ pl: 2 }}>
                {question.expected_answers.map((answer, idx) => (
                  <ListItem key={idx} sx={{ py: 0 }}>
                    <ListItemText
                      primary={
                        <Typography variant="body2" color="text.secondary">
                          • {answer}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Follow-up Suggestions */}
          {question.follow_up_suggestions && question.follow_up_suggestions.length > 0 && (
            <Accordion variant="outlined" sx={{ mt: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="caption" color="primary.main" fontWeight={600}>
                  Follow-up Suggestions ({question.follow_up_suggestions.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List dense>
                  {question.follow_up_suggestions.map((suggestion, idx) => (
                    <ListItem key={idx} sx={{ py: 0 }}>
                      <ListItemText
                        primary={
                          <Typography variant="body2">
                            {idx + 1}. {suggestion}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          )}
        </CardContent>
      </Card>
    );
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
          Loading Interview Preparation
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Please wait while we generate questions...
        </Typography>
      </Box>
    );
  }

  /**
   * Render no data state
   */
  if (!data) {
    return (
      <Alert severity="info">
        <AlertTitle>No Interview Data Found</AlertTitle>
        No interview preparation data available for ID: <strong>{prepId}</strong>
      </Alert>
    );
  }

  const {
    technical_questions,
    behavioral_questions,
    situational_questions,
    skill_verification_questions,
    areas_to_probe,
    skill_gaps_to_address,
    interview_tips,
    custom_questions,
  } = data;

  // Count total questions
  const totalQuestions =
    (technical_questions?.length || 0) +
    (behavioral_questions?.length || 0) +
    (situational_questions?.length || 0) +
    (skill_verification_questions?.length || 0);

  return (
    <Stack spacing={3}>
      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          icon={<CheckIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Interview Preparation Sheet
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<PictureAsPdfIcon />}
              onClick={handleExportPDF}
              size="small"
              disabled={exporting}
              color="success"
            >
              {exporting ? 'Exporting...' : 'Export PDF'}
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchPrep} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {technical_questions?.length || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Technical
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'secondary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="secondary.main" fontWeight={700}>
                  {behavioral_questions?.length || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Behavioral
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'info.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {situational_questions?.length || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Situational
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {skill_verification_questions?.length || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Verification
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Total Questions */}
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Total Questions: <strong>{totalQuestions}</strong>
          </Typography>
        </Box>
      </Paper>

      {/* Areas to Probe */}
      {areas_to_probe && areas_to_probe.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="warning" />
            Areas to Probe
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List>
            {areas_to_probe.map((area, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemText
                  primary={
                    <Typography variant="body1">
                      <strong>{index + 1}.</strong> {area}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Skill Gaps to Address */}
      {skill_gaps_to_address && skill_gaps_to_address.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" />
            Skill Gaps to Address
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {skill_gaps_to_address.map((gap, index) => (
              <Chip
                key={index}
                label={gap}
                color="error"
                variant="outlined"
                sx={{ fontSize: '0.875rem' }}
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Interview Tips */}
      {interview_tips && interview_tips.length > 0 && (
        <Paper
          elevation={1}
          sx={{
            p: 3,
            background: (theme) =>
              `linear-gradient(135deg, ${theme.palette.info.main}15 0%, ${theme.palette.info.main}05 100%)`,
            borderLeft: 6,
            borderColor: 'info.main',
          }}
        >
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LightbulbIcon color="info" />
            Interview Tips
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List>
            {interview_tips.map((tip, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemText
                  primary={
                    <Typography variant="body1">
                      <strong>{index + 1}.</strong> {tip}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Technical Questions */}
      {technical_questions && technical_questions.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TechnicalIcon color="primary" />
            Technical Questions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {technical_questions.map((question, index) => (
            <Box key={question.id || index}>{renderQuestion(question)}</Box>
          ))}
        </Paper>
      )}

      {/* Behavioral Questions */}
      {behavioral_questions && behavioral_questions.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BehavioralIcon color="secondary" />
            Behavioral Questions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {behavioral_questions.map((question, index) => (
            <Box key={question.id || index}>{renderQuestion(question)}</Box>
          ))}
        </Paper>
      )}

      {/* Situational Questions */}
      {situational_questions && situational_questions.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SituationalIcon color="info" />
            Situational Questions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {situational_questions.map((question, index) => (
            <Box key={question.id || index}>{renderQuestion(question)}</Box>
          ))}
        </Paper>
      )}

      {/* Skill Verification Questions */}
      {skill_verification_questions && skill_verification_questions.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <VerificationIcon color="success" />
            Skill Verification Questions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          {skill_verification_questions.map((question, index) => (
            <Box key={question.id || index}>{renderQuestion(question)}</Box>
          ))}
        </Paper>
      )}

      {/* Custom Questions */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Custom Questions
        </Typography>
        <Divider sx={{ mb: 2 }} />

        {/* Add Custom Question Form */}
        <Box sx={{ mb: 3 }}>
          <Stack spacing={2}>
            <TextField
              multiline
              rows={2}
              placeholder="Add a custom interview question..."
              value={newCustomQuestion}
              onChange={(e) => setNewCustomQuestion(e.target.value)}
              disabled={submitting}
              fullWidth
              size="small"
            />
            <Button
              variant="contained"
              startIcon={submitting ? <CircularProgress size={16} /> : <AddIcon />}
              onClick={handleAddCustomQuestion}
              disabled={!newCustomQuestion.trim() || submitting}
              sx={{ alignSelf: 'flex-start' }}
            >
              Add Question
            </Button>
          </Stack>
        </Box>

        {/* Display Custom Questions */}
        {custom_questions && custom_questions.length > 0 ? (
          <List>
            {custom_questions.map((question, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemText
                  primary={
                    <Typography variant="body1">
                      <strong>{index + 1}.</strong> {question}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Box sx={{ py: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No custom questions yet. Add your own questions above.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* No Questions Message */}
      {totalQuestions === 0 && (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <InfoIcon sx={{ fontSize: 64, color: 'info.main', mb: 2 }} />
          <Typography variant="h6" color="info.main" gutterBottom fontWeight={600}>
            No Questions Generated
          </Typography>
          <Typography variant="body1" color="text.secondary">
            No interview questions are available yet. Questions will be generated based on the candidate's resume and job requirements.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default InterviewPrepSheet;
