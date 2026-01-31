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
} from '@mui/material';
import {
  ViewKanban as ViewKanbanIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Work as WorkIcon,
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
} from '@mui/icons-material';
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
      } catch (error) {
        console.error('Error fetching workflow data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStagesAndStats();
  }, [selectedVacancy]);

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
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('workflow.board.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('workflow.board.subtitle')}
        </Typography>
      </Box>

      {/* Statistics Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">{t('workflow.board.stats.totalCandidates')}</Typography>
              </Box>
              <Typography variant="h4" color="primary">{totalCandidates}</Typography>
              <Typography variant="caption" color="text.secondary">
                {t('workflow.board.stats.allStages')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ViewKanbanIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">{t('workflow.board.stats.activeStages')}</Typography>
              </Box>
              <Typography variant="h4" color="success.main">{allStages.length}</Typography>
              <Typography variant="caption" color="text.secondary">
                {t('workflow.board.stats.configuredStages')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WorkIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">{t('workflow.board.stats.openVacancies')}</Typography>
              </Box>
              <Typography variant="h4" color="info.main">{vacancies.length}</Typography>
              <Typography variant="caption" color="text.secondary">
                {t('workflow.board.stats.activeVacancies')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
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
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
                onClick={handleRefresh}
                disabled={refreshing}
                sx={{ minWidth: 120 }}
              >
                {refreshing ? t('workflow.board.refreshing') : t('workflow.board.refresh')}
              </Button>
              <Button
                variant={bulkMode ? 'contained' : 'outlined'}
                startIcon={bulkMode ? <CheckCircleIcon /> : <RadioButtonUncheckedIcon />}
                onClick={handleToggleBulkMode}
                color={bulkMode ? 'primary' : 'secondary'}
                sx={{ minWidth: 120 }}
              >
                {bulkMode ? t('bulkActions.exitBulkMode') : t('bulkActions.enterBulkMode')}
              </Button>
              {selectedVacancy && (
                <Chip
                  icon={<FilterIcon />}
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
        <Alert severity="success" sx={{ mb: 4 }} onClose={() => setBulkMoveSuccess(null)}>
          <Typography variant="body2">{bulkMoveSuccess}</Typography>
        </Alert>
      </Collapse>

      {/* Stage Statistics */}
      {stageStats.length > 0 && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            {t('workflow.board.stageStats')}
          </Typography>
          <Grid container spacing={2}>
            {stageStats.map((stat) => (
              <Grid item xs={6} sm={4} md={3} lg={2} key={stat.stageId}>
                <Card
                  sx={{
                    textAlign: 'center',
                    bgcolor: stat.candidateCount > 0 ? 'primary.50' : 'grey.50',
                    border: 1,
                    borderColor: stat.candidateCount > 0 ? 'primary.main' : 'grey.300',
                  }}
                >
                  <CardContent sx={{ py: 1.5 }}>
                    <Typography variant="h4" color="primary" fontWeight={700}>
                      {stat.candidateCount}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {stat.stageName}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Bulk Actions Panel */}
      {bulkMode && (
        <Paper sx={{ p: 3, mb: 4 }}>
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
      <Paper sx={{ p: 3 }}>
        <WorkflowKanban />
      </Paper>

      {/* Info Box */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>💡 {t('workflow.board.tip')}</strong>
        </Typography>
      </Box>
    </Container>
  );
};

export default WorkflowBoardPage;
