/**
 * Страница расширенной аналитики для рекрутера
 *
 * Отображает продвинутую аналитику и метрики рекрутинга:
 * - Воронка найма с конверсией на каждом этапе
 * - Time-to-fill по вакансиям
 * - Эффективность источников кандидатов
 * - Анализ качества наемных сотрудников
 */

// Импорт хуков React
import { useState, useEffect } from 'react';

// Импорт компонентов MUI
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Tab,
  Tabs,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
} from '@mui/material';

// Импорт иконок MUI
import {
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

// Импорт API клиента и типов
import { analyticsClient, type FunnelMetricsResponse, type SourceTrackingResponse } from '@/api/analytics';

// Интерфейс для метрик воронки
interface FunnelMetrics {
  stage: string;
  count: number;
  conversion_rate: number;
}

// Интерфейс для метрик времени найма
interface TimeToFillMetrics {
  vacancy_id: string;
  vacancy_title: string;
  days: number;
}

// Интерфейс для эффективности источников
interface SourceMetrics {
  source: string;
  candidates: number;
  hires: number;
  conversion_rate: number;
}

// Интерфейс для метрик производительности рекрутера
interface RecruiterPerformanceMetrics {
  total_candidates_processed: number;
  total_interviews_conducted: number;
  successful_hires: number;
  success_rate: number;
  avg_time_per_candidate: number;
  interview_completion_rate: number;
}

/**
 * Компонент панели вкладок
 */
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Страница расширенной аналитики для рекрутера
 */
export function AdvancedAnalyticsPage() {
  // Состояние активной вкладки
  const [activeTab, setActiveTab] = useState(0);

  // Состояние периода времени для фильтрации
  const [timePeriod, setTimePeriod] = useState('30d');

  // Состояние загрузки данных
  const [loading, setLoading] = useState(false);

  // Состояние ошибки
  const [error, setError] = useState<string | null>(null);

  // Состояние данных воронки найма
  const [funnelData, setFunnelData] = useState<FunnelMetricsResponse | null>(null);

  // Состояние данных источников кандидатов
  const [sourceData, setSourceData] = useState<SourceTrackingResponse | null>(null);

  // Тестовые данные для времени найма (не реализовано в этом подзадании)
  const timeToFillData: TimeToFillMetrics[] = [
    { vacancy_id: '1', vacancy_title: 'Senior React Developer', days: 28 },
    { vacancy_id: '2', vacancy_title: 'Product Manager', days: 35 },
    { vacancy_id: '3', vacancy_title: 'DevOps Engineer', days: 21 },
  ];

  // Тестовые данные для производительности рекрутера (не реализовано в этом подзадании)
  const recruiterPerformanceData: RecruiterPerformanceMetrics = {
    total_candidates_processed: 156,
    total_interviews_conducted: 48,
    successful_hires: 12,
    success_rate: 7.7,
    avg_time_per_candidate: 4.2,
    interview_completion_rate: 92.5,
  };

  // Загрузка данных при монтировании и изменении периода
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Вычисляем даты на основе выбранного периода
        const endDate = new Date();
        const startDate = new Date();

        switch (timePeriod) {
          case '7d':
            startDate.setDate(endDate.getDate() - 7);
            break;
          case '30d':
            startDate.setDate(endDate.getDate() - 30);
            break;
          case '90d':
            startDate.setDate(endDate.getDate() - 90);
            break;
          case '1y':
            startDate.setFullYear(endDate.getFullYear() - 1);
            break;
        }

        const startDateStr = startDate.toISOString().split('T')[0];
        const endDateStr = endDate.toISOString().split('T')[0];

        // Параллельная загрузка данных воронки и источников
        const [funnelResponse, sourceResponse] = await Promise.all([
          analyticsClient.getFunnelMetrics(startDateStr, endDateStr),
          analyticsClient.getSourceTracking(startDateStr, endDateStr),
        ]);

        setFunnelData(funnelResponse);
        setSourceData(sourceResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки данных аналитики');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timePeriod]);

  // Обработчик смены вкладки
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Обработчик изменения периода
  const handlePeriodChange = (event: { target: { value: unknown } }) => {
    setTimePeriod(event.target.value as string);
  };

  // Обработчик экспорта отчета
  const handleExport = () => {
    // TODO: Implement export functionality
  };

  // Форматирование названия этапа для отображения
  const formatStageName = (stageName: string): string => {
    const stageNames: Record<string, string> = {
      uploaded: 'Uploaded',
      analyzed: 'Analyzed',
      screening: 'Screening',
      interview: 'Interview',
      technical: 'Technical',
      offer: 'Offer',
      hired: 'Hired',
    };
    return stageNames[stageName] || stageName;
  };

  // Форматирование названия источника для отображения
  const formatSourceName = (source: string): string => {
    if (source === 'unknown') return 'Unknown';
    return source.charAt(0).toUpperCase() + source.slice(1);
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" fontWeight={700}>
              Advanced Analytics
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Deep insights into your recruiting performance
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            Export Report
          </Button>
        </Stack>

        {/* Фильтры */}
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={timePeriod}
                label="Time Period"
                onChange={handlePeriodChange}
              >
                <MenuItem value="7d">Last 7 days</MenuItem>
                <MenuItem value="30d">Last 30 days</MenuItem>
                <MenuItem value="90d">Last 90 days</MenuItem>
                <MenuItem value="1y">Last year</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </Paper>

        {/* Отображение ошибки */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Состояние загрузки */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Вкладки аналитики */}
            <Paper sx={{ width: '100%' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Hiring Funnel" />
                <Tab label="Time to Fill" />
                <Tab label="Source Effectiveness" />
                <Tab label="Quality Metrics" />
                <Tab label="Recruiter Performance" />
              </Tabs>

              {/* Вкладка "Воронка найма" */}
              <TabPanel value={activeTab} index={0}>
                {funnelData && funnelData.stages.length > 0 ? (
                  <Grid container spacing={3}>
                    {funnelData.stages.map((stage) => (
                      <Grid item xs={12} sm={6} md={2.4} key={stage.stage_name}>
                        <Card>
                          <CardContent>
                            <Stack spacing={2}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <PeopleIcon color="primary" />
                                <Typography variant="caption" color="text.secondary">
                                  {formatStageName(stage.stage_name)}
                                </Typography>
                              </Box>
                              <Typography variant="h4" fontWeight={700}>
                                {stage.count}
                              </Typography>
                              <Typography variant="body2" color="success.main">
                                {(stage.conversion_rate_from_start * 100).toFixed(1)}% from start
                              </Typography>
                              {stage.conversion_rate_from_previous !== null && (
                                <Typography variant="caption" color="text.secondary">
                                  {(stage.conversion_rate_from_previous * 100).toFixed(1)}% from previous
                                </Typography>
                              )}
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Box sx={{ py: 4, textAlign: 'center' }}>
                    <Typography color="text.secondary">
                      Нет данных о воронке найма за выбранный период
                    </Typography>
                  </Box>
                )}
              </TabPanel>

              {/* Вкладка "Время найма" */}
              <TabPanel value={activeTab} index={1}>
                <Grid container spacing={2}>
                  {timeToFillData.map((item) => (
                    <Grid item xs={12} md={4} key={item.vacancy_id}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ScheduleIcon color="action" />
                              <Typography variant="h6">
                                {item.days} days
                              </Typography>
                            </Box>
                            <Typography variant="body1" fontWeight={600}>
                              {item.vacancy_title}
                            </Typography>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Вкладка "Эффективность источников" */}
              <TabPanel value={activeTab} index={2}>
                {sourceData && sourceData.sources.length > 0 ? (
                  <Grid container spacing={2}>
                    {sourceData.sources.map((source, index) => (
                      <Grid item xs={12} sm={6} md={3} key={index}>
                        <Card>
                          <CardContent>
                            <Stack spacing={2}>
                              <Typography variant="h6" noWrap>
                                {formatSourceName(source.source)}
                              </Typography>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2" color="text.secondary">
                                  Candidates
                                </Typography>
                                <Typography variant="body2" fontWeight={600}>
                                  {source.candidate_count}
                                </Typography>
                              </Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2" color="text.secondary">
                                  Hires
                                </Typography>
                                <Typography variant="body2" fontWeight={600}>
                                  {source.hired_count}
                                </Typography>
                              </Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2" color="text.secondary">
                                  Conversion
                                </Typography>
                                <Typography variant="body2" color="success.main" fontWeight={600}>
                                  {(source.conversion_rate * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Box sx={{ py: 4, textAlign: 'center' }}>
                    <Typography color="text.secondary">
                      Нет данных об источниках кандидатов за выбранный период
                    </Typography>
                  </Box>
                )}
              </TabPanel>

              {/* Вкладка "Метрики качества" */}
              <TabPanel value={activeTab} index={3}>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AssessmentIcon color="primary" />
                            <Typography variant="h6">
                              4.2
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Avg. Interview Score
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TrendingUpIcon color="success" />
                            <Typography variant="h6">
                              92%
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Retention Rate (90d)
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PeopleIcon color="action" />
                            <Typography variant="h6">
                              8.5
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Avg. Time to Productivity
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* Вкладка "Производительность рекрутера" */}
              <TabPanel value={activeTab} index={4}>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PeopleIcon color="primary" />
                            <Typography variant="caption" color="text.secondary">
                              Total Candidates Processed
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.total_candidates_processed}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AssessmentIcon color="info" />
                            <Typography variant="caption" color="text.secondary">
                              Interviews Conducted
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.total_interviews_conducted}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TrendingUpIcon color="success" />
                            <Typography variant="caption" color="text.secondary">
                              Successful Hires
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.successful_hires}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TrendingUpIcon color="success" />
                            <Typography variant="caption" color="text.secondary">
                              Success Rate
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.success_rate.toFixed(1)}%
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ScheduleIcon color="action" />
                            <Typography variant="caption" color="text.secondary">
                              Avg. Time per Candidate
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.avg_time_per_candidate.toFixed(1)} days
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Stack spacing={2}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AssessmentIcon color="primary" />
                            <Typography variant="caption" color="text.secondary">
                              Interview Completion Rate
                            </Typography>
                          </Box>
                          <Typography variant="h4" fontWeight={700}>
                            {recruiterPerformanceData.interview_completion_rate.toFixed(1)}%
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </TabPanel>
            </Paper>
          </>
        )}
      </Stack>
    </Container>
  );
}

export default AdvancedAnalyticsPage;
