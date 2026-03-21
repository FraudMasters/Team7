/**
 * Страница аналитики поисковых запросов
 *
 * Отображает статистику и аналитику по поисковым запросам рекрутеров,
 * включая популярные запросы, запросы с нулевыми результатами и тренды.
 */

// Импорт компонентов MUI
import {
  Box,
  Container,
  Typography,
  Stack,
} from '@mui/material';

// Импорт иконок MUI
import {
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';

// Импорт компонента аналитики
import { SearchAnalytics } from '../../components/SearchAnalytics';

// Импорт хука для определения размеров экрана
import { useBreakpoints } from '../../hooks';

// Импорт контекста аутентификации
import { useAuthContext } from '../../contexts/AuthContext';

// Импорт контекста организации
import { useOrganizationContext } from '../../contexts/OrganizationContext';

export function SearchAnalyticsPage() {
  // Определяем, мобильное ли устройство
  const { isMobile } = useBreakpoints();

  // Получаем данные пользователя для проверки роли администратора
  const { hasRole } = useAuthContext();

  // Получаем ID организации
  const { organization } = useOrganizationContext();

  // Проверяем, является ли пользователь администратором
  const isAdmin = hasRole('Admin');

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Заголовок страницы */}
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 4 }}>
        <AnalyticsIcon
          sx={{
            fontSize: isMobile ? 32 : 40,
            color: 'primary.main',
          }}
        />
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight={700}>
            Search Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Insights into recruiter search patterns and performance
          </Typography>
        </Box>
      </Stack>

      {/* Компонент аналитики */}
      <SearchAnalytics
        limit={15}
        isAdmin={isAdmin}
        organizationId={organization?.id}
      />
    </Container>
  );
}

export default SearchAnalyticsPage;
