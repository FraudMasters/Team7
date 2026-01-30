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
  Cancel as CrossIcon,
  Speed as SpeedIcon,
  Psychology as VectorIcon,
  Tune as TfidfIcon,
  Key as KeywordIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface UnifiedMatchMetricsProps {
  overallScore: number;
  keywordScore: number;
  tfidfScore: number;
  vectorScore: number;
  vectorSimilarity?: number;
  recommendation: 'excellent' | 'good' | 'maybe' | 'poor';
  keywordPassed: boolean;
  tfidfPassed: boolean;
  vectorPassed: boolean;
  tfidfMatched?: string[];
  tfidfMissing?: string[];
  matchedSkills: string[];
  missingSkills: string[];
}

const UnifiedMatchMetrics: React.FC<UnifiedMatchMetricsProps> = ({
  overallScore,
  keywordScore,
  tfidfScore,
  vectorScore,
  vectorSimilarity = 0,
  recommendation,
  keywordPassed,
  tfidfPassed,
  vectorPassed,
  tfidfMatched = [],
  tfidfMissing = [],
  matchedSkills = [],
  missingSkills = [],
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Get score color
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'success';
    if (score >= 0.4) return 'warning';
    return 'error';
  };

  const getScoreValue = (score: number) => Math.round(score * 100);

  // Get recommendation config
  const getRecommendationConfig = () => {
    switch (recommendation) {
      case 'excellent':
        return {
          color: 'success' as const,
          label: 'Отличный кандидат',
          icon: <CheckIcon />,
        };
      case 'good':
        return {
          color: 'success' as const,
          label: 'Хороший кандидат',
          icon: <CheckIcon />,
        };
      case 'maybe':
        return {
          color: 'warning' as const,
          label: 'Возможно подходит',
          icon: <SpeedIcon />,
        };
      case 'poor':
        return {
          color: 'error' as const,
          label: 'Слабое совпадение',
          icon: <CrossIcon />,
        };
      default:
        return {
          color: 'info' as const,
          label: 'Неизвестно',
          icon: <SpeedIcon />,
        };
    }
  };

  const recConfig = getRecommendationConfig();

  // Score card component
  const ScoreCard: React.FC<{
    title: string;
    score: number;
    icon: React.ReactNode;
    passed: boolean;
    description: string;
  }> = ({ title, score, icon, passed, description }) => (
    <Card
      variant="outlined"
      sx={{
        height: '100%',
        borderColor: passed ? 'success.main' : 'error.main',
        bgcolor: passed ? 'success.50' : 'error.50',
        transition: 'transform 0.2s',
        '&:hover': { transform: 'translateY(-4px)' },
      }}
    >
      <CardContent>
        <Stack spacing={2}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                p: 1,
                borderRadius: 1,
                bgcolor: passed ? 'success.main' : 'error.main',
                color: 'white',
              }}
            >
              {icon}
            </Box>
            <Typography variant="subtitle2" fontWeight={600}>
              {title}
            </Typography>
          </Box>

          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="h4" fontWeight={700}>
                {getScoreValue(score)}%
              </Typography>
              {passed ? (
                <CheckIcon color="success" />
              ) : (
                <CrossIcon color="error" />
              )}
            </Box>
            <LinearProgress
              variant="determinate"
              value={getScoreValue(score)}
              color={getScoreColor(score)}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          <Typography variant="caption" color="text.secondary">
            {description}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );

  // Detail row component
  const DetailRow: React.FC<{
    label: string;
    value: string | number | boolean | React.ReactNode;
    color?: 'success' | 'error' | 'warning' | 'info' | 'default';
  }> = ({ label, value, color = 'default' }) => (
    <TableRow>
      <TableCell component="th" scope="row" sx={{ borderBottom: 'none', pb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </TableCell>
      <TableCell sx={{ borderBottom: 'none', pb: 1 }}>
        {typeof value === 'boolean' ? (
          value ? (
            <Chip
              icon={<CheckIcon />}
              label="Да"
              color="success"
              size="small"
            />
          ) : (
            <Chip
              icon={<CrossIcon />}
              label="Нет"
              color="error"
              size="small"
            />
          )
        ) : typeof value === 'number' ? (
          <Typography variant="body2" fontWeight={600}>
            {value}
          </Typography>
        ) : (
          <Typography variant="body2">{value}</Typography>
        )}
      </TableCell>
    </TableRow>
  );

  return (
    <Stack spacing={3}>
      {/* Overall Score Card */}
      <Paper
        elevation={3}
        sx={{
          p: 3,
          bgcolor: `${recConfig.color}.main`,
          color: `${recConfig.color}.contrastText`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              {getScoreValue(overallScore)}%
            </Typography>
            <Typography variant="h6" fontWeight={600} sx={{ mt: 0.5 }}>
              {recConfig.label}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
              Общая оценка на основе трёх методов анализа
            </Typography>
          </Box>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.2)',
              fontSize: 48,
            }}
          >
            {recConfig.icon}
          </Box>
        </Box>
      </Paper>

      {/* Detailed Metrics Summary Cards */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <ScoreCard
            title="Ключевые слова"
            score={keywordScore}
            icon={<KeywordIcon />}
            passed={keywordPassed}
            description="Синонимы, нечёткое сравнение, составные навыки"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <ScoreCard
            title="TF-IDF взвешивание"
            score={tfidfScore}
            icon={<TfidfIcon />}
            passed={tfidfPassed}
            description="Учитывает важность каждого ключевого слова"
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <ScoreCard
            title="Семантическая похожесть"
            score={vectorScore}
            icon={<VectorIcon />}
            passed={vectorPassed}
            description="Понимает смысл, а не только ключевые слова"
          />
        </Grid>
      </Grid>

      {/* Skills Overview */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: 'success.50' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckIcon color="success" sx={{ mr: 1, fontSize: 20 }} />
                <Typography variant="subtitle2" fontWeight={600} color="success.main">
                  Найденные навыки
                </Typography>
              </Box>
              <Chip
                label={matchedSkills.length}
                size="small"
                color="success"
                sx={{ fontWeight: 700 }}
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%', bgcolor: 'error.50' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CrossIcon color="error" sx={{ mr: 1, fontSize: 20 }} />
                <Typography variant="subtitle2" fontWeight={600} color="error.main">
                  Недостающие навыки
                </Typography>
              </Box>
              <Chip
                label={missingSkills.length}
                size="small"
                color="error"
                sx={{ fontWeight: 700 }}
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Expand Button */}
      <Paper
        elevation={2}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': { elevation: 4, bgcolor: 'action.hover' },
        }}
        onClick={() => setDetailsOpen(!detailsOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon color="primary" />
            <Typography variant="subtitle1" fontWeight={600}>
              Подробная информация по метрикам
            </Typography>
          </Box>
          <IconButton size="small">
            {detailsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={detailsOpen} timeout="auto" unmountOnExit>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Grid container spacing={3}>
              {/* All Metrics Table */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Показатели матчинга
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <DetailRow
                        label="Общий скор"
                        value={`${getScoreValue(overallScore)}% (${overallScore.toFixed(3)})`}
                      />
                      <DetailRow
                        label="Рекомендация"
                        value={recConfig.label}
                      />
                      <DetailRow
                        label="Пройден overall"
                        value={overallScore >= 0.5}
                      />
                      <DetailRow label="—" value="" />
                      <DetailRow
                        label="Keyword скор"
                        value={`${getScoreValue(keywordScore)}%`}
                      />
                      <DetailRow
                        label="Keyword пройден"
                        value={keywordPassed}
                      />
                      <DetailRow label="—" value="" />
                      <DetailRow
                        label="TF-IDF скор"
                        value={`${getScoreValue(tfidfScore)}%`}
                      />
                      <DetailRow
                        label="TF-IDF пройден"
                        value={tfidfPassed}
                      />
                      <DetailRow label="—" value="" />
                      <DetailRow
                        label="Vector скор"
                        value={`${getScoreValue(vectorScore)}%`}
                      />
                      <DetailRow
                        label="Vector пройден"
                        value={vectorPassed}
                      />
                      <DetailRow
                        label="Косинусная похожесть"
                        value={vectorSimilarity.toFixed(4)}
                      />
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              {/* Skills Lists */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Навыки и ключевые слова
                </Typography>

                {/* Matched Skills */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                    Найденные навыки ({matchedSkills.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: 100, overflowY: 'auto' }}>
                    {matchedSkills.length > 0 ? (
                      matchedSkills.map((skill, index) => (
                        <Chip key={index} label={skill} size="small" color="success" variant="outlined" />
                      ))
                    ) : (
                      <Typography variant="caption" color="text.secondary">Нет найденных навыков</Typography>
                    )}
                  </Box>
                </Box>

                {/* Missing Skills */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                    Недостающие навыки ({missingSkills.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: 100, overflowY: 'auto' }}>
                    {missingSkills.length > 0 ? (
                      missingSkills.map((skill, index) => (
                        <Chip key={index} label={skill} size="small" color="error" variant="outlined" />
                      ))
                    ) : (
                      <Typography variant="caption" color="success.main">Все навыки найдены!</Typography>
                    )}
                  </Box>
                </Box>

                {/* TF-IDF Matched */}
                {tfidfMatched && tfidfMatched.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                      TF-IDF найденные ({tfidfMatched.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: 80, overflowY: 'auto' }}>
                      {tfidfMatched.map((kw, index) => (
                        <Chip key={index} label={kw} size="small" variant="filled" sx={{ bgcolor: 'lightgreen' }} />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* TF-IDF Missing */}
                {tfidfMissing && tfidfMissing.length > 0 && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                      TF-IDF недостающие (по важности)
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: 80, overflowY: 'auto' }}>
                      {tfidfMissing.map((kw, index) => (
                        <Chip
                          key={index}
                          label={kw}
                          size="small"
                          color="warning"
                          title={`Ранг важности: #${index + 1}`}
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </Grid>
            </Grid>

            {/* Technical Info */}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Метод анализа:</strong> Unified Matcher v1 (Keyword + TF-IDF + Vector)
                {' • '}
                <strong>Косинусная похожесть:</strong> {vectorSimilarity.toFixed(4)}
                {' • '}
                <strong>Thresholds:</strong> keyword ≥30%, tfidf ≥30%, vector ≥50%
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </Paper>

      {/* Vector Similarity Info (compact) */}
      {!detailsOpen && (
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Косинусная похожесть:</strong> {vectorSimilarity.toFixed(3)}
            {' • '}
            <strong>Метод анализа:</strong> unified-v1 (Keyword + TF-IDF + Vector)
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default UnifiedMatchMetrics;
