import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Campaign as CampaignIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { linkedinApi } from '@/services/linkedinApi';
import type { LinkedInCampaignResponse } from '@/types/api';
import { BentoCard } from '@/components/dashboard/BentoCard';

/**
 * Get status icon for display
 */
const getStatusIcon = (status: string) => {
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
 * Get status color for display
 */
const getStatusColor = (
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

const LinkedInCampaignsPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [campaigns, setCampaigns] = useState<LinkedInCampaignResponse[]>([]);
  const [total, setTotal] = useState(0);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  /**
   * Fetch campaigns from backend
   */
  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await linkedinApi.getCampaigns();

      setCampaigns(response.campaigns);
      setTotal(response.total);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load campaigns';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

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
   * Handle create campaign button click
   */
  const handleCreateCampaign = useCallback(() => {
    // TODO: Navigate to campaign creation page or open dialog
    alert('Create campaign functionality to be implemented');
  }, []);

  /**
   * Calculate statistics from campaign data
   */
  const statistics = useMemo(() => {
    const totalCampaigns = total;

    // Calculate active campaigns
    const activeCampaigns = campaigns.filter(
      (campaign) => campaign.status.toLowerCase() === 'active'
    ).length;

    // Calculate average response rate
    const totalResponseRate = campaigns.reduce(
      (sum, campaign) => sum + (campaign.response_rate || 0),
      0
    );
    const avgResponseRate =
      campaigns.length > 0
        ? (totalResponseRate / campaigns.length).toFixed(1)
        : '0.0';

    return {
      totalCampaigns,
      activeCampaigns,
      avgResponseRate,
    };
  }, [campaigns, total]);

  /**
   * Get paginated campaigns for current page
   */
  const paginatedCampaigns = useMemo(() => {
    const start = page * rowsPerPage;
    const end = start + rowsPerPage;
    return campaigns.slice(start, end);
  }, [campaigns, page, rowsPerPage]);

  /**
   * Render loading state
   */
  if (loading && campaigns.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {t('linkedin.campaigns.title', 'LinkedIn Campaigns')}
        </Typography>
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
            {t('linkedin.campaigns.loadingCampaigns', 'Loading Campaigns')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t(
              'linkedin.campaigns.loadingCampaignsMessage',
              'Please wait while we fetch the campaigns...'
            )}
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('linkedin.campaigns.title', 'LinkedIn Campaigns')}
      </Typography>

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Dashboard */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Total Campaigns Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.campaigns.stats.totalCampaigns', 'Total Campaigns')}
            value={statistics.totalCampaigns}
            subtitle={t('linkedin.campaigns.stats.allTime', 'All time')}
            icon={<CampaignIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>

        {/* Active Campaigns Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.campaigns.stats.activeCampaigns', 'Active Campaigns')}
            value={statistics.activeCampaigns}
            subtitle={t('linkedin.campaigns.stats.currentlyRunning', 'Currently running')}
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>

        {/* Average Response Rate Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.campaigns.stats.avgResponseRate', 'Avg Response Rate')}
            value={`${statistics.avgResponseRate}%`}
            subtitle={t('linkedin.campaigns.stats.acrossAllCampaigns', 'Across all campaigns')}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* Campaigns Table */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
            flexWrap: 'wrap',
            gap: 2,
          }}
        >
          <Box>
            <Typography variant="h5" fontWeight={600}>
              {t('linkedin.campaigns.listTitle', 'Campaigns')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {total}{' '}
              {total === 1
                ? t('linkedin.campaigns.campaignSingular', 'campaign')
                : t('linkedin.campaigns.campaignPlural', 'campaigns')}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Create Campaign Button */}
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateCampaign}
              color="primary"
              size="small"
            >
              {t('linkedin.campaigns.createCampaign', 'Create Campaign')}
            </Button>

            {/* Refresh Button */}
            <Button
              variant="outlined"
              startIcon={
                loading ? <CircularProgress size={16} /> : <RefreshIcon />
              }
              onClick={fetchCampaigns}
              disabled={loading}
              size="small"
            >
              {t('common.refresh', 'Refresh')}
            </Button>
          </Box>
        </Box>

        {/* Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('linkedin.campaigns.campaignName', 'Campaign Name')}</TableCell>
                <TableCell>{t('linkedin.campaigns.status', 'Status')}</TableCell>
                <TableCell>{t('linkedin.campaigns.targetCount', 'Target Count')}</TableCell>
                <TableCell>{t('linkedin.campaigns.sentCount', 'Sent')}</TableCell>
                <TableCell>{t('linkedin.campaigns.responseCount', 'Responses')}</TableCell>
                <TableCell>{t('linkedin.campaigns.responseRate', 'Response Rate')}</TableCell>
                <TableCell>{t('linkedin.campaigns.createdAt', 'Created')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedCampaigns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} sx={{ py: 8, textAlign: 'center' }}>
                    <CampaignIcon
                      sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }}
                    />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      {t('linkedin.campaigns.noCampaigns', 'No Campaigns Found')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t(
                        'linkedin.campaigns.noCampaignsMessage',
                        'No LinkedIn campaigns have been created yet.'
                      )}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedCampaigns.map((campaign) => (
                  <TableRow key={campaign.id} hover>
                    {/* Campaign Name */}
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {campaign.name || 'Unnamed Campaign'}
                      </Typography>
                      {campaign.description && (
                        <Typography variant="caption" color="text.secondary">
                          {campaign.description}
                        </Typography>
                      )}
                    </TableCell>

                    {/* Status Badge */}
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(campaign.status)}
                        label={campaign.status.toUpperCase()}
                        color={getStatusColor(campaign.status)}
                        size="small"
                        variant="filled"
                      />
                    </TableCell>

                    {/* Target Count */}
                    <TableCell>
                      <Typography variant="body2">
                        {campaign.target_count || 0}
                      </Typography>
                    </TableCell>

                    {/* Sent Count */}
                    <TableCell>
                      <Typography variant="body2">
                        {campaign.sent_count || 0}
                      </Typography>
                    </TableCell>

                    {/* Response Count */}
                    <TableCell>
                      <Typography variant="body2">
                        {campaign.response_count || 0}
                      </Typography>
                    </TableCell>

                    {/* Response Rate */}
                    <TableCell>
                      <Typography
                        variant="body2"
                        color={
                          campaign.response_rate > 20
                            ? 'success.main'
                            : campaign.response_rate > 10
                            ? 'warning.main'
                            : 'text.secondary'
                        }
                        fontWeight={campaign.response_rate > 10 ? 600 : 400}
                      >
                        {campaign.response_rate
                          ? `${campaign.response_rate.toFixed(1)}%`
                          : '0.0%'}
                      </Typography>
                    </TableCell>

                    {/* Created Date */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {campaign.created_at
                          ? new Date(campaign.created_at).toLocaleDateString()
                          : 'N/A'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={total}
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
      </Paper>
    </Container>
  );
};

export default LinkedInCampaignsPage;
