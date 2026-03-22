import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  CardActions,
  LinearProgress,
} from '@mui/material';
import {
  Science as ScienceIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

/**
 * A/B Test interface
 */
interface ABTest {
  id: string;
  name: string;
  description: string;
  variant_a_profile_id: string;
  variant_b_profile_id: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  traffic_allocation: number;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Weight Profile interface
 */
interface WeightProfile {
  id: string;
  name: string;
  description: string;
  is_preset: boolean;
  is_active: boolean;
}

/**
 * Create A/B Test form data
 */
interface CreateTestFormData {
  name: string;
  description: string;
  variant_a_profile_id: string;
  variant_b_profile_id: string;
  traffic_allocation: number;
}

/**
 * ABTestingDashboard Component
 *
 * Admin dashboard for managing A/B tests of different matching weight configurations.
 * Features:
 * - Create new A/B tests comparing two weight profiles
 * - View list of active and completed tests
 * - Start/stop/pause tests
 * - View test results and statistics
 *
 * @example
 * ```tsx
 * <ABTestingDashboard />
 * ```
 */
const ABTestingDashboard: React.FC = () => {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [profiles, setProfiles] = useState<WeightProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [formData, setFormData] = useState<CreateTestFormData>({
    name: '',
    description: '',
    variant_a_profile_id: '',
    variant_b_profile_id: '',
    traffic_allocation: 50,
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof CreateTestFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  /**
   * Fetch A/B tests from API
   */
  const fetchTests = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/ab-testing/');
      if (!response.ok) {
        throw new Error('Failed to fetch A/B tests');
      }
      const data = await response.json();
      setTests(data.tests || []);
    } catch (error) {
      console.error('Error fetching A/B tests:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load A/B tests',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch weight profiles from API
   */
  const fetchProfiles = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/matching-weights/');
      if (!response.ok) {
        throw new Error('Failed to fetch weight profiles');
      }
      const data = await response.json();
      setProfiles(data.profiles || []);
    } catch (error) {
      console.error('Error fetching weight profiles:', error);
    }
  }, []);

  /**
   * Load data on component mount
   */
  useEffect(() => {
    fetchTests();
    fetchProfiles();
  }, [fetchTests, fetchProfiles]);

  /**
   * Open create dialog
   */
  const handleOpenCreateDialog = () => {
    setCreateDialogOpen(true);
    setFormData({
      name: '',
      description: '',
      variant_a_profile_id: '',
      variant_b_profile_id: '',
      traffic_allocation: 50,
    });
    setFormErrors({});
  };

  /**
   * Close create dialog
   */
  const handleCloseCreateDialog = () => {
    setCreateDialogOpen(false);
    setFormData({
      name: '',
      description: '',
      variant_a_profile_id: '',
      variant_b_profile_id: '',
      traffic_allocation: 50,
    });
    setFormErrors({});
  };

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof CreateTestFormData, string>> = {};

    if (!formData.name.trim()) {
      errors.name = 'Test name is required';
    }

    if (!formData.variant_a_profile_id) {
      errors.variant_a_profile_id = 'Variant A profile is required';
    }

    if (!formData.variant_b_profile_id) {
      errors.variant_b_profile_id = 'Variant B profile is required';
    }

    if (formData.variant_a_profile_id === formData.variant_b_profile_id) {
      errors.variant_b_profile_id = 'Variant B must be different from Variant A';
    }

    if (formData.traffic_allocation < 0 || formData.traffic_allocation > 100) {
      errors.traffic_allocation = 'Traffic allocation must be between 0 and 100';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form field change
   */
  const handleFieldChange = (field: keyof CreateTestFormData, value: string | number) => {
    setFormData({
      ...formData,
      [field]: value,
    });
    // Clear error for this field
    if (formErrors[field]) {
      setFormErrors({
        ...formErrors,
        [field]: undefined,
      });
    }
  };

  /**
   * Create new A/B test
   */
  const handleCreateTest = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSubmitting(true);
      const response = await fetch('http://localhost:8000/api/ab-testing/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create A/B test');
      }

      const newTest = await response.json();

      setSnackbar({
        open: true,
        message: `A/B test "${newTest.name}" created successfully`,
        severity: 'success',
      });

      handleCloseCreateDialog();
      await fetchTests();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create A/B test';
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Update test status
   */
  const handleUpdateTestStatus = async (testId: string, status: 'active' | 'paused' | 'completed') => {
    try {
      const response = await fetch(`http://localhost:8000/api/ab-testing/${testId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error('Failed to update test status');
      }

      setSnackbar({
        open: true,
        message: `Test status updated to ${status}`,
        severity: 'success',
      });

      await fetchTests();
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to update test status',
        severity: 'error',
      });
    }
  };

  /**
   * Get status chip configuration
   */
  const getStatusChip = (status: ABTest['status']) => {
    const configs: Record<ABTest['status'], { label: string; color: 'default' | 'success' | 'warning' | 'info' | 'primary'; icon: React.ReactNode }> = {
      draft: {
        label: 'Draft',
        color: 'default',
        icon: <PendingIcon fontSize="small" />,
      },
      active: {
        label: 'Active',
        color: 'success',
        icon: <PlayArrowIcon fontSize="small" />,
      },
      paused: {
        label: 'Paused',
        color: 'warning',
        icon: <StopIcon fontSize="small" />,
      },
      completed: {
        label: 'Completed',
        color: 'info',
        icon: <CheckCircleIcon fontSize="small" />,
      },
    };

    const config = configs[status];
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        icon={config.icon}
      />
    );
  };

  /**
   * Get profile name by ID
   */
  const getProfileName = (profileId: string): string => {
    const profile = profiles.find(p => p.id === profileId);
    return profile?.name || profileId;
  };

  /**
   * Close snackbar
   */
  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  /**
   * Calculate statistics for summary cards
   */
  const stats = {
    total: tests.length,
    active: tests.filter(t => t.status === 'active').length,
    completed: tests.filter(t => t.status === 'completed').length,
    draft: tests.filter(t => t.status === 'draft').length,
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} className="ab-testing-dashboard">
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ScienceIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" component="h1" fontWeight={700}>
                A/B Testing Dashboard
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5 }}>
                Compare different matching weight configurations to optimize hiring outcomes
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchTests}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenCreateDialog}
            >
              Create A/B Test
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Summary Statistics */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Total Tests
              </Typography>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Active Tests
              </Typography>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {stats.active}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Completed Tests
              </Typography>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {stats.completed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Draft Tests
              </Typography>
              <Typography variant="h4" fontWeight={700} color="text.secondary">
                {stats.draft}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tests Table */}
      <Paper elevation={2} sx={{ p: 0 }}>
        <Box sx={{ p: 3, pb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            A/B Tests
          </Typography>
        </Box>

        {loading ? (
          <Box sx={{ p: 8, textAlign: 'center' }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              Loading A/B tests...
            </Typography>
          </Box>
        ) : tests.length === 0 ? (
          <Box sx={{ p: 8, textAlign: 'center' }}>
            <ScienceIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No A/B Tests Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Create your first A/B test to compare different matching weight configurations
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenCreateDialog}
            >
              Create First Test
            </Button>
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Test Name</TableCell>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Variant A</TableCell>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Variant B</TableCell>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Traffic Split</TableCell>
                  <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Created</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tests.map((test) => (
                  <TableRow
                    key={test.id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      '&:hover': { bgcolor: 'action.selected' },
                    }}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {test.name}
                      </Typography>
                      {test.description && (
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                          {test.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{getStatusChip(test.status)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {getProfileName(test.variant_a_profile_id)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {getProfileName(test.variant_b_profile_id)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={test.traffic_allocation}
                          sx={{
                            width: 60,
                            height: 6,
                            borderRadius: 3,
                            bgcolor: 'grey.200',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: 'primary.main',
                            },
                          }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {test.traffic_allocation}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(test.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                        {test.status === 'draft' && (
                          <Tooltip title="Start test">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleUpdateTestStatus(test.id, 'active')}
                            >
                              <PlayArrowIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {test.status === 'active' && (
                          <>
                            <Tooltip title="Pause test">
                              <IconButton
                                size="small"
                                color="warning"
                                onClick={() => handleUpdateTestStatus(test.id, 'paused')}
                              >
                                <StopIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Complete test">
                              <IconButton
                                size="small"
                                color="info"
                                onClick={() => handleUpdateTestStatus(test.id, 'completed')}
                              >
                                <CheckCircleIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                        {test.status === 'paused' && (
                          <Tooltip title="Resume test">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleUpdateTestStatus(test.id, 'active')}
                            >
                              <PlayArrowIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {(test.status === 'active' || test.status === 'completed') && (
                          <Tooltip title="View results">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => {
                                // Navigate to test results page
                                window.location.href = `/admin/ab-testing/${test.id}/results`;
                              }}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Create Test Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={handleCloseCreateDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScienceIcon />
            <Typography variant="h6" fontWeight={600}>
              Create New A/B Test
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Test Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              error={!!formErrors.name}
              helperText={formErrors.name}
              placeholder="e.g., Technical vs Balanced Weights"
            />

            <TextField
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={(e) => handleFieldChange('description', e.target.value)}
              placeholder="Brief description of what you're testing..."
            />

            <FormControl fullWidth required error={!!formErrors.variant_a_profile_id}>
              <InputLabel>Variant A (Control)</InputLabel>
              <Select
                value={formData.variant_a_profile_id}
                label="Variant A (Control)"
                onChange={(e) => handleFieldChange('variant_a_profile_id', e.target.value)}
              >
                {profiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{profile.name}</span>
                      {profile.is_preset && (
                        <Chip label="Preset" size="small" variant="outlined" />
                      )}
                      {profile.is_active && (
                        <Chip label="Active" size="small" color="success" variant="outlined" />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
              {formErrors.variant_a_profile_id && (
                <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.5 }}>
                  {formErrors.variant_a_profile_id}
                </Typography>
              )}
            </FormControl>

            <FormControl fullWidth required error={!!formErrors.variant_b_profile_id}>
              <InputLabel>Variant B (Treatment)</InputLabel>
              <Select
                value={formData.variant_b_profile_id}
                label="Variant B (Treatment)"
                onChange={(e) => handleFieldChange('variant_b_profile_id', e.target.value)}
              >
                {profiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{profile.name}</span>
                      {profile.is_preset && (
                        <Chip label="Preset" size="small" variant="outlined" />
                      )}
                      {profile.is_active && (
                        <Chip label="Active" size="small" color="success" variant="outlined" />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
              {formErrors.variant_b_profile_id && (
                <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.5 }}>
                  {formErrors.variant_b_profile_id}
                </Typography>
              )}
            </FormControl>

            <TextField
              label="Traffic Allocation (%)"
              type="number"
              fullWidth
              required
              value={formData.traffic_allocation}
              onChange={(e) => handleFieldChange('traffic_allocation', Number(e.target.value))}
              error={!!formErrors.traffic_allocation}
              helperText={formErrors.traffic_allocation || 'Percentage of traffic to allocate to variant B (0-100)'}
              inputProps={{ min: 0, max: 100 }}
            />

            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                This test will compare the performance of two different matching weight configurations.
                Results will be available once enough data has been collected.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2.5, pt: 1.5 }}>
          <Button onClick={handleCloseCreateDialog} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateTest}
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <AddIcon />}
          >
            {submitting ? 'Creating...' : 'Create Test'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ABTestingDashboard;
