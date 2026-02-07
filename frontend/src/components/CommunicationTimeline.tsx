import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Card,
  CardContent,
  Chip,
  Avatar,
  Divider,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Phone as PhoneIcon,
  Message as MessageIcon,
  Send as SendIcon,
  CallReceived as CallReceivedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { communicationsClient } from '@/api/communications';
import type {
  CommunicationResponse,
  CommunicationListResponse,
  ApiError,
} from '@/types/api';

/**
 * CommunicationTimeline Component Props
 */
interface CommunicationTimelineProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Optional vacancy ID to filter communications */
  vacancyId?: string;
  /** Optional communication type filter */
  communicationType?: 'email' | 'sms' | 'phone_call' | 'in_system';
  /** Optional direction filter */
  direction?: 'inbound' | 'outbound';
  /** Optional status filter */
  status?: 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced' | 'read';
  /** Maximum number of communications to display */
  limit?: number;
}

/**
 * Get communication type icon and color
 */
const getCommunicationTypeDisplay = (type: string) => {
  const displays: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    email: {
      icon: <EmailIcon />,
      color: 'primary',
      label: 'Email',
    },
    sms: {
      icon: <SmsIcon />,
      color: 'success',
      label: 'SMS',
    },
    phone_call: {
      icon: <PhoneIcon />,
      color: 'info',
      label: 'Phone Call',
    },
    in_system: {
      icon: <MessageIcon />,
      color: 'secondary',
      label: 'In-System Message',
    },
  };

  return (
    displays[type] || {
      icon: <MessageIcon />,
      color: 'default',
      label: type,
    }
  );
};

/**
 * Get communication status icon and color
 */
const getCommunicationStatusDisplay = (status: string) => {
  const displays: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    pending: {
      icon: <ScheduleIcon />,
      color: 'warning',
      label: 'Pending',
    },
    sent: {
      icon: <SendIcon />,
      color: 'info',
      label: 'Sent',
    },
    delivered: {
      icon: <CheckCircleIcon />,
      color: 'success',
      label: 'Delivered',
    },
    read: {
      icon: <CheckCircleIcon />,
      color: 'success',
      label: 'Read',
    },
    failed: {
      icon: <ErrorIcon />,
      color: 'error',
      label: 'Failed',
    },
    bounced: {
      icon: <ErrorIcon />,
      color: 'error',
      label: 'Bounced',
    },
  };

  return (
    displays[status] || {
      icon: <ScheduleIcon />,
      color: 'default',
      label: status,
    }
  );
};

/**
 * CommunicationTimeline Component
 *
 * Displays chronological communication history for a candidate including:
 * - Email messages (sent and received)
 * - SMS messages
 * - Phone call logs
 * - In-system messages
 *
 * Communications are displayed in a vertical timeline with color-coded
 * communication type indicators and detailed information for each message.
 * Supports filtering by type, direction, status, and searching by content.
 *
 * @example
 * ```tsx
 * <CommunicationTimeline resumeId="resume-uuid" />
 *
 * <CommunicationTimeline
 *   resumeId="resume-uuid"
 *   vacancyId="vacancy-uuid"
 *   communicationType="email"
 *   limit={20}
 * />
 * ```
 */
const CommunicationTimeline: React.FC<CommunicationTimelineProps> = ({
  resumeId,
  vacancyId,
  communicationType: initialType,
  direction: initialDirection,
  status: initialStatus,
  limit = 50,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [communications, setCommunications] = useState<CommunicationResponse[]>([]);

  // Filter states
  const [typeFilter, setTypeFilter] = useState<string>(initialType || 'all');
  const [directionFilter, setDirectionFilter] = useState<string>(initialDirection || 'all');
  const [statusFilter, setStatusFilter] = useState<string>(initialStatus || 'all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  /**
   * Fetch communication timeline data from backend
   */
  const fetchCommunications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: CommunicationListResponse = await communicationsClient.listCommunications(
        resumeId,
        vacancyId,
        undefined,
        typeFilter !== 'all' ? typeFilter as any : undefined,
        directionFilter !== 'all' ? directionFilter as any : undefined,
        statusFilter !== 'all' ? statusFilter as any : undefined,
        searchQuery || undefined,
        undefined,
        limit
      );

      // Communications are already sorted by created_at descending from API
      setCommunications(response.communications);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load communication timeline. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId, vacancyId, typeFilter, directionFilter, statusFilter, searchQuery, limit]);

  useEffect(() => {
    fetchCommunications();
  }, [fetchCommunications]);

  /**
   * Format timestamp for display
   */
  const formatTimestamp = useCallback((timestamp: string | null) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  }, []);

  /**
   * Get recruiter display name from recruiter_id
   */
  const getRecruiterName = useCallback((recruiterId: string | null) => {
    if (!recruiterId) return 'System';
    // Extract username from email or use ID
    if (recruiterId.includes('@')) {
      return recruiterId.split('@')[0];
    }
    return recruiterId;
  }, []);

  /**
   * Get recruiter initials for avatar
   */
  const getRecruiterInitials = useCallback((name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, []);

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
          {t('communicationTimeline.loading')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('communicationTimeline.loadingHint')}
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
          <Button color="inherit" onClick={fetchCommunications} startIcon={<RefreshIcon />}>
            {t('communicationTimeline.retry')}
          </Button>
        }
      >
        <AlertTitle>{t('communicationTimeline.errorTitle')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (communications.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('communicationTimeline.noCommunicationsTitle')}</AlertTitle>
        {t('communicationTimeline.noCommunications')}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MessageIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {t('communicationTimeline.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('communicationTimeline.subtitle', { count: communications.length })}
                {vacancyId && ` ${t('communicationTimeline.forVacancy')}`}
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchCommunications}
            size="small"
          >
            {t('communicationTimeline.refresh')}
          </Button>
        </Box>

        {/* Filters and Search */}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search communications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={6} sm={3} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                label="Type"
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="email">Email</MenuItem>
                <MenuItem value="sms">SMS</MenuItem>
                <MenuItem value="phone_call">Phone Call</MenuItem>
                <MenuItem value="in_system">In-System</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={3} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Direction</InputLabel>
              <Select
                value={directionFilter}
                onChange={(e) => setDirectionFilter(e.target.value)}
                label="Direction"
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="inbound">Inbound</MenuItem>
                <MenuItem value="outbound">Outbound</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="sent">Sent</MenuItem>
                <MenuItem value="delivered">Delivered</MenuItem>
                <MenuItem value="read">Read</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => {
                setTypeFilter('all');
                setDirectionFilter('all');
                setStatusFilter('all');
                setSearchQuery('');
              }}
            >
              Clear Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Communication Timeline */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Stack spacing={2}>
          {communications.map((communication, index) => {
            const typeDisplay = getCommunicationTypeDisplay(communication.type);
            const statusDisplay = getCommunicationStatusDisplay(communication.status);
            const recruiter = getRecruiterName(communication.recruiter_id);

            return (
              <Box key={communication.id}>
                <Card
                  variant="outlined"
                  sx={{
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateX(4px)',
                      boxShadow: 2,
                    },
                  }}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    {/* Communication Header */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mb: 1,
                        flexWrap: 'wrap',
                        gap: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Box
                          sx={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            bgcolor: `${typeDisplay.color}.main`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                          }}
                        >
                          {typeDisplay.icon}
                        </Box>
                        <Chip
                          label={typeDisplay.label}
                          size="small"
                          color={typeDisplay.color as any}
                          variant="outlined"
                        />
                        <Chip
                          icon={communication.direction === 'inbound' ? <CallReceivedIcon /> : <SendIcon />}
                          label={communication.direction}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={statusDisplay.label}
                          size="small"
                          color={statusDisplay.color as any}
                          variant="filled"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(communication.sent_at || communication.received_at)}
                        </Typography>
                      </Box>
                      {communication.vacancy_id && (
                        <Chip
                          label={communication.vacancy_id.slice(0, 8)}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>

                    {/* Communication Subject */}
                    {communication.subject && (
                      <Typography variant="subtitle2" fontWeight={600} color="text.primary" sx={{ mb: 0.5 }}>
                        {communication.subject}
                      </Typography>
                    )}

                    {/* Communication Body */}
                    {communication.body && (
                      <Typography variant="body2" color="text.primary" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
                        {communication.body.length > 300
                          ? `${communication.body.substring(0, 300)}...`
                          : communication.body}
                      </Typography>
                    )}

                    {/* Recruiter/Sender Info */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
                      <Avatar
                        sx={{
                          width: 24,
                          height: 24,
                          bgcolor: 'action.selected',
                          fontSize: '0.7rem',
                        }}
                      >
                        {getRecruiterInitials(recruiter)}
                      </Avatar>
                      <Typography variant="caption" color="text.secondary">
                        {recruiter}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
                {index < communications.length - 1 && (
                  <Divider sx={{ mt: 2, borderColor: 'divider' }} />
                )}
              </Box>
            );
          })}
        </Stack>
      </Paper>
    </Stack>
  );
};

export default CommunicationTimeline;
