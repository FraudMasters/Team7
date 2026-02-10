// Импорт хуков React для управления состоянием и побочными эффектами
import { useState, useEffect } from 'react';
// Импорт компонентов MUI для оформления интерфейса
import {
  Typography,  // Компонент для текста с различными стилями
  Box,         // Универсальный контейнер для верстки
  Alert,       // Предупреждающее сообщение
  CircularProgress, // Индикатор загрузки
  Button,      // Кнопка для действий
} from '@mui/material';
// Импорт хука для получения параметров из URL
import { useParams, useNavigate } from 'react-router-dom';
// Импорт хука для локализации
import { useTranslation } from 'react-i18next';
// Импорт компонента для отображения предложений по оптимизации резюме
import OptimizationSuggestions from '../../components/resume/OptimizationSuggestions';
// Импорт API клиента для получения данных оптимизации
import { resumeOptimizationClient } from '../../api/resumeOptimization';
// Импорт типов для типобезопасности
import type { OptimizationFeedback } from '../../types/api';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';

/**
 * Страница оптимизации резюме
 * Отображает AI-предложения по улучшению резюме, включая:
 * - Общий балл оптимизации
 * - Предложения по ключевым словам
 * - Рекомендации по форматированию
 * - Советы по структуре и содержанию
 * - Примеры улучшений
 */
const ResumeOptimizationPage: React.FC = () => {
  // Получение ID резюме из URL параметров
  const { id } = useParams<{ id: string }>();
  // Хук для навигации между страницами
  const navigate = useNavigate();
  // Хук для локализации интерфейса
  const { t } = useTranslation();

  // Состояние для хранения данных оптимизации
  const [optimizationData, setOptimizationData] = useState<OptimizationFeedback | null>(null);
  // Состояние индикатора загрузки
  const [loading, setLoading] = useState(true);
  // Состояние ошибки
  const [error, setError] = useState<string | null>(null);

  // Загрузка данных оптимизации при монтировании компонента или изменении ID
  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    const fetchOptimizationData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await resumeOptimizationClient.optimizeResume(id);
        setOptimizationData({
          resume_id: response.resume_id,
          suggestions: response.suggestions.map((s, idx) => ({
            type: s.category === 'keyword' ? 'keywords' :
                  s.category === 'formatting' ? 'structure' :
                  s.category === 'content' ? 'impact' : 'readability',
            priority: s.severity === 'high' ? 'high' :
                     s.severity === 'medium' ? 'medium' : 'low',
            category: s.category === 'keyword' ? 'keywords' :
                     s.category === 'formatting' ? 'structure' :
                     s.category === 'content' ? 'impact' : 'readability',
            title: s.title,
            description: s.description,
            current_state: s.current_value || t('optimization.unknownState', 'Current state unknown'),
            recommendation: s.suggestion,
            examples: [],
          })),
          total_suggestions: response.suggestions.length,
          high_priority_count: response.suggestions.filter(s => s.severity === 'high').length,
          medium_priority_count: response.suggestions.filter(s => s.severity === 'medium').length,
          low_priority_count: response.suggestions.filter(s => s.severity === 'low').length,
          keywords_found: [],
          missing_keywords: response.missing_keywords || [],
          score: response.overall_score || 0,
          error: response.error || null,
          processing_time_ms: response.processing_time_seconds ? response.processing_time_seconds * 1000 : undefined,
        });
      } catch (err) {
        const apiError = err as { detail?: string; status?: number };
        setError(apiError.detail || t('optimization.fetchError', 'Failed to fetch optimization data'));
      } finally {
        setLoading(false);
      }
    };

    fetchOptimizationData();
  }, [id, t]);

  // Обработчик применения предложения
  const handleApplySuggestion = (suggestion: typeof import('@/types/api').OptimizationSuggestion) => {
    // В будущем здесь может быть логика для автоматического применения предложений
    console.log('Apply suggestion:', suggestion);
  };

  // Отображение состояния отсутствия ID резюме
  if (!id) {
    return (
      <PageTransition>
        <Box sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
            {t('optimization.title', 'Resume Optimization')}
          </Typography>
          <Alert severity="error">
            {t('optimization.noResumeId', 'Resume ID not provided')}
          </Alert>
        </Box>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Box sx={{ p: 3 }}>
        {/* Заголовок страницы с кнопкой "Назад" */}
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
              {t('optimization.title', 'Resume Optimization')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('optimization.subtitle', 'AI-powered suggestions to improve your resume')}
            </Typography>
          </Box>
          <Button
            variant="outlined"
            onClick={() => navigate(-1)}
            sx={{ mt: 1 }}
          >
            {t('common.back', 'Back')}
          </Button>
        </Box>

        {/* Индикатор загрузки */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>
              {t('optimization.loading', 'Analyzing your resume for optimization opportunities...')}
            </Typography>
          </Box>
        )}

        {/* Отображение ошибки */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Отображение предложений по оптимизации */}
        {!loading && !error && (
          <OptimizationSuggestions
            optimizationData={optimizationData}
            loading={loading}
            error={error}
            title={t('optimization.suggestionsTitle', 'Optimization Suggestions')}
            onApplySuggestion={handleApplySuggestion}
          />
        )}
      </Box>
    </PageTransition>
  );
};

export default ResumeOptimizationPage;
export { ResumeOptimizationPage };
