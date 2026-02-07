import React, { useState, useCallback, useEffect } from 'react';
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
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  TextareaAutosize,
} from '@mui/material';
import {
  Send as SendIcon,
  Sms as SmsIcon,
  CheckCircle as CheckCircleIcon,
  FormatSize as FormatSizeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { smsClient } from '@/api/sms';
import { communicationTemplatesClient } from '@/api/communicationTemplates';
import type {
  SMSResponse,
  SMSSendRequest,
  CommunicationTemplateResponse,
  ApiError,
} from '@/types/api';

/**
 * SMSComposer Component Props
 */
interface SMSComposerProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Phone number to send SMS to */
  toNumber: string;
  /** Recruiter ID (current user) for sending SMS */
  recruiterId?: string;
  /** Optional vacancy ID associated with this communication */
  vacancyId?: string;
  /** Whether the component is read-only (no send) */
  readOnly?: boolean;
  /** Callback when SMS is sent successfully */
  onSMSSent?: (sms: SMSResponse) => void;
  /** Default provider to use (Twilio, AWS SNS, etc.) */
  defaultProvider?: string;
  /** Maximum character limit for SMS (default: 160) */
  maxCharacters?: number;
  /** Show template selection */
  showTemplates?: boolean;
}

/**
 * SMSComposer Component
 *
 * Provides SMS composition and sending functionality:
 * - Text input with character count
 * - Template selection and variable substitution
 * - SMS sending with delivery tracking
 * - Error handling and validation
 * - Support for multi-segment messages
 *
 * @example
 * ```tsx
 * <SMSComposer
 *   resumeId="resume-uuid"
 *   toNumber="+1234567890"
 *   recruiterId="recruiter-uuid"
 *   onSMSSent={(sms) => console.log('SMS sent:', sms)}
 * />
 *
 * <SMSComposer
 *   resumeId="resume-uuid"
 *   toNumber="+1234567890"
 *   recruiterId="recruiter-uuid"
 *   vacancyId="vacancy-uuid"
 *   defaultProvider="Twilio"
 *   showTemplates
 * />
 * ```
 */
const SMSComposer: React.FC<SMSComposerProps> = ({
  resumeId,
  toNumber,
  recruiterId,
  vacancyId,
  readOnly = false,
  onSMSSent,
  defaultProvider = 'Twilio',
  maxCharacters = 160,
  showTemplates = true,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // SMS composition state
  const [message, setMessage] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [provider, setProvider] = useState(defaultProvider);

  // Templates state
  const [templates, setTemplates] = useState<CommunicationTemplateResponse[]>([]);

  /**
   * Fetch SMS templates
   */
  const fetchTemplates = useCallback(async () => {
    if (!showTemplates) return;

    try {
      setTemplatesLoading(true);
      const response = await communicationTemplatesClient.listTemplates(
        0,
        50,
        'sms',
        undefined,
        undefined,
        true
      );
      setTemplates(response.templates);
    } catch (err) {
      const apiError = err as ApiError;
      // Don't show error for template loading failure, just log it
      console.warn('Failed to load SMS templates:', apiError.detail);
    } finally {
      setTemplatesLoading(false);
    }
  }, [showTemplates]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  /**
   * Calculate character count and segment information
   */
  const characterCount = message.length;
  const segmentCount = Math.ceil(characterCount / maxCharacters) || 1;
  const remainingCharacters = maxCharacters - (characterCount % maxCharacters);

  /**
   * Handle template selection
   */
  const handleTemplateChange = useCallback(
    async (templateId: string) => {
      setSelectedTemplateId(templateId);

      if (!templateId) {
        setMessage('');
        return;
      }

      try {
        setLoading(true);
        const template = await communicationTemplatesClient.getTemplate(templateId);

        // Use template body as message
        // Note: Variables in the template would need to be substituted
        // For now, we'll use the body as-is
        setMessage(template.body);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to load template. Please try again.');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * Handle sending SMS
   */
  const handleSendSMS = useCallback(async () => {
    if (!message.trim()) {
      setError('Message content cannot be empty.');
      return;
    }

    if (!recruiterId) {
      setError('Recruiter ID is required to send SMS.');
      return;
    }

    if (!toNumber) {
      setError('Recipient phone number is required.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const smsData: SMSSendRequest = {
        candidate_id: resumeId,
        recruiter_id: recruiterId,
        to_number: toNumber,
        message: message.trim(),
        provider,
        ...(vacancyId && { vacancy_id: vacancyId }),
      };

      const response = await smsClient.send(smsData);

      // Reset form
      setMessage('');
      setSelectedTemplateId('');

      setSuccessMessage('SMS sent successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Notify parent
      onSMSSent?.(response);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to send SMS. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [resumeId, recruiterId, toNumber, vacancyId, message, provider, onSMSSent]);

  /**
   * Get character count color based on remaining characters
   */
  const getCharacterCountColor = (): 'error' | 'warning' | 'success' => {
    if (remainingCharacters === 0 && characterCount > 0) return 'error';
    if (remainingCharacters < 20) return 'warning';
    return 'success';
  };

  if (readOnly) {
    return null;
  }

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

      {/* SMS Composer Form */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SmsIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            {t('sms.composeTitle')}
          </Typography>
        </Box>

        <Stack spacing={2}>
          {/* Template Selection */}
          {showTemplates && templates.length > 0 && (
            <FormControl fullWidth size="small">
              <InputLabel id="sms-template-label">{t('sms.selectTemplate')}</InputLabel>
              <Select
                labelId="sms-template-label"
                value={selectedTemplateId}
                onChange={(e) => handleTemplateChange(e.target.value)}
                label={t('sms.selectTemplate')}
                disabled={templatesLoading || submitting}
              >
                <MenuItem value="">
                  <em>{t('sms.noTemplate')}</em>
                </MenuItem>
                {templates.map((template) => (
                  <MenuItem key={template.id} value={template.id}>
                    {template.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {/* Provider Selection */}
          <FormControl fullWidth size="small">
            <InputLabel id="sms-provider-label">{t('sms.provider')}</InputLabel>
            <Select
              labelId="sms-provider-label"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              label={t('sms.provider')}
              disabled={submitting}
            >
              <MenuItem value="Twilio">Twilio</MenuItem>
              <MenuItem value="AWS SNS">AWS SNS</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>

          {/* Message Input */}
          <TextField
            multiline
            rows={4}
            placeholder={t('sms.messagePlaceholder')}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={submitting}
            fullWidth
            size="small"
            inputProps={{
              maxLength: maxCharacters * 10, // Allow up to 10 segments
            }}
          />

          {/* Character Count and Segments */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FormatSizeIcon fontSize="small" color={getCharacterCountColor()} />
              <Typography variant="caption" color="text.secondary">
                {characterCount} / {maxCharacters * 10}
              </Typography>
              <Chip
                label={`${segmentCount} segment${segmentCount > 1 ? 's' : ''}`}
                size="small"
                color={segmentCount > 1 ? 'warning' : 'default'}
              />
            </Box>

            <Typography
              variant="caption"
              color={getCharacterCountColor() === 'error' ? 'error.main' : 'text.secondary'}
            >
              {remainingCharacters} remaining
            </Typography>
          </Box>

          {/* Recipient Info */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant="caption" color="text.secondary">
              {t('sms.to')}: {toNumber}
            </Typography>

            <Button
              variant="contained"
              size="small"
              startIcon={
                submitting ? <CircularProgress size={16} /> : <SendIcon />
              }
              onClick={handleSendSMS}
              disabled={!message.trim() || submitting || loading}
            >
              {t('sms.send')}
            </Button>
          </Box>

          {/* Hint Text */}
          <Typography variant="caption" color="text.secondary">
            {segmentCount > 1
              ? t('sms.multiSegmentHint', { segments: segmentCount })
              : t('sms.singleSegmentHint')}
          </Typography>
        </Stack>
      </Paper>
    </Stack>
  );
};

export default SMSComposer;
