/**
 * Страница расширенной аналитики для рекрутера
 *
 * Отображает продвинутую аналитику и метрики рекрутинга:
 * - Воронка найма с конверсией на каждом этапе
 * - Time-to-fill по вакансиям
 * - Эффективность источников кандидатов
 * - Анализ качества наемных сотрудников
 */

// Импорт хука состояния React
import { useState } from 'react';

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
} from '@mui/material';

// Импорт иконок MUI
import {
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

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

  // Тестовые данные для воронки найма
  const funnelData: FunnelMetrics[] = [
    { stage: 'Applied', count: 450, conversion_rate: 100 },
    { stage: 'Screened', count: 180, conversion_rate: 40 },
    { stage: 'Interview', count: 90, conversion_rate: 50 },
    { stage: 'Offer', count: 45, conversion_rate: 50 },
    { stage: 'Hired', count: 35, conversion_rate: 78 },
  ];

  // Тестовые данные для времени найма
  const timeToFillData: TimeToFillMetrics[] = [
    { vacancy_id: '1', vacancy_title: 'Senior React Developer', days: 28 },
    { vacancy_id: '2', vacancy_title: 'Product Manager', days: 35 },
    { vacancy_id: '3', vacancy_title: 'DevOps Engineer', days: 21 },
  ];

  // Тестовые данные для эффективности источников
  const sourceData: SourceMetrics[] = [
    { source: 'LinkedIn', candidates: 150, hires: 20, conversion_rate: 13.3 },
    { source: 'Indeed', candidates: 200, hires: 10, conversion_rate: 5.0 },
    { source: 'Referral', candidates: 50, hires: 15, conversion_rate: 30.0 },
    { source: 'Direct', candidates: 50, hires: 5, conversion_rate: 10.0 },
  ];

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
    console.log('Exporting analytics report...');
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
              </Tabs>

              {/* Вкладка "Воронка найма" */}
              <TabPanel value={activeTab} index={0}>
                <Grid container spacing={3}>
                  {funnelData.map((item) => (
                    <Grid item xs={12} sm={6} md={2.4} key={item.stage}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <PeopleIcon color="primary" />
                              <Typography variant="caption" color="text.secondary">
                                {item.stage}
                              </Typography>
                            </Box>
                            <Typography variant="h4" fontWeight={700}>
                              {item.count}
                            </Typography>
                            <Typography variant="body2" color="success.main">
                              {item.conversion_rate}% conversion
                            </Typography>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
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
                <Grid container spacing={2}>
                  {sourceData.map((item, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="h6" noWrap>
                              {item.source}
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">
                                Candidates
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {item.candidates}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">
                                Hires
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                {item.hires}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">
                                Conversion
                              </Typography>
                              <Typography variant="body2" color="success.main" fontWeight={600}>
                                {item.conversion_rate}%
                              </Typography>
                            </Box>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
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
            </Paper>
          </>
        )}
      </Stack>
    </Container>
  );
}

export default AdvancedAnalyticsPage;
