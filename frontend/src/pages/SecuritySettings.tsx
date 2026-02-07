/**
 * Security Settings Page
 *
 * Comprehensive security configuration hub including:
 * - SSO (Single Sign-On) configuration with SAML providers
 * - 2FA (Two-Factor Authentication) setup and management
 * - Session management with active device tracking
 * - IP whitelist configuration for access control
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Tab,
  Tabs,
  Paper,
  Alert,
  Grid,
  Stack,
  Chip,
  Button,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Lock as LockIcon,
  Devices as DevicesIcon,
  Public as PublicIcon,
  AdminPanelSettings as AdminIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import TwoFactorAuthDialog from '@/components/TwoFactorAuthDialog';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const SecuritySettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [twoFactorDialogOpen, setTwoFactorDialogOpen] = useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTwoFactorSuccess = () => {
    // Refresh 2FA status or update UI
    setTwoFactorDialogOpen(false);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SecurityIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            Security Settings
          </Typography>
        </Box>
        <Chip
          icon={<AdminIcon />}
          label="Admin Only"
          color="primary"
          variant="outlined"
        />
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PublicIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  SSO Status
                </Typography>
              </Box>
              <Typography variant="h6" fontWeight={600}>
                Not Configured
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Configure SAML providers
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <LockIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  2FA Status
                </Typography>
              </Box>
              <Typography variant="h6" fontWeight={600}>
                Disabled
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Enable two-factor auth
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <DevicesIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </Box>
              <Typography variant="h6" fontWeight={600}>
                1
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Current device
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SecurityIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  IP Whitelist
                </Typography>
              </Box>
              <Typography variant="h6" fontWeight={600}>
                0 Rules
              </Typography>
              <Typography variant="caption" color="text.secondary">
                No restrictions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="security settings tabs">
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PublicIcon fontSize="small" />
                  <Typography variant="body2" fontWeight={500}>
                    SSO Configuration
                  </Typography>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LockIcon fontSize="small" />
                  <Typography variant="body2" fontWeight={500}>
                    Two-Factor Auth
                  </Typography>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DevicesIcon fontSize="small" />
                  <Typography variant="body2" fontWeight={500}>
                    Sessions
                  </Typography>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SecurityIcon fontSize="small" />
                  <Typography variant="body2" fontWeight={500}>
                    IP Whitelist
                  </Typography>
                </Box>
              }
            />
          </Tabs>
        </Box>

        {/* SSO Tab Panel */}
        <TabPanel value={tabValue} index={0}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <PublicIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Single Sign-On Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Configure SAML 2.0 identity providers for enterprise SSO integration
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                <Chip label="Okta" variant="outlined" />
                <Chip label="Azure AD" variant="outlined" />
                <Chip label="Google Workspace" variant="outlined" />
              </Stack>
              <Alert severity="info" sx={{ maxWidth: 500, mx: 'auto' }}>
                <Typography variant="body2">
                  SSO configuration will be available in the SSO Configuration page.
                  Navigate there to add and manage identity providers.
                </Typography>
              </Alert>
            </Box>
          </CardContent>
        </TabPanel>

        {/* 2FA Tab Panel */}
        <TabPanel value={tabValue} index={1}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <LockIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Two-Factor Authentication
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add an extra layer of security to your account with TOTP or SMS verification
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                <Chip label="TOTP (Authenticator App)" variant="outlined" />
                <Chip label="SMS Verification" variant="outlined" />
                <Chip label="Backup Codes" variant="outlined" />
              </Stack>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setTwoFactorDialogOpen(true)}
                sx={{ mb: 3 }}
              >
                Enable Two-Factor Authentication
              </Button>
              <Alert severity="info" sx={{ maxWidth: 500, mx: 'auto' }}>
                <Typography variant="body2">
                  Two-factor authentication adds an extra layer of security to your account.
                  Click the button above to set up TOTP-based 2FA with your authenticator app.
                </Typography>
              </Alert>
            </Box>
          </CardContent>
        </TabPanel>

        {/* Sessions Tab Panel */}
        <TabPanel value={tabValue} index={2}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <DevicesIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Session Management
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                View and manage all active sessions across your devices
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                <Chip label="View Active Sessions" variant="outlined" />
                <Chip label="Remote Logout" variant="outlined" />
                <Chip label="Device Info" variant="outlined" />
              </Stack>
              <Alert severity="info" sx={{ maxWidth: 500, mx: 'auto' }}>
                <Typography variant="body2">
                  Session management will be available in the Session Management page.
                  Navigate there to view active sessions and revoke access.
                </Typography>
              </Alert>
            </Box>
          </CardContent>
        </TabPanel>

        {/* IP Whitelist Tab Panel */}
        <TabPanel value={tabValue} index={3}>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <SecurityIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                IP Whitelist Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Restrict access to your organization by configuring allowed IP ranges
              </Typography>
              <Stack direction="row" spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                <Chip label="CIDR Notation" variant="outlined" />
                <Chip label="IP Ranges" variant="outlined" />
                <Chip label="Access Control" variant="outlined" />
              </Stack>
              <Alert severity="info" sx={{ maxWidth: 500, mx: 'auto' }}>
                <Typography variant="body2">
                  IP whitelist configuration will be available in the IP Whitelist page.
                  Navigate there to add and manage IP access rules.
                </Typography>
              </Alert>
            </Box>
          </CardContent>
        </TabPanel>
      </Card>

      {/* Two-Factor Auth Dialog */}
      <TwoFactorAuthDialog
        open={twoFactorDialogOpen}
        onClose={() => setTwoFactorDialogOpen(false)}
        onSuccess={handleTwoFactorSuccess}
        userId="current-user-id" // TODO: Get from auth context
      />
    </Container>
  );
};

export default SecuritySettingsPage;
