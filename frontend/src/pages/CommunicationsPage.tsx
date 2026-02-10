/**
 * Communications Page
 *
 * Provides comprehensive communication tracking and management functionality including:
 * - Timeline view of all communications
 * - Email management and tracking
 * - SMS message management
 * - Call log tracking
 * - Template management for emails and SMS
 * - Settings for email sync configuration
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  Paper,
  Grid,
  Chip,
  Button,
  TextField,
  Alert,
  Stack,
  IconButton,
  LinearProgress,
  CircularProgress,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Phone as PhoneIcon,
  Description as TemplateIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import axios from 'axios';

/**
 * Tab panel type
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

/**
 * Tab panel component
 */
const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

/**
 * Communication types
 */
type CommunicationTab = 'timeline' | 'emails' | 'sms' | 'calls' | 'templates' | 'settings';

interface CommunicationLog {
  id: string;
  type: 'email' | 'sms' | 'call';
  candidate_id?: string;
  candidate_name?: string;
  subject?: string;
  content: string;
  direction: 'inbound' | 'outbound';
  status: 'sent' | 'delivered' | 'failed' | 'pending';
  created_at: string;
  metadata?: Record<string, unknown>;
}

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  category: string;
  variables: string[];
  created_at: string;
  updated_at: string;
}

interface EmailSyncConfig {
  provider: 'gmail' | 'outlook' | 'imap';
  enabled: boolean;
  email_address?: string;
  last_sync?: string;
  sync_frequency_minutes: number;
}

const CommunicationsPage: React.FC = () => {
  const { t } = useTranslation();
  const [currentTab, setCurrentTab] = useState<CommunicationTab>('timeline');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [communications, setCommunications] = useState<CommunicationLog[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [syncConfig, setSyncConfig] = useState<EmailSyncConfig>({
    provider: 'gmail',
    enabled: false,
    sync_frequency_minutes: 30,
  });

  // Fetch communications on mount
  useEffect(() => {
    fetchCommunications();
    fetchTemplates();
    fetchSyncConfig();
  }, []);

  const fetchCommunications = async () => {
    try {
      setLoading(true);
      setError(null);
      // Placeholder for API call
      // const response = await axios.get('/api/communications/');
      // setCommunications(response.data);
      setCommunications([]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch communications';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      // Placeholder for API call
      // const response = await axios.get('/api/communications/templates');
      // setTemplates(response.data);
      setTemplates([]);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  };

  const fetchSyncConfig = async () => {
    try {
      // Placeholder for API call
      // const response = await axios.get('/api/communications/email-sync/config');
      // setSyncConfig(response.data);
    } catch (err) {
      console.error('Failed to fetch sync config:', err);
    }
  };

  const getCommunicationIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <EmailIcon />;
      case 'sms':
        return <SmsIcon />;
      case 'call':
        return <PhoneIcon />;
      default:
        return <TimelineIcon />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'info' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'sent':
      case 'delivered':
        return 'success';
      case 'pending':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDirectionColor = (direction: string): 'info' | 'success' => {
    return direction === 'inbound' ? 'info' : 'success';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <EmailIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            Communications
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchCommunications}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
          >
            New Message
          </Button>
        </Stack>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={
            currentTab === 'timeline' ? 0 :
            currentTab === 'emails' ? 1 :
            currentTab === 'sms' ? 2 :
            currentTab === 'calls' ? 3 :
            currentTab === 'templates' ? 4 :
            5
          }
          onChange={(_, newValue) => {
            setCurrentTab(
              newValue === 0 ? 'timeline' :
              newValue === 1 ? 'emails' :
              newValue === 2 ? 'sms' :
              newValue === 3 ? 'calls' :
              newValue === 4 ? 'templates' :
              'settings'
            );
          }}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            icon={<TimelineIcon />}
            label="Timeline"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<EmailIcon />}
            label="Emails"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<SmsIcon />}
            label="SMS"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<PhoneIcon />}
            label="Calls"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<TemplateIcon />}
            label="Templates"
            sx={{ textTransform: 'none' }}
          />
          <Tab
            icon={<SettingsIcon />}
            label="Settings"
            sx={{ textTransform: 'none' }}
          />
        </Tabs>

        {/* Timeline Tab */}
        <TabPanel value={0} index={currentTab === 'timeline' ? 0 : -1}>
          <Box sx={{ px: 2 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : communications.length === 0 ? (
              <Card sx={{ textAlign: 'center', py: 6 }}>
                <TimelineIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No communications yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Start communicating with candidates to see them here
                </Typography>
              </Card>
            ) : (
              <Stack spacing={2}>
                {communications.map((comm) => (
                  <Card key={comm.id} variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <Box sx={{ color: 'primary.main' }}>
                          {getCommunicationIcon(comm.type)}
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {comm.type === 'email' && comm.subject ? comm.subject : `${comm.type} message`}
                          </Typography>
                          {comm.candidate_name && (
                            <Typography variant="body2" color="text.secondary">
                              with {comm.candidate_name}
                            </Typography>
                          )}
                        </Box>
                        <Stack direction="row" spacing={1}>
                          <Chip
                            label={comm.direction}
                            size="small"
                            color={getDirectionColor(comm.direction)}
                          />
                          <Chip
                            label={comm.status}
                            size="small"
                            color={getStatusColor(comm.status)}
                          />
                        </Stack>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {comm.content}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                        {format(new Date(comm.created_at), 'PPPp')}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            )}
          </Box>
        </TabPanel>

        {/* Emails Tab */}
        <TabPanel value={1} index={currentTab === 'emails' ? 1 : -1}>
          <Box sx={{ px: 2 }}>
            <Typography variant="h6" gutterBottom>
              Email Communications
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Email management features coming soon. Configure email sync in Settings.
            </Alert>
          </Box>
        </TabPanel>

        {/* SMS Tab */}
        <TabPanel value={2} index={currentTab === 'sms' ? 2 : -1}>
          <Box sx={{ px: 2 }}>
            <Typography variant="h6" gutterBottom>
              SMS Messages
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              SMS management features coming soon.
            </Alert>
          </Box>
        </TabPanel>

        {/* Calls Tab */}
        <TabPanel value={3} index={currentTab === 'calls' ? 3 : -1}>
          <Box sx={{ px: 2 }}>
            <Typography variant="h6" gutterBottom>
              Call Logs
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Call logging features coming soon.
            </Alert>
          </Box>
        </TabPanel>

        {/* Templates Tab */}
        <TabPanel value={4} index={currentTab === 'templates' ? 4 : -1}>
          <Box sx={{ px: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Message Templates
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                size="small"
              >
                New Template
              </Button>
            </Box>
            {templates.length === 0 ? (
              <Card sx={{ textAlign: 'center', py: 6 }}>
                <TemplateIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No templates yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create templates for common communications
                </Typography>
              </Card>
            ) : (
              <Grid container spacing={2}>
                {templates.map((template) => (
                  <Grid item xs={12} md={6} key={template.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box>
                            <Typography variant="subtitle1" fontWeight={600}>
                              {template.name}
                            </Typography>
                            <Chip label={template.category} size="small" sx={{ mt: 1 }} />
                          </Box>
                          <Stack direction="row" spacing={1}>
                            <IconButton size="small">
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small" color="error">
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Stack>
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Subject: {template.subject}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {template.body.substring(0, 100)}
                          {template.body.length > 100 && '...'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={5} index={currentTab === 'settings' ? 5 : -1}>
          <Box sx={{ px: 2 }}>
            <Typography variant="h6" gutterBottom>
              Email Sync Configuration
            </Typography>

            <Grid container spacing={3} sx={{ mt: 2 }}>
              {/* Email Provider */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Email Provider
                    </Typography>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Connect your email account to automatically sync communications
                    </Alert>
                    <Stack spacing={2}>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<EmailIcon />}
                      >
                        Connect Gmail
                      </Button>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<EmailIcon />}
                      >
                        Connect Outlook
                      </Button>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<EmailIcon />}
                      >
                        Configure IMAP/SMTP
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Sync Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Sync Settings
                    </Typography>
                    <Stack spacing={3}>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Sync Frequency
                        </Typography>
                        <TextField
                          fullWidth
                          type="number"
                          defaultValue={30}
                          helperText="How often to check for new emails automatically (recommended: 15-60 minutes)"
                          size="small"
                        />
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Last Sync
                        </Typography>
                        <Typography variant="body1">
                          {syncConfig.last_sync
                            ? format(new Date(syncConfig.last_sync), 'PPPp')
                            : 'Never synced'
                          }
                        </Typography>
                      </Box>
                      <Button
                        variant="contained"
                        startIcon={<RefreshIcon />}
                        disabled={!syncConfig.enabled}
                      >
                        Sync Now
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* SMS Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      SMS Configuration
                    </Typography>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Configure SMS provider for text message communications
                    </Alert>
                    <Stack spacing={2}>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<SmsIcon />}
                      >
                        Configure Twilio
                      </Button>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<SmsIcon />}
                      >
                        Configure AWS SNS
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Call Settings */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Call Integration
                    </Typography>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Integrate with phone systems for call logging
                    </Alert>
                    <Stack spacing={2}>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<PhoneIcon />}
                      >
                        Configure Twilio
                      </Button>
                      <Button
                        variant="outlined"
                        fullWidth
                        startIcon={<PhoneIcon />}
                      >
                        Configure RingCentral
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      {/* Stats Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EmailIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Communications
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {communications.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EmailIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Emails
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {communications.filter((c) => c.type === 'email').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SmsIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  SMS
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {communications.filter((c) => c.type === 'sms').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TemplateIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Templates
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {templates.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CommunicationsPage;
