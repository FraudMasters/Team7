/**
 * Страница настройки весов соответствия для рекрутера
 *
 * Позволяет рекрутерам настраивать относительные веса алгоритмов сопоставления:
 * ключевое слово, TF-IDF и векторная схожесть. Включает пресеты профиля
 * для различных типов ролей (технические, творческие, управленческие).
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
import { apiClient } from '@/api/client';
import type {
  PresetProfile,
  MatchingWeightsProfile,
  MatchingWeightsCreate,
} from '@/types/api';

// Импорт компонентов для слайдеров весов
import { WeightSliderCardStack } from '@/components/WeightSliderCard';

// Импорт MUI компонента анимации переходов
import { PageTransition } from '@components/mui/PageTransition';

// Интерфейс состояния весов
interface WeightState {
  keyword: number;
  tfidf: number;
  vector: number;
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
 */
const PRESETS: Record<string, WeightState> = {
  // Технические роли - упор на ключевые навыки
  technical: { keyword: 60, tfidf: 25, vector: 15 },
  // Творческие роли - упор на семантическое понимание
  creative: { keyword: 20, tfidf: 25, vector: 55 },
  // Управленческие роли - сбалансированный подход
  executive: { keyword: 33, tfidf: 34, vector: 33 },
  // Сбалансированный профиль
  balanced: { keyword: 34, tfidf: 33, vector: 33 },
};

/**
 * Страница настройки весов соответствия для рекрутера
 */
function WeightsPage() {
  const { t } = useTranslation();

  // Состояние весов алгоритмов сопоставления
  const [weights, setWeights] = useState<WeightState>({
    keyword: 50,
    tfidf: 30,
    vector: 20,
  });

  // Состояния UI
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // Состояние кастомного профиля
  const [profileName, setProfileName] = useState('');
  const [profileDescription, setProfileDescription] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Существующие профили
  const [existingProfiles, setExistingProfiles] = useState<MatchingWeightsProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);

  // Пресеты из API
  const [presets, setPresets] = useState<PresetProfile[]>([]);

  /**
   * Вычисляем общий процент веса
   */
  const totalWeight = weights.keyword + weights.tfidf + weights.vector;

  /**
   * Проверяем, что веса валидны (сумма равна 100)
   */
  const isValid = Math.abs(totalWeight - 100) < 1;

  /**
   * Обработчик изменения веса
   */
  const handleWeightChange = useCallback((type: 'keyword' | 'tfidf' | 'vector', value: number) => {
    setWeights((prev) => ({
      ...prev,
      [type]: value,
    }));
    setSuccess(false);
  }, []);

  /**
   * Применить пресет весов
   */
  const applyPreset = useCallback((presetKey: string) => {
    const preset = PRESETS[presetKey];
    if (preset) {
      setWeights(preset);
      setSuccess(false);
    }
  }, []);

  /**
   * Нормализовать веса, чтобы сумма была равна 100
   */
  const normalizeWeights = useCallback(() => {
    if (totalWeight === 0) return;

    const normalized = {
      keyword: Math.round((weights.keyword / totalWeight) * 100),
      tfidf: Math.round((weights.tfidf / totalWeight) * 100),
      vector: Math.round((weights.vector / totalWeight) * 100),
    };

    // Корректировка ошибок округления
    const normalizedTotal = normalized.keyword + normalized.tfidf + normalized.vector;
    if (normalizedTotal !== 100) {
      normalized.vector += (100 - normalizedTotal);
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
        apiClient.listWeightProfiles(),
        apiClient.getPresetProfiles(),
      ]);

      setExistingProfiles(profilesResult.profiles);
      setPresets(presetsResult.presets);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load profiles';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Сохранить профиль
   */
  const handleSaveProfile = useCallback(async () => {
    if (!profileName.trim()) {
      setError(t('matchingWeights.errors.nameRequired', { defaultValue: 'Profile name is required' }));
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const createData: MatchingWeightsCreate = {
        name: profileName,
        description: profileDescription || undefined,
        keyword_weight: weights.keyword / 100,
        tfidf_weight: weights.tfidf / 100,
        vector_weight: weights.vector / 100,
        change_reason: 'Created from weight customization UI',
      };

      await apiClient.createWeightProfile(createData);

      setSuccess(true);
      setShowSaveDialog(false);
      setProfileName('');
      setProfileDescription('');
      loadProfiles();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save profile';
      setError(message);
    } finally {
      setSaving(false);
    }
  }, [profileName, profileDescription, weights, t, loadProfiles]);

  /**
   * Загрузить существующий профиль
   */
  const loadExistingProfile = useCallback((profileId: string) => {
    const profile = existingProfiles.find((p) => p.id === profileId);
    if (profile) {
      setWeights({
        keyword: profile.weights_percentage.keyword,
        tfidf: profile.weights_percentage.tfidf,
        vector: profile.weights_percentage.vector,
      });
      setSelectedProfile(profileId);
    }
  }, [existingProfiles]);

  // Загружаем профили при монтировании компонента
  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Box>
          <Typography variant="h4" gutterBottom>
            <TuneIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            {t('matchingWeights.title', { defaultValue: 'Matching Algorithm Weights' })}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('matchingWeights.subtitle', {
              defaultValue: 'Customize how the matching algorithm scores candidates. Adjust the relative importance of each matching method.',
            })}
          </Typography>
        </Box>

        {/* Предупреждение об ошибке */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Сообщение об успехе */}
        {success && (
          <Alert
            severity="success"
            icon={<SuccessIcon />}
            onClose={() => setSuccess(false)}
          >
            {t('matchingWeights.success.saved', { defaultValue: 'Weights saved successfully!' })}
          </Alert>
        )}

        {/* Состояние загрузки */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Отображение распределения весов */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                {t('matchingWeights.currentDistribution', { defaultValue: 'Current Weight Distribution' })}
              </Typography>

              {/* Визуализация прогресс-барами */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ flex: 1, mr: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(weights.keyword / totalWeight) * 100}
                      sx={{
                        backgroundColor: '#E3F2FD',
                        '& .MuiLinearProgress-bar': { backgroundColor: '#2196F3' },
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                    {t('matchingWeights.keyword.label', { defaultValue: 'Keyword' })}: {weights.keyword}%
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ flex: 1, mr: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(weights.tfidf / totalWeight) * 100}
                      sx={{
                        backgroundColor: '#FFF3E0',
                        '& .MuiLinearProgress-bar': { backgroundColor: '#FF9800' },
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                    {t('matchingWeights.tfidf.label', { defaultValue: 'TF-IDF' })}: {weights.tfidf}%
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ flex: 1, mr: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(weights.vector / totalWeight) * 100}
                      sx={{
                        backgroundColor: '#F3E5F5',
                        '& .MuiLinearProgress-bar': { backgroundColor: '#9C27B0' },
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
                    {t('matchingWeights.vector.label', { defaultValue: 'Vector' })}: {weights.vector}%
                  </Typography>
                </Box>
              </Box>

              {/* Предупреждение о валидации */}
              {!isValid && (
                <Alert
                  severity="warning"
                  icon={<WarningIcon />}
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={normalizeWeights}
                    >
                      {t('matchingWeights.normalize', { defaultValue: 'Normalize to 100%' })}
                    </Button>
                  }
                >
                  {t('matchingWeights.errors.not100', {
                    defaultValue: `Weights must sum to 100% (currently: ${totalWeight}%)`,
                  })}
                </Alert>
              )}

              {/* Отображение суммы */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                <Typography variant="subtitle2">
                  {t('matchingWeights.totalWeight', { defaultValue: 'Total Weight' })}:
                </Typography>
                <Chip
                  label={`${totalWeight}%`}
                  color={isValid ? 'success' : 'warning'}
                  variant={isValid ? 'filled' : 'outlined'}
                />
              </Box>
            </Paper>

            {/* Вкладки для пресетов и кастомных настроек */}
            <Paper sx={{ width: '100%' }}>
              <Tabs
                value={tabValue}
                onChange={(_, newValue) => setTabValue(newValue)}
                variant="fullWidth"
              >
                <Tab
                  icon={<PresetIcon />}
                  label={t('matchingWeights.tabs.presets', { defaultValue: 'Presets' })}
                />
                <Tab
                  icon={<TuneIcon />}
                  label={t('matchingWeights.tabs.custom', { defaultValue: 'Custom' })}
                />
                <Tab
                  icon={<HistoryIcon />}
                  label={t('matchingWeights.tabs.saved', { defaultValue: 'Saved Profiles' })}
                  disabled={existingProfiles.length === 0}
                />
              </Tabs>

              {/* Вкладка пресетов */}
              <TabPanel value={tabValue} index={0}>
                <Grid container spacing={2}>
                  {Object.entries(PRESETS).map(([key, preset]) => (
                    <Grid item xs={12} sm={6} md={3} key={key}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          border: '2px solid transparent',
                          '&:hover': {
                            borderColor: 'primary.main',
                            transform: 'translateY(-4px)',
                          },
                        }}
                        onClick={() => applyPreset(key)}
                      >
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {t(`matchingWeights.presets.${key}.name`, {
                              defaultValue: key.charAt(0).toUpperCase() + key.slice(1),
                            })}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                            <Chip
                              label={`${t('matchingWeights.keyword.label', { defaultValue: 'Keyword' })}: ${preset.keyword}%`}
                              size="small"
                              sx={{ backgroundColor: '#E3F2FD' }}
                            />
                            <Chip
                              label={`${t('matchingWeights.tfidf.label', { defaultValue: 'TF-IDF' })}: ${preset.tfidf}%`}
                              size="small"
                              sx={{ backgroundColor: '#FFF3E0' }}
                            />
                            <Chip
                              label={`${t('matchingWeights.vector.label', { defaultValue: 'Vector' })}: ${preset.vector}%`}
                              size="small"
                              sx={{ backgroundColor: '#F3E5F5' }}
                            />
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {t(`matchingWeights.presets.${key}.description`, {
                              defaultValue: 'Preset description',
                            })}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Вкладка кастомных настроек */}
              <TabPanel value={tabValue} index={1}>
                <Stack spacing={4}>
                  <WeightSliderCardStack
                    weights={weights}
                    onWeightChange={handleWeightChange}
                    disabled={false}
                  />

                  {/* Кнопки действий */}
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                    <Button
                      variant="outlined"
                      onClick={normalizeWeights}
                      disabled={isValid}
                    >
                      {t('matchingWeights.normalize', { defaultValue: 'Normalize' })}
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<SaveIcon />}
                      onClick={() => setShowSaveDialog(true)}
                      disabled={!isValid}
                    >
                      {t('matchingWeights.saveProfile', { defaultValue: 'Save as Profile' })}
                    </Button>
                  </Box>
                </Stack>
              </TabPanel>

              {/* Вкладка сохраненных профилей */}
              <TabPanel value={tabValue} index={2}>
                <Grid container spacing={2}>
                  {existingProfiles.map((profile) => (
                    <Grid item xs={12} sm={6} md={4} key={profile.id}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          border: selectedProfile === profile.id ? '2px solid primary.main' : '2px solid transparent',
                          '&:hover': {
                            borderColor: 'primary.main',
                          },
                        }}
                        onClick={() => loadExistingProfile(profile.id)}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="h6">
                              {profile.name}
                            </Typography>
                            {profile.is_preset && (
                              <Chip label={t('matchingWeights.preset', { defaultValue: 'Preset' })} size="small" />
                            )}
                          </Box>
                          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                            <Chip label={`K: ${profile.weights_percentage.keyword}%`} size="small" />
                            <Chip label={`T: ${profile.weights_percentage.tfidf}%`} size="small" />
                            <Chip label={`V: ${profile.weights_percentage.vector}%`} size="small" />
                          </Box>
                          {profile.description && (
                            <Typography variant="caption" color="text.secondary">
                              {profile.description}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>
            </Paper>

            {/* Раздел с объяснением */}
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                {t('matchingWeights.explanation.title', { defaultValue: 'Understanding the Weights' })}
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, backgroundColor: '#E3F2FD', borderRadius: 1 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      {t('matchingWeights.keyword.label', { defaultValue: 'Keyword Matching' })}
                    </Typography>
                    <Typography variant="body2">
                      {t('matchingWeights.keyword.explanation', {
                        defaultValue: 'Direct skill matching including synonyms, fuzzy matching, and compound skills. Best for technical roles where exact skills matter.',
                      })}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, backgroundColor: '#FFF3E0', borderRadius: 1 }}>
                    <Typography variant="subtitle2" sx={{ color: '#FF9800' }} gutterBottom>
                      {t('matchingWeights.tfidf.label', { defaultValue: 'TF-IDF Matching' })}
                    </Typography>
                    <Typography variant="body2">
                      {t('matchingWeights.tfidf.explanation', {
                        defaultValue: 'Weighted scoring based on keyword importance in the job description. Good for identifying critical requirements.',
                      })}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, backgroundColor: '#F3E5F5', borderRadius: 1 }}>
                    <Typography variant="subtitle2" sx={{ color: '#9C27B0' }} gutterBottom>
                      {t('matchingWeights.vector.label', { defaultValue: 'Vector Similarity' })}
                    </Typography>
                    <Typography variant="body2">
                      {t('matchingWeights.vector.explanation', {
                        defaultValue: 'Semantic similarity using AI embeddings. Best for creative roles where conceptual understanding matters most.',
                      })}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </>
        )}

        {/* Диалог сохранения профиля */}
        <Dialog open={showSaveDialog} onClose={() => setShowSaveDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {t('matchingWeights.saveDialog.title', { defaultValue: 'Save as Custom Profile' })}
          </DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 2 }}>
              <TextField
                fullWidth
                label={t('matchingWeights.saveDialog.name', { defaultValue: 'Profile Name' })}
                placeholder={t('matchingWeights.saveDialog.namePlaceholder', {
                  defaultValue: 'e.g., My Technical Role Profile',
                })}
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                autoFocus
              />
              <TextField
                fullWidth
                multiline
                rows={2}
                label={t('matchingWeights.saveDialog.description', { defaultValue: 'Description (Optional)' })}
                placeholder={t('matchingWeights.saveDialog.descriptionPlaceholder', {
                  defaultValue: 'When should this profile be used?',
                })}
                value={profileDescription}
                onChange={(e) => setProfileDescription(e.target.value)}
              />
              <Box sx={{ p: 2, backgroundColor: 'grey.100', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t('matchingWeights.saveDialog.preview', { defaultValue: 'Weights to save:' })}
                </Typography>
                <Typography variant="body2">
                  Keyword: {weights.keyword}%, TF-IDF: {weights.tfidf}%, Vector: {weights.vector}%
                </Typography>
              </Box>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSaveDialog(false)}>
              {t('matchingWeights.cancel', { defaultValue: 'Cancel' })}
            </Button>
            <Button
              onClick={handleSaveProfile}
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={!profileName.trim() || saving}
            >
              {saving
                ? t('matchingWeights.saving', { defaultValue: 'Saving...' })
                : t('matchingWeights.save', { defaultValue: 'Save' })}
            </Button>
          </DialogActions>
        </Dialog>
      </Stack>
      </Container>
    </PageTransition>
  );
}

export default WeightsPage;
export { WeightsPage };
