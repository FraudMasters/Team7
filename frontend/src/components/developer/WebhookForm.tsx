/**
 * Webhook Form Component
 *
 * Dialog component for creating new webhook subscriptions with URL, events, and secret.
 *
 * @module components/developer/WebhookForm
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Box,
  Typography,
  Alert,
  AlertTitle,
  Chip,
  Divider,
  Stack,
  CircularProgress,
  InputAdornment,
  Link,
} from '@mui/material';
import {
  Webhook as WebhookIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Http as HttpIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { webhooksClient, WebhookEventType, type CreateWebhookSubscriptionRequest } from '@/api/webhooks';

/**
 * Available event options grouped by category
 */
const EVENT_GROUPS = {
  'Candidate Events': [
    { value: WebhookEventType.CandidateCreated, label: 'Candidate Created', description: 'When a new candidate is added' },
    { value: WebhookEventType.CandidateUpdated, label: 'Candidate Updated', description: 'When candidate details change' },
    { value: WebhookEventType.CandidateDeleted, label: 'Candidate Deleted', description: 'When a candidate is removed' },
  ],
  'Ranking Events': [
    { value: WebhookEventType.RankingCreated, label: 'Ranking Created', description: 'When a candidate is ranked' },
    { value: WebhookEventType.RankingUpdated, label: 'Ranking Updated', description: 'When ranking scores change' },
    { value: WebhookEventType.RankingDeleted, label: 'Ranking Deleted', description: 'When a ranking is removed' },
  ],
  'Status & Stage Events': [
    { value: WebhookEventType.StatusChanged, label: 'Status Changed', description: 'When candidate status changes' },
    { value: WebhookEventType.StageChanged, label: 'Stage Changed', description: 'When candidate moves to a new stage' },
  ],
  'Resume Events': [
    { value: WebhookEventType.ResumeUploaded, label: 'Resume Uploaded', description: 'When a resume is uploaded' },
    { value: WebhookEventType.ResumeProcessed, label: 'Resume Processed', description: 'When resume parsing completes' },
    { value: WebhookEventType.ResumeAnalyzed, label: 'Resume Analyzed', description: 'When resume analysis finishes' },
  ],
  'Vacancy Events': [
    { value: WebhookEventType.VacancyCreated, label: 'Vacancy Created', description: 'When a job vacancy is created' },
    { value: WebhookEventType.VacancyUpdated, label: 'Vacancy Updated', description: 'When vacancy details change' },
    { value: WebhookEventType.VacancyFilled, label: 'Vacancy Filled', description: 'When a vacancy is marked filled' },
  ],
  'Match Events': [
    { value: WebhookEventType.MatchCreated, label: 'Match Created', description: 'When a candidate-vacancy match is created' },
    { value: WebhookEventType.MatchUpdated, label: 'Match Updated', description: 'When match scores change' },
  ],
  'Workflow Events': [
    { value: WebhookEventType.WorkflowTriggered, label: 'Workflow Triggered', description: 'When a workflow automation is triggered' },
    { value: WebhookEventType.WorkflowCompleted, label: 'Workflow Completed', description: 'When a workflow finishes successfully' },
    { value: WebhookEventType.WorkflowFailed, label: 'Workflow Failed', description: 'When a workflow encounters an error' },
  ],
  'Other Events': [
    { value: WebhookEventType.FeedbackSubmitted, label: 'Feedback Submitted', description: 'When feedback is submitted' },
    { value: WebhookEventType.NoteCreated, label: 'Note Created', description: 'When a candidate note is added' },
    { value: WebhookEventType.NoteUpdated, label: 'Note Updated', description: 'When a candidate note is modified' },
    { value: WebhookEventType.ReportGenerated, label: 'Report Generated', description: 'When a report is generated' },
    { value: WebhookEventType.ReportExported, label: 'Report Exported', description: 'When a report is exported' },
  ],
} as const;

interface WebhookFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * WebhookForm Component
 *
 * Provides a form dialog for creating new webhook subscriptions with:
 * - Endpoint URL input
 * - Event selection (grouped by category)
 * - Optional HMAC secret for signature verification
 *
 * @example
 * ```tsx
 * <WebhookForm
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   onSuccess={() => console.log('Webhook created')}
 * />
 * ```
 */
const WebhookForm: React.FC<WebhookFormProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [url, setUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set());
  const [secret, setSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEventToggle = (event: string) => {
    const newEvents = new Set(selectedEvents);
    if (newEvents.has(event)) {
      newEvents.delete(event);
    } else {
      newEvents.add(event);
    }
    setSelectedEvents(newEvents);
  };

  const handleSubmit = async () => {
    if (!url.trim()) {
      setError('Please enter a webhook URL');
      return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setError('URL must start with http:// or https://');
      return;
    }

    if (selectedEvents.size === 0) {
      setError('Please select at least one event');
      return;
    }

    if (secret && secret.length < 8) {
      setError('Secret must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: CreateWebhookSubscriptionRequest = {
        url: url.trim(),
        events: Array.from(selectedEvents),
      };

      // Add secret if provided
      if (secret) {
        request.secret = secret;
      }

      await webhooksClient.createSubscription(request);
      onSuccess();

      // Reset form
      setUrl('');
      setSelectedEvents(new Set());
      setSecret('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create webhook subscription');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setUrl('');
      setSelectedEvents(new Set());
      setSecret('');
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <WebhookIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Create Webhook Subscription
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Error Alert */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          )}

          {/* Info Alert */}
          <Alert severity="info">
            <AlertTitle>Webhook Configuration</AlertTitle>
            Configure an endpoint URL to receive real-time event notifications.
            Optionally add a secret for HMAC signature verification.
          </Alert>

          {/* URL Input */}
          <TextField
            label="Webhook URL"
            fullWidth
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/webhook"
            disabled={loading}
            helperText="The endpoint URL that will receive webhook POST requests"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <HttpIcon color="action" />
                </InputAdornment>
              ),
            }}
          />

          {/* Events Selection */}
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Select Events
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose which events you want to receive notifications for. Select at least one event.
            </Typography>

            {Object.entries(EVENT_GROUPS).map(([groupName, events]) => (
              <Box key={groupName} sx={{ mb: 2 }}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                  sx={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  {groupName}
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {events.map((event) => (
                    <Chip
                      key={event.value}
                      label={event.label}
                      onClick={() => handleEventToggle(event.value)}
                      color={selectedEvents.has(event.value) ? 'primary' : 'default'}
                      variant={selectedEvents.has(event.value) ? 'filled' : 'outlined'}
                      clickable
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
            ))}

            {selectedEvents.size > 0 && (
              <Box sx={{ mt: 2 }}>
                <Divider sx={{ mb: 1 }} />
                <Typography variant="caption" color="text.secondary">
                  Selected: {selectedEvents.size} event{selectedEvents.size !== 1 ? 's' : ''}
                </Typography>
              </Box>
            )}
          </Box>

          {/* Secret Configuration */}
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Secret (Optional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add a secret to enable HMAC signature verification for enhanced security.
              Webhooks will include an <code>X-AgentHR-Signature</code> header.
            </Typography>

            <TextField
              label="HMAC Secret"
              fullWidth
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Enter a secret key (min 8 characters)"
              disabled={loading}
              type="password"
              helperText="Leave empty to disable signature verification"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />

            {secret && secret.length >= 8 && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <AlertTitle>Signature Verification Enabled</AlertTitle>
                Webhook deliveries will include an HMAC-SHA256 signature in the
                <code>X-AgentHR-Signature</code> header. Verify this signature on your server
                to ensure webhook authenticity.
              </Alert>
            )}
          </Box>

          {/* Documentation Link */}
          <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Need Help?
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Learn more about webhooks and signature verification in our{' '}
              <Link href="#" underline="hover">
                webhook documentation
              </Link>.
            </Typography>
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={loading} startIcon={<CloseIcon />}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !url.trim() || selectedEvents.size === 0}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Creating...' : 'Create Webhook'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WebhookForm;
