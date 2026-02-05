/**
 * Страница анализа компенсаций
 *
 * Отображает анализ заработных плат и компенсационных пакетов:
 * - Распределение зарплат по позициям
 * - Сравнение с рынком
 * - Анализ бонусов и льгот
 * - Рекомендации по компенсации
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  LinearProgress,
} from '@mui/material';

// Импорт иконок MUI
import {
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';

// Интерфейс для данных о зарплате
interface SalaryData {
  position: string;
  min: number;
  median: number;
  max: number;
  currency: string;
}

// Интерфейс для сравнения с рынком
interface MarketComparison {
  position: string;
  our_salary: number;
  market_median: number;
  difference_percent: number;
}

// Интерфейс для структуры компенсации
interface CompensationBreakdown {
  category: string;
  amount: number;
  percentage: number;
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
 * Страница анализа компенсаций
 */
export function CompensationAnalysisPage() {
  // Состояние активной вкладки
  const [activeTab, setActiveTab] = useState(0);

  // Состояние фильтров
  const [selectedPosition, setSelectedPosition] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');

  // Состояние загрузки
  const [loading, setLoading] = useState(false);

  // Тестовые данные о зарплатах
  const salaryData: SalaryData[] = [
    { position: 'Senior React Developer', min: 80000, median: 110000, max: 150000, currency: 'USD' },
    { position: 'Product Manager', min: 90000, median: 125000, max: 170000, currency: 'USD' },
    { position: 'DevOps Engineer', min: 85000, median: 115000, max: 160000, currency: 'USD' },
  ];

  // Тестовые данные для сравнения с рынком
  const marketComparison: MarketComparison[] = [
    { position: 'Senior React Developer', our_salary: 110000, market_median: 105000, difference_percent: 4.8 },
    { position: 'Product Manager', our_salary: 125000, market_median: 130000, difference_percent: -3.8 },
    { position: 'DevOps Engineer', our_salary: 115000, market_median: 112000, difference_percent: 2.7 },
  ];

  // Тестовые данные структуры компенсации
  const compensationBreakdown: CompensationBreakdown[] = [
    { category: 'Base Salary', amount: 110000, percentage: 85 },
    { category: 'Bonus', amount: 15000, percentage: 11.5 },
    { category: 'Equity', amount: 5000, percentage: 3.5 },
  ];

  // Обработчик смены вкладки
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Compensation Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyze salary data, market positioning, and compensation structures
          </Typography>
        </Box>

        {/* Фильтры */}
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Position</InputLabel>
                <Select
                  value={selectedPosition}
                  label="Position"
                  onChange={(e) => setSelectedPosition(e.target.value)}
                >
                  <MenuItem value="">All Positions</MenuItem>
                  {salaryData.map((item) => (
                    <MenuItem key={item.position} value={item.position}>
                      {item.position}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Location</InputLabel>
                <Select
                  value={selectedLocation}
                  label="Location"
                  onChange={(e) => setSelectedLocation(e.target.value)}
                >
                  <MenuItem value="">All Locations</MenuItem>
                  <MenuItem value="remote">Remote</MenuItem>
                  <MenuItem value="ny">New York</MenuItem>
                  <MenuItem value="sf">San Francisco</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
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
                <Tab label="Salary Distribution" />
                <Tab label="Market Comparison" />
                <Tab label="Compensation Structure" />
                <Tab label="Recommendations" />
              </Tabs>

              {/* Вкладка "Распределение зарплат" */}
              <TabPanel value={activeTab} index={0}>
                <Grid container spacing={3}>
                  {salaryData.map((item) => (
                    <Grid item xs={12} md={4} key={item.position}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="h6" noWrap>
                              {item.position}
                            </Typography>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Min
                              </Typography>
                              <Typography variant="body1">
                                {item.min.toLocaleString()} {item.currency}
                              </Typography>
                            </Box>
                            <Box sx={{ bgcolor: 'primary.main', color: 'white', p: 2, borderRadius: 1 }}>
                              <Typography variant="caption" display="block">
                                Median
                              </Typography>
                              <Typography variant="h5" fontWeight={700}>
                                {item.median.toLocaleString()} {item.currency}
                              </Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Max
                              </Typography>
                              <Typography variant="body1">
                                {item.max.toLocaleString()} {item.currency}
                              </Typography>
                            </Box>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Вкладка "Сравнение с рынком" */}
              <TabPanel value={activeTab} index={1}>
                <Grid container spacing={2}>
                  {marketComparison.map((item) => (
                    <Grid item xs={12} md={4} key={item.position}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="h6" noWrap>
                              {item.position}
                            </Typography>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">
                                Our Salary
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                ${item.our_salary.toLocaleString()}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">
                                Market Median
                              </Typography>
                              <Typography variant="body2" fontWeight={600}>
                                ${item.market_median.toLocaleString()}
                              </Typography>
                            </Box>
                            <Chip
                              icon={item.difference_percent >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />}
                              label={`${item.difference_percent >= 0 ? '+' : ''}${item.difference_percent}% vs market`}
                              color={item.difference_percent >= 0 ? 'success' : 'warning'}
                              size="small"
                            />
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Вкладка "Структура компенсации" */}
              <TabPanel value={activeTab} index={2}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Compensation Breakdown
                        </Typography>
                        <Stack spacing={3}>
                          {compensationBreakdown.map((item) => (
                            <Box key={item.category}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">{item.category}</Typography>
                                <Typography variant="body2" fontWeight={600}>
                                  ${item.amount.toLocaleString()} ({item.percentage}%)
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={item.percentage}
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </Box>
                          ))}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* Вкладка "Рекомендации" */}
              <TabPanel value={activeTab} index={3}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ borderLeft: 4, borderColor: 'warning.main' }}>
                      <CardContent>
                        <Stack direction="row" spacing={2} alignItems="flex-start">
                          <LightbulbIcon color="warning" />
                          <Box>
                            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                              Review Product Manager Compensation
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Product Manager salaries are 3.8% below market median. Consider adjusting the range to remain competitive.
                            </Typography>
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ borderLeft: 4, borderColor: 'success.main' }}>
                      <CardContent>
                        <Stack direction="row" spacing={2} alignItems="flex-start">
                          <AssessmentIcon color="success" />
                          <Box>
                            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                              Strong Market Position
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Our compensation for technical roles is competitive. Current positioning is attracting quality candidates.
                            </Typography>
                          </Box>
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

export default CompensationAnalysisPage;
