/**
 * Workflows Management Page
 *
 * Main page for managing workflow automations with visual builder.
 *
 * @module pages/developer/Workflows
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Chip,
  Divider,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  AccountTree as WorkflowsIcon,
  PlayArrow as ActiveIcon,
  Pause as PausedIcon,
  Drafts as DraftIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import WorkflowBuilder from '@/components/developer/WorkflowBuilder';
import { workflowsClient, type Workflow, type WorkflowStatistics } from '@/api/workflows';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`workflow-tabpanel-${index}`}
      aria-labelledby={`workflow-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Format date to readable string
 */
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Workflows Page Component
 *
 * Provides a comprehensive interface for managing workflow automations:
 * - View all workflow automations
 * - Create new workflows with visual builder
 * - Activate/pause/delete workflows
 * - View execution history
 * - Display usage statistics
 */
const Workflows: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [statistics, setStatistics] = useState<WorkflowStatistics | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [workflowsLoading, setWorkflowsLoading] = useState(true);
  const [workflowsError, setWorkflowsError] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const fetchStatistics = useCallback(async () => {
    setStatsLoading(true);
    setStatsError(null);

    try {
      const stats = await workflowsClient.getStatistics();
      setStatistics(stats);
    } catch (err) {
      setStatsError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const fetchWorkflows = useCallback(async () => {
    setWorkflowsLoading(true);
    setWorkflowsError(null);

    try {
      const data = await workflowsClient.listWorkflows();
      setWorkflows(data);
    } catch (err) {
      setWorkflowsError(err instanceof Error ? err.message : 'Failed to load workflows');
    } finally {
      setWorkflowsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
    fetchWorkflows();
  }, [fetchStatistics, fetchWorkflows, refreshTrigger]);

  const handleCreateWorkflow = useCallback(() => {
    setCreateDialogOpen(true);
  }, []);

  const handleCreateSuccess = useCallback(() => {
    setCreateDialogOpen(false);
    setRefreshTrigger((prev) => prev + 1);
    fetchStatistics();
    fetchWorkflows();
  }, [fetchStatistics, fetchWorkflows]);

  const handleDialogClose = useCallback(() => {
    setCreateDialogOpen(false);
  }, []);

  const handleEditWorkflow = useCallback((workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setEditDialogOpen(true);
  }, []);

  const handleEditSuccess = useCallback(() => {
    setEditDialogOpen(false);
    setSelectedWorkflow(null);
    setRefreshTrigger((prev) => prev + 1);
    fetchStatistics();
    fetchWorkflows();
  }, [fetchStatistics, fetchWorkflows]);

  const handleEditDialogClose = useCallback(() => {
    setEditDialogOpen(false);
    setSelectedWorkflow(null);
  }, []);

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  }, []);

  const handleActivate = useCallback(async (workflowId: string) => {
    try {
      await workflowsClient.activateWorkflow(workflowId);
      fetchWorkflows();
      fetchStatistics();
    } catch (err) {
      setWorkflowsError(err instanceof Error ? err.message : 'Failed to activate workflow');
    }
  }, [fetchWorkflows, fetchStatistics]);

  const handlePause = useCallback(async (workflowId: string) => {
    try {
      await workflowsClient.pauseWorkflow(workflowId);
      fetchWorkflows();
      fetchStatistics();
    } catch (err) {
      setWorkflowsError(err instanceof Error ? err.message : 'Failed to pause workflow');
    }
  }, [fetchWorkflows, fetchStatistics]);

  const handleDelete = useCallback(async (workflowId: string) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) {
      return;
    }

    try {
      await workflowsClient.deleteWorkflow(workflowId);
      fetchWorkflows();
      fetchStatistics();
    } catch (err) {
      setWorkflowsError(err instanceof Error ? err.message : 'Failed to delete workflow');
    }
  }, [fetchWorkflows, fetchStatistics]);

  const activeWorkflows = workflows.filter((w) => w.is_active);
  const pausedWorkflows = workflows.filter((w) => !w.is_active && w.status !== 'draft');
  const draftWorkflows = workflows.filter((w) => w.status === 'draft');

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Workflows
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Create and manage workflow automations with AI-powered agents
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateWorkflow}
          size="large"
        >
          Create Workflow
        </Button>
      </Stack>

      {/* Statistics Cards */}
      {!statsLoading && statistics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'primary.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <WorkflowsIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.total_workflows}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Workflows
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <ActiveIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.active_workflows}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Workflows
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <TrendingUpIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.successful_executions_today}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Successful Today
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'error.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <ErrorIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.failed_executions_today}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Failed Today
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Getting Started Section */}
      <Paper sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Getting Started with Workflows
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Automate your recruitment processes with AI-powered workflows. Build visual automations
          triggered by events, schedules, or manual execution.
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="Webhook Triggers" size="small" variant="outlined" />
          <Chip label="Scheduled Actions" size="small" variant="outlined" />
          <Chip label="No-Code Builder" size="small" variant="outlined" />
          <Chip label="Conditional Logic" size="small" variant="outlined" />
        </Box>
      </Paper>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Active (${activeWorkflows.length})`} />
          <Tab label={`Paused (${pausedWorkflows.length})`} />
          <Tab label={`Draft (${draftWorkflows.length})`} />
        </Tabs>
      </Box>

      {/* Active Workflows */}
      <TabPanel value={tabValue} index={0}>
        {workflowsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              Loading workflows...
            </Typography>
          </Box>
        ) : workflowsError ? (
          <Alert severity="error">{workflowsError}</Alert>
        ) : activeWorkflows.length === 0 ? (
          <Paper
            sx={{
              p: 6,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Active Workflows
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create your first workflow to start automating your recruitment processes
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={2}>
            {activeWorkflows.map((workflow) => (
              <Grid item xs={12} md={6} key={workflow.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderColor: 'success.main',
                    bgcolor: 'success.50',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleEditWorkflow(workflow)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600}>
                            {workflow.name}
                          </Typography>
                          <Chip
                            icon={<CheckCircleIcon fontSize="small" />}
                            label="Active"
                            color="success"
                            size="small"
                          />
                        </Box>
                        {workflow.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {workflow.description}
                          </Typography>
                        )}
                        <Chip label={workflow.trigger_type} size="small" variant="outlined" />
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Executions
                        </Typography>
                        <Typography variant="body2">{workflow.execution_count}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Success Rate
                        </Typography>
                        <Typography variant="body2" color="success.main">
                          {workflow.success_rate.toFixed(1)}%
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Last Run
                        </Typography>
                        <Typography variant="body2">{formatDate(workflow.last_executed_at)}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Paused Workflows */}
      <TabPanel value={tabValue} index={1}>
        {pausedWorkflows.length === 0 ? (
          <Paper
            sx={{
              p: 6,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" color="text.secondary">
              No Paused Workflows
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={2}>
            {pausedWorkflows.map((workflow) => (
              <Grid item xs={12} md={6} key={workflow.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    opacity: 0.8,
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600}>
                            {workflow.name}
                          </Typography>
                          <Chip label="Paused" size="small" variant="outlined" />
                        </Box>
                        {workflow.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {workflow.description}
                          </Typography>
                        )}
                        <Chip label={workflow.trigger_type} size="small" variant="outlined" />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Draft Workflows */}
      <TabPanel value={tabValue} index={2}>
        {draftWorkflows.length === 0 ? (
          <Paper
            sx={{
              p: 6,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" color="text.secondary">
              No Draft Workflows
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={2}>
            {draftWorkflows.map((workflow) => (
              <Grid item xs={12} md={6} key={workflow.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600}>
                            {workflow.name}
                          </Typography>
                          <Chip icon={<DraftIcon fontSize="small" />} label="Draft" size="small" />
                        </Box>
                        {workflow.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {workflow.description}
                          </Typography>
                        )}
                        <Chip label={workflow.trigger_type} size="small" variant="outlined" />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Create Workflow Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={handleDialogClose}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create Workflow</DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <WorkflowBuilder
            onSuccess={handleCreateSuccess}
            onCancel={handleDialogClose}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Workflow Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={handleEditDialogClose}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Edit Workflow</DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedWorkflow && (
            <WorkflowBuilder
              workflowId={selectedWorkflow.id}
              onSuccess={handleEditSuccess}
              onCancel={handleEditDialogClose}
            />
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default Workflows;
