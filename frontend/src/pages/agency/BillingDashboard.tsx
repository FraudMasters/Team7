import React, { useState, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  CalendarToday as CalendarIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { BentoCard } from '@/components/dashboard/BentoCard';
import DashboardFilters, { DashboardFiltersState } from '@/components/analytics/DashboardFilters';
import { useAgencyBilling } from '@/hooks/useAgencyData';

/**
 * Billing Dashboard Page (Agency Module)
 *
 * Shows billing and usage tracking for agency with:
 * - Total revenue metrics
 * - Per-client billing breakdown
 * - Usage tracking
 * - Configurable date range filtering
 * - Export functionality
 */
const BillingDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<DashboardFiltersState>({
    dateRange: {
      startDate: '',
      endDate: '',
      preset: 'last_30_days',
    },
    recruiterId: null,
    vacancyId: null,
  });
  const [refreshing, setRefreshing] = useState(false);

  /**
   * Fetch billing data with current filters
   */
  const {
    data: billingData,
    isLoading,
    error,
    refetch,
  } = useAgencyBilling({
    startDate: filters.dateRange.startDate,
    endDate: filters.dateRange.endDate,
  });

  /**
   * Handle filters change from DashboardFilters component
   */
  const handleFiltersChange = (newFilters: DashboardFiltersState) => {
    setFilters(newFilters);
  };

  /**
   * Handle apply button click
   */
  const handleApplyFilter = (appliedFilters: DashboardFiltersState) => {
    setFilters(appliedFilters);
  };

  /**
   * Handle manual refresh
   */
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  /**
   * Handle export to CSV
   */
  const handleExport = useCallback(() => {
    if (!billingData?.clients) return;

    // Generate CSV content
    const headers = ['Client Name', 'Status', 'Monthly Fee', 'Usage Costs', 'Total', 'Candidates', 'Active Jobs'];
    const rows = billingData.clients.map((client) => [
      client.name,
      client.status,
      `$${client.monthly_fee.toFixed(2)}`,
      `$${client.usage_costs.toFixed(2)}`,
      `$${client.total_billing.toFixed(2)}`,
      client.candidates_count.toString(),
      client.active_jobs_count.toString(),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    // Download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `billing-report-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [billingData]);

  /**
   * Format currency
   */
  const formatCurrency = (amount: number): string => {
    return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  /**
   * Get status color
   */
  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'active':
        return 'success';
      case 'suspended':
        return 'warning';
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} className="billing-dashboard">
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {t('billingDashboard.title', 'Billing Dashboard')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('billingDashboard.subtitle', 'Track revenue and usage across all clients')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh">
            <IconButton
              onClick={handleRefresh}
              disabled={refreshing || isLoading}
              size="small"
              sx={{ alignSelf: 'flex-start' }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={!billingData?.clients || billingData.clients.length === 0}
          >
            {t('billingDashboard.exportButton', 'Export CSV')}
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Box sx={{ mb: 4 }}>
        <DashboardFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onApply={handleApplyFilter}
          showRecruiterFilter={false}
          showVacancyFilter={false}
        />
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {t('billingDashboard.errorLoading', 'Failed to load billing data. Please try again.')}
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Billing Metrics */}
      {!isLoading && billingData && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* Total Revenue */}
            <Grid item xs={12} sm={6} md={3}>
              <BentoCard
                title={t('billingDashboard.totalRevenue', 'Total Revenue')}
                value={formatCurrency(billingData.total_revenue || 0)}
                subtitle={t('billingDashboard.currentPeriod', 'Current period')}
                icon={<MoneyIcon sx={{ color: 'white' }} />}
                color="primary"
              />
            </Grid>

            {/* Monthly Recurring Revenue */}
            <Grid item xs={12} sm={6} md={3}>
              <BentoCard
                title={t('billingDashboard.mrr', 'Monthly Recurring')}
                value={formatCurrency(billingData.monthly_recurring || 0)}
                subtitle={t('billingDashboard.recurringFees', 'Recurring fees')}
                icon={<TrendingUpIcon sx={{ color: 'white' }} />}
                color="success"
              />
            </Grid>

            {/* Usage Costs */}
            <Grid item xs={12} sm={6} md={3}>
              <BentoCard
                title={t('billingDashboard.usageCosts', 'Usage Costs')}
                value={formatCurrency(billingData.usage_costs || 0)}
                subtitle={t('billingDashboard.variableCosts', 'Variable costs')}
                icon={<CalendarIcon sx={{ color: 'white' }} />}
                color="warning"
              />
            </Grid>

            {/* Active Clients */}
            <Grid item xs={12} sm={6} md={3}>
              <BentoCard
                title={t('billingDashboard.activeClients', 'Active Clients')}
                value={billingData.active_clients_count || 0}
                subtitle={t('billingDashboard.payingClients', 'Paying clients')}
                icon={<BusinessIcon sx={{ color: 'white' }} />}
                color="secondary"
              />
            </Grid>
          </Grid>

          {/* Per-Client Breakdown Table */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" fontWeight={600}>
                {t('billingDashboard.clientBreakdown', 'Per-Client Breakdown')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {billingData.clients?.length || 0} {t('billingDashboard.clients', 'clients')}
              </Typography>
            </Box>

            {billingData.clients && billingData.clients.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('billingDashboard.table.clientName', 'Client Name')}</TableCell>
                      <TableCell>{t('billingDashboard.table.status', 'Status')}</TableCell>
                      <TableCell align="right">{t('billingDashboard.table.monthlyFee', 'Monthly Fee')}</TableCell>
                      <TableCell align="right">{t('billingDashboard.table.usageCosts', 'Usage Costs')}</TableCell>
                      <TableCell align="right">{t('billingDashboard.table.total', 'Total')}</TableCell>
                      <TableCell align="right">{t('billingDashboard.table.candidates', 'Candidates')}</TableCell>
                      <TableCell align="right">{t('billingDashboard.table.activeJobs', 'Active Jobs')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {billingData.clients.map((client) => (
                      <TableRow key={client.tenant_id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {client.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={client.status}
                            size="small"
                            color={getStatusColor(client.status)}
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {formatCurrency(client.monthly_fee)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {formatCurrency(client.usage_costs)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={600}>
                            {formatCurrency(client.total_billing)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="text.secondary">
                            {client.candidates_count.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="text.secondary">
                            {client.active_jobs_count.toLocaleString()}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  {t('billingDashboard.noData', 'No billing data available for the selected period')}
                </Typography>
              </Box>
            )}
          </Paper>
        </>
      )}
    </Container>
  );
};

export default BillingDashboard;
