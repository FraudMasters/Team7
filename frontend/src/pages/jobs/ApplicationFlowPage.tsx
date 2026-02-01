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
import { useJob } from '../../hooks/useJobs';
import { ResumeUpload } from '../../components/resume/ResumeUpload';

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
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUploadComplete = (id: string) => {
    setResumeId(id);
    setActiveStep(1);
  };

  const handleSubmit = async () => {
    if (!resumeId || !id) return;

    setSubmitting(true);
    setError(null);

    try {
      // TODO: Implement actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setActiveStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

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
              <ResumeUpload onUploadComplete={handleUploadComplete} />
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
                />
                <TextField
                  label="Phone"
                  type="tel"
                  fullWidth
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
                <TextField
                  label="Cover Letter (Optional)"
                  multiline
                  rows={6}
                  fullWidth
                  value={formData.coverLetter}
                  onChange={(e) => setFormData({ ...formData, coverLetter: e.target.value })}
                  placeholder="Tell us why you're a great fit..."
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
                <Typography variant="body2" color="text.secondary">Email</Typography>
                <Typography>{formData.email}</Typography>
              </Box>

              {formData.phone && (
                <Box>
                  <Typography variant="body2" color="text.secondary">Phone</Typography>
                  <Typography>{formData.phone}</Typography>
                </Box>
              )}

              {error && <Alert severity="error">{error}</Alert>}

              <Stack direction="row" spacing={2}>
                <Button onClick={() => setActiveStep(1)}>Back</Button>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={submitting}
                  startIcon={submitting ? <CircularProgress size={16} /> : null}
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
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
