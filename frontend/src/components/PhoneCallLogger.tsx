import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  AlertTitle,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Phone as PhoneIcon,
  CheckCircle as CheckCircleIcon,
  Call as CallIcon,
  PhoneMissed as PhoneMissedIcon,
  PhoneInTalk as PhoneInTalkIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { communicationsClient } from '@/api/communications';
import type {
  CommunicationCreate,
  CommunicationResponse,
  ApiError,
  CallType,
  CommunicationDirection,
} from '@/types/api';

/**
 * Call outcome options for tracking
 */
export type CallOutcome = 'reached' | 'left_voicemail' | 'no_answer' | 'wrong_number' | 'call_back_requested' | 'not_interested';

/**
 * PhoneCallLogger Component Props
 */
interface PhoneCallLoggerProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Recruiter ID (current user) for logging calls */
  recruiterId?: string;
  /** Callback when call is logged successfully */
  onCallLogged?: (call: CommunicationResponse) => void;
  /** Default phone number for the candidate */
  candidatePhone?: string;
  /** Recruiter's phone number */
  recruiterPhone?: string;
}

/**
 * PhoneCallLogger Component
 *
 * Form for logging phone calls with candidates:
 * - Supports inbound, outbound, and missed calls
 * - Tracks call duration in minutes
 * - Records call notes and outcome
 * - Handles loading and error states gracefully
 * - Creates both Communication and PhoneCall records
 *
 * @example
 * ```tsx
 * <PhoneCallLogger
 *   resumeId="resume-uuid"
 *   recruiterId="recruiter-uuid"
 *   candidatePhone="+1234567890"
 *   recruiterPhone="+0987654321"
 *   onCallLogged={(call) => console.log('Call logged:', call)}
 * />
 * ```
 */
const PhoneCallLogger: React.FC<PhoneCallLoggerProps> = ({
  resumeId,
  recruiterId,
  onCallLogged,
  candidatePhone = '',
  recruiterPhone = '',
}) => {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [callType, setCallType] = useState<CallType>('outbound');
  const [direction, setDirection] = useState<CommunicationDirection>('outbound');
  const [fromNumber, setFromNumber] = useState(recruiterPhone);
  const [toNumber, setToNumber] = useState(candidatePhone);
  const [duration, setDuration] = useState<number>(0);
  const [notes, setNotes] = useState('');
  const [outcome, setOutcome] = useState<CallOutcome>('reached');

  /**
   * Update phone numbers based on direction
   */
  const handleDirectionChange = useCallback((newDirection: CommunicationDirection) => {
    setDirection(newDirection);
    if (newDirection === 'outbound') {
      setFromNumber(recruiterPhone);
      setToNumber(candidatePhone);
    } else {
      setFromNumber(candidatePhone);
      setToNumber(recruiterPhone);
    }
  }, [recruiterPhone, candidatePhone]);

  /**
   * Update call type and auto-set direction for missed calls
   */
  const handleCallTypeChange = useCallback((newCallType: CallType) => {
    setCallType(newCallType);
    if (newCallType === 'missed') {
      setDirection('inbound');
      setFromNumber(candidatePhone);
      setToNumber(recruiterPhone);
      setDuration(0);
    }
  }, [candidatePhone, recruiterPhone]);

  /**
   * Format duration for display
   */
  const formatDuration = useCallback((minutes: number): string => {
    if (minutes < 60) {
      return `${minutes}m`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }, []);

  /**
   * Get call outcome display label
   */
  const getOutcomeLabel = useCallback((outcome: CallOutcome): string => {
    const labels: Record<CallOutcome, string> = {
      reached: 'Reached Candidate',
      left_voicemail: 'Left Voicemail',
      no_answer: 'No Answer',
      wrong_number: 'Wrong Number',
      call_back_requested: 'Call Back Requested',
      not_interested: 'Not Interested',
    };
    return labels[outcome];
  }, []);

  /**
   * Handle logging the phone call
   */
  const handleLogCall = useCallback(async () => {
    // Validation
    if (!recruiterId) {
      setError('Recruiter ID is required to log calls.');
      return;
    }

    if (!fromNumber.trim() || !toNumber.trim()) {
      setError('Both phone numbers are required.');
      return;
    }

    if (callType !== 'missed' && duration <= 0) {
      setError('Call duration must be greater than 0 for connected calls.');
      return;
    }

    if (callType !== 'missed' && !notes.trim()) {
      setError('Call notes are required for connected calls.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      // Prepare communication data
      const callData: CommunicationCreate = {
        candidate_id: resumeId,
        recruiter_id: recruiterId,
        type: 'phone_call',
        direction: callType === 'missed' ? 'inbound' : direction,
        status: 'sent',
        subject: `Phone Call - ${getOutcomeLabel(outcome)}`,
        body: notes.trim(),
        metadata: {
          call_type: callType,
          from_number: fromNumber.trim(),
          to_number: toNumber.trim(),
          duration_minutes: duration,
          outcome: outcome,
        },
      };

      const response = await communicationsClient.createCommunication(callData);

      // Reset form
      setNotes('');
      setDuration(0);
      setOutcome('reached');
      if (candidatePhone) {
        setToNumber(candidatePhone);
      }
      if (recruiterPhone) {
        setFromNumber(recruiterPhone);
      }

      setSuccessMessage('Phone call logged successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Notify parent
      onCallLogged?.(response);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to log phone call. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [
    resumeId,
    recruiterId,
    callType,
    direction,
    fromNumber,
    toNumber,
    duration,
    notes,
    outcome,
    candidatePhone,
    recruiterPhone,
    getOutcomeLabel,
    onCallLogged,
  ]);

  /**
   * Get icon for call type
   */
  const getCallTypeIcon = useCallback((type: CallType) => {
    switch (type) {
      case 'inbound':
        return <PhoneInTalkIcon />;
      case 'outbound':
        return <CallIcon />;
      case 'missed':
        return <PhoneMissedIcon />;
      default:
        return <PhoneIcon />;
    }
  }, []);

  return (
    <Stack spacing={2}>
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
          icon={<CheckCircleIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Phone Call Logger Form */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            {t('phoneCall.logCall')}
          </Typography>
        </Box>

        <Stack spacing={2}>
          {/* Call Type Selection */}
          <FormControl fullWidth size="small">
            <InputLabel id="call-type-label">{t('phoneCall.callType')}</InputLabel>
            <Select
              labelId="call-type-label"
              value={callType}
              label={t('phoneCall.callType')}
              onChange={(e) => handleCallTypeChange(e.target.value as CallType)}
              disabled={submitting}
            >
              <MenuItem value="outbound">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CallIcon fontSize="small" />
                  <span>{t('phoneCall.outbound')}</span>
                </Box>
              </MenuItem>
              <MenuItem value="inbound">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PhoneInTalkIcon fontSize="small" />
                  <span>{t('phoneCall.inbound')}</span>
                </Box>
              </MenuItem>
              <MenuItem value="missed">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PhoneMissedIcon fontSize="small" />
                  <span>{t('phoneCall.missed')}</span>
                </Box>
              </MenuItem>
            </Select>
          </FormControl>

          {/* Phone Numbers */}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <TextField
              label={t('phoneCall.fromNumber')}
              value={fromNumber}
              onChange={(e) => setFromNumber(e.target.value)}
              disabled={submitting}
              fullWidth
              size="small"
              placeholder="+1 (555) 000-0000"
            />
            <TextField
              label={t('phoneCall.toNumber')}
              value={toNumber}
              onChange={(e) => setToNumber(e.target.value)}
              disabled={submitting}
              fullWidth
              size="small"
              placeholder="+1 (555) 000-0000"
            />
          </Stack>

          {/* Duration (disabled for missed calls) */}
          {callType !== 'missed' && (
            <TextField
              label={t('phoneCall.duration')}
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value) || 0)}
              disabled={submitting}
              fullWidth
              size="small"
              inputProps={{ min: 0, step: 1 }}
              helperText={duration > 0 ? formatDuration(duration) : ''}
            />
          )}

          {/* Call Outcome (disabled for missed calls) */}
          {callType !== 'missed' && (
            <FormControl fullWidth size="small">
              <InputLabel id="outcome-label">{t('phoneCall.outcome')}</InputLabel>
              <Select
                labelId="outcome-label"
                value={outcome}
                label={t('phoneCall.outcome')}
                onChange={(e) => setOutcome(e.target.value as CallOutcome)}
                disabled={submitting}
              >
                <MenuItem value="reached">{getOutcomeLabel('reached')}</MenuItem>
                <MenuItem value="left_voicemail">{getOutcomeLabel('left_voicemail')}</MenuItem>
                <MenuItem value="no_answer">{getOutcomeLabel('no_answer')}</MenuItem>
                <MenuItem value="wrong_number">{getOutcomeLabel('wrong_number')}</MenuItem>
                <MenuItem value="call_back_requested">{getOutcomeLabel('call_back_requested')}</MenuItem>
                <MenuItem value="not_interested">{getOutcomeLabel('not_interested')}</MenuItem>
              </Select>
            </FormControl>
          )}

          {/* Call Notes */}
          <TextField
            multiline
            rows={4}
            label={t('phoneCall.notes')}
            placeholder={t('phoneCall.notesPlaceholder')}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={submitting}
            fullWidth
            size="small"
            required={callType !== 'missed'}
          />

          {/* Submit Button */}
          <Button
            variant="contained"
            size="large"
            startIcon={
              submitting ? <CircularProgress size={20} /> : getCallTypeIcon(callType)
            }
            onClick={handleLogCall}
            disabled={submitting || (callType !== 'missed' && (!notes.trim() || duration <= 0))}
            fullWidth
          >
            {submitting ? t('phoneCall.logging') : t('phoneCall.logCall')}
          </Button>

          {/* Helper Text */}
          <Typography variant="caption" color="text.secondary">
            {callType === 'missed'
              ? t('phoneCall.missedCallHint')
              : t('phoneCall.requiredFieldsHint')
            }
          </Typography>
        </Stack>
      </Paper>
    </Stack>
  );
};

export default PhoneCallLogger;
