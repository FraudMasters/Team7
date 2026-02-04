import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  IconButton,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { gdprClient } from '@/api/gdpr';
import type {
  ConsentRecordResponse,
  ConsentListResponse,
} from '@/types/api';

/**
 * Consent type definition
 */
interface ConsentType {
  type: string;
  label: string;
  description: string;
  category: 'core' | 'analytics' | 'marketing' | 'cookies';
  required: boolean;
}

/**
 * Consent manager component props
 */
interface ConsentManagerProps {
  /** Optional user ID to filter consents */
  userId?: string;
  /** Optional organization ID to filter consents */
  organizationId?: string;
  /** Optional callback when consent is changed */
  onConsentChange?: () => void;
}

/**
 * Available consent types based on GDPR requirements
 */
const CONSENT_TYPES: ConsentType[] = [
  {
    type: 'data_processing',
    label: 'Data Processing',
    description: 'Allow processing of your personal data for recruitment purposes',
    category: 'core',
    required: true,
  },
  {
    type: 'data_storing',
    label: 'Data Storage',
    description: 'Allow storing your data in our database',
    category: 'core',
    required: true,
  },
  {
    type: 'resume_analysis',
    label: 'Resume Analysis',
    description: 'Allow automated analysis of your resume for skill extraction',
    category: 'core',
    required: false,
  },
  {
    type: 'skill_extraction',
    label: 'Skill Extraction',
    description: 'Allow extraction of skills and experience from your resume',
    category: 'core',
    required: false,
  },
  {
    type: 'ai_analysis',
    label: 'AI Analysis',
    description: 'Allow AI-powered analysis for better job matching',
    category: 'analytics',
    required: false,
  },
  {
    type: 'matching',
    label: 'Job Matching',
    description: 'Allow matching your profile with open positions',
    category: 'core',
    required: false,
  },
  {
    type: 'communication',
    label: 'Communication',
    description: 'Allow sending you updates about your applications',
    category: 'core',
    required: false,
  },
  {
    type: 'analytics',
    label: 'Analytics',
    description: 'Allow usage of anonymous analytics for service improvement',
    category: 'analytics',
    required: false,
  },
  {
    type: 'marketing',
    label: 'Marketing',
    description: 'Allow sending marketing communications and job alerts',
    category: 'marketing',
    required: false,
  },
  {
    type: 'cookies_essential',
    label: 'Essential Cookies',
    description: 'Required for the website to function properly',
    category: 'cookies',
    required: true,
  },
  {
    type: 'cookies_functional',
    label: 'Functional Cookies',
    description: 'Enable enhanced functionality and personalization',
    category: 'cookies',
    required: false,
  },
  {
    type: 'cookies_analytics',
    label: 'Analytics Cookies',
    description: 'Help us understand how you use the website',
    category: 'cookies',
    required: false,
  },
  {
    type: 'cookies_marketing',
    label: 'Marketing Cookies',
    description: 'Used to deliver relevant advertisements',
    category: 'cookies',
    required: false,
  },
];

/**
 * ConsentManager Component
 *
 * Provides a comprehensive interface for managing GDPR consent records. Features include:
 * - List all granted and withdrawn consents
 * - Grant new consents
 * - Revoke existing consents
 * - View consent history
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <ConsentManager
 *   userId="user-123"
 *   onConsentChange={() => console.log('Consent changed')}
 * />
 * ```
 */
const ConsentManager: React.FC<ConsentManagerProps> = ({
  userId,
  organizationId,
  onConsentChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [consents, setConsents] = useState<ConsentRecordResponse[]>([]);
  const [withdrawDialogOpen, setWithdrawDialogOpen] = useState(false);
  const [consentToWithdraw, setConsentToWithdraw] = useState<ConsentRecordResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  /**
   * Fetch consent records from backend
   */
  const fetchConsents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result: ConsentListResponse = await gdprClient.listConsents(
        userId,
        organizationId,
        undefined,
        true // Only active consents
      );
      setConsents(result.consents || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load consent records';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [userId, organizationId]);

  useEffect(() => {
    fetchConsents();
  }, [fetchConsents]);

  /**
   * Get consent status for a specific consent type
   */
  const getConsentForType = (consentType: string): ConsentRecordResponse | undefined => {
    return consents.find((c) => c.consent_type === consentType && c.is_active);
  };

  /**
   * Handle granting consent
   */
  const handleGrantConsent = async (consentType: string) => {
    setSubmitting(true);
    setError(null);

    try {
      const granted = await gdprClient.grantConsent({
        consent_type: consentType,
        granted: true,
        user_id: userId,
        organization_id: organizationId,
      });

      // Optimistic update
      setConsents([...consents, granted]);

      if (onConsentChange) {
        onConsentChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to grant consent';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Open withdraw confirmation dialog
   */
  const handleWithdrawClick = (consent: ConsentRecordResponse) => {
    setConsentToWithdraw(consent);
    setWithdrawDialogOpen(true);
  };

  /**
   * Confirm withdraw
   */
  const handleWithdrawConfirm = async () => {
    if (!consentToWithdraw) return;

    setSubmitting(true);
    try {
      const withdrawn = await gdprClient.withdrawConsent({
        consent_type: consentToWithdraw.consent_type,
        user_id: userId,
        organization_id: organizationId,
        reason: 'User revoked consent via consent manager',
      });

      // Optimistic update - remove from active consents
      setConsents(consents.filter((c) => c.id !== consentToWithdraw.id));
      setWithdrawDialogOpen(false);
      setConsentToWithdraw(null);

      if (onConsentChange) {
        onConsentChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to withdraw consent';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get category color for chips
   */
  const getCategoryColor = (category: string): 'success' | 'info' | 'warning' | 'error' => {
    switch (category) {
      case 'core':
        return 'success';
      case 'analytics':
        return 'info';
      case 'marketing':
        return 'warning';
      case 'cookies':
        return 'error';
      default:
        return 'info';
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading consent records...
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchConsents} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Consent Management
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchConsents}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          Manage your privacy consents for data processing and storage. You can grant or revoke
          consents at any time. Revoking consent may affect certain features.
        </Typography>

        {/* Summary Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {consents.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Active Consents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {consents.filter((c) => c.consent_type.startsWith('data_')).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Data Processing
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'info.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {consents.filter((c) => c.consent_type.startsWith('cookies_')).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Cookie Consents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Required Consents Notice */}
      <Alert severity="info" icon={<InfoIcon />}>
        <AlertTitle>Required Consents</AlertTitle>
        Some consents are required for the service to function properly. These are marked with a
        required badge.
      </Alert>

      {/* Consent Types List */}
      <Grid container spacing={2}>
        {CONSENT_TYPES.map((consentType) => {
          const consent = getConsentForType(consentType.type);
          const hasConsent = !!consent;

          return (
            <Grid item xs={12} key={consentType.type}>
              <Card
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6" fontWeight={600}>
                          {consentType.label}
                        </Typography>
                        <Chip
                          label={consentType.category}
                          size="small"
                          color={getCategoryColor(consentType.category)}
                        />
                        {consentType.required && (
                          <Chip label="Required" size="small" color="default" variant="filled" />
                        )}
                        {hasConsent && (
                          <Chip
                            icon={<CheckCircleIcon />}
                            label="Granted"
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        )}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {consentType.description}
                      </Typography>
                      {hasConsent && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                          Granted on {new Date(consent!.granted_at).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        {hasConsent ? 'Granted' : 'Not Granted'}
                      </Typography>
                      <Switch
                        checked={hasConsent}
                        onChange={() => {
                          if (hasConsent) {
                            handleWithdrawClick(consent!);
                          } else {
                            handleGrantConsent(consentType.type);
                          }
                        }}
                        disabled={submitting || consentType.required}
                        color={hasConsent ? 'success' : 'default'}
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Withdraw Confirmation Dialog */}
      <Dialog open={withdrawDialogOpen} onClose={() => !submitting && setWithdrawDialogOpen(false)}>
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Withdraw Consent</Typography>
            <IconButton
              onClick={() => setWithdrawDialogOpen(false)}
              disabled={submitting}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to withdraw your consent for "
            {CONSENT_TYPES.find((ct) => ct.type === consentToWithdraw?.consent_type)?.label}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Withdrawing consent may affect certain features. Your data will no longer be processed
            for this purpose, but existing data may be retained as required by law or for legitimate
            business purposes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWithdrawDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleWithdrawConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <CancelIcon />}
          >
            {submitting ? 'Withdrawing...' : 'Withdraw Consent'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default ConsentManager;
