/**
 * Communication History Page
 *
 * Кандидатский портал для просмотра истории всех коммуникаций.
 * Предоставляет следующие возможности:
 * - Просмотр всех коммуникаций (email, SMS, звонки, системные сообщения)
 * - Фильтрация по типу коммуникации
 * - Фильтрация по направлению (входящие/исходящие)
 * - Фильтрация по статусу (отправлено, доставлено, прочитано, ошибка)
 * - Поиск по содержимому коммуникаций
 * - Временная шкала коммуникаций в хронологическом порядке
 *
 * Использует компонент CommunicationTimeline для отображения коммуникаций.
 */
import React from 'react';
import { Container, Typography, Box, Paper, Alert, AlertTitle } from '@mui/material';
import { Message as MessageIcon, Info as InfoIcon } from '@mui/icons-material';
import { useAuth } from '@/hooks/useAuth';
import CommunicationTimeline from '@/components/CommunicationTimeline';
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';

/**
 * CommunicationHistoryPage Component
 *
 * Страница для просмотра истории коммуникаций кандидата.
 * Отображает все коммуникации между кандидатом и рекрутерами,
 * включая email, SMS, звонки и системные сообщения.
 *
 * Компонент автоматически определяет текущего пользователя
 * и отображает только его коммуникации.
 *
 * @example
 * ```tsx
 * // В React Router
 * <Route path="/candidate/communications" element={<CommunicationHistoryPage />} />
 * ```
 */
const CommunicationHistoryPage: React.FC = () => {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();

  // Показываем загрузку при инициализации аутентификации
  if (authLoading) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingState message="Loading your communications..." />
        </Container>
      </PageTransition>
    );
  }

  // Проверяем аутентификацию
  if (!isAuthenticated || !user) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="warning">
            <AlertTitle>Authentication Required</AlertTitle>
            Please log in to view your communication history.
          </Alert>
        </Container>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <MessageIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                Communication History
              </Typography>
              <Typography variant="body1" color="text.secondary">
                View all your communications with recruiters
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Информационная панель */}
        <Paper
          elevation={1}
          sx={{
            p: 2.5,
            mb: 3,
            bgcolor: 'info.lighter',
            borderLeft: 4,
            borderColor: 'info.main',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
            <InfoIcon color="info" sx={{ mt: 0.25 }} />
            <Box>
              <Typography variant="subtitle2" fontWeight={600} color="info.dark" gutterBottom>
                About Communication History
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This page shows all communications related to your job applications. You can filter by
                type (email, SMS, phone calls), direction (inbound/outbound), and status. Use the search
                bar to find specific messages.
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Компонент временной шкалы коммуникаций */}
        {/*
          CommunicationTimeline отображает все коммуникации для кандидата
          с возможностью фильтрации, поиска и детальным просмотром
        */}
        <CommunicationTimeline
          resumeId={user.id}
          limit={100}
        />
      </Container>
    </PageTransition>
  );
};

export default CommunicationHistoryPage;
