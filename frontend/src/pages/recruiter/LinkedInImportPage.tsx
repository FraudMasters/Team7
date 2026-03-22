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
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api/client';
import type { LinkedInImportHistoryItem } from '@/types/api';
import { BentoCard } from '@/components/dashboard/BentoCard';

/**
 * Get status icon for display
 */
const getStatusIcon = (status: string) => {
  switch (status.toLowerCase()) {
    case 'success':
    case 'completed':
      return <CheckIcon fontSize="small" />;
    case 'failed':
    case 'error':
      return <ErrorIcon fontSize="small" />;
    case 'in_progress':
    case 'processing':
      return <CircularProgress size={16} />;
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
    case 'success':
    case 'completed':
      return 'success';
    case 'failed':
    case 'error':
      return 'error';
    case 'in_progress':
    case 'processing':
      return 'info';
    default:
      return 'default';
  }
};

const LinkedInImportPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LinkedInImportHistoryItem[]>([]);
  const [total, setTotal] = useState(0);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  /**
   * Fetch import history from backend
   */
  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getLinkedInImportHistory(
        page * rowsPerPage,
        rowsPerPage
      );

      setData(response.imports);
      setTotal(response.total_imports);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load import history';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

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
   * Calculate statistics from import data
   */
  const statistics = useMemo(() => {
    const totalImports = total;

    // Calculate success rate
    const successfulImports = data.filter(
      (item) => item.status.toLowerCase() === 'success' || item.status.toLowerCase() === 'completed'
    ).length;
    const successRate = totalImports > 0
      ? ((successfulImports / totalImports) * 100).toFixed(1)
      : '0.0';

    // Calculate recent imports (last 7 days)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const recentImports = data.filter((item) => {
      if (!item.imported_at) return false;
      const importDate = new Date(item.imported_at);
      return importDate >= sevenDaysAgo;
    }).length;

    return {
      totalImports,
      successRate,
      recentImports,
    };
  }, [data, total]);

  /**
   * Render loading state
   */
  if (loading && data.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          {t('linkedin.import.title', 'Import from LinkedIn')}
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
            {t('linkedin.import.loadingHistory', 'Loading Import History')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t(
              'linkedin.import.loadingHistoryMessage',
              'Please wait while we fetch the import history...'
            )}
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('linkedin.import.title', 'Import from LinkedIn')}
      </Typography>

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Dashboard */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Total Imports Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.import.stats.totalImports', 'Total Imports')}
            value={statistics.totalImports}
            subtitle={t('linkedin.import.stats.allTime', 'All time')}
            icon={<AssessmentIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>

        {/* Success Rate Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.import.stats.successRate', 'Success Rate')}
            value={`${statistics.successRate}%`}
            subtitle={t('linkedin.import.stats.successful', 'Successful imports')}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>

        {/* Recent Imports Card */}
        <Grid item xs={12} sm={6} lg={4}>
          <BentoCard
            title={t('linkedin.import.stats.recentImports', 'Recent Imports')}
            value={statistics.recentImports}
            subtitle={t('linkedin.import.stats.lastSevenDays', 'Last 7 days')}
            icon={<AccessTimeIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* Import History Table */}
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
              {t('linkedin.import.historyTitle', 'Import History')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {total} {total === 1 ? t('linkedin.import.importSingular', 'import') : t('linkedin.import.importPlural', 'imports')}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Refresh Button */}
            <Button
              variant="outlined"
              startIcon={
                loading ? <CircularProgress size={16} /> : <RefreshIcon />
              }
              onClick={fetchHistory}
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
                <TableCell>{t('linkedin.import.profileName', 'Profile Name')}</TableCell>
                <TableCell>{t('linkedin.import.importDate', 'Import Date')}</TableCell>
                <TableCell>{t('linkedin.import.status', 'Status')}</TableCell>
                <TableCell>{t('linkedin.import.resumeId', 'Resume ID')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} sx={{ py: 8, textAlign: 'center' }}>
                    <CloudUploadIcon
                      sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }}
                    />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      {t('linkedin.import.noImports', 'No Imports Found')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t(
                        'linkedin.import.noImportsMessage',
                        'No LinkedIn profiles have been imported yet.'
                      )}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data.map((item) => (
                  <TableRow key={item.import_id} hover>
                    {/* Profile Name */}
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {item.profile_name || 'Unknown'}
                      </Typography>
                    </TableCell>

                    {/* Import Date */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {item.imported_at
                          ? new Date(item.imported_at).toLocaleString()
                          : 'N/A'}
                      </Typography>
                    </TableCell>

                    {/* Status Badge */}
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(item.status)}
                        label={item.status.toUpperCase()}
                        color={getStatusColor(item.status)}
                        size="small"
                        variant="filled"
                      />
                    </TableCell>

                    {/* Resume ID */}
                    <TableCell>
                      <Typography
                        variant="body2"
                        color={item.resume_id ? 'text.primary' : 'text.secondary'}
                      >
                        {item.resume_id || 'N/A'}
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

export default LinkedInImportPage;
