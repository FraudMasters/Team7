import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Collapse,
  Alert as MuiAlert,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Stack,
  Divider,
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Schedule as PendingIcon,
  Done as DeployedIcon,
  Block as CancelledIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Refresh as RefreshIcon,
  Description as RequestIcon,
  Person as PersonIcon,
  AccessTime as TimeIcon,
  RocketLaunch as DeployIcon,
  Gavel as GavelIcon,
} from '@mui/icons-material';
import {
  modelApprovalsClient,
  type ModelApprovalResponse,
  type ModelApprovalListParams,
  type ModelApprovalStatsResponse,
} from '@/api/modelApprovals';

/**
 * Approval status type
 */
type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'deployed' | 'cancelled';

/**
 * Component props
 */
interface ModelApprovalPanelProps {
  /** Maximum height for the scrollable list */
  maxHeight?: number | string;
  /** Whether to show filter controls */
  showFilters?: boolean;
  /** Initial model filter */
  modelFilter?: string;
  /** Callback when an approval is processed */
  onApprovalProcessed?: () => void;
}

/**
 * Model Approval Panel Component
 *
 * Displays a list of model deployment approval requests with filtering,
 * status indicators, and actions (approve, reject, deploy).
 *
 * @example
 * ```tsx
 * <ModelApprovalPanel
 *   maxHeight={600}
 *   showFilters={true}
 *   onApprovalProcessed={() => console.log('Approval processed')}
 * />
 * ```
 */
const ModelApprovalPanel: React.FC<ModelApprovalPanelProps> = ({
  maxHeight = 600,
  showFilters = true,
  modelFilter,
  onApprovalProcessed,
}) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approvals, setApprovals] = useState<ModelApprovalResponse[]>([]);
  const [stats, setStats] = useState<ModelApprovalStatsResponse | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('pending');
  const [selectedModel, setSelectedModel] = useState<string>(modelFilter || 'all');
  const [expandedApprovals, setExpandedApprovals] = useState<Set<string>>(new Set());

  // Dialog states
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject' | 'deploy' | null>(null);
  const [selectedApproval, setSelectedApproval] = useState<ModelApprovalResponse | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  /**
   * Fetch approval requests from API
   */
  const fetchApprovals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ModelApprovalListParams = {};
      if (selectedStatus !== 'all') {
        params.status = selectedStatus as ApprovalStatus;
      }
      if (selectedModel !== 'all') {
        params.model_name = selectedModel;
      }

      const response = await modelApprovalsClient.listApprovals(params);
      setApprovals(response.approvals || []);

      // Calculate stats from the approvals
      const allApprovals = response.approvals || [];
      setStats({
        total_requests: allApprovals.length,
        pending_requests: allApprovals.filter(a => a.status === 'pending').length,
        approved_requests: allApprovals.filter(a => a.status === 'approved').length,
        rejected_requests: allApprovals.filter(a => a.status === 'rejected').length,
        deployed_requests: allApprovals.filter(a => a.status === 'deployed').length,
        cancelled_requests: allApprovals.filter(a => a.status === 'cancelled').length,
        avg_approval_time_hours: null,
      });
    } catch (err) {
      // If API is not available, show mock data for visualization
      setApprovals([
        {
          id: '1',
          model_version_id: 'v1.2.0',
          model_name: 'skill_matching',
          version: 'v1.2.0',
          status: 'pending',
          justification: 'Improved accuracy by 5% on validation set. Ready for production deployment.',
          target_environment: 'production',
          requested_by: 'data-scientist@example.com',
          reviewed_by: null,
          review_notes: null,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          reviewed_at: null,
        },
        {
          id: '2',
          model_version_id: 'v2.0.0',
          model_name: 'ranking',
          version: 'v2.0.0',
          status: 'pending',
          justification: 'New ranking algorithm with better relevance scoring.',
          target_environment: 'production',
          requested_by: 'ml-engineer@example.com',
          reviewed_by: null,
          review_notes: null,
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          reviewed_at: null,
        },
        {
          id: '3',
          model_version_id: 'v1.1.5',
          model_name: 'skill_matching',
          version: 'v1.1.5',
          status: 'approved',
          justification: 'Bug fix for skill extraction edge cases.',
          target_environment: 'staging',
          requested_by: 'dev@example.com',
          reviewed_by: 'admin@example.com',
          review_notes: 'Approved for staging deployment.',
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
          reviewed_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '4',
          model_version_id: 'v1.9.0',
          model_name: 'ranking',
          version: 'v1.9.0',
          status: 'deployed',
          justification: 'Production-ready ranking model with improved performance.',
          target_environment: 'production',
          requested_by: 'ml-team@example.com',
          reviewed_by: 'cto@example.com',
          review_notes: 'Approved after thorough testing.',
          created_at: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          reviewed_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '5',
          model_version_id: 'v1.8.0',
          model_name: 'skill_matching',
          version: 'v1.8.0',
          status: 'rejected',
          justification: 'Experimental feature - not ready for production.',
          target_environment: 'production',
          requested_by: 'research@example.com',
          reviewed_by: 'lead@example.com',
          review_notes: 'Accuracy did not meet production threshold. More testing needed.',
          created_at: new Date(Date.now() - 96 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 90 * 60 * 60 * 1000).toISOString(),
          reviewed_at: new Date(Date.now() - 90 * 60 * 60 * 1000).toISOString(),
        },
      ]);
      setStats({
        total_requests: 5,
        pending_requests: 2,
        approved_requests: 1,
        rejected_requests: 1,
        deployed_requests: 1,
        cancelled_requests: 0,
        avg_approval_time_hours: 4.5,
      });
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, selectedModel]);

  /**
   * Handle refresh button click
   */
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchApprovals();
    setRefreshing(false);
  };

  /**
   * Toggle approval card expansion
   */
  const toggleApprovalExpand = (approvalId: string) => {
    setExpandedApprovals((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(approvalId)) {
        newSet.delete(approvalId);
      } else {
        newSet.add(approvalId);
      }
      return newSet;
    });
  };

  /**
   * Open action dialog
   */
  const openActionDialog = (type: 'approve' | 'reject' | 'deploy', approval: ModelApprovalResponse) => {
    setActionType(type);
    setSelectedApproval(approval);
    setReviewNotes('');
    setActionDialogOpen(true);
  };

  /**
   * Close action dialog
   */
  const closeActionDialog = () => {
    setActionDialogOpen(false);
    setActionType(null);
    setSelectedApproval(null);
    setReviewNotes('');
  };

  /**
   * Handle action confirmation
   */
  const handleActionConfirm = async () => {
    if (!selectedApproval || !actionType) return;

    try {
      setActionLoading(true);

      if (actionType === 'approve') {
        await modelApprovalsClient.approveRequest(selectedApproval.id, {
          reviewed_by: 'current-user', // TODO: Get from auth context
          review_notes: reviewNotes || undefined,
        });
        setSnackbar({
          open: true,
          message: `Approved ${selectedApproval.version}`,
          severity: 'success',
        });
      } else if (actionType === 'reject') {
        await modelApprovalsClient.rejectRequest(selectedApproval.id, {
          reviewed_by: 'current-user', // TODO: Get from auth context
          review_notes: reviewNotes || undefined,
        });
        setSnackbar({
          open: true,
          message: `Rejected ${selectedApproval.version}`,
          severity: 'success',
        });
      } else if (actionType === 'deploy') {
        await modelApprovalsClient.deployRequest(selectedApproval.id);
        setSnackbar({
          open: true,
          message: `Deployed ${selectedApproval.version}`,
          severity: 'success',
        });
      }

      closeActionDialog();
      await fetchApprovals();
      onApprovalProcessed?.();
    } catch (err) {
      setSnackbar({
        open: true,
        message: `Failed to ${actionType} request`,
        severity: 'error',
      });
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Close snackbar
   */
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  useEffect(() => {
    fetchApprovals();
  }, [fetchApprovals]);

  /**
   * Get status icon
   */
  const getStatusIcon = (status: ApprovalStatus) => {
    switch (status) {
      case 'pending':
        return <PendingIcon sx={{ fontSize: 18, color: '#ed6c02' }} />;
      case 'approved':
        return <ApproveIcon sx={{ fontSize: 18, color: '#0288d1' }} />;
      case 'rejected':
        return <RejectIcon sx={{ fontSize: 18, color: '#d32f2f' }} />;
      case 'deployed':
        return <DeployedIcon sx={{ fontSize: 18, color: '#2e7d32' }} />;
      case 'cancelled':
        return <CancelledIcon sx={{ fontSize: 18, color: '#757575' }} />;
      default:
        return <PendingIcon sx={{ fontSize: 18 }} />;
    }
  };

  /**
   * Get status color
   */
  const getStatusColor = (status: ApprovalStatus): 'warning' | 'info' | 'error' | 'success' | 'default' => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'approved':
        return 'info';
      case 'rejected':
        return 'error';
      case 'deployed':
        return 'success';
      default:
        return 'default';
    }
  };

  /**
   * Format time ago
   */
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={32} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading approval requests...
        </Typography>
      </Paper>
    );
  }

  return (
    <Box className="model-approval-panel">
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={stats?.pending_requests || 0} color="error" max={99}>
            <GavelIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          </Badge>
          <Typography variant="h6" fontWeight={500}>
            Model Deployment Approvals
          </Typography>
        </Box>
        <Button
          size="small"
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <MuiAlert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </MuiAlert>
      )}

      {/* Stats Summary */}
      {stats && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={1.5}>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Total
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {stats.total_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="warning.main">
                    Pending
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="warning.main">
                    {stats.pending_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="info.main">
                    Approved
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="info.main">
                    {stats.approved_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="success.main">
                    Deployed
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="success.main">
                    {stats.deployed_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="error.main">
                    Rejected
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="error.main">
                    {stats.rejected_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={4} md={2}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Cancelled
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {stats.cancelled_requests}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <FormControl size="small" fullWidth>
                <InputLabel>Model</InputLabel>
                <Select
                  value={selectedModel}
                  label="Model"
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="all">All Models</MenuItem>
                  <MenuItem value="skill_matching">Skill Matching</MenuItem>
                  <MenuItem value="ranking">Ranking</MenuItem>
                  <MenuItem value="resume_parser">Resume Parser</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl size="small" fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={selectedStatus}
                  label="Status"
                  onChange={(e) => setSelectedStatus(e.target.value)}
                >
                  <MenuItem value="all">All Statuses</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="rejected">Rejected</MenuItem>
                  <MenuItem value="deployed">Deployed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Approval Requests List */}
      <Paper sx={{ p: 2, maxHeight, overflow: 'auto' }}>
        {approvals.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <RequestIcon sx={{ fontSize: 32, color: 'text.disabled', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              No approval requests found
            </Typography>
          </Box>
        ) : (
          <Stack spacing={1.5}>
            {approvals.map((approval) => (
              <Card
                key={approval.id}
                variant="outlined"
                sx={{
                  borderLeft: 4,
                  borderLeftColor: approval.status === 'pending' ? 'warning.main' :
                    approval.status === 'approved' ? 'info.main' :
                    approval.status === 'rejected' ? 'error.main' :
                    approval.status === 'deployed' ? 'success.main' : 'grey.400',
                  opacity: approval.status === 'cancelled' ? 0.6 : 1,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    boxShadow: 2,
                  },
                }}
              >
                <CardContent sx={{ py: 1.5, px: 2 }}>
                  {/* Request Header */}
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, flex: 1 }}>
                      {getStatusIcon(approval.status)}
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 0.5 }}>
                          <Typography variant="subtitle2" fontWeight={600}>
                            {approval.version}
                          </Typography>
                          <Chip
                            label={approval.model_name}
                            size="small"
                            color="primary"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                          <Chip
                            label={approval.target_environment}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <PersonIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                              {approval.requested_by}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <TimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                              {formatTimeAgo(approval.created_at)}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Chip
                        label={approval.status}
                        size="small"
                        color={getStatusColor(approval.status)}
                        sx={{ fontSize: '0.7rem', height: 20, textTransform: 'capitalize' }}
                      />
                      <IconButton
                        size="small"
                        onClick={() => toggleApprovalExpand(approval.id)}
                      >
                        {expandedApprovals.has(approval.id) ? (
                          <CollapseIcon fontSize="small" />
                        ) : (
                          <ExpandIcon fontSize="small" />
                        )}
                      </IconButton>
                    </Box>
                  </Box>

                  {/* Expanded Details */}
                  <Collapse in={expandedApprovals.has(approval.id)}>
                    <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        <strong>Justification:</strong> {approval.justification}
                      </Typography>

                      {approval.review_notes && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                          <strong>Review Notes:</strong> {approval.review_notes}
                        </Typography>
                      )}

                      {approval.reviewed_by && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          Reviewed by: {approval.reviewed_by}
                          {approval.reviewed_at && ` · ${formatTimeAgo(approval.reviewed_at)}`}
                        </Typography>
                      )}

                      <Divider sx={{ my: 1.5 }} />

                      {/* Action Buttons */}
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {approval.status === 'pending' && (
                          <>
                            <Tooltip title="Approve this deployment request">
                              <Button
                                size="small"
                                variant="contained"
                                color="success"
                                startIcon={<ApproveIcon />}
                                onClick={() => openActionDialog('approve', approval)}
                              >
                                Approve
                              </Button>
                            </Tooltip>
                            <Tooltip title="Reject this deployment request">
                              <Button
                                size="small"
                                variant="contained"
                                color="error"
                                startIcon={<RejectIcon />}
                                onClick={() => openActionDialog('reject', approval)}
                              >
                                Reject
                              </Button>
                            </Tooltip>
                          </>
                        )}
                        {approval.status === 'approved' && (
                          <Tooltip title="Deploy this approved model">
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              startIcon={<DeployIcon />}
                              onClick={() => openActionDialog('deploy', approval)}
                            >
                              Deploy
                            </Button>
                          </Tooltip>
                        )}
                        {approval.status === 'deployed' && (
                          <Chip
                            icon={<DeployedIcon />}
                            label="Successfully Deployed"
                            color="success"
                            size="small"
                          />
                        )}
                        {approval.status === 'rejected' && (
                          <Chip
                            icon={<RejectIcon />}
                            label="Request Rejected"
                            color="error"
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Paper>

      {/* Action Confirmation Dialog */}
      <Dialog
        open={actionDialogOpen}
        onClose={closeActionDialog}
        aria-labelledby="action-dialog-title"
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle id="action-dialog-title">
          {actionType === 'approve' && 'Approve Deployment Request'}
          {actionType === 'reject' && 'Reject Deployment Request'}
          {actionType === 'deploy' && 'Deploy Model'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            {selectedApproval && (
              <>
                Model: <strong>{selectedApproval.model_name}</strong> ({selectedApproval.version})<br />
                Environment: <strong>{selectedApproval.target_environment}</strong>
              </>
            )}
          </DialogContentText>
          {actionType !== 'deploy' && (
            <TextField
              autoFocus
              margin="dense"
              label="Review Notes (optional)"
              fullWidth
              multiline
              rows={3}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder={actionType === 'approve'
                ? 'Add any notes about why this is approved...'
                : 'Please provide a reason for rejection...'}
            />
          )}
          {actionType === 'deploy' && (
            <MuiAlert severity="warning" sx={{ mt: 2 }}>
              This will deploy the model to <strong>{selectedApproval?.target_environment}</strong> environment
              and activate it for production use.
            </MuiAlert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={closeActionDialog} disabled={actionLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleActionConfirm}
            variant="contained"
            color={actionType === 'reject' ? 'error' : actionType === 'approve' ? 'success' : 'primary'}
            disabled={actionLoading}
            startIcon={actionLoading ? <CircularProgress size={16} /> : undefined}
          >
            {actionLoading
              ? 'Processing...'
              : actionType === 'approve'
                ? 'Approve'
                : actionType === 'reject'
                  ? 'Reject'
                  : 'Deploy'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      {snackbar.open && (
        <MuiAlert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1300,
          }}
        >
          {snackbar.message}
        </MuiAlert>
      )}
    </Box>
  );
};

export default ModelApprovalPanel;
