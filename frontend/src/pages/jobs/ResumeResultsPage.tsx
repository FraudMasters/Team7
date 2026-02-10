// Импорт хуков React для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для оформления интерфейса
import {
  Typography,  // Компонент для текста с различными стилями
  Box,         // Универсальный контейнер для верстки
  Tabs,        // Вкладки для переключения между секциями
  Tab,         // Отдельная вкладка
  Alert,       // Предупреждающее сообщение
  Button,      // Кнопка для действий
} from '@mui/material';
// Импорт хуков для навигации
import { useParams, useNavigate } from 'react-router-dom';
// Импорт хука для локализации
import { useTranslation } from 'react-i18next';
// Импорт компонентов для отображения результатов анализа резюме
import AnalysisResults from '../../components/AnalysisResults';
import VacancyMatchResults from '../../components/VacancyMatchResults';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';

/**
 * Страница результатов анализа резюме
 * Отображает комплексные результаты анализа резюме, включая:
 * - Обнаружение ошибок с бейджами серьезности
 * - Проверку грамматики и орфографии
 * - Извлечение ключевых слов и навыков
 * - Сводку опыта
 * - Подсветку навыков (зеленый - совпавшие, красный - отсутствующие)
 */
const ResumeResultsPage: React.FC = () => {
  // Получение ID резюме из URL параметров
  const { id } = useParams<{ id: string }>();
  // Хук для навигации между страницами
  const navigate = useNavigate();
  // Хук для локализации интерфейса
  const { t } = useTranslation();
  // Состояние активной вкладки (0 - анализ, 1 - соответствие вакансиям)
  const [activeTab, setActiveTab] = useState(0);

  // Обработчик переключения вкладок
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Отображение состояния отсутствия ID резюме
  if (!id) {
    return (
      <PageTransition>
        <Box sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
            {t('results.title', 'Resume Analysis Results')}
          </Typography>
          <Alert severity="error">
            {t('results.noResumeId', 'Resume ID not provided')}
          </Alert>
        </Box>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Box sx={{ p: 3 }}>
        {/* Заголовок страницы с ID резюме */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
              {t('results.title', 'Resume Analysis Results')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Resume ID: {id}
            </Typography>
          </Box>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate(`/jobs/resume-optimization/${id}`)}
          >
            {t('results.viewOptimization', 'View Optimization')}
          </Button>
        </Box>

        {/* Панель вкладок для переключения между видами результатов */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="results tabs">
            <Tab label={t('results.tabs.analysis', 'Analysis')} />
            <Tab label={t('results.tabs.vacancyMatches', 'Vacancy Matches')} />
          </Tabs>
        </Box>

        {/* Отображение контента в зависимости от активной вкладки */}
        {activeTab === 0 && <AnalysisResults resumeId={id} />}
        {activeTab === 1 && <VacancyMatchResults resumeId={id} />}
      </Box>
    </PageTransition>
  );
};

export default ResumeResultsPage;
export { ResumeResultsPage };
