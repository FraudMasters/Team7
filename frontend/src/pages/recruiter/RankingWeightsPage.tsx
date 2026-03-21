/**
 * Страница настройки весов ранжирования для рекрутера
 *
 * Позволяет рекрутерам настраивать относительные веса функций ранжирования кандидатов:
 * общий скор соответствия, ключевые слова, TF-IDF, векторная схожесть, навыки, опыт,
 * образование и другие факторы. Включает пресеты профиля для различных типов ролей
 * (технические, продажи, управленческие, сбалансированные).
 */

// Импорт React и хуков
import React, { useState, useCallback, useEffect } from 'react';

// Импорт хука для интернационализации
import { useTranslation } from 'react-i18next';

// Импорт компонентов MUI
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Stack,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material';

// Импорт иконок MUI
import {
  Save as SaveIcon,
  Tune as TuneIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  History as HistoryIcon,
  AutoAwesome as PresetIcon,
} from '@mui/icons-material';

// Импорт API клиента и типов
import { rankingWeightsClient } from '@/api';
import type {
  RankingWeightProfile,
  RankingWeightPreset,
  RankingWeightProfileCreate,
} from '@/types/rankingWeights';

// Импорт компонентов для слайдеров весов
import { RankingWeightSliderCardStack } from '@/components/RankingWeightSliderCard';

// Импорт компонента превью влияния весов
import RankingWeightImpactPreview from '@/components/RankingWeightImpactPreview';

// Импорт MUI компонента анимации переходов
import { PageTransition } from '@components/mui/PageTransition';

// Интерфейс состояния весов ранжирования (все 13 функций)
interface RankingWeightState {
  overall_match_score: number;
  keyword_score: number;
  tfidf_score: number;
  vector_score: number;
  skills_match_ratio: number;
  experience_months: number;
  experience_relevance: number;
  education_level: number;
  recent_experience: number;
  skill_rarity: number;
  title_similarity: number;
  freshness_score: number;
  completeness_score: number;
}

// Свойства панели вкладок
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Компонент панели вкладок
function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Предустановленные конфигурации весов для различных типов ролей
 * Значения в процентах (0-100), должны в сумме давать 100
 */
const PRESETS: Record<string, RankingWeightState> = {
  // Технические роли - упор на навыки и релевантный опыт
  technical: {
    overall_match_score: 10,
    keyword_score: 15,
    tfidf_score: 5,
    vector_score: 5,
    skills_match_ratio: 25, // Высокий вес на навыки
    experience_months: 5,
    experience_relevance: 15, // Релевантный опыт важен
    education_level: 8,
    recent_experience: 5,
    skill_rarity: 5, // Редкие навыки ценятся
    title_similarity: 2,
    freshness_score: 5,
    completeness_score: 5,
  },
  // Роли в продажах - упор на опыт и активность
  sales: {
    overall_match_score: 10,
    keyword_score: 8,
    tfidf_score: 5,
    vector_score: 5,
    skills_match_ratio: 10,
    experience_months: 15, // Опыт важен
    experience_relevance: 20, // Релевантный опыт критичен
    education_level: 5,
    recent_experience: 12, // Недавняя активность важна
    skill_rarity: 3,
    title_similarity: 2,
    freshness_score: 10, // Активные кандидаты
    completeness_score: 5,
  },
  // Управленческие роли - упор на опыт и образование
  executive: {
    overall_match_score: 8,
    keyword_score: 5,
    tfidf_score: 5,
    vector_score: 8,
    skills_match_ratio: 8,
    experience_months: 20, // Большой опыт важен
    experience_relevance: 22, // Релевантный опыт критичен
    education_level: 12, // Образование важно
    recent_experience: 5,
    skill_rarity: 2,
    title_similarity: 5,
    freshness_score: 5,
    completeness_score: 5,
  },
  // Сбалансированный профиль - равномерное распределение
  balanced: {
    overall_match_score: 8,
    keyword_score: 8,
    tfidf_score: 8,
    vector_score: 8,
    skills_match_ratio: 8,
    experience_months: 8,
    experience_relevance: 8,
    education_level: 7,
    recent_experience: 7,
    skill_rarity: 7,
    title_similarity: 7,
    freshness_score: 8,
    completeness_score: 8,
  },
};

/**
 * Страница настройки весов ранжирования для рекрутера
 */
function RankingWeightsPage() {
  const { t } = useTranslation();

  // Состояние весов функций ранжирования
  const [weights, setWeights] = useState<RankingWeightState>({
    overall_match_score: 8,
    keyword_score: 8,
    tfidf_score: 8,
    vector_score: 8,
    skills_match_ratio: 8,
    experience_months: 8,
    experience_relevance: 8,
    education_level: 7,
    recent_experience: 7,
    skill_rarity: 7,
    title_similarity: 7,
    freshness_score: 8,
    completeness_score: 8,
  });

  // Состояния UI
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // Состояние для превью влияния весов
  const [showImpactPreview, setShowImpactPreview] = useState(false);
  const [previewVacancyId, setPreviewVacancyId] = useState<string>('');
  const [savedWeights, setSavedWeights] = useState<RankingWeightState | null>(null);

  // Состояние кастомного профиля
  const [profileName, setProfileName] = useState('');
  const [profileDescription, setProfileDescription] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Существующие профили
  const [existingProfiles, setExistingProfiles] = useState<RankingWeightProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);

  // Пресеты из API
  const [presets, setPresets] = useState<RankingWeightPreset[]>([]);

  /**
   * Вычисляем общий процент веса
   */
  const totalWeight =
    weights.overall_match_score +
    weights.keyword_score +
    weights.tfidf_score +
    weights.vector_score +
    weights.skills_match_ratio +
    weights.experience_months +
    weights.experience_relevance +
    weights.education_level +
    weights.recent_experience +
    weights.skill_rarity +
    weights.title_similarity +
    weights.freshness_score +
    weights.completeness_score;

  /**
   * Проверяем, что веса валидны (сумма равна 100)
   */
  const isValid = Math.abs(totalWeight - 100) < 1;

  /**
   * Обработчик изменения веса
   */
  const handleWeightChange = useCallback(
    (
      type:
        | 'overall_match_score'
        | 'keyword_score'
        | 'tfidf_score'
        | 'vector_score'
        | 'skills_match_ratio'
        | 'experience_months'
        | 'experience_relevance'
        | 'education_level'
        | 'recent_experience'
        | 'skill_rarity'
        | 'title_similarity'
        | 'freshness_score'
        | 'completeness_score',
      value: number
    ) => {
      setWeights((prev) => ({
        ...prev,
        [type]: value,
      }));
      setSuccess(false);

      // Enable impact preview when weights change
      if (!savedWeights) {
        setSavedWeights(weights);
      }
    },
    [weights, savedWeights]
  );

  /**
   * Применить пресет весов
   */
  const applyPreset = useCallback((presetKey: string) => {
    const preset = PRESETS[presetKey];
    if (preset) {
      if (!savedWeights) {
        setSavedWeights(weights);
      }
      setWeights(preset);
      setSuccess(false);
    }
  }, [weights, savedWeights]);

  /**
   * Нормализовать веса, чтобы сумма была равна 100
   */
  const normalizeWeights = useCallback(() => {
    if (totalWeight === 0) return;

    const normalized = {
      overall_match_score: Math.round((weights.overall_match_score / totalWeight) * 100),
      keyword_score: Math.round((weights.keyword_score / totalWeight) * 100),
      tfidf_score: Math.round((weights.tfidf_score / totalWeight) * 100),
      vector_score: Math.round((weights.vector_score / totalWeight) * 100),
      skills_match_ratio: Math.round((weights.skills_match_ratio / totalWeight) * 100),
      experience_months: Math.round((weights.experience_months / totalWeight) * 100),
      experience_relevance: Math.round((weights.experience_relevance / totalWeight) * 100),
      education_level: Math.round((weights.education_level / totalWeight) * 100),
      recent_experience: Math.round((weights.recent_experience / totalWeight) * 100),
      skill_rarity: Math.round((weights.skill_rarity / totalWeight) * 100),
      title_similarity: Math.round((weights.title_similarity / totalWeight) * 100),
      freshness_score: Math.round((weights.freshness_score / totalWeight) * 100),
      completeness_score: Math.round((weights.completeness_score / totalWeight) * 100),
    };

    // Корректировка ошибок округления
    const normalizedTotal =
      normalized.overall_match_score +
      normalized.keyword_score +
      normalized.tfidf_score +
      normalized.vector_score +
      normalized.skills_match_ratio +
      normalized.experience_months +
      normalized.experience_relevance +
      normalized.education_level +
      normalized.recent_experience +
      normalized.skill_rarity +
      normalized.title_similarity +
      normalized.freshness_score +
      normalized.completeness_score;

    if (normalizedTotal !== 100) {
      normalized.completeness_score += 100 - normalizedTotal;
    }

    setWeights(normalized);
  }, [weights, totalWeight]);

  /**
   * Загрузить профили из API
   */
  const loadProfiles = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Загружаем кастомные профили и пресеты
      const [profilesResult, presetsResult] = await Promise.all([
        rankingWeightsClient.listWeightProfiles(),
        rankingWeightsClient.getPresetProfiles(),
      ]);

      setExistingProfiles(profilesResult.profiles);
      setPresets(presetsResult.presets);

      // Если есть активный профиль, загружаем его
      const activeProfile = profilesResult.profiles.find((p) => p.is_active);
      if (activeProfile) {
        setWeights({
          overall_match_score: activeProfile.overall_match_score_weight * 100,
          keyword_score: activeProfile.keyword_score_weight * 100,
          tfidf_score: activeProfile.tfidf_score_weight * 100,
          vector_score: activeProfile.vector_score_weight * 100,
          skills_match_ratio: activeProfile.skills_match_ratio_weight * 100,
          experience_months: activeProfile.experience_months_weight * 100,
          experience_relevance: activeProfile.experience_relevance_weight * 100,
          education_level: activeProfile.education_level_weight * 100,
          recent_experience: activeProfile.recent_experience_weight * 100,
          skill_rarity: activeProfile.skill_rarity_weight * 100,
          title_similarity: activeProfile.title_similarity_weight * 100,
          freshness_score: activeProfile.freshness_score_weight * 100,
          completeness_score: activeProfile.completeness_score_weight * 100,
        });
        setSelectedProfile(activeProfile.id);
      }
    } catch (err: any) {
      setError(err.detail || 'Failed to load ranking weight profiles');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Сохранить текущие веса
   */
  const handleSave = useCallback(async () => {
    if (!isValid) {
      setError('Weights must sum to 100%');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Преобразуем процентные веса (0-100) в доли (0-1)
      const profileData: RankingWeightProfileCreate = {
        name: profileName || 'Custom Ranking Profile',
        description: profileDescription,
        overall_match_score_weight: weights.overall_match_score / 100,
        keyword_score_weight: weights.keyword_score / 100,
        tfidf_score_weight: weights.tfidf_score / 100,
        vector_score_weight: weights.vector_score / 100,
        skills_match_ratio_weight: weights.skills_match_ratio / 100,
        experience_months_weight: weights.experience_months / 100,
        experience_relevance_weight: weights.experience_relevance / 100,
        education_level_weight: weights.education_level / 100,
        recent_experience_weight: weights.recent_experience / 100,
        skill_rarity_weight: weights.skill_rarity / 100,
        title_similarity_weight: weights.title_similarity / 100,
        freshness_score_weight: weights.freshness_score / 100,
        completeness_score_weight: weights.completeness_score / 100,
        is_active: true,
      };

      await rankingWeightsClient.createWeightProfile(profileData);

      setSuccess(true);
      setShowSaveDialog(false);
      setProfileName('');
      setProfileDescription('');

      // Перезагружаем профили
      await loadProfiles();

      // Скрываем сообщение об успехе через 3 секунды
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.detail || 'Failed to save ranking weight profile');
    } finally {
      setSaving(false);
    }
  }, [
    isValid,
    weights,
    profileName,
    profileDescription,
    loadProfiles,
  ]);

  /**
   * Загрузить профиль
   */
  const loadProfile = useCallback((profile: RankingWeightProfile) => {
    if (!savedWeights) {
      setSavedWeights(weights);
    }
    setWeights({
      overall_match_score: profile.overall_match_score_weight * 100,
      keyword_score: profile.keyword_score_weight * 100,
      tfidf_score: profile.tfidf_score_weight * 100,
      vector_score: profile.vector_score_weight * 100,
      skills_match_ratio: profile.skills_match_ratio_weight * 100,
      experience_months: profile.experience_months_weight * 100,
      experience_relevance: profile.experience_relevance_weight * 100,
      education_level: profile.education_level_weight * 100,
      recent_experience: profile.recent_experience_weight * 100,
      skill_rarity: profile.skill_rarity_weight * 100,
      title_similarity: profile.title_similarity_weight * 100,
      freshness_score: profile.freshness_score_weight * 100,
      completeness_score: profile.completeness_score_weight * 100,
    });
    setSelectedProfile(profile.id);
    setSuccess(false);
  }, [weights, savedWeights]);

  /**
   * Загрузить пресет
   */
  const loadPresetProfile = useCallback((preset: RankingWeightPreset) => {
    if (!savedWeights) {
      setSavedWeights(weights);
    }
    setWeights({
      overall_match_score: preset.weights.overall_match_score_weight * 100,
      keyword_score: preset.weights.keyword_score_weight * 100,
      tfidf_score: preset.weights.tfidf_score_weight * 100,
      vector_score: preset.weights.vector_score_weight * 100,
      skills_match_ratio: preset.weights.skills_match_ratio_weight * 100,
      experience_months: preset.weights.experience_months_weight * 100,
      experience_relevance: preset.weights.experience_relevance_weight * 100,
      education_level: preset.weights.education_level_weight * 100,
      recent_experience: preset.weights.recent_experience_weight * 100,
      skill_rarity: preset.weights.skill_rarity_weight * 100,
      title_similarity: preset.weights.title_similarity_weight * 100,
      freshness_score: preset.weights.freshness_score_weight * 100,
      completeness_score: preset.weights.completeness_score_weight * 100,
    });
    setSuccess(false);
  }, [weights, savedWeights]);

  /**
   * Загрузить данные при монтировании компонента
   */
  useEffect(() => {
    loadProfiles();

    // Check if vacancy_id is provided in URL params for preview
    const urlParams = new URLSearchParams(window.location.search);
    const vacancyId = urlParams.get('vacancy_id');
    if (vacancyId) {
      setPreviewVacancyId(vacancyId);
      setShowImpactPreview(true);
    }
  }, [loadProfiles]);

  /**
   * Convert weights from percentage (0-100) to decimal (0-1)
   */
  const weightsToDecimal = (w: RankingWeightState): Record<string, number> => ({
    overall_match_score_weight: w.overall_match_score / 100,
    keyword_score_weight: w.keyword_score / 100,
    tfidf_score_weight: w.tfidf_score / 100,
    vector_score_weight: w.vector_score / 100,
    skills_match_ratio_weight: w.skills_match_ratio / 100,
    experience_months_weight: w.experience_months / 100,
    experience_relevance_weight: w.experience_relevance / 100,
    education_level_weight: w.education_level / 100,
    recent_experience_weight: w.recent_experience / 100,
    skill_rarity_weight: w.skill_rarity / 100,
    title_similarity_weight: w.title_similarity / 100,
    freshness_score_weight: w.freshness_score / 100,
    completeness_score_weight: w.completeness_score / 100,
  });

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            <TuneIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            {t('rankingWeights.title', { defaultValue: 'Ranking Weights Configuration' })}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('rankingWeights.subtitle', {
              defaultValue:
                'Configure the importance of different ranking features to customize how candidates are scored and ranked.',
            })}
          </Typography>
        </Box>

        {/* Уведомления */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert
            severity="success"
            sx={{ mb: 3 }}
            icon={<SuccessIcon />}
            onClose={() => setSuccess(false)}
          >
            {t('rankingWeights.saveSuccess', {
              defaultValue: 'Ranking weight profile saved successfully!',
            })}
          </Alert>
        )}

        {/* Индикатор загрузки */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Панель управления */}
            <Paper sx={{ mb: 3 }}>
              <Box sx={{ p: 3 }}>
                <Grid container spacing={2} alignItems="center">
                  {/* Общий вес */}
                  <Grid item xs={12} md={4}>
                    <Card
                      sx={{
                        backgroundColor: isValid ? 'success.light' : 'warning.light',
                        color: isValid ? 'success.dark' : 'warning.dark',
                      }}
                    >
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {t('rankingWeights.totalWeight', { defaultValue: 'Total Weight' })}
                        </Typography>
                        <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                          {totalWeight.toFixed(0)}%
                        </Typography>
                        {!isValid && (
                          <Typography variant="caption">
                            {t('rankingWeights.mustEqual100', {
                              defaultValue: 'Must equal 100%',
                            })}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Кнопки действий */}
                  <Grid item xs={12} md={8}>
                    <Stack direction="row" spacing={2} justifyContent="flex-end" flexWrap="wrap">
                      <Button
                        variant="outlined"
                        onClick={normalizeWeights}
                        disabled={totalWeight === 0}
                      >
                        {t('rankingWeights.normalize', { defaultValue: 'Normalize to 100%' })}
                      </Button>

                      <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={() => setShowSaveDialog(true)}
                        disabled={!isValid || saving}
                      >
                        {saving
                          ? t('rankingWeights.saving', { defaultValue: 'Saving...' })
                          : t('rankingWeights.save', { defaultValue: 'Save Profile' })}
                      </Button>
                    </Stack>
                  </Grid>
                </Grid>
              </Box>

              {/* Прогресс-бар валидации */}
              <LinearProgress
                variant="determinate"
                value={Math.min(totalWeight, 100)}
                sx={{
                  height: 8,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: isValid ? 'success.main' : 'warning.main',
                  },
                }}
              />
            </Paper>

            {/* Вкладки */}
            <Paper sx={{ mb: 3 }}>
              <Tabs
                value={tabValue}
                onChange={(_, newValue) => setTabValue(newValue)}
                variant="fullWidth"
                sx={{ borderBottom: 1, borderColor: 'divider' }}
              >
                <Tab label={t('rankingWeights.tabs.current', { defaultValue: 'Current Weights' })} />
                <Tab label={t('rankingWeights.tabs.presets', { defaultValue: 'Presets' })} />
                <Tab
                  label={t('rankingWeights.tabs.customProfiles', { defaultValue: 'Custom Profiles' })}
                />
                {showImpactPreview && (
                  <Tab
                    label={t('rankingWeights.tabs.impactPreview', { defaultValue: 'Impact Preview' })}
                  />
                )}
              </Tabs>

              {/* Панель 1: Текущие веса */}
              <TabPanel value={tabValue} index={0}>
                <RankingWeightSliderCardStack
                  weights={weights}
                  onWeightChange={handleWeightChange}
                  disabled={saving}
                />
              </TabPanel>

              {/* Панель 2: Пресеты */}
              <TabPanel value={tabValue} index={1}>
                <Grid container spacing={3}>
                  {/* Локальные пресеты */}
                  {Object.entries(PRESETS).map(([key, preset]) => (
                    <Grid item xs={12} sm={6} md={3} key={key}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          '&:hover': {
                            boxShadow: 6,
                            transform: 'translateY(-4px)',
                          },
                        }}
                        onClick={() => applyPreset(key)}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <PresetIcon sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="h6">
                              {t(`rankingWeights.presets.${key}.name`, {
                                defaultValue: key.charAt(0).toUpperCase() + key.slice(1),
                              })}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            {t(`rankingWeights.presets.${key}.description`, {
                              defaultValue: `Optimized for ${key} roles`,
                            })}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}

                  {/* API пресеты */}
                  {presets.map((preset) => (
                    <Grid item xs={12} sm={6} md={3} key={preset.preset_type}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          border: '2px solid',
                          borderColor: 'primary.main',
                          '&:hover': {
                            boxShadow: 6,
                            transform: 'translateY(-4px)',
                          },
                        }}
                        onClick={() => loadPresetProfile(preset)}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <PresetIcon sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="h6">{preset.name}</Typography>
                            <Chip
                              label="API"
                              size="small"
                              color="primary"
                              sx={{ ml: 'auto' }}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {preset.description}
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="caption" color="text.secondary">
                            {preset.use_case}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Панель 3: Кастомные профили */}
              <TabPanel value={tabValue} index={2}>
                {existingProfiles.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      {t('rankingWeights.noCustomProfiles', {
                        defaultValue: 'No custom profiles yet. Save your first profile!',
                      })}
                    </Typography>
                  </Box>
                ) : (
                  <Grid container spacing={3}>
                    {existingProfiles
                      .filter((p) => !p.is_preset)
                      .map((profile) => (
                        <Grid item xs={12} sm={6} md={4} key={profile.id}>
                          <Card
                            sx={{
                              cursor: 'pointer',
                              border: selectedProfile === profile.id ? '2px solid' : '1px solid',
                              borderColor:
                                selectedProfile === profile.id ? 'primary.main' : 'grey.300',
                              transition: 'all 0.3s',
                              '&:hover': {
                                boxShadow: 4,
                                borderColor: 'primary.main',
                              },
                            }}
                            onClick={() => loadProfile(profile)}
                          >
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                {profile.name}
                                {profile.is_active && (
                                  <Chip
                                    label={t('rankingWeights.active', { defaultValue: 'Active' })}
                                    size="small"
                                    color="success"
                                    sx={{ ml: 1 }}
                                  />
                                )}
                              </Typography>
                              {profile.description && (
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                  {profile.description}
                                </Typography>
                              )}
                              <Divider sx={{ my: 1 }} />
                              <Typography variant="caption" color="text.secondary">
                                {t('rankingWeights.lastUpdated', { defaultValue: 'Updated' })}:{' '}
                                {new Date(profile.updated_at).toLocaleDateString()}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                  </Grid>
                )}
              </TabPanel>

              {/* Панель 4: Превью влияния весов */}
              {showImpactPreview && (
                <TabPanel value={tabValue} index={3}>
                  <Stack spacing={3}>
                    {/* Vacancy ID input */}
                    {!previewVacancyId && (
                      <TextField
                        label={t('rankingWeights.vacancyId', { defaultValue: 'Vacancy ID' })}
                        value={previewVacancyId}
                        onChange={(e) => setPreviewVacancyId(e.target.value)}
                        fullWidth
                        helperText={t('rankingWeights.vacancyIdHelp', {
                          defaultValue: 'Enter a vacancy ID to preview ranking changes',
                        })}
                      />
                    )}

                    {/* Impact Preview Component */}
                    {previewVacancyId && savedWeights && (
                      <RankingWeightImpactPreview
                        vacancyId={previewVacancyId}
                        beforeWeights={weightsToDecimal(savedWeights)}
                        afterWeights={weightsToDecimal(weights)}
                      />
                    )}

                    {!savedWeights && (
                      <Alert severity="info">
                        {t('rankingWeights.noChangesYet', {
                          defaultValue:
                            'Adjust weights on the "Current Weights" tab to see impact preview',
                        })}
                      </Alert>
                    )}
                  </Stack>
                </TabPanel>
              )}
            </Paper>
          </>
        )}

        {/* Диалог сохранения профиля */}
        <Dialog
          open={showSaveDialog}
          onClose={() => setShowSaveDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            {t('rankingWeights.saveDialogTitle', { defaultValue: 'Save Ranking Weight Profile' })}
          </DialogTitle>
          <DialogContent>
            <Stack spacing={3} sx={{ mt: 2 }}>
              <TextField
                label={t('rankingWeights.profileName', { defaultValue: 'Profile Name' })}
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                fullWidth
                required
              />
              <TextField
                label={t('rankingWeights.profileDescription', { defaultValue: 'Description' })}
                value={profileDescription}
                onChange={(e) => setProfileDescription(e.target.value)}
                fullWidth
                multiline
                rows={3}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSaveDialog(false)}>
              {t('rankingWeights.cancel', { defaultValue: 'Cancel' })}
            </Button>
            <Button
              onClick={handleSave}
              variant="contained"
              disabled={!profileName || saving}
              startIcon={<SaveIcon />}
            >
              {saving
                ? t('rankingWeights.saving', { defaultValue: 'Saving...' })
                : t('rankingWeights.save', { defaultValue: 'Save' })}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </PageTransition>
  );
}

export default RankingWeightsPage;
