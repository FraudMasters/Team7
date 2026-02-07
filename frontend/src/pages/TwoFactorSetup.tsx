/**
 * Two-Factor Authentication Setup Page
 *
 * Provides comprehensive 2FA management functionality including:
 * - TOTP (authenticator app) setup and verification
 * - SMS-based 2FA setup and verification
 * - Backup code generation and display
 * - 2FA status monitoring and management
 * - Disable 2FA with verification
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Stack,
  Divider,
  IconButton,
  InputAdornment,
  Copy as CopyIcon,
  QRCode as QRCodeIcon,
  Phone as PhoneIcon,
  Shield as ShieldIcon,
  Key as KeyIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  InfoOutlined as InfoIcon,
} from '@mui/icons-material';
import { twoFactorClient } from '@/api/twoFactor';
import type {
  TwoFactorStatusResponse,
  TwoFactorSetupResponse,
  TwoFactorVerifyResponse,
  BackupCodesResponse,
} from '@/types/api';

type TwoFactorMethod = 'totp' | 'sms';
type SetupStep = 'method' | 'setup' | 'verify' | 'complete';

const TwoFactorSetupPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 2FA Status
  const [status, setStatus] = useState<TwoFactorStatusResponse | null>(null);

  // Setup state
  const [setupStep, setSetupStep] = useState<SetupStep>('method');
  const [selectedMethod, setSelectedMethod] = useState<TwoFactorMethod>('totp');
  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verifyCode, setVerifyCode] = useState('');

  // Backup codes
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [backupCodesDialogOpen, setBackupCodesDialogOpen] = useState(false);

  // Disable 2FA
  const [disableDialogOpen, setDisableDialogOpen] = useState(false);
  const [disableCode, setDisableCode] = useState('');

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      // For demo purposes, use a mock user ID
      const userId = 'current-user';
      const response = await twoFactorClient.getStatus(userId);
      setStatus(response);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch 2FA status';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleSetupStart = async (method: TwoFactorMethod) => {
    try {
      setLoading(true);
      setSelectedMethod(method);
      setSetupStep('setup');

      const userId = 'current-user';
      const response = await twoFactorClient.setup({
        user_id: userId,
        method,
        phone: method === 'sms' ? phoneNumber : undefined,
      });

      setSetupData(response);
      setBackupCodes(response.backup_codes || []);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to initiate 2FA setup';
      setError(message);
      setSetupStep('method');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      setError('Please enter a valid 6-digit verification code');
      return;
    }

    try {
      setLoading(true);
      const userId = 'current-user';
      const response = await twoFactorClient.verify({
        user_id: userId,
        code: verifyCode,
      });

      if (response.success) {
        setSuccess('Two-factor authentication enabled successfully!');
        setSetupStep('complete');
        fetchStatus();
      } else {
        setError(response.message || 'Verification failed. Please try again.');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Verification failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    if (!disableCode || disableCode.length !== 6) {
      setError('Please enter a valid 6-digit verification code');
      return;
    }

    try {
      setLoading(true);
      const userId = 'current-user';
      await twoFactorClient.disable({
        user_id: userId,
        code: disableCode,
      });

      setSuccess('Two-factor authentication disabled successfully!');
      setDisableDialogOpen(false);
      setDisableCode('');
      fetchStatus();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to disable 2FA';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateBackupCodes = async () => {
    try {
      setLoading(true);
      const userId = 'current-user';
      const response = await twoFactorClient.generateBackupCodes({
        user_id: userId,
        code: verifyCode,
      });

      setBackupCodes(response.backup_codes);
      setBackupCodesDialogOpen(true);
      setSuccess(response.message);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate backup codes';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
  };

  const copyAllBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    setSuccess('All backup codes copied to clipboard!');
  };

  if (loading && !status) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ width: '100%', mt: 4 }}>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <ShieldIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            Two-Factor Authentication
          </Typography>
        </Box>
        {status?.enabled && (
          <Chip
            icon={<CheckCircleIcon />}
            label="Enabled"
            color="success"
            sx={{ px: 2, py: 1 }}
          />
        )}
      </Box>

      {/* Error/Success Messages */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Current Status Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Current Status
          </Typography>
          {status?.enabled ? (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <CheckCircleIcon color="success" fontSize="large" />
                <Box>
                  <Typography variant="body1" fontWeight={500}>
                    Two-factor authentication is enabled
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Method: {status.method === 'totp' ? 'Authenticator App (TOTP)' : 'SMS'}
                  </Typography>
                </Box>
              </Box>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  startIcon={<KeyIcon />}
                  onClick={handleGenerateBackupCodes}
                >
                  Generate Backup Codes
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDisableDialogOpen(true)}
                >
                  Disable 2FA
                </Button>
              </Stack>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <WarningIcon color="warning" fontSize="large" />
              <Box>
                <Typography variant="body1" fontWeight={500}>
                  Two-factor authentication is not enabled
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enable 2FA to add an extra layer of security to your account
                </Typography>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {!status?.enabled && (
        /* Setup 2FA Section */
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Setup Two-Factor Authentication
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Choose a method to receive verification codes
            </Typography>

            {setupStep === 'method' && (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                      border: selectedMethod === 'totp' ? 2 : 1,
                      borderColor: selectedMethod === 'totp' ? 'primary.main' : 'divider',
                    }}
                    onClick={() => setSelectedMethod('totp')}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <QRCodeIcon fontSize="large" color="primary" />
                        <Box>
                          <Typography variant="h6" fontWeight={600}>
                            Authenticator App
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Recommended
                          </Typography>
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Use an authenticator app like Google Authenticator, Authy, or Microsoft
                        Authenticator to generate verification codes
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card
                    variant="outlined"
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                      border: selectedMethod === 'sms' ? 2 : 1,
                      borderColor: selectedMethod === 'sms' ? 'primary.main' : 'divider',
                    }}
                    onClick={() => setSelectedMethod('sms')}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <PhoneIcon fontSize="large" color="primary" />
                        <Box>
                          <Typography variant="h6" fontWeight={600}>
                            SMS Verification
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Text message
                          </Typography>
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Receive verification codes via text message to your mobile phone
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {selectedMethod === 'sms' && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Phone Number"
                      placeholder="+1 234 567 8900"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      helperText="Enter your phone number in international format"
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    onClick={() => handleSetupStart(selectedMethod)}
                    disabled={selectedMethod === 'sms' && !phoneNumber}
                  >
                    Continue
                  </Button>
                </Grid>
              </Grid>
            )}

            {setupStep === 'setup' && setupData && (
              <Box>
                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    <strong>Step 1:</strong> Scan the QR code or enter the secret key manually in
                    your authenticator app
                  </Typography>
                </Alert>

                <Grid container spacing={3} justifyContent="center">
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      <Box sx={{ textAlign: 'center', mb: 2 }}>
                        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                          QR Code
                        </Typography>
                        <Box
                          sx={{
                            width: 200,
                            height: 200,
                            bgcolor: 'grey.100',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            mx: 'auto',
                            borderRadius: 1,
                          }}
                        >
                          <Typography variant="caption" color="text.secondary">
                            QR Code Placeholder
                          </Typography>
                        </Box>
                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                          Scan with your authenticator app
                        </Typography>
                      </Box>
                    </Card>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        Secret Key
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <TextField
                          fullWidth
                          value={setupData.secret}
                          InputProps={{
                            readOnly: true,
                            sx: { fontFamily: 'monospace', fontSize: '1.1rem' },
                          }}
                        />
                        <IconButton
                          onClick={() => copyToClipboard(setupData.secret)}
                          color="primary"
                        >
                          <CopyIcon />
                        </IconButton>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Enter this code manually if you can't scan the QR code
                      </Typography>
                    </Card>
                  </Grid>

                  <Grid item xs={12}>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        <strong>Important:</strong> Save your backup codes below before continuing.
                        You'll need them if you lose access to your authenticator app.
                      </Typography>
                    </Alert>

                    <Button
                      variant="contained"
                      size="large"
                      fullWidth
                      onClick={() => setSetupStep('verify')}
                    >
                      I've Saved My Backup Codes - Continue
                    </Button>
                  </Grid>
                </Grid>

                {/* Backup Codes Section */}
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h6" gutterBottom>
                    Backup Codes
                  </Typography>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Save these backup codes in a secure location. You can use them to access your
                      account if you lose your authenticator app or phone.
                    </Typography>
                  </Alert>

                  <Grid container spacing={1}>
                    {backupCodes.map((code, index) => (
                      <Grid item xs={6} sm={4} md={3} key={index}>
                        <Card variant="outlined">
                          <CardContent sx={{ textAlign: 'center', py: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                            >
                              {code}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  <Button
                    variant="outlined"
                    startIcon={<CopyIcon />}
                    onClick={copyAllBackupCodes}
                    sx={{ mt: 2 }}
                  >
                    Copy All Codes
                  </Button>
                </Box>
              </Box>
            )}

            {setupStep === 'verify' && (
              <Box sx={{ maxWidth: 500, mx: 'auto' }}>
                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    <strong>Step 2:</strong> Enter the 6-digit verification code from your
                    authenticator app to complete setup
                  </Typography>
                </Alert>

                <TextField
                  fullWidth
                  label="Verification Code"
                  placeholder="123456"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  inputProps={{ maxLength: 6, style: { textAlign: 'center', fontSize: '1.5rem' } }}
                  sx={{ mb: 3 }}
                />

                <Stack direction="row" spacing={2}>
                  <Button
                    variant="outlined"
                    onClick={() => setSetupStep('setup')}
                    sx={{ flex: 1 }}
                  >
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleVerifyCode}
                    disabled={verifyCode.length !== 6}
                    sx={{ flex: 1 }}
                  >
                    Verify & Enable
                  </Button>
                </Stack>
              </Box>
            )}

            {setupStep === 'complete' && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <CheckCircleIcon
                  color="success"
                  sx={{ fontSize: 80, mb: 2 }}
                />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Two-Factor Authentication Enabled!
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                  Your account is now protected with two-factor authentication
                </Typography>
                <Alert severity="info" sx={{ maxWidth: 600, mx: 'auto', mb: 3 }}>
                  <Typography variant="body2">
                    Next time you log in, you'll need to enter a verification code from your
                    authenticator app. Make sure to keep your backup codes in a safe place.
                  </Typography>
                </Alert>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Information Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ShieldIcon color="primary" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Enhanced Security
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                2FA adds an extra layer of protection, making it much harder for unauthorized users
                to access your account
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <KeyIcon color="primary" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Backup Codes
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Save your backup codes securely. They're your only way back in if you lose access
                to your authenticator app
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <InfoIcon color="primary" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Recommended
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                We recommend using an authenticator app over SMS for better security and
                reliability
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Backup Codes Dialog */}
      <Dialog
        open={backupCodesDialogOpen}
        onClose={() => setBackupCodesDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Backup Codes</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Save these codes in a secure location. Each code can only be used once.
            </Typography>
          </Alert>
          <Grid container spacing={1}>
            {backupCodes.map((code, index) => (
              <Grid item xs={6} sm={4} key={index}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 1 }}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                      {code}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={copyAllBackupCodes} startIcon={<CopyIcon />}>
            Copy All
          </Button>
          <Button onClick={() => setBackupCodesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Disable 2FA Dialog */}
      <Dialog open={disableDialogOpen} onClose={() => setDisableDialogOpen(false)} maxWidth="sm">
        <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Disabling 2FA will make your account less secure. Are you sure you want to continue?
            </Typography>
          </Alert>
          <TextField
            fullWidth
            label="Enter Verification Code"
            placeholder="123456"
            value={disableCode}
            onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            inputProps={{ maxLength: 6, style: { textAlign: 'center' } }}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDisableDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDisable2FA}
            color="error"
            disabled={disableCode.length !== 6}
            variant="contained"
          >
            Disable 2FA
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default TwoFactorSetupPage;
