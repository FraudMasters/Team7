import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Typography,
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Stack,
  CircularProgress,
} from '@/components/ui';
import { candidateAppealsClient, AppealType, AppealResponse } from '@/api/candidateAppeals';

/**
 * Appeal Portal Page Component
 *
 * Allows candidates to submit appeals against AI ranking decisions.
 * Candidates can provide additional context, skills, or documentation
 * that may have been missed during initial evaluation.
 *
 * @example
 * URL: /candidate/appeal?rank_id=test-uuid
 */
const AppealPortal: React.FC = () => {
  const [searchParams] = useSearchParams();
  const rankId = searchParams.get('rank_id') || '';

  // Form state
  const [email, setEmail] = useState('');
  const [appealType, setAppealType] = useState<AppealType>('ranking_position');
  const [appealText, setAppealText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<AppealResponse | null>(null);

  /**
   * Handle form submission
   */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate email
      if (!email || !email.includes('@')) {
        throw new Error('Please enter a valid email address');
      }

      // Validate appeal text length (min 10 characters from backend schema)
      if (appealText.length < 10) {
        throw new Error('Appeal explanation must be at least 10 characters long');
      }

      // Validate rank_id
      if (!rankId) {
        throw new Error('Invalid rank ID. Please use a valid appeal link.');
      }

      // Submit appeal
      const appeal = await candidateAppealsClient.createAppeal({
        candidate_rank_id: rankId,
        candidate_email: email,
        appeal_type: appealType,
        appeal_text: appealText,
      });

      setSuccess(appeal);

      // Clear form
      setEmail('');
      setAppealText('');
      setAppealType('ranking_position');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else if (typeof err === 'object' && err !== null && 'detail' in err) {
        setError((err as { detail: string }).detail);
      } else {
        setError('Failed to submit appeal. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get appeal type description
   */
  const getAppealTypeDescription = (type: AppealType): string => {
    const descriptions: Record<AppealType, string> = {
      ranking_position: 'Challenge your ranking position',
      score_explanation: 'Request explanation for your score',
      missing_skills: 'Report skills that were not considered',
    };
    return descriptions[type];
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" as="h1" gutterBottom fontWeight={600}>
            Submit an Appeal
          </Typography>
          <Typography variant="body1" color="secondary" paragraph>
            If you believe your AI ranking doesn't accurately reflect your qualifications,
            you can submit an appeal with additional context and information.
          </Typography>

          {/* Success message */}
          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body2" fontWeight={600}>
                Appeal submitted successfully!
              </Typography>
              <Typography variant="body2">
                Appeal ID: {success.id}
              </Typography>
              <Typography variant="body2">
                Status: {success.status}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                We will review your appeal and notify you at {success.candidate_email} when there's an update.
              </Typography>
            </Alert>
          )}

          {/* Error message */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Appeal form */}
          <Box component="form" onSubmit={handleSubmit} noValidate>
            <Stack spacing={3}>
              {/* Rank ID display (read-only) */}
              <Box>
                <Typography variant="body2" color="secondary" gutterBottom>
                  Ranking ID
                </Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {rankId || 'No rank ID provided'}
                </Typography>
              </Box>

              {/* Email input */}
              <TextField
                required
                fullWidth
                id="email"
                label="Your Email Address"
                name="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                helperText="We'll use this email to notify you of updates to your appeal"
                disabled={loading}
              />

              {/* Appeal type dropdown */}
              <FormControl fullWidth required disabled={loading}>
                <InputLabel id="appeal-type-label">Appeal Type</InputLabel>
                <Select
                  labelId="appeal-type-label"
                  id="appeal-type"
                  value={appealType}
                  label="Appeal Type"
                  onChange={(e) => setAppealType(e.target.value as AppealType)}
                >
                  <MenuItem value="ranking_position">
                    Ranking Position - Challenge your ranking position
                  </MenuItem>
                  <MenuItem value="score_explanation">
                    Score Explanation - Request explanation for your score
                  </MenuItem>
                  <MenuItem value="missing_skills">
                    Missing Skills - Report skills that were not considered
                  </MenuItem>
                </Select>
              </FormControl>

              {/* Appeal text input */}
              <TextField
                required
                fullWidth
                multiline
                rows={6}
                id="appeal-text"
                label="Your Explanation"
                name="appealText"
                value={appealText}
                onChange={(e) => setAppealText(e.target.value)}
                helperText={`Provide detailed information about why you're appealing (minimum 10 characters, current: ${appealText.length})`}
                disabled={loading}
                placeholder="Example: I have 5 years of experience with React and advanced TypeScript skills that may not have been fully captured in my initial profile. I've also completed several certifications in cloud computing..."
              />

              {/* Submit button */}
              <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={loading || !email || !appealText || appealText.length < 10}
                sx={{ mt: 2, py: 1.5 }}
              >
                {loading ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Submitting Appeal...
                  </>
                ) : (
                  'Submit Appeal'
                )}
              </Button>

              {/* Info box */}
              <Alert severity="info">
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  What happens next?
                </Typography>
                <Typography variant="body2">
                  1. Your appeal will be reviewed by our recruitment team
                </Typography>
                <Typography variant="body2">
                  2. You'll receive an email notification when your appeal is under review
                </Typography>
                <Typography variant="body2">
                  3. If accepted, your ranking may be updated based on the additional information provided
                </Typography>
              </Alert>
            </Stack>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default AppealPortal;
