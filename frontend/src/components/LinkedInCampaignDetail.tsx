import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  CircularProgress,
  Button,
  Alert,
  Grid,
  Stack,
  Divider,
  Card,
  CardContent,
  Avatar,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Campaign as CampaignIcon,
  TrendingUp as TrendingUpIcon,
  Send as SendIcon,
  Reply as ReplyIcon,
  Person as PersonIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  HelpOutline as HelpIcon,
  Email as EmailIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Info as InfoIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { linkedinApi } from '@/services/linkedinApi';
import type {
  LinkedInCampaignResponse,
  LinkedInCampaignStatsResponse,
  LinkedInOutreachResponse,
  LinkedInOutreachResponseStatus,
} from '@/types/api';
import { BentoCard } from '@/components/dashboard/BentoCard';

/**
 * Get status icon for campaign status display
 */
const getCampaignStatusIcon = (status: string) => {
  switch (status.toLowerCase()) {
    case 'active':
      return <PlayIcon fontSize="small" />;
    case 'paused':
      return <PauseIcon fontSize="small" />;
    case 'completed':
    case 'cancelled':
      return <StopIcon fontSize="small" />;
    case 'draft':
      return <InfoIcon fontSize="small" />;
    default:
      return <InfoIcon fontSize="small" />;
  }
};

/**
 * Get status color for campaign status display
 */
const getCampaignStatusColor = (
  status: string
): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (status.toLowerCase()) {
    case 'active':
      return 'success';
    case 'paused':
      return 'warning';
    case 'completed':
      return 'info';
    case 'cancelled':
      return 'error';
    case 'draft':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * Get status icon for outreach response status
 */
const getResponseStatusIcon = (status: LinkedInOutreachResponseStatus) => {
  switch (status) {
    case 'interested':
      return <CheckIcon fontSize="small" />;
    case 'not_interested':
      return <CancelIcon fontSize="small" />;
    case 'replied':
      return <ReplyIcon fontSize="small" />;
    case 'no_response':
      return <HelpIcon fontSize="small" />;
    case 'opened':
      return <EmailIcon fontSize="small" />;
    case 'bounced':
      return <CancelIcon fontSize="small" />;
    default:
      return <HelpIcon fontSize="small" />;
  }
};

/**
 * Get status color for outreach response status
 */
const getResponseStatusColor = (
  status: LinkedInOutreachResponseStatus
): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (status) {
    case 'interested':
      return 'success';
    case 'not_interested':
      return 'error';
    case 'replied':
      return 'info';
    case 'opened':
      return 'info';
    case 'bounced':
      return 'error';
    case 'no_response':
    default:
      return 'default';
  }
};

/**
 * LinkedInCampaignDetail Component
 *
 * Displays detailed view of a LinkedIn outreach campaign including:
 * - Campaign statistics and metrics
 * - Outreach message list with response tracking
 * - Activity timeline showing campaign progress
 *
 * @example
 * ```tsx
 * // Accessed via route: /recruiter/linkedin/campaigns/:id
 * <LinkedInCampaignDetail />
 * ```
 */
const LinkedInCampaignDetail: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Campaign data state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [campaign, setCampaign] = useState<LinkedInCampaignResponse | null>(null);
  const [stats, setStats] = useState<LinkedInCampaignStatsResponse | null>(null);
  const [outreachList, setOutreachList] = useState<LinkedInOutreachResponse[]>([]);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  /**
   * Fetch campaign details, stats, and outreach list
   */
  const fetchCampaignData = useCallback(async () => {
    if (!id) {
      setError('Campaign ID is missing');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch all campaign data in parallel
      const [campaignData, statsData, outreachData] = await Promise.all([
        linkedinApi.getCampaign(id),
        linkedinApi.getCampaignStats(id),
        linkedinApi.getOutreachList(id),
      ]);

      setCampaign(campaignData);
      setStats(statsData);
      setOutreachList(outreachData);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load campaign details';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCampaignData();
  }, [fetchCampaignData]);

  /**
   * Handle page change
   */
  const handleChangePage = useCallback((event: unknown, newPage: number) => {
    setPage(newPage);
  }, []);

  /**
   * Handle rows per page change
   */
  const handleChangeRowsPerPage = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setRowsPerPage(parseInt(event.target.value, 10));
      setPage(0);
    },
    []
  );

  /**
   * Get paginated outreach list for current page
   */
  const paginatedOutreach = useMemo(() => {
    const start = page * rowsPerPage;
    const end = start + rowsPerPage;
    return outreachList.slice(start, end);
  }, [outreachList, page, rowsPerPage]);

  /**
   * Render loading state
   */
  if (loading && !campaign) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
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
            {t('linkedin.campaigns.loadingCampaignDetails', 'Loading Campaign Details')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t(
              'linkedin.campaigns.loadingCampaignDetailsMessage',
              'Please wait while we fetch the campaign information...'
            )}
          </Typography>
        </Box>
      </Container>
    );
  }

  /**
   * Render error state
   */
  if (error || !campaign) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={() => navigate('/recruiter/linkedin/campaigns')}>
              {t('common.backToList', 'Back to List')}
            </Button>
          }
        >
          <Typography variant="body1" fontWeight={600}>
            {error || t('linkedin.campaigns.campaignNotFound', 'Campaign not found')}
          </Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header with Back Button */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/recruiter/linkedin/campaigns')}
          sx={{ mb: 2 }}
        >
          {t('common.back', 'Back')}
        </Button>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <CampaignIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4" component="h1" fontWeight={700}>
            {campaign.name}
          </Typography>
          <Chip
            icon={getCampaignStatusIcon(campaign.status)}
            label={campaign.status.toUpperCase()}
            color={getCampaignStatusColor(campaign.status)}
            size="medium"
            variant="filled"
          />
        </Box>

        {campaign.description && (
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            {campaign.description}
          </Typography>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {t('linkedin.campaigns.createdAt', 'Created')}: {new Date(campaign.created_at).toLocaleDateString()}
        </Typography>
      </Box>

      {/* Statistics Dashboard */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Target Count Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('linkedin.campaigns.stats.targetCount', 'Target Count')}
            value={campaign.target_count || 0}
            subtitle={t('linkedin.campaigns.stats.candidates', 'Candidates')}
            icon={<PersonIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>

        {/* Sent Count Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('linkedin.campaigns.stats.sentCount', 'Messages Sent')}
            value={campaign.sent_count || 0}
            subtitle={t('linkedin.campaigns.stats.totalOutreach', 'Total outreach')}
            icon={<SendIcon sx={{ color: 'white' }} />}
            color="info"
          />
        </Grid>

        {/* Response Count Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('linkedin.campaigns.stats.responseCount', 'Responses')}
            value={campaign.response_count || 0}
            subtitle={t('linkedin.campaigns.stats.received', 'Received')}
            icon={<ReplyIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>

        {/* Response Rate Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('linkedin.campaigns.stats.responseRate', 'Response Rate')}
            value={`${campaign.response_rate ? campaign.response_rate.toFixed(1) : '0.0'}%`}
            subtitle={t('linkedin.campaigns.stats.ofSent', 'Of sent messages')}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* Detailed Statistics (if available) */}
      {stats && (
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {t('linkedin.campaigns.detailedStats', 'Detailed Statistics')}
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    {t('linkedin.campaigns.stats.interested', 'Interested')}
                  </Typography>
                  <Typography variant="h5" fontWeight={600} color="success.main">
                    {stats.interested || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    {t('linkedin.campaigns.stats.notInterested', 'Not Interested')}
                  </Typography>
                  <Typography variant="h5" fontWeight={600} color="error.main">
                    {stats.not_interested || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="caption" color="text.secondary">
                    {t('linkedin.campaigns.stats.noResponse', 'No Response')}
                  </Typography>
                  <Typography variant="h5" fontWeight={600} color="text.secondary">
                    {stats.no_response || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Outreach List */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <TimelineIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h5" fontWeight={600}>
              {t('linkedin.campaigns.outreachList', 'Outreach Messages')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {outreachList.length}{' '}
              {outreachList.length === 1
                ? t('linkedin.campaigns.messageSingular', 'message')
                : t('linkedin.campaigns.messagePlural', 'messages')}
            </Typography>
          </Box>
        </Box>

        {/* Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('linkedin.campaigns.outreach.profile', 'Profile')}</TableCell>
                <TableCell>{t('linkedin.campaigns.outreach.subject', 'Subject')}</TableCell>
                <TableCell>{t('linkedin.campaigns.outreach.sentAt', 'Sent At')}</TableCell>
                <TableCell>{t('linkedin.campaigns.outreach.status', 'Response Status')}</TableCell>
                <TableCell>{t('linkedin.campaigns.outreach.respondedAt', 'Responded At')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedOutreach.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} sx={{ py: 8, textAlign: 'center' }}>
                    <EmailIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      {t('linkedin.campaigns.noOutreach', 'No Outreach Messages')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t(
                        'linkedin.campaigns.noOutreachMessage',
                        'No outreach messages have been sent for this campaign yet.'
                      )}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedOutreach.map((outreach) => (
                  <TableRow key={outreach.id} hover>
                    {/* Profile ID */}
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                          <PersonIcon fontSize="small" />
                        </Avatar>
                        <Typography variant="body2" sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {outreach.linkedin_profile_id.substring(0, 8)}...
                        </Typography>
                      </Box>
                    </TableCell>

                    {/* Subject */}
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {outreach.message_subject || t('linkedin.campaigns.outreach.noSubject', 'No subject')}
                      </Typography>
                    </TableCell>

                    {/* Sent At */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {outreach.message_sent_at
                          ? new Date(outreach.message_sent_at).toLocaleDateString()
                          : 'N/A'}
                      </Typography>
                    </TableCell>

                    {/* Response Status */}
                    <TableCell>
                      <Chip
                        icon={getResponseStatusIcon(outreach.response_status)}
                        label={outreach.response_status.replace('_', ' ').toUpperCase()}
                        color={getResponseStatusColor(outreach.response_status)}
                        size="small"
                        variant="filled"
                      />
                    </TableCell>

                    {/* Responded At */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {outreach.response_received_at
                          ? new Date(outreach.response_received_at).toLocaleDateString()
                          : '-'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {outreachList.length > 0 && (
          <TablePagination
            component="div"
            count={outreachList.length}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[10, 25, 50, 100]}
            labelRowsPerPage={t('common.rowsPerPage', 'Rows per page:')}
            labelDisplayedRows={({ from, to, count }) =>
              `${from}-${to} ${t('common.of', 'of')} ${count !== -1 ? count : `${t('common.moreThan', 'more than')} ${to}`}`
            }
          />
        )}
      </Paper>
    </Container>
  );
};

export default LinkedInCampaignDetail;
