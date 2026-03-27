import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Box, Button, Typography, Paper, Stack, Alert, CircularProgress } from '@mui/material';
import {
  Event as EventIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { AvailabilitySlotPicker, AvailabilitySlot } from '../components/AvailabilitySlotPicker';
import { candidateSchedulingClient } from '../api/candidate-scheduling';
import type {
  TokenVerificationResponse,
  AvailableSlotsResponse,
  SelfScheduleResponse,
  ApiError
} from '../api/candidate-scheduling';

export function CandidateSelfSchedulePage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenInfo, setTokenInfo] = useState<TokenVerificationResponse | null>(null);
  const [slotsData, setSlotsData] = useState<AvailableSlotsResponse | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [success, setSuccess] = useState<SelfScheduleResponse | null>(null);

  useEffect(() => {
    if (!token) {
      setError('Invalid scheduling link. Please check the URL and try again.');
      setLoading(false);
      return;
    }

    loadSchedulingData();
  }, [token]);

  const loadSchedulingData = async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const verification = await candidateSchedulingClient.verifyToken(token);

      if (!verification.valid) {
        setError(verification.message);
        setTokenInfo(verification);
        setLoading(false);
        return;
      }

      setTokenInfo(verification);

      const slots = await candidateSchedulingClient.getAvailableSlots(token);
      setSlotsData(slots);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load scheduling information. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSlot = (slot: AvailabilitySlot) => {
    setSelectedSlot(slot);
  };

  const handleBookInterview = async () => {
    if (!token || !selectedSlot) return;

    setSubmitting(true);
    setError(null);

    try {
      const result = await candidateSchedulingClient.scheduleInterview({
        token,
        selected_slot: selectedSlot.start_time,
        duration_minutes: 60,
        interview_type: 'video',
      });

      setSuccess(result);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to book interview. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <Stack spacing={2} alignItems="center">
            <CircularProgress size={48} />
            <Typography variant="body1" color="text.secondary">
              Loading scheduling information...
            </Typography>
          </Stack>
        </Box>
      </Container>
    );
  }

  if (success) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Stack spacing={3} alignItems="center">
            <CheckCircleIcon sx={{ fontSize: 72, color: 'success.main' }} />
            <Typography variant="h4" fontWeight={700} textAlign="center">
              Interview Scheduled Successfully!
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center">
              {success.message}
            </Typography>

            <Box sx={{ width: '100%', bgcolor: 'grey.50', p: 3, borderRadius: 2, mt: 2 }}>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Interview Details
                  </Typography>
                  <Typography variant="h6" fontWeight="medium">
                    {success.title}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Date & Time
                  </Typography>
                  <Typography variant="body1">
                    {new Date(success.scheduled_start).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </Typography>
                  <Typography variant="body1">
                    {new Date(success.scheduled_start).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true,
                    })} - {new Date(success.scheduled_end).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true,
                    })}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Duration
                  </Typography>
                  <Typography variant="body1">
                    {success.duration_minutes} minutes
                  </Typography>
                </Box>

                {success.recruiter_name && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Interviewer
                    </Typography>
                    <Typography variant="body1">
                      {success.recruiter_name}
                    </Typography>
                  </Box>
                )}

                {success.meeting_link && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Meeting Link
                    </Typography>
                    <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                      <a href={success.meeting_link} target="_blank" rel="noopener noreferrer">
                        {success.meeting_link}
                      </a>
                    </Typography>
                  </Box>
                )}

                {success.location && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Location
                    </Typography>
                    <Typography variant="body1">
                      {success.location}
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Box>

            <Alert severity="info" sx={{ width: '100%', mt: 3 }}>
              A confirmation email has been sent to your email address with calendar invite and interview details.
            </Alert>
          </Stack>
        </Paper>
      </Container>
    );
  }

  if (!tokenInfo || !tokenInfo.valid) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Stack spacing={3} alignItems="center">
            <Typography variant="h4" fontWeight={700} textAlign="center">
              Invalid Scheduling Link
            </Typography>
            <Alert severity="error" sx={{ width: '100%' }}>
              {error || 'This scheduling link is invalid or has expired. Please contact the recruiter for a new link.'}
            </Alert>
          </Stack>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Stack spacing={1}>
          <Typography variant="h4" fontWeight={700}>
            Schedule Your Interview
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {tokenInfo.vacancy_title ? `${tokenInfo.vacancy_title} - ` : ''}Interview with {tokenInfo.recruiter_name}
          </Typography>
          {tokenInfo.expires_at && (
            <Typography variant="caption" color="text.secondary">
              This link expires on {new Date(tokenInfo.expires_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
              })}
            </Typography>
          )}
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 4 }}>
        {slotsData ? (
          <>
            <AvailabilitySlotPicker
              slots={slotsData.available_slots.map(slot => ({
                start_time: slot.start_time,
                end_time: slot.end_time,
                available: slot.available,
                confidence: 1.0,
              }))}
              loading={false}
              error={null}
              onSelectSlot={handleSelectSlot}
              selectedSlot={selectedSlot}
              durationMinutes={60}
            />

            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<EventIcon />}
                onClick={handleBookInterview}
                disabled={!selectedSlot || submitting}
                sx={{ minWidth: 200 }}
              >
                {submitting ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
                    Booking...
                  </>
                ) : (
                  'Book Interview'
                )}
              </Button>
            </Box>
          </>
        ) : (
          <Box display="flex" justifyContent="center" alignItems="center" py={8}>
            <Typography variant="body1" color="text.secondary">
              No available time slots found. Please contact the recruiter.
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default CandidateSelfSchedulePage;
