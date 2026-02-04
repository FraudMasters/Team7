import React, { useState, useCallback } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Stack,
  Divider,
  Paper,
  Chip,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  QRCode2 as QRCodeIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { twoFactorClient } from '@/api/twoFactor';
import type {
  TwoFactorSetupResponse,
  TwoFactorStatusResponse,
} from '@/types/api';

/**
 * Two-Factor Authentication Dialog Props
 */
interface TwoFactorAuthDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Callback when 2FA is successfully enabled */
  onSuccess?: () => void;
  /** User ID for the current user */
  userId: string;
  /** Current 2FA status (optional) */
  currentStatus?: TwoFactorStatusResponse;
}

/**
 * Setup step enum for tracking progress
 */
enum SetupStep {
  Overview = 'overview',
  ScanQR = 'scan_qr',
  VerifyCode = 'verify_code',
  BackupCodes = 'backup_codes',
  Complete = 'complete',
}

/**
 * TwoFactorAuthDialog Component
 *
 * Provides a step-by-step wizard for setting up two-factor authentication (TOTP):
 * - Overview of 2FA benefits
 * - QR code display for authenticator app scanning
 * - Verification code entry and validation
 * - Backup codes display for account recovery
 * - Success confirmation
 *
 * @example
 * ```tsx
 * <TwoFactorAuthDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   onSuccess={() => console.log('2FA enabled!')}
 *   userId="user-123"
 * />
 * ```
 */
const TwoFactorAuthDialog: React.FC<TwoFactorAuthDialogProps> = ({
  open,
  onClose,
  onSuccess,
  userId,
  currentStatus,
}) => {
  const { t } = useTranslation();

  // State management
  const [currentStep, setCurrentStep] = useState<SetupStep>(SetupStep.Overview);
  const [isInitializing, setIsInitializing] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [backupCodesCopied, setBackupCodesCopied] = useState(false);

  /**
   * Initialize 2FA setup by calling the setup endpoint
   */
  const handleInitializeSetup = useCallback(async () => {
    setIsInitializing(true);
    setError(null);

    try {
      const response = await twoFactorClient.setup({
        user_id: userId,
        method: 'totp',
      });

      setSetupData(response);
      setCurrentStep(SetupStep.ScanQR);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('twoFactor.setupError');
      setError(errorMessage);
    } finally {
      setIsInitializing(false);
    }
  }, [userId, t]);

  /**
   * Verify the TOTP code
   */
  const handleVerifyCode = useCallback(async () => {
    if (!verificationCode.trim() || isVerifying) {
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const response = await twoFactorClient.verify({
        user_id: userId,
        code: verificationCode.trim(),
      });

      if (response.success) {
        setCurrentStep(SetupStep.BackupCodes);
      } else {
        setError(t('twoFactor.invalidCode'));
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('twoFactor.verificationError');
      setError(errorMessage);
    } finally {
      setIsVerifying(false);
    }
  }, [userId, verificationCode, isVerifying, t]);

  /**
   * Copy backup codes to clipboard
   */
  const handleCopyBackupCodes = useCallback(() => {
    if (!setupData?.backup_codes) {
      return;
    }

    const codesText = setupData.backup_codes.join('\n');
    navigator.clipboard.writeText(codesText).then(() => {
      setBackupCodesCopied(true);
      setTimeout(() => setBackupCodesCopied(false), 2000);
    });
  }, [setupData]);

  /**
   * Handle completion of setup
   */
  const handleComplete = useCallback(() => {
    setCurrentStep(SetupStep.Complete);
    onSuccess?.();
  }, [onSuccess]);

  /**
   * Handle dialog close
   */
  const handleClose = useCallback(() => {
    if (!isInitializing && !isVerifying) {
      setCurrentStep(SetupStep.Overview);
      setVerificationCode('');
      setError(null);
      setSetupData(null);
      setShowBackupCodes(false);
      setBackupCodesCopied(false);
      onClose();
    }
  }, [isInitializing, isVerifying, onClose]);

  /**
   * Handle verification code input change (6 digits only)
   */
  const handleCodeChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value.replace(/\D/g, '').slice(0, 6);
    setVerificationCode(value);
    setError(null);
  }, []);

  /**
   * Render overview step
   */
  const renderOverview = () => (
    <Stack spacing={3}>
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <QRCodeIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {t('twoFactor.setupTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('twoFactor.setupDescription')}
        </Typography>
      </Box>

      <Divider />

      <Stack spacing={2}>
        <Typography variant="subtitle2" fontWeight={600}>
          {t('twoFactor.howItWorks')}
        </Typography>

        <Stack spacing={1}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Chip label="1" size="small" sx={{ minWidth: 24 }} />
            <Typography variant="body2">
              {t('twoFactor.step1')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Chip label="2" size="small" sx={{ minWidth: 24 }} />
            <Typography variant="body2">
              {t('twoFactor.step2')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <Chip label="3" size="small" sx={{ minWidth: 24 }} />
            <Typography variant="body2">
              {t('twoFactor.step3')}
            </Typography>
          </Box>
        </Stack>
      </Stack>

      <Alert severity="info">
        <Typography variant="body2">
          {t('twoFactor.recommendation')}
        </Typography>
      </Alert>
    </Stack>
  );

  /**
   * Render QR code scanning step
   */
  const renderScanQR = () => (
    <Stack spacing={3}>
      <Box sx={{ textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          {t('twoFactor.scanQRTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('twoFactor.scanQRDescription')}
        </Typography>
      </Box>

      {/* QR Code Placeholder */}
      <Paper
        elevation={3}
        sx={{
          p: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        {isInitializing ? (
          <CircularProgress size={60} />
        ) : setupData?.provisioning_uri ? (
          <>
            <Box
              sx={{
                width: 200,
                height: 200,
                bgcolor: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px solid',
                borderColor: 'divider',
                borderRadius: 2,
                mb: 2,
              }}
            >
              <QRCodeIcon sx={{ fontSize: 120, color: 'text.secondary' }} />
            </Box>
            <Alert severity="info" sx={{ maxWidth: 400 }}>
              <Typography variant="caption">
                {t('twoFactor.qrPlaceholder')}
              </Typography>
            </Alert>
          </>
        ) : null}
      </Paper>

      {/* Manual entry option */}
      <Box>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {t('twoFactor.manualEntryTitle')}
        </Typography>
        {setupData?.secret && (
          <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography
              variant="body2"
              sx={{
                fontFamily: 'monospace',
                wordBreak: 'break-all',
                textAlign: 'center',
                letterSpacing: 2,
              }}
            >
              {setupData.secret}
            </Typography>
          </Paper>
        )}
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('twoFactor.manualEntryHint')}
        </Typography>
      </Box>

      {/* Supported apps */}
      <Box>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          {t('twoFactor.supportedApps')}
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap">
          <Chip label="Google Authenticator" variant="outlined" size="small" />
          <Chip label="Authy" variant="outlined" size="small" />
          <Chip label="Microsoft Authenticator" variant="outlined" size="small" />
          <Chip label="1Password" variant="outlined" size="small" />
          <Chip label="LastPass" variant="outlined" size="small" />
        </Stack>
      </Box>
    </Stack>
  );

  /**
   * Render verification code step
   */
  const renderVerifyCode = () => (
    <Stack spacing={3}>
      <Box sx={{ textAlign: 'center' }}>
        <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {t('twoFactor.verifyTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('twoFactor.verifyDescription')}
        </Typography>
      </Box>

      {/* Verification Code Input */}
      <TextField
        autoFocus
        fullWidth
        label={t('twoFactor.enterCode')}
        value={verificationCode}
        onChange={handleCodeChange}
        placeholder="000000"
        inputProps={{
          maxLength: 6,
          style: { textAlign: 'center', letterSpacing: 8, fontSize: 24 },
        }}
        disabled={isVerifying}
        error={!!error}
      />

      {/* Error Alert */}
      {error && (
        <Alert severity="error" icon={<ErrorIcon />}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      <Alert severity="info">
        <Typography variant="body2">
          {t('twoFactor.codeHint')}
        </Typography>
      </Alert>
    </Stack>
  );

  /**
   * Render backup codes step
   */
  const renderBackupCodes = () => (
    <Stack spacing={3}>
      <Box sx={{ textAlign: 'center' }}>
        <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {t('twoFactor.backupCodesTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('twoFactor.backupCodesDescription')}
        </Typography>
      </Box>

      <Alert severity="warning">
        <Typography variant="body2" fontWeight={600}>
          {t('twoFactor.backupCodesWarning')}
        </Typography>
      </Alert>

      {/* Backup Codes */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          bgcolor: 'background.default',
          maxHeight: 300,
          overflow: 'auto',
        }}
      >
        {setupData?.backup_codes ? (
          <Stack spacing={1}>
            {setupData.backup_codes.map((code, index) => (
              <Typography
                key={index}
                variant="body2"
                sx={{
                  fontFamily: 'monospace',
                  textAlign: 'center',
                  py: 0.5,
                  borderBottom: index < setupData.backup_codes.length - 1 ? 1 : 0,
                  borderColor: 'divider',
                }}
              >
                {code}
              </Typography>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            {t('twoFactor.noBackupCodes')}
          </Typography>
        )}
      </Paper>

      {/* Actions */}
      <Stack direction="row" spacing={2} justifyContent="center">
        <Button
          variant="outlined"
          startIcon={backupCodesCopied ? <CheckCircleIcon /> : undefined}
          onClick={handleCopyBackupCodes}
          disabled={backupCodesCopied}
        >
          {backupCodesCopied ? t('twoFactor.copied') : t('twoFactor.copyCodes')}
        </Button>
        <Button
          variant="outlined"
          onClick={() => setShowBackupCodes(!showBackupCodes)}
          endIcon={showBackupCodes ? <VisibilityOffIcon /> : <VisibilityIcon />}
        >
          {showBackupCodes ? t('twoFactor.hide') : t('twoFactor.show')}
        </Button>
      </Stack>

      {!showBackupCodes && (
        <Alert severity="info">
          <Typography variant="body2">
            {t('twoFactor.savedConfirmation')}
          </Typography>
        </Alert>
      )}
    </Stack>
  );

  /**
   * Render completion step
   */
  const renderComplete = () => (
    <Stack spacing={3} alignItems="center">
      <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main' }} />
      <Typography variant="h6" align="center">
        {t('twoFactor.enabledTitle')}
      </Typography>
      <Typography variant="body2" color="text.secondary" align="center">
        {t('twoFactor.enabledMessage')}
      </Typography>

      <Alert severity="success" sx={{ width: '100%' }}>
        <Typography variant="body2">
          {t('twoFactor.successMessage')}
        </Typography>
      </Alert>
    </Stack>
  );

  /**
   * Get dialog actions based on current step
   */
  const renderDialogActions = () => {
    switch (currentStep) {
      case SetupStep.Overview:
        return (
          <>
            <Button onClick={handleClose} disabled={isInitializing}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="contained"
              onClick={handleInitializeSetup}
              disabled={isInitializing}
              startIcon={isInitializing ? <CircularProgress size={16} /> : undefined}
            >
              {t('twoFactor.getStarted')}
            </Button>
          </>
        );

      case SetupStep.ScanQR:
        return (
          <>
            <Button onClick={handleClose} disabled={isInitializing}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="contained"
              onClick={() => setCurrentStep(SetupStep.VerifyCode)}
              disabled={!setupData || isInitializing}
            >
              {t('twoFactor.next')}
            </Button>
          </>
        );

      case SetupStep.VerifyCode:
        return (
          <>
            <Button onClick={() => setCurrentStep(SetupStep.ScanQR)} disabled={isVerifying}>
              {t('common.back')}
            </Button>
            <Button
              variant="contained"
              onClick={handleVerifyCode}
              disabled={verificationCode.length !== 6 || isVerifying}
              startIcon={isVerifying ? <CircularProgress size={16} /> : undefined}
            >
              {isVerifying ? t('twoFactor.verifying') : t('twoFactor.verify')}
            </Button>
          </>
        );

      case SetupStep.BackupCodes:
        return (
          <>
            <Button onClick={handleClose}>
              {t('common.close')}
            </Button>
            <Button variant="contained" onClick={handleComplete}>
              {t('twoFactor.complete')}
            </Button>
          </>
        );

      case SetupStep.Complete:
        return (
          <Button variant="contained" onClick={handleClose}>
            {t('common.done')}
          </Button>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { minHeight: currentStep === SetupStep.ScanQR ? 600 : 'auto' },
      }}
    >
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={2}>
          <QRCodeIcon color="primary" />
          <Typography variant="h6" component="div">
            {t('twoFactor.dialogTitle')}
          </Typography>
        </Stack>
      </DialogTitle>

      <DialogContent>
        {currentStep === SetupStep.Overview && renderOverview()}
        {currentStep === SetupStep.ScanQR && renderScanQR()}
        {currentStep === SetupStep.VerifyCode && renderVerifyCode()}
        {currentStep === SetupStep.BackupCodes && renderBackupCodes()}
        {currentStep === SetupStep.Complete && renderComplete()}
      </DialogContent>

      <DialogActions>
        <Stack direction="row" spacing={2} justifyContent="flex-end" width="100%">
          {renderDialogActions()}
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default TwoFactorAuthDialog;
