import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Grid,
  Chip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useNotificationContext } from '../contexts/NotificationContext';
import {
  NotificationType,
  NotificationTypeSettings,
  NotificationPreferencesResponse,
} from '../types/api';

/**
 * Notification preferences component
 *
 * Allows users to manage notification settings per event type.
 * Supports toggling channels (in-app, email, push, SMS),
 * configuring digest frequency, and setting quiet hours.
 *
 * @example
 * ```tsx
 * <NotificationPreferences />
 * ```
 */
export function NotificationPreferences() {
  const { preferences, isLoadingPreferences, loadPreferences, updatePreferences } =
    useNotificationContext();

  const [localPreferences, setLocalPreferences] = useState<NotificationPreferencesResponse | null>(
    null
  );
  const [expandedPanel, setExpandedPanel] = useState<string | false>(false);
  const [updating, setUpdating] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load preferences on mount
  useEffect(() => {
    if (!preferences) {
      loadPreferences();
    } else {
      setLocalPreferences(preferences);
    }
  }, [preferences, loadPreferences]);

  // Handle panel expansion
  const handlePanelChange = (panel: string) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedPanel(isExpanded ? panel : false);
  };

  // Handle channel toggle
  const handleChannelToggle = async (
    type: NotificationType,
    channel: keyof NotificationTypeSettings['channels']
  ) => {
    if (!localPreferences) return;

    const currentSettings = localPreferences.preferences[type];
    const updatedChannels = {
      ...currentSettings.channels,
      [channel]: !currentSettings.channels[channel],
    };

    // Optimistic update
    setLocalPreferences({
      ...localPreferences,
      preferences: {
        ...localPreferences.preferences,
        [type]: {
          ...currentSettings,
          channels: updatedChannels,
        },
      },
    });

    setUpdating({ ...updating, [`${type}-${channel}`]: true });
    setError(null);

    try {
      await updatePreferences(type, {
        channels: updatedChannels,
      });

      setSuccessMessage(`${getNotificationTypeLabel(type)} updated successfully`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError((err as Error).message);

      // Revert on error
      setLocalPreferences({
        ...localPreferences,
        preferences: {
          ...localPreferences.preferences,
          [type]: {
            ...currentSettings,
            channels: currentSettings.channels,
          },
        },
      });
    } finally {
      setUpdating({ ...updating, [`${type}-${channel}`]: false });
    }
  };

  // Handle digest frequency change
  const handleDigestFrequencyChange = async (type: NotificationType, frequency: string) => {
    if (!localPreferences) return;

    const currentSettings = localPreferences.preferences[type];
    const updatedFrequency = frequency as NotificationTypeSettings['digest_frequency'];

    // Optimistic update
    setLocalPreferences({
      ...localPreferences,
      preferences: {
        ...localPreferences.preferences,
        [type]: {
          ...currentSettings,
          digest_frequency: updatedFrequency,
        },
      },
    });

    setUpdating({ ...updating, [`${type}-digest`]: true });
    setError(null);

    try {
      await updatePreferences(type, {
        digest_frequency: updatedFrequency,
      });

      setSuccessMessage(`${getNotificationTypeLabel(type)} digest frequency updated`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError((err as Error).message);

      // Revert on error
      setLocalPreferences({
        ...localPreferences,
        preferences: {
          ...localPreferences.preferences,
          [type]: {
            ...currentSettings,
            digest_frequency: currentSettings.digest_frequency,
          },
        },
      });
    } finally {
      setUpdating({ ...updating, [`${type}-digest`]: false });
    }
  };

  // Handle quiet hours toggle
  const handleQuietHoursToggle = async (type: NotificationType) => {
    if (!localPreferences) return;

    const currentSettings = localPreferences.preferences[type];
    const updatedQuietHours = {
      ...currentSettings.quiet_hours,
      enabled: !currentSettings.quiet_hours.enabled,
    };

    // Optimistic update
    setLocalPreferences({
      ...localPreferences,
      preferences: {
        ...localPreferences.preferences,
        [type]: {
          ...currentSettings,
          quiet_hours: updatedQuietHours,
        },
      },
    });

    setUpdating({ ...updating, [`${type}-quiet`]: true });
    setError(null);

    try {
      await updatePreferences(type, {
        quiet_hours: updatedQuietHours,
      });

      setSuccessMessage(`${getNotificationTypeLabel(type)} quiet hours updated`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError((err as Error).message);

      // Revert on error
      setLocalPreferences({
        ...localPreferences,
        preferences: {
          ...localPreferences.preferences,
          [type]: {
            ...currentSettings,
            quiet_hours: currentSettings.quiet_hours,
          },
        },
      });
    } finally {
      setUpdating({ ...updating, [`${type}-quiet`]: false });
    }
  };

  // Handle quiet hours time change
  const handleQuietHoursTimeChange = async (
    type: NotificationType,
    field: 'start_time' | 'end_time',
    value: string
  ) => {
    if (!localPreferences) return;

    const currentSettings = localPreferences.preferences[type];
    const updatedQuietHours = {
      ...currentSettings.quiet_hours,
      [field]: value,
    };

    // Optimistic update
    setLocalPreferences({
      ...localPreferences,
      preferences: {
        ...localPreferences.preferences,
        [type]: {
          ...currentSettings,
          quiet_hours: updatedQuietHours,
        },
      },
    });

    setUpdating({ ...updating, [`${type}-${field}`]: true });
    setError(null);

    try {
      await updatePreferences(type, {
        quiet_hours: updatedQuietHours,
      });

      setSuccessMessage(`${getNotificationTypeLabel(type)} quiet hours updated`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError((err as Error).message);

      // Revert on error
      setLocalPreferences({
        ...localPreferences,
        preferences: {
          ...localPreferences.preferences,
          [type]: {
            ...currentSettings,
            quiet_hours: currentSettings.quiet_hours,
          },
        },
      });
    } finally {
      setUpdating({ ...updating, [`${type}-${field}`]: false });
    }
  };

  if (isLoadingPreferences || !localPreferences) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const notificationTypes: NotificationType[] = [
    'candidate_applied',
    'candidate_responded',
    'resume_uploaded',
    'candidate_moved',
    'new_match',
    'interview_scheduled',
    'offer_sent',
    'offer_accepted',
    'offer_rejected',
    'reminder',
    'system',
  ];

  return (
    <Box>
      {/* Success Message */}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Typography variant="h6" fontWeight={600} gutterBottom>
        Notification Preferences
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Customize how you receive notifications for different event types
      </Typography>

      {notificationTypes.map((type) => {
        const settings = localPreferences.preferences[type];
        const isUpdating = Object.keys(updating).some((key) => key.startsWith(type));

        return (
          <Accordion
            key={type}
            expanded={expandedPanel === type}
            onChange={handlePanelChange(type)}
            disabled={isUpdating}
            sx={{
              mb: 1,
              opacity: isUpdating ? 0.6 : 1,
              transition: 'opacity 0.2s',
            }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Typography fontWeight={600}>{getNotificationTypeLabel(type)}</Typography>
                <Chip
                  size="small"
                  label={settings.digest_frequency}
                  color={settings.digest_frequency === 'immediate' ? 'primary' : 'default'}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {/* Channel Toggles */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Delivery Channels
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="In-App Notifications" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={settings.channels.in_app}
                          onChange={() => handleChannelToggle(type, 'in_app')}
                          disabled={updating[`${type}-in_app`]}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Email" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={settings.channels.email}
                          onChange={() => handleChannelToggle(type, 'email')}
                          disabled={updating[`${type}-email`]}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Push Notifications" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={settings.channels.push}
                          onChange={() => handleChannelToggle(type, 'push')}
                          disabled={updating[`${type}-push`]}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="SMS" />
                      <ListItemSecondaryAction>
                        <Switch
                          checked={settings.channels.sms}
                          onChange={() => handleChannelToggle(type, 'sms')}
                          disabled={updating[`${type}-sms`]}
                        />
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                </Grid>

                <Grid item xs={12}>
                  <Divider />
                </Grid>

                {/* Digest Frequency */}
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Digest Frequency</InputLabel>
                    <Select
                      value={settings.digest_frequency}
                      label="Digest Frequency"
                      onChange={(e) =>
                        handleDigestFrequencyChange(type, e.target.value as string)
                      }
                      disabled={updating[`${type}-digest`]}
                    >
                      <MenuItem value="immediate">Immediate</MenuItem>
                      <MenuItem value="hourly">Hourly</MenuItem>
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="weekly">Weekly</MenuItem>
                      <MenuItem value="never">Never</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                {/* Quiet Hours */}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="subtitle2">Quiet Hours</Typography>
                    <Switch
                      checked={settings.quiet_hours.enabled}
                      onChange={() => handleQuietHoursToggle(type)}
                      disabled={updating[`${type}-quiet`]}
                    />
                  </Box>
                </Grid>

                {settings.quiet_hours.enabled && (
                  <>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        type="time"
                        label="Start Time"
                        value={settings.quiet_hours.start_time}
                        onChange={(e) =>
                          handleQuietHoursTimeChange(type, 'start_time', e.target.value)
                        }
                        disabled={updating[`${type}-start_time`]}
                        size="small"
                        inputProps={{ step: 300 }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        type="time"
                        label="End Time"
                        value={settings.quiet_hours.end_time}
                        onChange={(e) =>
                          handleQuietHoursTimeChange(type, 'end_time', e.target.value)
                        }
                        disabled={updating[`${type}-end_time`]}
                        size="small"
                        inputProps={{ step: 300 }}
                      />
                    </Grid>
                  </>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Box>
  );
}

/**
 * Get human-readable label for notification type
 */
function getNotificationTypeLabel(type: NotificationType): string {
  const labels: Record<NotificationType, string> = {
    candidate_applied: 'Candidate Applied',
    candidate_responded: 'Candidate Responded',
    resume_uploaded: 'Resume Uploaded',
    candidate_moved: 'Candidate Moved',
    new_match: 'New Match',
    interview_scheduled: 'Interview Scheduled',
    offer_sent: 'Offer Sent',
    offer_accepted: 'Offer Accepted',
    offer_rejected: 'Offer Rejected',
    reminder: 'Reminder',
    system: 'System',
    digest: 'Digest',
  };
  return labels[type] || type;
}
