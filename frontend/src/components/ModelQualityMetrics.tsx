import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingIcon,
  Description as DocIcon,
  Code as CodeIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface QualityMetrics {
  text_extraction_success_rate: number;
  avg_extraction_time_seconds: number;
  ner_accuracy: number;
  entities_per_resume_avg: number;
  avg_keywords_per_resume: number;
  keyword_relevance_avg: number;
  grammar_error_rate: number;
  matching_confidence_avg: number;
  matching_precision: number;
  matching_recall: number;
  avg_analysis_time_seconds: number;
  error_rate: number;
  total_analyzed: number;
}

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: 'success' | 'warning' | 'error';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, subtitle, color }) => {
  const getColor = () => {
    switch (color) {
      case 'success': return '#2e7d32';
      case 'warning': return '#ed6c02';
      case 'error': return '#d32f2f';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ pb: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          {title}
        </Typography>
        <Typography variant="h6" fontWeight={600} color={getColor()} sx={{ lineHeight: 1.2 }}>
          {value}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontSize: '0.65rem' }}>
          {subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
};

const ModelQualityMetrics: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/analytics/quality-metrics');
        setMetrics(response.data);
      } catch (error) {
        console.error('Error fetching quality metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={32} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          {t('metrics.loading')}
        </Typography>
      </Paper>
    );
  }

  if (!metrics) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <WarningIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
        <Typography variant="body1" color="text.secondary">
          {t('metrics.noData')}
        </Typography>
      </Paper>
    );
  }

  const getHealthColor = () => {
    if (metrics.text_extraction_success_rate >= 0.95 && metrics.avg_keywords_per_resume >= 15) {
      return 'success';
    }
    if (metrics.text_extraction_success_rate >= 0.90 && metrics.avg_keywords_per_resume >= 10) {
      return 'warning';
    }
    return 'error';
  };

  const healthColor = getHealthColor();

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SpeedIcon sx={{ fontSize: 20, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={500}>
            {t('metrics.title')}
          </Typography>
        </Box>
        <Chip
          label={metrics.total_analyzed}
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.75rem' }}
        />
      </Box>

      {/* Processing Metrics */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
          <CodeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="caption" color="text.secondary" fontWeight={500}>
            ОБРАБОТКА
          </Typography>
        </Box>
        <Grid container spacing={1.5}>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Ключевых слов"
              value={metrics.avg_keywords_per_resume.toFixed(1)}
              subtitle="навыков / резюме"
              color={metrics.avg_keywords_per_resume >= 15 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Сущностей"
              value={metrics.entities_per_resume_avg.toFixed(1)}
              subtitle="имена, даты, организации"
              color={metrics.entities_per_resume_avg >= 25 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Время извл."
              value={`${metrics.avg_extraction_time_seconds.toFixed(1)}s`}
              subtitle="извлечение текста"
              color={metrics.avg_extraction_time_seconds <= 3 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Полный анализ"
              value={`${metrics.avg_analysis_time_seconds.toFixed(1)}s`}
              subtitle="включая NLP"
              color={metrics.avg_analysis_time_seconds <= 10 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Успешность"
              value={`${(metrics.text_extraction_success_rate * 100).toFixed(0)}%`}
              subtitle="резюме обработано"
              color={metrics.text_extraction_success_rate >= 0.95 ? 'success' : 'warning'}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Model Quality */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
          <TrendingIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="caption" color="text.secondary" fontWeight={500}>
            КАЧЕСТВО ML
          </Typography>
        </Box>
        <Grid container spacing={1.5}>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="NER точность"
              value={`${(metrics.ner_accuracy * 100).toFixed(0)}%`}
              subtitle="распознавание сущностей"
              color={metrics.ner_accuracy >= 0.80 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Релевантность"
              value={`${(metrics.keyword_relevance_avg * 100).toFixed(0)}%`}
              subtitle="качество ключевых слов"
              color={metrics.keyword_relevance_avg >= 0.65 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Precision"
              value={`${(metrics.matching_precision * 100).toFixed(0)}%`}
              subtitle="точность подбора"
              color={metrics.matching_precision >= 0.70 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Recall"
              value={`${(metrics.matching_recall * 100).toFixed(0)}%`}
              subtitle="полнота подбора"
              color={metrics.matching_recall >= 0.70 ? 'success' : 'warning'}
            />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <MetricCard
              title="Ошибки"
              value={`${(metrics.error_rate * 100).toFixed(1)}%`}
              subtitle="коэффициент ошибок"
              color={metrics.error_rate <= 0.05 ? 'success' : 'error'}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* System Status - compact */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Статус системы
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {healthColor === 'success' ? 'Работает отлично' : healthColor === 'warning' ? 'Нормально' : 'Требует внимания'}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">Грам. ошибок</Typography>
              <Typography variant="body2" color={metrics.grammar_error_rate === 0 ? 'success.main' : 'warning.main'}>
                {metrics.grammar_error_rate === 0 ? 'Нет' : `${(metrics.grammar_error_rate * 100).toFixed(0)}%`}
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">Доверие</Typography>
              <Typography variant="body2" color={metrics.matching_confidence_avg >= 0.7 ? 'success.main' : 'warning.main'}>
                {(metrics.matching_confidence_avg * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ModelQualityMetrics;
