/**
 * Страница состояния системы (System Health)
 *
 * Отображает статус работоспособности всех сервисов системы:
 * - Микросервисы (API Gateway, Vacancy Service, Candidate Service и др.)
 * - Базы данных
 * - Внешние API
 * - Метрики производительности
 * - Логи ошибок
 */

// Импорт хука эффекта React
import { useEffect, useState } from 'react';

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
  Button,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tab,
  Tabs,
} from '@mui/material';

// Импорт иконок MUI
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';

// Интерфейс статуса сервиса
interface ServiceStatus {
  name: string;
  type: 'microservice' | 'database' | 'external_api';
  status: 'healthy' | 'degraded' | 'down';
  response_time: number;
  uptime: number;
  last_check: string;
}

// Интерфейс метрики производительности
interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'critical';
  threshold: { warning: number; critical: number };
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
 * Страница состояния системы
 */
export function SystemHealthPage() {
  // Состояние активной вкладки
  const [activeTab, setActiveTab] = useState(0);

  // Состояние загрузки
  const [loading, setLoading] = useState(true);

  // Состояние обновления
  const [refreshing, setRefreshing] = useState(false);

  // Состояние статусов сервисов
  const [services, setServices] = useState<ServiceStatus[]>([]);

  // Состояние метрик производительности
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);

  // Загрузка данных о состоянии системы
  const loadHealthData = async () => {
    setLoading(true);
    try {
      // Имитация API вызова
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Тестовые данные сервисов
      setServices([
        {
          name: 'API Gateway',
          type: 'microservice',
          status: 'healthy',
          response_time: 45,
          uptime: 99.95,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Vacancy Service',
          type: 'microservice',
          status: 'healthy',
          response_time: 82,
          uptime: 99.8,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Candidate Service',
          type: 'microservice',
          status: 'degraded',
          response_time: 350,
          uptime: 98.5,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Matching Service',
          type: 'microservice',
          status: 'healthy',
          response_time: 156,
          uptime: 99.2,
          last_check: new Date().toISOString(),
        },
        {
          name: 'PostgreSQL - Main',
          type: 'database',
          status: 'healthy',
          response_time: 12,
          uptime: 99.99,
          last_check: new Date().toISOString(),
        },
        {
          name: 'Redis - Cache',
          type: 'database',
          status: 'healthy',
          response_time: 2,
          uptime: 99.95,
          last_check: new Date().toISOString(),
        },
        {
          name: 'OpenAI API',
          type: 'external_api',
          status: 'healthy',
          response_time: 520,
          uptime: 99.0,
          last_check: new Date().toISOString(),
        },
      ]);

      // Тестовые данные метрик
      setMetrics([
        {
          name: 'CPU Usage',
          value: 45,
          unit: '%',
          status: 'good',
          threshold: { warning: 70, critical: 90 },
        },
        {
          name: 'Memory Usage',
          value: 62,
          unit: '%',
          status: 'good',
          threshold: { warning: 80, critical: 95 },
        },
        {
          name: 'Disk Usage',
          value: 55,
          unit: '%',
          status: 'good',
          threshold: { warning: 80, critical: 90 },
        },
        {
          name: 'Request Rate',
          value: 245,
          unit: 'req/min',
          status: 'good',
          threshold: { warning: 500, critical: 1000 },
        },
      ]);
    } catch (error) {
      console.error('Failed to load health data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    loadHealthData();
  }, []);

  // Обработчик обновления
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadHealthData();
    setRefreshing(false);
  };

  // Обработчик смены вкладки
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Получить иконку статуса
  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckIcon color="success" />;
      case 'degraded':
        return <WarningIcon color="warning" />;
      case 'down':
        return <ErrorIcon color="error" />;
    }
  };

  // Получить цвет для метрики
  const getMetricColor = (status: PerformanceMetric['status']) => {
    switch (status) {
      case 'good':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
    }
  };

  // Подсчитать общее состояние
  const healthSummary = {
    total: services.length,
    healthy: services.filter((s) => s.status === 'healthy').length,
    degraded: services.filter((s) => s.status === 'degraded').length,
    down: services.filter((s) => s.status === 'down').length,
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      <Stack spacing={4}>
        {/* Заголовок страницы */}
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" fontWeight={700}>
              System Health
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitor the status and performance of all system services
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            Refresh
          </Button>
        </Stack>

        {/* Сводка состояния */}
        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <CheckIcon color="success" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="success.main">
                      {healthSummary.healthy}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Healthy</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <WarningIcon color="warning" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="warning.main">
                      {healthSummary.degraded}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Degraded</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <ErrorIcon color="error" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="error.main">
                      {healthSummary.down}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Down</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <SpeedIcon color="action" sx={{ fontSize: 40 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700}>
                      {services.length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">Total Services</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Состояние загрузки */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Предупреждение о проблемах */}
            {healthSummary.degraded > 0 && (
              <Alert severity="warning">
                {healthSummary.degraded} service(s) are operating in degraded mode. Please investigate.
              </Alert>
            )}
            {healthSummary.down > 0 && (
              <Alert severity="error">
                {healthSummary.down} service(s) are down. Immediate attention required.
              </Alert>
            )}

            {/* Вкладки */}
            <Paper sx={{ width: '100%' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Services" />
                <Tab label="Performance" />
                <Tab label="Logs" />
              </Tabs>

              {/* Вкладка "Сервисы" */}
              <TabPanel value={activeTab} index={0}>
                <List>
                  {services.map((service, index) => (
                    <React.Fragment key={service.name}>
                      <ListItem>
                        <ListItemIcon>
                          {service.type === 'microservice' && <CloudIcon />}
                          {service.type === 'database' && <StorageIcon />}
                          {service.type === 'external_api' && <MemoryIcon />}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="subtitle1" fontWeight={600}>
                                {service.name}
                              </Typography>
                              <Chip
                                label={service.status}
                                color={service.status === 'healthy' ? 'success' : service.status === 'degraded' ? 'warning' : 'error'}
                                size="small"
                              />
                            </Stack>
                          }
                          secondary={
                            <Stack spacing={0.5}>
                              <Typography variant="caption">
                                Response: {service.response_time}ms | Uptime: {service.uptime}%
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Last check: {new Date(service.last_check).toLocaleString()}
                              </Typography>
                            </Stack>
                          }
                        />
                        <ListItemIcon sx={{ justifyContent: 'flex-end' }}>
                          {getStatusIcon(service.status)}
                        </ListItemIcon>
                      </ListItem>
                      {index < services.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </TabPanel>

              {/* Вкладка "Производительность" */}
              <TabPanel value={activeTab} index={1}>
                <Grid container spacing={3}>
                  {metrics.map((metric) => (
                    <Grid item xs={12} sm={6} md={3} key={metric.name}>
                      <Card>
                        <CardContent>
                          <Stack spacing={2}>
                            <Typography variant="body2" color="text.secondary">
                              {metric.name}
                            </Typography>
                            <Typography variant="h4" fontWeight={700} color={`${getMetricColor(metric.status)}.main` as any}>
                              {metric.value}
                              <Typography variant="body1" component="span" color="text.secondary">
                                {metric.unit}
                              </Typography>
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={metric.unit === '%' ? metric.value : (metric.value / metric.threshold.critical) * 100}
                              color={getMetricColor(metric.status) as any}
                            />
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>

              {/* Вкладка "Логи" */}
              <TabPanel value={activeTab} index={2}>
                <Paper sx={{ p: 2, bgcolor: 'grey.900', color: 'grey.100' }}>
                  <Typography variant="caption" component="div">
                    {`[${new Date().toISOString()}] INFO System health check completed\n` +
                    `[${new Date().toISOString()}] WARNING Candidate Service response time elevated (350ms)\n` +
                    `[${new Date().toISOString()}] INFO All databases operational\n` +
                    `[${new Date().toISOString()}] INFO External API services responsive`}
                  </Typography>
                </Paper>
              </TabPanel>
            </Paper>
          </>
        )}
      </Stack>
    </Container>
  );
}

export default SystemHealthPage;
