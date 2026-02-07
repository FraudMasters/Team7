import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  CircularProgress,
  Chip,
  Alert,
  Collapse,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives/Icon';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import WorkflowKanban from '@components/WorkflowKanban';
import BulkCandidateActions from '@components/BulkCandidateActions';
import type { WorkflowStageResponse, CandidateListItem } from '../types/api';

interface Vacancy {
  id: string;
  title: string;
  location?: string;
}

interface StageStats {
  stageId: string;
  stageName: string;
  candidateCount: number;
}

interface StageTimeMetrics {
  average_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  candidate_count: number;
}

interface StageDropoffMetrics {
  candidates_entered: number;
  candidates_exited: number;
  candidates_current: number;
  dropoff_rate: number;
}

interface StageMetrics {
  stage_id: string | null;
  stage_name: string;
  display_name: string | null;
  time_metrics: StageTimeMetrics;
  dropoff_metrics: StageDropoffMetrics;
}

interface StageMetricsResponse {
  stage_id: string | null;
  metrics: StageMetrics[];
  total_stages: number;
}

interface BulkMoveResult {
  resume_id: string;
  success: boolean;
  error?: string;
  new_stage?: string;
}


/**
 * Workflow Board Page (Recruiter Module)
 *
 * Main kanban board for managing candidates through workflow stages.
 * Provides filtering by vacancy and displays stage statistics.
 */
const WorkflowBoardPage: React.FC = () => {
  const { t } = useTranslation();
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [selectedVacancy, setSelectedVacancy] = useState<string>('');
  const [allStages, setAllStages] = useState<WorkflowStageResponse[]>([]);
  const [stageStats, setStageStats] = useState<StageStats[]>([]);
  const [stageMetrics, setStageMetrics] = useState<StageMetrics[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [bulkMode, setBulkMode] = useState(false);
  const [allCandidates, setAllCandidates] = useState<CandidateListItem[]>([]);
  const [loadingBulkCandidates, setLoadingBulkCandidates] = useState(false);
  const [bulkMoveSuccess, setBulkMoveSuccess] = useState<string | null>(null);

  // Load vacancies on mount
  useEffect(() => {
    const fetchVacancies = async () => {
      try {
        const response = await axios.get<Vacancy[]>('/api/vacancies/?limit=100');
        setVacancies(response.data);
      } catch (error) {
        console.error('Error fetching vacancies:', error);
      }
    };
    fetchVacancies();
  }, []);

  /**
   * Fetch stage metrics (time in stage, drop-off rates)
   */
  const fetchStageMetrics = useCallback(async () => {
    try {
      setLoadingMetrics(true);
      const response = await axios.get<StageMetricsResponse>('/api/candidates/metrics');
      setStageMetrics(response.data.metrics);
    } catch (error) {
      console.error('Error fetching stage metrics:', error);
      setStageMetrics([]);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  // Load stages and stats on mount or vacancy change
  useEffect(() => {
    const fetchStagesAndStats = async () => {
      try {
        setLoading(true);

        // Fetch workflow stages
        const stagesResponse = await axios.get<WorkflowStageResponse[]>('/api/workflow-stages/');
        const stagesData = stagesResponse.data.sort((a, b) => a.stage_order - b.stage_order);
        setAllStages(stagesData);

        // Fetch candidates for each stage to build stats
        const statsPromises = stagesData.map(async (stage) => {
          try {
            const url = selectedVacancy
              ? `/api/candidates/?stage_id=${stage.id}&vacancy_id=${selectedVacancy}`
              : `/api/candidates/?stage_id=${stage.id}`;
            const response = await axios.get<CandidateListItem[]>(url);
            return {
              stageId: stage.id,
              stageName: stage.stage_name,
              candidateCount: response.data.length,
            };
          } catch (error) {
            console.error(`Error fetching stats for stage ${stage.id}:`, error);
            return {
              stageId: stage.id,
              stageName: stage.stage_name,
              candidateCount: 0,
            };
          }
        });

        const stats = await Promise.all(statsPromises);
        setStageStats(stats);

        // Fetch stage metrics
        await fetchStageMetrics();
      } catch (error) {
        console.error('Error fetching workflow data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStagesAndStats();
  }, [selectedVacancy, fetchStageMetrics]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // The WorkflowKanban component will refetch its data
    // We just need to refetch our stats
    try {
      const statsPromises = allStages.map(async (stage) => {
        try {
          const url = selectedVacancy
            ? `/api/candidates/?stage_id=${stage.id}&vacancy_id=${selectedVacancy}`
            : `/api/candidates/?stage_id=${stage.id}`;
          const response = await axios.get<CandidateListItem[]>(url);
          return {
            stageId: stage.id,
            stageName: stage.stage_name,
            candidateCount: response.data.length,
          };
        } catch (error) {
          return {
            stageId: stage.id,
            stageName: stage.stage_name,
            candidateCount: 0,
          };
        }
      });

      const stats = await Promise.all(statsPromises);
      setStageStats(stats);

      // Refresh metrics
      await fetchStageMetrics();
    } catch (error) {
      console.error('Error refreshing stats:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const totalCandidates = stageStats.reduce((sum, stat) => sum + stat.candidateCount, 0);

  /**
   * Fetch all candidates for bulk operations
   */
  const fetchAllCandidates = useCallback(async () => {
    if (allStages.length === 0) return;

    setLoadingBulkCandidates(true);
    try {
      const candidatesPromises = allStages.map(async (stage) => {
        const url = selectedVacancy
          ? `/api/candidates/?stage_id=${stage.id}&vacancy_id=${selectedVacancy}`
          : `/api/candidates/?stage_id=${stage.id}`;
        const response = await axios.get<CandidateListItem[]>(url);
        return response.data;
      });

      const candidatesArrays = await Promise.all(candidatesPromises);
      const allCandidatesData = candidatesArrays.flat();

      setAllCandidates(allCandidatesData);
    } catch (error) {
      console.error('Error fetching candidates for bulk mode:', error);
    } finally {
      setLoadingBulkCandidates(false);
    }
  }, [allStages, selectedVacancy]);

  /**
   * Toggle bulk selection mode
   */
  const handleToggleBulkMode = useCallback(() => {
    const newMode = !bulkMode;
    setBulkMode(newMode);

    if (newMode) {
      fetchAllCandidates();
    } else {
      setAllCandidates([]);
      setBulkMoveSuccess(null);
    }
  }, [bulkMode, fetchAllCandidates]);

  /**
   * Handle bulk move completion
   */
  const handleBulkMoveComplete = useCallback((results: BulkMoveResult[]) => {
    const successCount = results.filter((r) => r.success).length;

    if (successCount > 0) {
      setBulkMoveSuccess(
        t('bulkActions.moveSuccess', {
          count: successCount,
          plural: successCount === 1 ? '' : 's',
        })
      );

      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setBulkMoveSuccess(null);
      }, 5000);

      // Refresh data to reflect changes
      handleRefresh();
    }
  }, [t]);

  if (loading) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
          <CircularProgress />
          <Typography variant="body2" sx={{ ml: 2 }}>{t('workflow.loading')}</Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, sm: 3, md: 4 } }}>
      {/* Header */}
      <Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          fontWeight={600}
          sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.25rem' } }}
        >
          {t('workflow.board.title')}
        </Typography>
        <Typography variant="body1" color="secondary" sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
          {t('workflow.board.subtitle')}
        </Typography>
      </Box>

      {/* Statistics Summary */}
      <Grid container spacing={2} sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
        <Grid item xs={6} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="users" size={24} sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' } }}>
                  {t('workflow.board.stats.totalCandidates')}
                </Typography>
              </Box>
              <Typography variant="h4" color="primary" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
                {totalCandidates}
              </Typography>
              <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                {t('workflow.board.stats.allStages')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="trello" size={24} sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6" sx={{ fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' } }}>
                  {t('workflow.board.stats.activeStages')}
                </Typography>
              </Box>
              <Typography variant="h4" color="success.main" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
                {allStages.length}
              </Typography>
              <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                {t('workflow.board.stats.configuredStages')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="briefcase" size={24} sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6" sx={{ fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' } }}>
                  {t('workflow.board.stats.openVacancies')}
                </Typography>
              </Box>
              <Typography variant="h4" color="info.main" sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
                {vacancies.length}
              </Typography>
              <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                {t('workflow.board.stats.activeVacancies')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3, md: 4 } }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={6}>
            <TextField
              fullWidth
              select
              label={t('workflow.board.filterByVacancy')}
              value={selectedVacancy}
              onChange={(e) => setSelectedVacancy(e.target.value)}
              SelectProps={{ native: true }}
              helperText={t('workflow.board.vacancyHelper')}
            >
              <option value="">{t('workflow.board.allVacancies')}</option>
              {vacancies.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.title} {v.location ? `(${v.location})` : ''}
                </option>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={6}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                startIcon={refreshing ? <CircularProgress size={16} /> : <Icon name="refresh-cw" size={20} />}
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? t('workflow.board.refreshing') : t('workflow.board.refresh')}
              </Button>
              <Button
                variant={bulkMode ? 'contained' : 'outlined'}
                startIcon={bulkMode ? <Icon name="check-circle" size={20} /> : <Icon name="circle" size={20} />}
                onClick={handleToggleBulkMode}
                color={bulkMode ? 'primary' : 'secondary'}
              >
                {bulkMode ? t('bulkActions.exitBulkMode') : t('bulkActions.enterBulkMode')}
              </Button>
              {selectedVacancy && (
                <Chip
                  icon={<Icon name="filter" size={16} />}
                  label={t('workflow.board.filteredByVacancy')}
                  onDelete={() => setSelectedVacancy('')}
                  color="primary"
                  variant="outlined"
                />
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Bulk Move Success Alert */}
      <Collapse in={!!bulkMoveSuccess}>
        <Alert severity="success" sx={{ mb: { xs: 2, sm: 3, md: 4 } }} onClose={() => setBulkMoveSuccess(null)}>
          <Typography variant="body2">{bulkMoveSuccess}</Typography>
        </Alert>
      </Collapse>

      {/* Stage Statistics */}
      {stageStats.length > 0 && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3, md: 4 } }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 2, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
            {t('workflow.board.stageStats')}
          </Typography>
          <Grid container spacing={1}>
            {stageStats.map((stat) => (
              <Grid item xs={4} sm={3} md={2} lg={2} key={stat.stageId}>
                <Card
                  sx={{
                    textAlign: 'center',
                    bgcolor: stat.candidateCount > 0 ? 'primary.50' : 'grey.50',
                    border: 1,
                    borderColor: stat.candidateCount > 0 ? 'primary.main' : 'grey.300',
                  }}
                >
                  <CardContent sx={{ py: { xs: 1, sm: 1.5 }, px: { xs: 0.5, sm: 1 } }}>
                    <Typography variant="h5" color="primary" fontWeight={700} sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }}>
                      {stat.candidateCount}
                    </Typography>
                    <Typography variant="caption" color="secondary" noWrap sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                      {stat.stageName}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Stage Metrics */}
      {!loadingMetrics && stageMetrics.length > 0 && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3, md: 4 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              {t('workflow.board.stageMetrics')}
            </Typography>
            <Tooltip title={t('workflow.board.metricsTooltip')}>
              <Icon name="clock" size={20} sx={{ color: 'action' }} />
            </Tooltip>
          </Box>
          <Grid container spacing={{ xs: 1, sm: 2 }}>
            {stageMetrics.map((metric) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={metric.stage_name}>
                <Card
                  sx={{
                    height: '100%',
                    border: 1,
                    borderColor: 'divider',
                    '&:hover': {
                      borderColor: 'primary.main',
                      boxShadow: 2,
                    },
                    transition: 'all 0.2s ease-in-out',
                  }}
                >
                  <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                    {/* Stage Name */}
                    <Typography variant="subtitle2" color="primary" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                      {metric.display_name || metric.stage_name}
                    </Typography>

                    {/* Time in Stage */}
                    <Box sx={{ mb: { xs: 1, sm: 1.5 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Icon name="clock" size={16} sx={{ mr: 0.5, color: 'secondary' }} />
                        <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                          {t('workflow.board.timeInStage')}
                        </Typography>
                      </Box>
                      <Box sx={{ ml: 2 }}>
                        <Typography variant="body2" fontWeight={500} sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                          {metric.time_metrics.average_days.toFixed(1)} {t('workflow.board.daysAvg')}
                        </Typography>
                        <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                          {t('workflow.board.median')}: {metric.time_metrics.median_days.toFixed(1)} {t('workflow.board.days')} •
                          {t('workflow.board.range')}: {metric.time_metrics.min_days.toFixed(1)}-{metric.time_metrics.max_days.toFixed(1)}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Drop-off Rate */}
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Icon name="trending-down" size={16} sx={{ mr: 0.5, color: 'secondary' }} />
                        <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                          {t('workflow.board.dropoffRate')}
                        </Typography>
                      </Box>
                      <Box sx={{ ml: 2 }}>
                        <Typography
                          variant="body2"
                          fontWeight={500}
                          color={metric.dropoff_metrics.dropoff_rate > 0.3 ? 'error.main' : 'success.main'}
                          sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                        >
                          {(metric.dropoff_metrics.dropoff_rate * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="secondary" sx={{ fontSize: { xs: '0.6rem', sm: '0.75rem' } }}>
                          {metric.dropoff_metrics.candidates_exited} / {metric.dropoff_metrics.candidates_entered} {t('workflow.board.exited')}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Bulk Actions Panel */}
      {bulkMode && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 2, sm: 3, md: 4 } }}>
          {loadingBulkCandidates ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2 }}>
                {t('bulkActions.loadingCandidates')}
              </Typography>
            </Box>
          ) : (
            <BulkCandidateActions
              candidates={allCandidates.map((c) => ({
                resume_id: c.id,
                name: c.filename,
                current_stage: c.stage_name,
                match_percentage: undefined,
              }))}
              stages={allStages}
              onBulkMoveComplete={handleBulkMoveComplete}
              vacancyId={selectedVacancy || undefined}
              containerHeight={500}
            />
          )}
        </Paper>
      )}

      {/* Kanban Board */}
      <Paper sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
        <WorkflowKanban />
      </Paper>

      {/* Info Box */}
      <Box sx={{ mt: { xs: 2, sm: 3, md: 4 } }}>
        <Typography variant="body2" color="secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          <strong>💡 {t('workflow.board.tip')}</strong>
        </Typography>
      </Box>
    </Container>
  );
};

export default WorkflowBoardPage;
