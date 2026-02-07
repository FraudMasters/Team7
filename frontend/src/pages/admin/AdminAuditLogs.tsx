/**
 * Admin Audit Logs Page
 *
 * Provides comprehensive audit trail viewing functionality for system administrators including:
 * - Filterable list of all audit logs
 * - Search by action type, entity type, user, and date range
 * - Export functionality for compliance reporting
 * - Detailed log inspection dialog
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Grid,
  IconButton,
  Stack,
  Pagination,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterListIcon,
  Visibility as VisibilityIcon,
  History as HistoryIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Event as EventIcon,
  Category as CategoryIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import auditLogApi from '../../services/auditLogApi';
import type { AuditLog, AuditLogsQuery } from '@/types/api';

interface FilterState {
  action_type: string;
  entity_type: string;
  user_id: string;
  start_date: string;
  end_date: string;
}

const AdminAuditLogsPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    action_type: '',
    entity_type: '',
    user_id: '',
    start_date: '',
    end_date: '',
  });
  const [filterOptions, setFilterOptions] = useState({
    action_types: [] as string[],
    entity_types: [] as string[],
  });

  // Dialog states
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const queryParams: AuditLogsQuery = {
        limit: rowsPerPage,
        offset: (page - 1) * rowsPerPage,
      };

      if (filters.action_type) queryParams.action_type = filters.action_type;
      if (filters.entity_type) queryParams.entity_type = filters.entity_type;
      if (filters.user_id) queryParams.user_id = filters.user_id;
      if (filters.start_date) queryParams.start_date = filters.start_date;
      if (filters.end_date) queryParams.end_date = filters.end_date;

      const response = await auditLogApi.getAuditLogs(queryParams);
      setLogs(response.logs);
      setTotalCount(response.total_count);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch audit logs';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [filters, page, rowsPerPage]);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const [actionTypes, entityTypes] = await Promise.all([
        auditLogApi.getActionTypes(),
        auditLogApi.getEntityTypes(),
      ]);

      setFilterOptions({
        action_types: actionTypes.action_types,
        entity_types: entityTypes.entity_types,
      });
    } catch (err) {
      console.error('Failed to fetch filter options:', err);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
    fetchFilterOptions();
  }, [fetchLogs, fetchFilterOptions]);

  const handleExport = async () => {
    try {
      const queryParams: AuditLogsQuery = {};
      if (filters.action_type) queryParams.action_type = filters.action_type;
      if (filters.entity_type) queryParams.entity_type = filters.entity_type;
      if (filters.user_id) queryParams.user_id = filters.user_id;
      if (filters.start_date) queryParams.start_date = filters.start_date;
      if (filters.end_date) queryParams.end_date = filters.end_date;
      queryParams.limit = 10000; // Export more records

      const response = await auditLogApi.getAuditLogs(queryParams);

      // Convert to CSV
      const headers = ['Timestamp', 'Action', 'Entity Type', 'Entity ID', 'User ID', 'Organization ID', 'IP Address', 'Details'];
      const rows = response.logs.map((log) => [
        format(new Date(log.created_at), 'yyyy-MM-dd HH:mm:ss'),
        log.action_type,
        log.entity_type || '',
        log.entity_id || '',
        log.user_id || '',
        log.organization_id || '',
        log.ip_address || '',
        log.reason || '',
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
      ].join('\n');

      // Download file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `audit-logs-${format(new Date(), 'yyyy-MM-dd-HHmmss')}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSuccess(`Exported ${response.logs.length} audit logs to CSV.`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to export audit logs';
      setError(message);
    }
  };

  const handleClearFilters = () => {
    setFilters({
      action_type: '',
      entity_type: '',
      user_id: '',
      start_date: '',
      end_date: '',
    });
    setPage(1);
  };

  const getActionTypeColor = (actionType: string): 'success' | 'info' | 'warning' | 'error' | 'default' => {
    if (actionType.includes('create') || actionType.includes('upload')) return 'success';
    if (actionType.includes('update') || actionType.includes('modify')) return 'info';
    if (actionType.includes('delete') || actionType.includes('remove')) return 'error';
    if (actionType.includes('export') || actionType.includes('download')) return 'warning';
    return 'default';
  };

  const getActionLabel = (action: string): string => {
    return action
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (loading && logs.length === 0) {
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
          <HistoryIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            Admin Audit Logs
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchLogs}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={logs.length === 0}
          >
            Export
          </Button>
        </Stack>
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

      {/* Filters Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FilterListIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Filters</Typography>
            {(filters.action_type || filters.entity_type || filters.user_id || filters.start_date || filters.end_date) && (
              <Button
                size="small"
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
                sx={{ ml: 'auto' }}
              >
                Clear All
              </Button>
            )}
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Action Type</InputLabel>
                <Select
                  value={filters.action_type}
                  onChange={(e) => {
                    setFilters({ ...filters, action_type: e.target.value });
                    setPage(1);
                  }}
                  label="Action Type"
                >
                  <MenuItem value="">
                    <em>All Actions</em>
                  </MenuItem>
                  {filterOptions.action_types.map((type) => (
                    <MenuItem key={type} value={type}>
                      {getActionLabel(type)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Entity Type</InputLabel>
                <Select
                  value={filters.entity_type}
                  onChange={(e) => {
                    setFilters({ ...filters, entity_type: e.target.value });
                    setPage(1);
                  }}
                  label="Entity Type"
                >
                  <MenuItem value="">
                    <em>All Entities</em>
                  </MenuItem>
                  {filterOptions.entity_types.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="User ID"
                value={filters.user_id}
                onChange={(e) => {
                  setFilters({ ...filters, user_id: e.target.value });
                  setPage(1);
                }}
                placeholder="Enter user ID"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="date"
                label="Start Date"
                value={filters.start_date}
                onChange={(e) => {
                  setFilters({ ...filters, start_date: e.target.value });
                  setPage(1);
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="date"
                label="End Date"
                value={filters.end_date}
                onChange={(e) => {
                  setFilters({ ...filters, end_date: e.target.value });
                  setPage(1);
                }}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <HistoryIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Logs
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CategoryIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Action Types
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {filterOptions.action_types.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BusinessIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Entity Types
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {filterOptions.entity_types.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EventIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Showing
                </Typography>
              </Box>
              <Typography variant="body1" fontWeight={500}>
                {logs.length} of {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Audit Logs Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Entity</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Organization</TableCell>
                  <TableCell>IP Address</TableCell>
                  <TableCell align="right">Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No audit logs found. Adjust filters or perform some actions to generate logs.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(log.created_at), 'MMM dd, HH:mm:ss')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {format(new Date(log.created_at), 'yyyy')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getActionLabel(log.action_type)}
                          size="small"
                          color={getActionTypeColor(log.action_type)}
                        />
                      </TableCell>
                      <TableCell>
                        {log.entity_type ? (
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              {log.entity_type.charAt(0).toUpperCase() + log.entity_type.slice(1)}
                            </Typography>
                            {log.entity_id && (
                              <Typography variant="caption" color="text.secondary">
                                ID: {log.entity_id}
                              </Typography>
                            )}
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {log.user_id ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <PersonIcon fontSize="small" color="disabled" />
                            <Typography variant="body2">
                              {log.user_id}
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            System
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {log.organization_id ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <BusinessIcon fontSize="small" color="disabled" />
                            <Typography variant="body2">
                              {log.organization_id}
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {log.ip_address || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedLog(log);
                              setDetailsDialogOpen(true);
                            }}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalCount > rowsPerPage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={Math.ceil(totalCount / rowsPerPage)}
                page={page}
                onChange={(e, newPage) => setPage(newPage)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => {
          setDetailsDialogOpen(false);
          setSelectedLog(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Audit Log Details</DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Log ID
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {selectedLog.id}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Timestamp
                </Typography>
                <Typography variant="body2">
                  {format(new Date(selectedLog.created_at), 'PPPp')}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Action Type
                </Typography>
                <Chip
                  label={getActionLabel(selectedLog.action_type)}
                  size="small"
                  color={getActionTypeColor(selectedLog.action_type)}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Entity
                </Typography>
                <Typography variant="body2">
                  {selectedLog.entity_type
                    ? `${selectedLog.entity_type} (${selectedLog.entity_id || 'N/A'})`
                    : 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  User
                </Typography>
                <Typography variant="body2">
                  {selectedLog.user_id || 'System'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Organization
                </Typography>
                <Typography variant="body2">
                  {selectedLog.organization_id || 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  IP Address
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {selectedLog.ip_address || 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  User Agent
                </Typography>
                <Typography variant="body2" sx={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>
                  {selectedLog.user_agent || 'N/A'}
                </Typography>
              </Grid>
              {selectedLog.reason && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Reason
                  </Typography>
                  <Typography variant="body2">
                    {selectedLog.reason}
                  </Typography>
                </Grid>
              )}
              {selectedLog.action_data && Object.keys(selectedLog.action_data).length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Action Data
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: 'grey.50',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      overflow: 'auto',
                      maxHeight: 200,
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(selectedLog.action_data, null, 2)}
                    </pre>
                  </Box>
                </Grid>
              )}
              {selectedLog.before_value && Object.keys(selectedLog.before_value).length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Before Value
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: 'error.light',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      overflow: 'auto',
                      maxHeight: 200,
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(selectedLog.before_value, null, 2)}
                    </pre>
                  </Box>
                </Grid>
              )}
              {selectedLog.after_value && Object.keys(selectedLog.after_value).length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    After Value
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: 'success.light',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      overflow: 'auto',
                      maxHeight: 200,
                    }}
                  >
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {JSON.stringify(selectedLog.after_value, null, 2)}
                    </pre>
                  </Box>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setDetailsDialogOpen(false);
              setSelectedLog(null);
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminAuditLogsPage;
