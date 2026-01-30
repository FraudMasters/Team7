import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack,
  Chip,
  LinearProgress,
  Tooltip,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  TrendingUp as PositiveIcon,
  TrendingDown as NegativeIcon,
  Psychology as AIIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  BarChart as ImportanceIcon,
} from '@mui/icons-material';
import { FeatureExplanation } from '../types/api';

interface RankingExplanationProps {
  summary: string;
  topPositiveFactors: FeatureExplanation[];
  topNegativeFactors: FeatureExplanation[];
  featureContributions: Record<string, number>;
  rankingScore: number;
  hireProbability: number;
}

const RankingExplanation: React.FC<RankingExplanationProps> = ({
  summary,
  topPositiveFactors = [],
  topNegativeFactors = [],
  featureContributions = {},
  rankingScore,
  hireProbability,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [factorsOpen, setFactorsOpen] = useState(false);

  // Get contribution color
  const getContributionColor = (contribution: number) => {
    if (contribution > 0) return 'success';
    if (contribution < 0) return 'error';
    return 'default';
  };

  const getContributionValue = (contribution: number) => {
    const absValue = Math.abs(contribution * 100);
    return `${contribution > 0 ? '+' : ''}${absValue.toFixed(1)}%`;
  };

  // Get recommendation config based on score
  const getScoreConfig = () => {
    if (rankingScore >= 80) {
      return {
        color: 'success' as const,
        label: 'Исключительный кандидат',
      };
    } else if (rankingScore >= 60) {
      return {
        color: 'success' as const,
        label: 'Хороший кандидат',
      };
    } else if (rankingScore >= 40) {
      return {
        color: 'warning' as const,
        label: 'Средний кандидат',
      };
    } else {
      return {
        color: 'error' as const,
        label: 'Слабый кандидат',
      };
    }
  };

  const scoreConfig = getScoreConfig();

  // Factor bar component
  const FactorBar: React.FC<{
    label: string;
    contribution: number;
    description?: string;
    value?: number;
  }> = ({ label, contribution, description, value }) => {
    const absContribution = Math.abs(contribution * 100);
    const isPositive = contribution >= 0;

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isPositive ? (
              <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
            ) : (
              <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
            )}
            <Typography variant="body2" fontWeight={600}>
              {label}
            </Typography>
          </Box>
          <Chip
            label={getContributionValue(contribution)}
            size="small"
            color={getContributionColor(contribution) as 'success' | 'error' | 'default'}
            sx={{ fontWeight: 700, height: 24 }}
          />
        </Box>
        <LinearProgress
          variant="determinate"
          value={Math.min(absContribution, 100)}
          color={getContributionColor(contribution) === 'default' ? 'primary' : (getContributionColor(contribution) as 'success' | 'error')}
          sx={{
            height: 8,
            borderRadius: 4,
            mb: description ? 0.5 : 0,
          }}
        />
        {description && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            {description}
          </Typography>
        )}
        {value !== undefined && (
          <Typography variant="caption" color="text.secondary">
            Значение: {Math.round(value * 100)}%
          </Typography>
        )}
      </Box>
    );
  };

  // Detail row component
  const DetailRow: React.FC<{
    label: string;
    value: string | number | React.ReactNode;
  }> = ({ label, value }) => (
    <TableRow>
      <TableCell component="th" scope="row" sx={{ borderBottom: 'none', pb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </TableCell>
      <TableCell sx={{ borderBottom: 'none', pb: 1 }}>
        <Typography variant="body2" fontWeight={600}>
          {value}
        </Typography>
      </TableCell>
    </TableRow>
  );

  return (
    <Stack spacing={3}>
      {/* Summary Card */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          bgcolor: `${scoreConfig.color}.main`,
          color: `${scoreConfig.color}.contrastText`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <AIIcon sx={{ fontSize: 28 }} />
              <Typography variant="h5" fontWeight={700}>
                Объяснение AI-ранжирования
              </Typography>
            </Box>
            <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
              {scoreConfig.label}
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.95, whiteSpace: 'pre-line' }}>
              {summary}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.2)',
              textAlign: 'center',
              ml: 2,
              minWidth: 120,
            }}
          >
            <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>
              Рейтинг
            </Typography>
            <Typography variant="h3" fontWeight={700}>
              {Math.round(rankingScore)}%
            </Typography>
            <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.3)' }} />
            <Typography variant="caption" display="block" sx={{ opacity: 0.9 }}>
              Вероятность успеха
            </Typography>
            <Typography variant="h6" fontWeight={600}>
              {Math.round(hireProbability * 100)}%
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Key Factors Overview */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: 'success.50',
              borderLeft: 4,
              borderColor: 'success.main',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PositiveIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="subtitle1" fontWeight={600} color="success.main">
                Сильные стороны
              </Typography>
              <Chip
                label={topPositiveFactors.length}
                size="small"
                color="success"
                sx={{ ml: 'auto', fontWeight: 700 }}
              />
            </Box>
            {topPositiveFactors.length > 0 ? (
              <Stack spacing={1.5}>
                {topPositiveFactors.slice(0, 3).map((factor, index) => (
                  <Box key={index}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {factor.feature_name}
                      </Typography>
                      <Chip
                        label={`+${Math.round(factor.contribution_percentage)}%`}
                        size="small"
                        color="success"
                        sx={{ height: 20, fontSize: '0.75rem' }}
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(factor.contribution_percentage, 100)}
                      color="success"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                      {factor.description}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Нет явных преимуществ
              </Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              height: '100%',
              bgcolor: 'error.50',
              borderLeft: 4,
              borderColor: 'error.main',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <NegativeIcon color="error" sx={{ mr: 1 }} />
              <Typography variant="subtitle1" fontWeight={600} color="error.main">
                Области для улучшения
              </Typography>
              <Chip
                label={topNegativeFactors.length}
                size="small"
                color="error"
                sx={{ ml: 'auto', fontWeight: 700 }}
              />
            </Box>
            {topNegativeFactors.length > 0 ? (
              <Stack spacing={1.5}>
                {topNegativeFactors.slice(0, 3).map((factor, index) => (
                  <Box key={index}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {factor.feature_name}
                      </Typography>
                      <Chip
                        label={`${Math.round(factor.contribution_percentage)}%`}
                        size="small"
                        color="error"
                        sx={{ height: 20, fontSize: '0.75rem' }}
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(Math.abs(factor.contribution_percentage), 100)}
                      color="error"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                      {factor.description}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="success.main">
                Нет явных недостатков
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Expandable Details */}
      <Paper
        elevation={2}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': { elevation: 4, bgcolor: 'action.hover' },
        }}
        onClick={() => setFactorsOpen(!factorsOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ImportanceIcon color="primary" />
            <Typography variant="subtitle1" fontWeight={600}>
              Детальный разбор факторов
            </Typography>
            <Tooltip title="Показывает вклад каждого фактора в итоговый рейтинг">
              <InfoIcon fontSize="small" color="info" sx={{ ml: 0.5 }} />
            </Tooltip>
          </Box>
          <IconButton size="small">
            {factorsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={factorsOpen} timeout="auto" unmountOnExit>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Grid container spacing={3}>
              {/* All Feature Contributions */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Вклад факторов в рейтинг
                </Typography>
                <Box sx={{ mt: 2 }}>
                  {Object.entries(featureContributions).map(([feature, contribution]) => (
                    <FactorBar
                      key={feature}
                      label={feature}
                      contribution={contribution}
                    />
                  ))}
                </Box>
              </Grid>

              {/* Detailed Metrics Table */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Показатели модели
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <DetailRow
                        label="Рейтинг"
                        value={`${Math.round(rankingScore)}%`}
                      />
                      <DetailRow
                        label="Вероятность успеха"
                        value={`${Math.round(hireProbability * 100)}%`}
                      />
                      <DetailRow
                        label="Положительных факторов"
                        value={topPositiveFactors.length}
                      />
                      <DetailRow
                        label="Отрицательных факторов"
                        value={topNegativeFactors.length}
                      />
                      <DetailRow
                        label="Всего факторов"
                        value={Object.keys(featureContributions).length}
                      />
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Feature Legend */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" fontWeight={600} gutterBottom display="block">
                    Обозначения:
                  </Typography>
                  <Stack spacing={0.5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PositiveIcon sx={{ fontSize: 16, color: 'success.main' }} />
                      <Typography variant="caption" color="text.secondary">
                        Положительное влияние на рейтинг
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NegativeIcon sx={{ fontSize: 16, color: 'error.main' }} />
                      <Typography variant="caption" color="text.secondary">
                        Отрицательное влияние на рейтинг
                      </Typography>
                    </Box>
                  </Stack>
                </Box>
              </Grid>
            </Grid>

            {/* Technical Info */}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Метод:</strong> Explainable AI (SHAP values)
                {' • '}
                <strong>Факторы:</strong> {Object.keys(featureContributions).join(', ')}
                {' • '}
                <strong>Интерпретация:</strong> Значения показывают вклад каждого фактора в итоговый рейтинг
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </Paper>

      {/* Compact Footer */}
      {!factorsOpen && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>AI-модель:</strong> Candidate Ranking v1.0
            {' • '}
            <strong>Метод объяснения:</strong> SHAP (SHapley Additive exPlanations)
            {' • '}
            <strong>Факторов:</strong> {Object.keys(featureContributions).length}
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default RankingExplanation;
