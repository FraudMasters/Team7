import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  Alert,
  AlertTitle,
  Stack,
  Tab,
  Tabs,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Download as DownloadIcon,
  DeleteForever as DeleteIcon,
  Description as DocumentIcon,
  Security as SecurityIcon,
  Cookie as CookieIcon,
  Visibility as VisibilityIcon,
  Gavel as GavelIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { PageTransition } from '../../components/ui/PageTransition';
import ConsentManager from '../../components/ConsentManager';
import DataExportDialog from '../../components/DataExportDialog';
import DataDeletionRequest from '../../components/DataDeletionRequest';

/**
 * Tab Panel Component
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`privacy-tabpanel-${index}`}
      aria-labelledby={`privacy-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Privacy Settings Page
 *
 * Comprehensive GDPR compliance page providing:
 * - Consent management for all data processing activities
 * - Data export functionality (right to data portability)
 * - Data deletion requests (right to be forgotten)
 * - Cookie preferences management
 * - Information about GDPR rights
 *
 * Accessible at: /settings/privacy
 */
export function PrivacySettingsPage() {
  const { t } = useTranslation();
  const [currentTab, setCurrentTab] = useState(0);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Mock resume ID - in production this would come from auth context
  const resumeId = 'demo-resume-id';

  /**
   * Handle tab change
   */
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  /**
   * Handle opening export dialog
   */
  const handleOpenExport = () => {
    setExportDialogOpen(true);
  };

  /**
   * Handle opening delete dialog
   */
  const handleOpenDelete = () => {
    setDeleteDialogOpen(true);
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <ShieldIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Privacy Settings
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Manage your data privacy and GDPR rights
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* GDPR Rights Notice */}
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 4 }}>
          <AlertTitle>Your GDPR Rights</AlertTitle>
          <Typography variant="body2">
            Under GDPR, you have the right to access, rectify, erase, restrict processing, data
            portability, and object to processing. This page gives you control over your personal
            data.
          </Typography>
        </Alert>

        {/* Main Content */}
        <Grid container spacing={3}>
          {/* Quick Actions */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Quick Actions
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Common privacy-related actions for managing your data
              </Typography>

              <Grid container spacing={2}>
                {/* Export Data */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card
                    variant="outlined"
                    sx={{
                      height: '100%',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                        borderColor: 'primary.main',
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        <DownloadIcon
                          sx={{ fontSize: 40, color: 'primary.main', mb: 2 }}
                        />
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          Export My Data
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
                          Download all your personal data in JSON or CSV format
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={handleOpenExport}
                          fullWidth
                        >
                          Export
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Delete Account */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card
                    variant="outlined"
                    sx={{
                      height: '100%',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      borderColor: 'error.main',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        <DeleteIcon
                          sx={{ fontSize: 40, color: 'error.main', mb: 2 }}
                        />
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom color="error.main">
                          Delete Account
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
                          Permanently delete all your personal data
                        </Typography>
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          onClick={handleOpenDelete}
                          fullWidth
                        >
                          Delete
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* View Consent */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card
                    variant="outlined"
                    sx={{
                      height: '100%',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                        borderColor: 'info.main',
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        <VisibilityIcon
                          sx={{ fontSize: 40, color: 'info.main', mb: 2 }}
                        />
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          View Consents
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
                          See what you've consented to and manage permissions
                        </Typography>
                        <Button
                          variant="outlined"
                          color="info"
                          size="small"
                          onClick={() => setCurrentTab(0)}
                          fullWidth
                        >
                          View
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Privacy Policy */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card
                    variant="outlined"
                    sx={{
                      height: '100%',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                        borderColor: 'success.main',
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        <DocumentIcon
                          sx={{ fontSize: 40, color: 'success.main', mb: 2 }}
                        />
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          Privacy Policy
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
                          Read our detailed privacy policy and data practices
                        </Typography>
                        <Button
                          variant="outlined"
                          color="success"
                          size="small"
                          href="/privacy-policy"
                          target="_blank"
                          fullWidth
                        >
                          Read
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Tabbed Content */}
          <Grid item xs={12}>
            <Paper sx={{ width: '100%' }}>
              <Tabs
                value={currentTab}
                onChange={handleTabChange}
                aria-label="Privacy settings tabs"
                sx={{
                  borderBottom: 1,
                  borderColor: 'divider',
                  px: 2,
                }}
              >
                <Tab
                  icon={<SecurityIcon />}
                  label="Consent Management"
                  id="privacy-tab-0"
                  aria-controls="privacy-tabpanel-0"
                />
                <Tab
                  icon={<GavelIcon />}
                  label="Your Rights"
                  id="privacy-tab-1"
                  aria-controls="privacy-tabpanel-1"
                />
                <Tab
                  icon={<CookieIcon />}
                  label="Cookie Settings"
                  id="privacy-tab-2"
                  aria-controls="privacy-tabpanel-2"
                />
              </Tabs>

              {/* Consent Management Tab */}
              <TabPanel value={currentTab} index={0}>
                <Box sx={{ px: 2 }}>
                  <Alert severity="info" sx={{ mb: 3 }}>
                    <AlertTitle>Manage Your Consents</AlertTitle>
                    <Typography variant="body2">
                      You can grant or revoke consent for various data processing activities at any
                      time. Required consents are marked and cannot be disabled.
                    </Typography>
                  </Alert>

                  <ConsentManager userId={currentTab === 0 ? resumeId : undefined} />
                </Box>
              </TabPanel>

              {/* Your Rights Tab */}
              <TabPanel value={currentTab} index={1}>
                <Box sx={{ px: 2 }}>
                  <Stack spacing={3}>
                    <Typography variant="h6" fontWeight={600}>
                      Your GDPR Rights
                    </Typography>

                    <Alert severity="success">
                      <AlertTitle>Right to Information</AlertTitle>
                      <Typography variant="body2">
                        You have the right to be informed about how your personal data is being
                        used. Our privacy policy provides detailed information about data collection,
                        processing, and storage.
                      </Typography>
                    </Alert>

                    <Alert severity="info">
                      <AlertTitle>Right to Access</AlertTitle>
                      <Typography variant="body2">
                        You can request a copy of all your personal data that we hold. Use the "Export
                        My Data" button above to download your information.
                      </Typography>
                    </Alert>

                    <Alert severity="warning">
                      <AlertTitle>Right to Rectification</AlertTitle>
                      <Typography variant="body2">
                        You have the right to correct inaccurate or incomplete data. Visit your
                        profile page to update your personal information.
                      </Typography>
                    </Alert>

                    <Alert severity="error">
                      <AlertTitle>Right to Erasure (Right to be Forgotten)</AlertTitle>
                      <Typography variant="body2">
                        You can request the deletion of your personal data. Use the "Delete Account"
                        button above to submit a deletion request. This action cannot be undone.
                      </Typography>
                    </Alert>

                    <Alert severity="info">
                      <AlertTitle>Right to Restrict Processing</AlertTitle>
                      <Typography variant="body2">
                        You can request that we limit how we use your data. This doesn't delete the
                        data but prevents certain processing activities.
                      </Typography>
                    </Alert>

                    <Alert severity="success">
                      <AlertTitle>Right to Data Portability</AlertTitle>
                      <Typography variant="body2">
                        You have the right to receive your data in a structured, commonly used
                        format. The export functionality provides your data in JSON or CSV format.
                      </Typography>
                    </Alert>

                    <Alert severity="warning">
                      <AlertTitle>Right to Object</AlertTitle>
                      <Typography variant="body2">
                        You can object to certain processing activities, such as direct marketing or
                        automated decision-making.
                      </Typography>
                    </Alert>

                    <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                        Need Help?
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        If you have questions about your privacy rights or need assistance exercising
                        them, please contact our Data Protection Officer.
                      </Typography>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<DocumentIcon />}
                        href="mailto:dpo@agenthr.com"
                      >
                        Contact DPO
                      </Button>
                    </Box>
                  </Stack>
                </Box>
              </TabPanel>

              {/* Cookie Settings Tab */}
              <TabPanel value={currentTab} index={2}>
                <Box sx={{ px: 2 }}>
                  <Stack spacing={3}>
                    <Typography variant="h6" fontWeight={600}>
                      Cookie Preferences
                    </Typography>

                    <Alert severity="info">
                      <AlertTitle>About Cookies</AlertTitle>
                      <Typography variant="body2" paragraph>
                        Cookies are small text files stored on your device when you visit our
                        website. They help us provide you with a better experience by remembering
                        your preferences and understanding how you use our service.
                      </Typography>
                    </Alert>

                    <Paper variant="outlined" sx={{ p: 3 }}>
                      <Stack spacing={3}>
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Chip label="Required" size="small" color="error" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Essential Cookies
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Required for the website to function properly. These include authentication,
                            session management, and security features. Cannot be disabled.
                          </Typography>
                        </Box>

                        <Divider />

                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Chip label="Optional" size="small" color="info" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Analytics Cookies
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            Help us understand how you use the website by collecting anonymous usage
                            data. This helps us improve the service.
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Example: Google Analytics, usage statistics
                          </Typography>
                        </Box>

                        <Divider />

                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Chip label="Optional" size="small" color="warning" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Marketing Cookies
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            Used to deliver relevant advertisements and measure campaign effectiveness.
                          They may be set by us or third-party providers.
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Example: Social media sharing, retargeting pixels
                          </Typography>
                        </Box>

                        <Divider />

                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Chip label="Optional" size="small" color="success" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Functional Cookies
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            Enable enhanced functionality and personalization, such as preferences,
                            language settings, and customizations.
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Example: Theme selection, language preference, font size
                          </Typography>
                        </Box>
                      </Stack>
                    </Paper>

                    <Alert severity="warning">
                      <AlertTitle>Managing Cookies</AlertTitle>
                      <Typography variant="body2">
                        Cookie preferences can be managed through the cookie banner that appears on
                        your first visit, or through your browser settings. Note that blocking all
                        cookies may affect website functionality.
                      </Typography>
                    </Alert>

                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Button variant="outlined" startIcon={<CookieIcon />}>
                        Reset Cookie Settings
                      </Button>
                      <Button variant="outlined" startIcon={<DocumentIcon />} href="/cookie-policy">
                        Cookie Policy
                      </Button>
                    </Box>
                  </Stack>
                </Box>
              </TabPanel>
            </Paper>
          </Grid>

          {/* Additional Information */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: 'action.hover' }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Data Security
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                We implement industry-standard security measures to protect your personal data,
                including encryption, secure servers, and access controls. We regularly review and
                update our security practices.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                For detailed information about how we protect your data, please refer to our
                Security Policy or contact our security team.
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Dialogs */}
        <DataExportDialog
          open={exportDialogOpen}
          onClose={() => setExportDialogOpen(false)}
          resumeId={resumeId}
        />

        <DataDeletionRequest
          resumeId={resumeId}
          open={deleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
        />
      </Container>
    </PageTransition>
  );
}
