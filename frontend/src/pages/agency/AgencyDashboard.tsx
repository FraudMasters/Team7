import { Container, Box, Typography, Grid, Paper } from '@mui/material';
import {
  Business as BusinessIcon,
  People as PeopleIcon,
  Work as WorkIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { BentoCard } from '../../components/dashboard/BentoCard';
import { useAgencyAnalytics, useClientTenants } from '../../hooks/useAgencyData';

/**
 * Страница дашборда агентства
 *
 * Отображает ключевые метрики агентства: общее количество клиентов, активные клиенты,
 * количество кандидатов, размещения и доход. Использует MUI компоненты для отображения
 * карточек метрик в стиле Bento Grid с поддержкой мультитенантности.
 */
export function AgencyDashboard() {
  // Получаем аналитические данные агентства
  const { data: analytics } = useAgencyAnalytics();

  // Получаем данные о клиентских тенантах
  const { data: clientTenantsData } = useClientTenants();

  // Вычисляем количество активных клиентов
  const activeClientsCount =
    clientTenantsData?.client_tenants?.filter((tenant) => tenant.status === 'active').length || 0;

  // Вычисляем общее количество клиентов
  const totalClientsCount = clientTenantsData?.client_tenants?.length || 0;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Заголовок дашборда */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Agency Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's your multi-client overview.
        </Typography>
      </Box>

      {/* Сетка метрик в стиле Bento Grid */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Карточка с общим количеством клиентов */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Clients"
            value={analytics?.total_clients ?? totalClientsCount}
            subtitle="All clients"
            icon={<BusinessIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>

        {/* Карточка с количеством активных клиентов */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Active Clients"
            value={analytics?.active_clients ?? activeClientsCount}
            subtitle="Currently active"
            icon={<BusinessIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>

        {/* Карточка с общим количеством кандидатов */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Candidates"
            value={analytics?.total_candidates ?? '--'}
            subtitle="Across all clients"
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>

        {/* Карточка с количеством размещений */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Placements"
            value={analytics?.total_placements ?? '--'}
            subtitle="This month"
            icon={<WorkIcon sx={{ color: 'white' }} />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Дополнительные метрики */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Карточка с месячным доходом */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Monthly Revenue"
            value={
              analytics?.monthly_revenue
                ? `$${analytics.monthly_revenue.toLocaleString()}`
                : '--'
            }
            subtitle="This month"
            icon={<MoneyIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>
      </Grid>

      {/* Список клиентов (Client Performance) */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Client Performance
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Client performance metrics will be displayed here...
            </Typography>
          </Box>
        </Paper>
      </Grid>
    </Container>
  );
}
