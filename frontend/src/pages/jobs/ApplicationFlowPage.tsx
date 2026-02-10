import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  Box,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import { config } from '@/config';
import { useJob } from '../../hooks/useJobs';
import { useSubmitJobApplication } from '../../hooks/useJobApplications';
import ResumeUploader from '../../components/ResumeUploader';

const steps = ['Upload Resume', 'Contact Info', 'Review', 'Submit'];

export function ApplicationFlowPage() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading: jobLoading } = useJob(id || '');

  const [activeStep, setActiveStep] = useState(0);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    phone: '',
    coverLetter: '',
  });
  const [submitError, setSubmitError] = useState<string | null>(null);

  const submitMutation = useSubmitJobApplication();

  const handleUploadComplete = (id: string) => {
    setResumeId(id);
    setActiveStep(1);
    setSubmitError(null);
  };

  const handleUploadError = (error: string) => {
    setSubmitError(error);
  };

  const handleSubmit = async () => {
    if (!resumeId || !id) return;

    setSubmitError(null);

    try {
      await submitMutation.mutateAsync({
        vacancy_id: id,
        resume_id: resumeId,
        email: formData.email,
        phone: formData.phone || undefined,
        cover_letter: formData.coverLetter || undefined,
      });
      setActiveStep(3);
    } catch (err: any) {
      setSubmitError(err.detail || 'Failed to submit application. Please try again.');
    }
  };

  const isSubmitting = submitMutation.isPending;

  if (jobLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Apply for {job?.title}
        </Typography>

        <Stepper activeStep={activeStep} sx={{ my: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mt: 4 }}>
          {/* Step 1: Upload Resume */}
          {activeStep === 0 && (
            <Stack spacing={4}>
              <Typography variant="body1" color="text.secondary">
                Upload your resume and we'll match your skills to this position.
              </Typography>
              <ResumeUploader
                uploadUrl={`${config.api.url}/api/resumes/upload`}
                onUploadComplete={handleUploadComplete}
                onUploadError={handleUploadError}
                onUploadStart={() => {}}
              />
            </Stack>
          )}

          {/* Step 2: Contact Info */}
          {activeStep === 1 && (
            <Stack spacing={4}>
              <Alert severity="success">
                Your resume has been analyzed! Please complete your details below.
              </Alert>

              <Stack spacing={3}>
                <TextField
                  label="Email"
                  type="email"
                  fullWidth
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!formData.email}
                  helperText={!formData.email ? 'Email is required' : ''}
                />
                <TextField
                  label="Phone"
                  type="tel"
                  fullWidth
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
                />
                <TextField
                  label="Cover Letter (Optional)"
                  multiline
                  rows={6}
                  fullWidth
                  value={formData.coverLetter}
                  onChange={(e) => setFormData({ ...formData, coverLetter: e.target.value })}
                  placeholder="Tell us why you're a great fit for this role..."
                />
              </Stack>

              <Stack direction="row" spacing={2}>
                <Button onClick={() => setActiveStep(0)}>Back</Button>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(2)}
                  disabled={!formData.email}
                >
                  Review
                </Button>
              </Stack>
            </Stack>
          )}

          {/* Step 3: Review */}
          {activeStep === 2 && (
            <Stack spacing={4}>
              <Typography variant="h6">Review Your Application</Typography>

              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Email
                </Typography>
                <Typography variant="body1">{formData.email}</Typography>
              </Box>

              {formData.phone && (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Phone
                  </Typography>
                  <Typography variant="body1">{formData.phone}</Typography>
                </Box>
              )}

              {formData.coverLetter && (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Cover Letter
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {formData.coverLetter}
                  </Typography>
                </Box>
              )}

              {submitError && <Alert severity="error">{submitError}</Alert>}

              <Stack direction="row" spacing={2}>
                <Button onClick={() => setActiveStep(1)}>Back</Button>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  startIcon={isSubmitting ? <CircularProgress size={16} /> : null}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Application'}
                </Button>
              </Stack>
            </Stack>
          )}

          {/* Step 4: Success */}
          {activeStep === 3 && (
            <Stack spacing={4} alignItems="center" textAlign="center">
              <Typography variant="h5" fontWeight={700} color="success.main">
                Application Submitted!
              </Typography>
              <Typography variant="body1" color="text.secondary">
                We'll review your application and get back to you soon.
              </Typography>
              <Button variant="contained" href="/jobs">
                Browse More Jobs
              </Button>
            </Stack>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
