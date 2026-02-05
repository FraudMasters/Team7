/**
 * Страница деталей кандидата
 *
 * Отображает подробную информацию о кандидате, включая:
 * - Анализ резюме с определением ошибок и извлечением навыков
 * - Результаты проверки грамматики и орфографии
 * - Сводку об опыте работы
 * - Результаты сопоставления с вакансиями с подсветкой навыков
 * - Рекомендацию лучшего соответствия
 */

// Импорт основных типов React и хука состояния
import React, { useState } from 'react';

// Импорт компонентов MUI для верстки
import { Typography, Box, Tabs, Tab, Container } from '@mui/material';

// Импорт хука React Router для получения параметров URL
import { useParams } from 'react-router-dom';

// Импорт хука для интернационализации
import { useTranslation } from 'react-i18next';

// Импорт бизнес-компонентов для отображения анализа и сопоставления
import AnalysisResults from '@components/AnalysisResults';
import VacancyMatchResults from '@components/VacancyMatchResults';

// Импорт MUI компонентов для анимации переходов и обработки ошибок
import { PageTransition } from '@components/mui/PageTransition';
import { ErrorState } from '@components/mui/ErrorState';

const CandidateDetailPage: React.FC = () => {
  // Получаем ID кандидата из параметров URL
  const { id } = useParams<{ id: string }>();

  // Хук для интернационализации
  const { t } = useTranslation();

  // Состояние активной вкладки
  const [activeTab, setActiveTab] = useState(0);

  // Отображаем ошибку, если ID кандидата не предоставлен
  if (!id) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title="Candidate Not Found"
            message="No candidate ID provided. Please select a valid candidate from the candidates list."
            onRetry={() => window.history.back()}
          />
        </Container>
      </PageTransition>
    );
  }

  // Обработчик смены вкладки
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Заголовок страницы с информацией о кандидате */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          Candidate Details
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Resume ID: {id}
        </Typography>
      </Box>

      {/* Вкладки для переключения между разделами */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="candidate details tabs">
          <Tab label="Analysis" />
          <Tab label="Vacancy Matches" />
        </Tabs>
      </Box>

      {/* Содержимое активной вкладки */}
      {activeTab === 0 && <AnalysisResults resumeId={id} />}
      {activeTab === 1 && <VacancyMatchResults resumeId={id} />}
    </Container>
    </PageTransition>
  );
};

export default CandidateDetailPage;
export { CandidateDetailPage };
