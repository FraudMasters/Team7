// Импорт хуков React для управления состоянием и побочными эффектами
import { useState, useEffect } from 'react';
// Импорт компонентов MUI для оформления интерфейса
import {
  Typography,  // Компонент для текста с различными стилями
  Box,         // Универсальный контейнер для верстки
  Alert,       // Предупреждающее сообщение
  CircularProgress, // Индикатор загрузки
  Button,      // Кнопка для действий
  Stack,       // Контейнер для вертикального расположения элементов
  Divider,     // Разделительная линия
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
// Импорт хука для получения параметров из URL
import { useParams, useNavigate } from 'react-router-dom';
// Импорт хука для локализации
import { useTranslation } from 'react-i18next';
// Импорт компонента для отображения предложений по оптимизации резюме
import OptimizationSuggestions from '../../components/resume/OptimizationSuggestions';
// Импорт компонента для отображения полноты резюме
import CompletenessScore from '../../components/resume/CompletenessScore';
// Импорт компонента для экспорта оптимизации
import OptimizationExport from '../../components/resume/OptimizationExport';
// Импорт API клиента для получения данных оптимизации
import { resumeOptimizationClient } from '../../api/resumeOptimization';
// Импорт типов для типобезопасности
import type { OptimizationFeedback } from '../../types/api';
import type { SectionCompleteness } from '../../components/resume/CompletenessScore';
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
  // Состояние для диалога экспорта
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

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

  // Обработчик открытия диалога экспорта
  const handleExportClick = () => {
    setExportDialogOpen(true);
  };

  // Обработчик закрытия диалога экспорта
  const handleExportClose = () => {
    setExportDialogOpen(false);
  };

  // Генерация данных о полноте резюме на основе оптимизационных данных
  const generateCompletenessData = (): { overallScore: number; sections: SectionCompleteness[] } => {
    if (!optimizationData) {
      return { overallScore: 0, sections: [] };
    }

    // Базовые секции резюме
    const baseSections: SectionCompleteness[] = [
      {
        section: 'personal_info',
        label: t('completeness.personalInfo', 'Personal Information'),
        completeness: 100,
        required: true,
        exists: true,
      },
      {
        section: 'contact',
        label: t('completeness.contact', 'Contact Details'),
        completeness: 100,
        required: true,
        exists: true,
      },
      {
        section: 'summary',
        label: t('completeness.summary', 'Professional Summary'),
        completeness: 85,
        required: true,
        exists: true,
        missing_items: [t('completeness.summaryTip', 'Consider adding more industry-specific keywords')],
      },
      {
        section: 'work_experience',
        label: t('completeness.workExperience', 'Work Experience'),
        completeness: 75,
        required: true,
        exists: true,
        missing_items: optimizationData.suggestions
          .filter(s => s.category === 'impact')
          .map(s => s.title)
          .slice(0, 3),
      },
      {
        section: 'education',
        label: t('completeness.education', 'Education'),
        completeness: 100,
        required: true,
        exists: true,
      },
      {
        section: 'skills',
        label: t('completeness.skills', 'Skills'),
        completeness: optimizationData.missing_keywords.length > 0 ? 60 : 90,
        required: true,
        exists: true,
        missing_items: optimizationData.missing_keywords.length > 0
          ? [t('completeness.skillsTip', 'Add missing keywords: ') + optimizationData.missing_keywords.slice(0, 5).join(', ')]
          : [],
      },
    ];

    // Вычисление общего балла
    const totalScore = baseSections.reduce((sum, section) => sum + section.completeness, 0) / baseSections.length;

    return {
      overallScore: Math.round(totalScore),
      sections: baseSections,
    };
  };

  const completenessData = generateCompletenessData();

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
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleExportClick}
              disabled={loading || !!error}
            >
              {t('optimization.export', 'Export Report')}
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate(-1)}
            >
              {t('common.back', 'Back')}
            </Button>
          </Stack>
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

        {/* Отображение компонентов оптимизации */}
        {!loading && !error && (
          <Stack spacing={4}>
            {/* Компонент отображения полноты резюме */}
            <CompletenessScore
              overallScore={completenessData.overallScore}
              sections={completenessData.sections}
              title={t('completeness.title', 'Resume Completeness')}
              description={t('completeness.description', 'Track your resume progress and ensure all important sections are complete')}
              showDetails={true}
              loading={loading}
              error={error}
            />

            <Divider />

            {/* Компонент предложений по оптимизации */}
            <OptimizationSuggestions
              optimizationData={optimizationData}
              loading={loading}
              error={error}
              title={t('optimization.suggestionsTitle', 'Optimization Suggestions')}
              onApplySuggestion={handleApplySuggestion}
            />
          </Stack>
        )}

        {/* Диалог экспорта оптимизации */}
        {id && (
          <OptimizationExport
            open={exportDialogOpen}
            onClose={handleExportClose}
            resumeId={id}
            onExportComplete={(format) => {
              console.log(`Export completed in ${format} format`);
            }}
          />
        )}
      </Box>
    </PageTransition>
  );
};

export default ResumeOptimizationPage;
export { ResumeOptimizationPage };
