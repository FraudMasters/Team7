/**
 * A/B Testing Dashboard Page
 *
 * Admin interface for managing A/B tests comparing different
 * matching algorithm weight configurations.
 */
import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Science as ScienceIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as NeutralIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api';

/**
 * A/B Test status enum
 */
type ABTestStatus = 'draft' | 'running' | 'completed' | 'paused';

/**
 * A/B Test interface
 */
interface ABTest {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  variant_a_profile_id: string;
  variant_b_profile_id: string;
  status: ABTestStatus;
  start_date?: string;
  end_date?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Weight profile interface
 */
interface WeightProfile {
  id: string;
  name: string;
  description?: string;
}

/**
 * Test statistics interface
 */
interface TestStatistics {
  test_id: string;
  variant_a: {
    count: number;
    avg_score: number;
    hire_rate: number;
    conversion_rate: number;
  };
  variant_b: {
    count: number;
    avg_score: number;
    hire_rate: number;
    conversion_rate: number;
  };
  winner?: 'a' | 'b' | 'tie';
  confidence: number;
  statistical_significance: boolean;
}

/**
 * Tab panel props
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Status chip color mapping
 */
const getStatusColor = (status: ABTestStatus): 'default' | 'primary' | 'success' | 'warning' | 'error' => {
  const colors: Record<ABTestStatus, 'default' | 'primary' | 'success' | 'warning' | 'error'> = {
    draft: 'default',
    running: 'primary',
    completed: 'success',
    paused: 'warning',
  };
  return colors[status] || 'default';
};

/**
 * Status label mapping
 */
const getStatusLabel = (status: ABTestStatus, t: (key: string) => string): string => {
  const labels: Record<ABTestStatus, string> = {
    draft: t('abTesting.status.draft', 'Draft'),
    running: t('abTesting.status.running', 'Running'),
    completed: t('abTesting.status.completed', 'Completed'),
    paused: t('abTesting.status.paused', 'Paused'),
  };
  return labels[status] || status;
};

/**
 * A/B Testing Dashboard Page Component
 */
export function ABTestingPage() {
  const { t } = useTranslation();
  const [tests, setTests] = useState<ABTest[]>([]);
  const [profiles, setProfiles] = useState<WeightProfile[]>([]);
  const [statistics, setStatistics] = useState<Record<string, TestStatistics>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  // Dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newTest, setNewTest] = useState({
    name: '',
    description: '',
    variant_a_profile_id: '',
    variant_b_profile_id: '',
  });

  /**
   * Fetch A/B tests from API
   */
  const fetchTests = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.getAxiosInstance().get('/api/ab-testing/', {
        params: { organization_id: 'default' },
      });
      setTests(response.data.tests || []);
    } catch (err) {
      setError(t('abTesting.error.fetch', 'Failed to load A/B tests'));
      console.error('Failed to fetch A/B tests:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch weight profiles from API
   */
  const fetchProfiles = async () => {
    try {
      const response = await apiClient.getAxiosInstance().get('/api/matching-weights/profiles');
      setProfiles(response.data.profiles || []);
    } catch (err) {
      console.error('Failed to fetch weight profiles:', err);
    }
  };

  /**
   * Fetch test statistics
   */
  const fetchStatistics = async (testId: string) => {
    try {
      const response = await apiClient.getAxiosInstance().get(`/api/ab-testing/${testId}/statistics`);
      setStatistics(prev => ({ ...prev, [testId]: response.data }));
    } catch (err) {
      console.error(`Failed to fetch statistics for test ${testId}:`, err);
    }
  };

  useEffect(() => {
    fetchTests();
    fetchProfiles();
  }, []);

  // Fetch statistics for running/completed tests
  useEffect(() => {
    tests
      .filter(test => test.status === 'running' || test.status === 'completed')
      .forEach(test => fetchStatistics(test.id));
  }, [tests]);

  /**
   * Create new A/B test
   */
  const handleCreateTest = async () => {
    try {
      await apiClient.getAxiosInstance().post('/api/ab-testing/', {
        organization_id: 'default',
        ...newTest,
      });
      setCreateDialogOpen(false);
      setNewTest({ name: '', description: '', variant_a_profile_id: '', variant_b_profile_id: '' });
      fetchTests();
    } catch (err) {
      setError(t('abTesting.error.create', 'Failed to create A/B test'));
    }
  };

  /**
   * Update test status
   */
  const handleStatusChange = async (testId: string, newStatus: ABTestStatus) => {
    try {
      await apiClient.patch(`/api/ab-testing/${testId}`, { status: newStatus });
      fetchTests();
    } catch (err) {
      setError(t('abTesting.error.update', 'Failed to update test status'));
    }
  };

  /**
   * Render winner indicator
   */
  const renderWinner = (stats?: TestStatistics) => {
    if (!stats) return null;

    if (stats.winner === 'a') {
      return (
        <Tooltip title={`Variant A leads with ${stats.confidence.toFixed(1)}% confidence`}>
          <TrendingUpIcon color="success" />
        </Tooltip>
      );
    } else if (stats.winner === 'b') {
      return (
        <Tooltip title={`Variant B leads with ${stats.confidence.toFixed(1)}% confidence`}>
          <TrendingUpIcon color="primary" />
        </Tooltip>
      );
    } else {
      return (
        <Tooltip title="No clear winner yet">
          <NeutralIcon color="disabled" />
        </Tooltip>
      );
    }
  };

  const runningTests = tests.filter(t => t.status === 'running');
  const completedTests = tests.filter(t => t.status === 'completed');
  const draftTests = tests.filter(t => t.status === 'draft' || t.status === 'paused');

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            {t('abTesting.title', 'A/B Testing Dashboard')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('abTesting.subtitle', 'Compare different weight configurations to optimize hiring outcomes')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchTests}>
            {t('common.refresh', 'Refresh')}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            disabled={profiles.length < 2}
          >
            {t('abTesting.createTest', 'Create Test')}
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                {t('abTesting.totalTests', 'Total Tests')}
              </Typography>
              <Typography variant="h4" fontWeight={600}>
                {tests.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                {t('abTesting.runningTests', 'Running')
              </Typography>
              <Typography variant="h4" fontWeight={600} color="primary">
                {runningTests.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                {t('abTesting.completedTests', 'Completed')}
              </Typography>
              <Typography variant="h4" fontWeight={600} color="success.main">
                {completedTests.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2" gutterBottom>
                {t('abTesting.profilesAvailable', 'Profiles Available')}
              </Typography>
              <Typography variant="h4" fontWeight={600}>
                {profiles.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={t('abTesting.tabs.all', 'All Tests')} />
          <Tab label={t('abTesting.tabs.running', 'Running')} />
          <Tab label={t('abTesting.tabs.completed', 'Completed')} />
        </Tabs>

        {/* Loading State */}
        {loading && <LinearProgress />}

        {/* All Tests Tab */}
        <TabPanel value={tabValue} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('abTesting.table.name', 'Name')}</TableCell>
                  <TableCell>{t('abTesting.table.status', 'Status')}</TableCell>
                  <TableCell>{t('abTesting.table.variantA', 'Variant A')}</TableCell>
                  <TableCell>{t('abTesting.table.variantB', 'Variant B')}</TableCell>
                  <TableCell>{t('abTesting.table.winner', 'Winner')}</TableCell>
                  <TableCell>{t('abTesting.table.actions', 'Actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tests.length === 0 && !loading && (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" sx={{ py: 4 }}>
                        {t('abTesting.noTests', 'No A/B tests yet. Create your first test to start optimizing.')}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {tests.map((test) => (
                  <TableRow key={test.id} hover>
                    <TableCell>
                      <Typography fontWeight={500}>{test.name}</Typography>
                      {test.description && (
                        <Typography variant="caption" color="text.secondary">
                          {test.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(test.status, t)}
                        color={getStatusColor(test.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {profiles.find(p => p.id === test.variant_a_profile_id)?.name || test.variant_a_profile_id}
                    </TableCell>
                    <TableCell>
                      {profiles.find(p => p.id === test.variant_b_profile_id)?.name || test.variant_b_profile_id}
                    </TableCell>
                    <TableCell>{renderWinner(statistics[test.id])}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {test.status === 'draft' && (
                          <Tooltip title={t('abTesting.actions.start', 'Start')}>
                            <IconButton size="small" color="primary" onClick={() => handleStatusChange(test.id, 'running')}>
                              <PlayIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {test.status === 'running' && (
                          <>
                            <Tooltip title={t('abTesting.actions.pause', 'Pause')}>
                              <IconButton size="small" color="warning" onClick={() => handleStatusChange(test.id, 'paused')}>
                                <PauseIcon />
                            </IconButton>
                            </Tooltip>
                            <Tooltip title={t('abTesting.actions.stop', 'Complete')}>
                              <IconButton size="small" color="error" onClick={() => handleStatusChange(test.id, 'completed')}>
                                <StopIcon />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                        {test.status === 'paused' && (
                          <Tooltip title={t('abTesting.actions.resume', 'Resume')}>
                            <IconButton size="small" color="primary" onClick={() => handleStatusChange(test.id, 'running')}>
                              <PlayIcon />
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
        </TabPanel>

        {/* Running Tests Tab */}
        <TabPanel value={tabValue} index={1}>
          {runningTests.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              {t('abTesting.noRunningTests', 'No tests currently running.')}
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {runningTests.map(test => (
                <Grid item xs={12} md={6} key={test.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">{test.name}</Typography>
                        <Chip label={t('abTesting.status.running', 'Running')} color="primary" size="small" />
                      </Box>
                      {statistics[test.id] && (
                        <Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {t('abTesting.variantAResults', 'Variant A')}: {statistics[test.id].variant_a.count} samples
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {t('abTesting.variantBResults', 'Variant B')}: {statistics[test.id].variant_b.count} samples
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={statistics[test.id].confidence}
                            sx={{ mt: 1 }}
                          />
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>

        {/* Completed Tests Tab */}
        <TabPanel value={tabValue} index={2}>
          {completedTests.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              {t('abTesting.noCompletedTests', 'No completed tests yet.')}
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {completedTests.map(test => (
                <Grid item xs={12} md={6} key={test.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h6">{test.name}</Typography>
                        {renderWinner(statistics[test.id])}
                      </Box>
                      {statistics[test.id] && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2">
                            {t('abTesting.winner', 'Winner')}: {statistics[test.id].winner?.toUpperCase() || 'Tie'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {t('abTesting.confidence', 'Confidence')}: {statistics[test.id].confidence.toFixed(1)}%
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>
      </Paper>

      {/* Create Test Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('abTesting.createDialog.title', 'Create A/B Test')}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label={t('abTesting.createDialog.name', 'Test Name')}
              value={newTest.name}
              onChange={(e) => setNewTest({ ...newTest, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label={t('abTesting.createDialog.description', 'Description')}
              value={newTest.description}
              onChange={(e) => setNewTest({ ...newTest, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth required>
              <InputLabel>{t('abTesting.createDialog.variantA', 'Variant A (Profile)')}</InputLabel>
              <Select
                value={newTest.variant_a_profile_id}
                onChange={(e) => setNewTest({ ...newTest, variant_a_profile_id: e.target.value })}
                label={t('abTesting.createDialog.variantA', 'Variant A (Profile)')}
              >
                {profiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    {profile.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth required>
              <InputLabel>{t('abTesting.createDialog.variantB', 'Variant B (Profile)')}</InputLabel>
              <Select
                value={newTest.variant_b_profile_id}
                onChange={(e) => setNewTest({ ...newTest, variant_b_profile_id: e.target.value })}
                label={t('abTesting.createDialog.variantB', 'Variant B (Profile)')}
              >
                {profiles.filter(p => p.id !== newTest.variant_a_profile_id).map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    {profile.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('common.cancel', 'Cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleCreateTest}
            disabled={!newTest.name || !newTest.variant_a_profile_id || !newTest.variant_b_profile_id}
          >
            {t('abTesting.createDialog.create', 'Create Test')}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default ABTestingPage;
