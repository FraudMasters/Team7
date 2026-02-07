import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Warning as WarningIcon,
  Person as SimilarIcon,
  Star as BestFitIcon,
  ErrorOutline as AtRiskIcon,
} from '@mui/icons-material';
import {
  SimilarCandidate,
  BestFitCandidate,
  AtRiskCandidate,
} from '../types/api';

type RecommendationData = SimilarCandidate | BestFitCandidate | AtRiskCandidate;

interface RecommendationExplanationProps {
  recommendation: RecommendationData;
  recommendationType: 'similar' | 'best_fit' | 'at_risk';
}

const RecommendationExplanation: React.FC<RecommendationExplanationProps> = ({
  recommendation,
  recommendationType,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Get recommendation config
  const getRecommendationConfig = () => {
    switch (recommendationType) {
      case 'similar':
        return {
          icon: <SimilarIcon />,
          title: 'Похожий кандидат',
          color: 'info' as const,
          bgColor: 'info.50',
          borderColor: 'info.main',
        };
      case 'best_fit':
        return {
          icon: <BestFitIcon />,
          title: 'Лучший кандидат',
          color: 'success' as const,
          bgColor: 'success.50',
          borderColor: 'success.main',
        };
      case 'at_risk':
        return {
          icon: <AtRiskIcon />,
          title: 'Кандидат под риском',
          color: 'warning' as const,
          bgColor: 'warning.50',
          borderColor: 'warning.main',
        };
      default:
        return {
          icon: <AIIcon />,
          title: 'Рекомендация',
          color: 'primary' as const,
          bgColor: 'primary.50',
          borderColor: 'primary.main',
        };
    }
  };

  const config = getRecommendationConfig();

  // Get score display based on type
  const getScoreDisplay = () => {
    switch (recommendationType) {
      case 'similar':
        return {
          label: 'Схожесть',
          value: Math.round((recommendation as SimilarCandidate).similarity_score * 100),
          suffix: '%',
        };
      case 'best_fit':
        return {
          label: 'Соответствие',
          value: Math.round((recommendation as BestFitCandidate).match_score),
          suffix: '%',
        };
      case 'at_risk':
        const atRiskRec = recommendation as AtRiskCandidate;
        return {
          label: 'Риск потери',
          value: Math.round(atRiskRec.risk_score * 100),
          suffix: '%',
          riskLevel: atRiskRec.risk_level,
        };
    }
  };

  const scoreDisplay = getScoreDisplay();

  // Get explanation text
  const getExplanationText = () => {
    switch (recommendationType) {
      case 'similar':
        return (recommendation as SimilarCandidate).match_reason;
      case 'best_fit':
        return (recommendation as BestFitCandidate).recommendation;
      case 'at_risk':
        return (recommendation as AtRiskCandidate).recommended_action;
    }
  };

  // Get feature contributions
  const getFeatureContributions = (): Array<{ label: string; value: number; description: string }> => {
    const contributions = (recommendation as any).feature_contributions;

    if (!contributions || typeof contributions !== 'object') {
      return [];
    }

    // Define readable labels for feature keys
    const labelMap: Record<string, { label: string; description: string }> = {
      similarity_score: { label: 'Векторная схожесть', description: 'Семантическое сходство резюме' },
      skills_overlap: { label: 'Пересечение навыков', description: 'Общие навыки с требуемыми' },
      experience_similarity: { label: 'Схожесть опыта', description: 'Соответствие опыта работе' },
      overall_match_score: { label: 'Общая оценка', description: 'Комплексная оценка соответствия' },
      keyword_score: { label: 'Ключевые слова', description: 'Совпадение ключевых слов' },
      tfidf_score: { label: 'TF-IDF', description: 'Вес важных терминов' },
      vector_score: { label: 'Векторная оценка', description: 'Эмбеддинг сходство' },
      skills_match_ratio: { label: 'Соотношение навыков', description: 'Доля совпавших навыков' },
      experience_months: { label: 'Опыт (месяцы)', description: 'Общий стаж работы' },
      experience_relevance: { label: 'Релевантность опыта', description: 'Опыт в требуемой области' },
      education_level: { label: 'Образование', description: 'Уровень образования' },
      recent_experience: { label: 'Недавний опыт', description: 'Опыт за последние годы' },
      skill_rarity_score: { label: 'Редкость навыков', description: 'Уникальные навыки' },
      title_similarity: { label: 'Схожесть должности', description: 'Совпадение названия должности' },
      freshness_score: { label: 'Актуальность', description: 'Свежесть резюме' },
      completeness_score: { label: 'Полнота', description: 'Заполненность резюме' },
    };

    // Convert contributions to array, filter out zero values, and normalize to percentages
    const contributionsArray = Object.entries(contributions)
      .filter(([_, value]) => Math.abs(value) > 0.01) // Filter out very small values
      .map(([key, value]) => {
        const meta = labelMap[key] || { label: key, description: '' };
        // Normalize value to percentage (rough approximation)
        const normalizedValue = Math.min(Math.abs(value) * 100, 100);
        return {
          label: meta.label,
          value: normalizedValue,
          description: meta.description,
        };
      })
      .sort((a, b) => b.value - a.value) // Sort by value descending
      .slice(0, 5); // Take top 5

    return contributionsArray;
  };

  // Get factors based on type
  const getFactors = () => {
    switch (recommendationType) {
      case 'similar': {
        const rec = recommendation as SimilarCandidate;
        return {
          positive: rec.shared_skills.map((skill, index) => ({
            label: skill,
            value: 100 - index * 10,
            description: 'Общий навык',
          })),
        };
      }
      case 'best_fit': {
        const rec = recommendation as BestFitCandidate;
        return {
          positive: rec.skills_match.map((skill, index) => ({
            label: skill,
            value: 100 - index * 5,
            description: 'Требуемый навык',
          })),
          negative: rec.missing_skills.map((skill, index) => ({
            label: skill,
            value: -(50 - index * 5),
            description: 'Отсутствующий навык',
          })),
        };
      }
      case 'at_risk': {
        const rec = recommendation as AtRiskCandidate;
        return {
          negative: rec.risk_factors.map((factor, index) => ({
            label: factor,
            value: -(100 - index * 10),
            description: 'Фактор риска',
          })),
        };
      }
    }
  };

  const factors = getFactors();
  const featureContributions = getFeatureContributions();

  // Factor bar component
  const FactorBar: React.FC<{
    label: string;
    value: number;
    description?: string;
  }> = ({ label, value, description }) => {
    const isPositive = value >= 0;
    const absValue = Math.abs(value);

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
            label={`${isPositive ? '+' : ''}${absValue}%`}
            size="small"
            color={isPositive ? 'success' : 'error'}
            sx={{ fontWeight: 700, height: 24 }}
          />
        </Box>
        <LinearProgress
          variant="determinate"
          value={absValue}
          color={isPositive ? 'success' : 'error'}
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
    <Stack spacing={2}>
      {/* Summary Card */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          bgcolor: config.bgColor,
          borderLeft: 4,
          borderColor: config.borderColor,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {config.icon}
              <Typography variant="h6" fontWeight={700} color="text.primary">
                {config.title}
              </Typography>
              {recommendationType === 'at_risk' && scoreDisplay.riskLevel && (
                <Chip
                  label={scoreDisplay.riskLevel}
                  size="small"
                  color="warning"
                  sx={{ ml: 1 }}
                />
              )}
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-line' }}>
              {getExplanationText()}
            </Typography>
          </Box>
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              bgcolor: 'background.paper',
              textAlign: 'center',
              ml: 2,
              minWidth: 100,
            }}
          >
            <Typography variant="caption" display="block" color="text.secondary">
              {scoreDisplay.label}
            </Typography>
            <Typography variant="h4" fontWeight={700} color="text.primary">
              {scoreDisplay.value}
              {scoreDisplay.suffix}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Key Factors */}
      {factors.positive && factors.positive.length > 0 && (
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: 'success.50',
            borderLeft: 4,
            borderColor: 'success.main',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
            <PositiveIcon color="success" sx={{ mr: 1, fontSize: 20 }} />
            <Typography variant="subtitle2" fontWeight={600} color="success.main">
              {recommendationType === 'similar' ? 'Общие навыки' : 'Сильные стороны'}
            </Typography>
            <Chip
              label={factors.positive.length}
              size="small"
              color="success"
              sx={{ ml: 'auto', fontWeight: 700, height: 20 }}
            />
          </Box>
          {factors.positive.slice(0, 3).map((factor, index) => (
            <FactorBar
              key={index}
              label={factor.label}
              value={factor.value}
              description={factor.description}
            />
          ))}
        </Paper>
      )}

      {factors.negative && factors.negative.length > 0 && (
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: 'error.50',
            borderLeft: 4,
            borderColor: 'error.main',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
            {recommendationType === 'at_risk' ? (
              <WarningIcon color="warning" sx={{ mr: 1, fontSize: 20 }} />
            ) : (
              <NegativeIcon color="error" sx={{ mr: 1, fontSize: 20 }} />
            )}
            <Typography variant="subtitle2" fontWeight={600} color="error.main">
              {recommendationType === 'at_risk' ? 'Факторы риска' : 'Области для улучшения'}
            </Typography>
            <Chip
              label={factors.negative.length}
              size="small"
              color={recommendationType === 'at_risk' ? 'warning' : 'error'}
              sx={{ ml: 'auto', fontWeight: 700, height: 20 }}
            />
          </Box>
          {factors.negative.slice(0, 3).map((factor, index) => (
            <FactorBar
              key={index}
              label={factor.label}
              value={factor.value}
              description={factor.description}
            />
          ))}
        </Paper>
      )}

      {/* Expandable Details */}
      <Paper
        elevation={1}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': { elevation: 2, bgcolor: 'action.hover' },
        }}
        onClick={() => setDetailsOpen(!detailsOpen)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ImportanceIcon color="primary" fontSize="small" />
            <Typography variant="body2" fontWeight={600}>
              Детальная информация
            </Typography>
            <Tooltip title="Дополнительные сведения о рекомендации">
              <InfoIcon fontSize="small" color="info" sx={{ ml: 0.5 }} />
            </Tooltip>
          </Box>
          <IconButton size="small">
            {detailsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={detailsOpen} timeout="auto" unmountOnExit>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Grid container spacing={2}>
              {/* Feature Contributions */}
              {featureContributions.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ImportanceIcon fontSize="small" color="primary" />
                    Вклад факторов в оценку
                  </Typography>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      bgcolor: 'background.default',
                      borderColor: 'primary.light',
                    }}
                  >
                    <Grid container spacing={1}>
                      {featureContributions.map((contribution, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" fontWeight={600}>
                                {contribution.label}
                              </Typography>
                              <Typography variant="caption" color="primary" fontWeight={700}>
                                {Math.round(contribution.value)}%
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={contribution.value}
                              color="primary"
                              sx={{
                                height: 6,
                                borderRadius: 3,
                                mb: 0.5,
                              }}
                            />
                            {contribution.description && (
                              <Typography variant="caption" color="text.secondary" display="block">
                                {contribution.description}
                              </Typography>
                            )}
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                </Grid>
              )}
              {/* Detailed Metrics Table */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Показатели рекомендации
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <DetailRow
                        label={scoreDisplay.label}
                        value={`${scoreDisplay.value}${scoreDisplay.suffix}`}
                      />
                      {recommendationType === 'best_fit' && (
                        <>
                          <DetailRow
                            label="Владеет навыками"
                            value={(recommendation as BestFitCandidate).skills_match.length}
                          />
                          <DetailRow
                            label="Отсутствующие навыки"
                            value={(recommendation as BestFitCandidate).missing_skills.length}
                          />
                          {(recommendation as BestFitCandidate).years_experience !== null && (
                            <DetailRow
                              label="Опыт работы"
                              value={`${(recommendation as BestFitCandidate).years_experience} лет`}
                            />
                          )}
                        </>
                      )}
                      {recommendationType === 'at_risk' && (recommendation as AtRiskCandidate).days_since_contact !== null && (
                        <DetailRow
                          label="Дней с момента связи"
                          value={(recommendation as AtRiskCandidate).days_since_contact}
                        />
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              {/* All Factors */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Все факторы
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {factors.positive && factors.positive.length > 0 && (
                    <>
                      <Typography variant="caption" fontWeight={600} color="success.main">
                        Положительные:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                        {factors.positive.map((factor, index) => (
                          <Chip
                            key={index}
                            label={factor.label}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </>
                  )}
                  {factors.negative && factors.negative.length > 0 && (
                    <>
                      <Typography variant="caption" fontWeight={600} color="error.main">
                        {recommendationType === 'at_risk' ? 'Риски:' : 'Отрицательные:'}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {factors.negative.map((factor, index) => (
                          <Chip
                            key={index}
                            label={factor.label}
                            size="small"
                            color={recommendationType === 'at_risk' ? 'warning' : 'error'}
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </>
                  )}
                </Box>
              </Grid>
            </Grid>

            {/* Technical Info */}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                <strong>Тип рекомендации:</strong> {recommendation.recommendation_type}
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </Paper>
    </Stack>
  );
};

export default RecommendationExplanation;
