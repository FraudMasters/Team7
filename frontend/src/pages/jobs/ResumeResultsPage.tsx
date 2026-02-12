// Импорт хуков React для управления состоянием
import { useState, useEffect, useCallback } from 'react';
// Импорт компонентов MUI для оформления интерфейса
import {
  Typography,  // Компонент для текста с различными стилями
  Box,         // Универсальный контейнер для верстки
  Tabs,        // Вкладки для переключения между секциями
  Tab,         // Отдельная вкладка
  Alert,       // Предупреждающее сообщение
  Button,      // Кнопка для действий
  CircularProgress, // Индикатор загрузки
} from '@mui/material';
// Импорт хуков для навигации
import { useParams, useNavigate } from 'react-router-dom';
// Импорт хука для локализации
import { useTranslation } from 'react-i18next';
// Импорт компонентов для отображения результатов анализа резюме
import AnalysisResults from '../../components/AnalysisResults';
import VacancyMatchResults from '../../components/VacancyMatchResults';
// Импорт новых компонентов для визуального фидбека и редактирования
import VisualParsingFeedback from '../../components/VisualParsingFeedback';
import ParsedDataEditor from '../../components/ParsedDataEditor';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
// Импорт API клиентов
import { parsingCorrectionsClient } from '@/api/parsingCorrections';
// Импорт типов
import type {
  VisualParsingFeedback as VisualParsingFeedbackType,
  ParsingCorrectionResponse,
  FieldSourceLocation,
} from '@/types/parsingCorrection';

/**
 * Интерфейс для данных анализа резюме
 */
interface ResumeAnalysisData {
  id: string;
  filename: string;
  status: string;
  raw_text: string;
  skills: Array<{
    id?: string;
    name: string;
    category?: string;
    proficiency_level?: string;
    years_of_experience?: number;
  }>;
  education: Array<{
    id?: string;
    institution_name: string;
    degree: string;
    field_of_study?: string;
    start_date?: string;
    end_date?: string;
  }>;
  work_experience: Array<{
    id?: string;
    company_name: string;
    position_title: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    employment_type?: string;
  }>;
  languages: Array<{ name: string; proficiency?: string }>;
  source_locations?: FieldSourceLocation[];
}

/**
 * Страница результатов анализа резюме
 * Отображает комплексные результаты анализа резюме, включая:
 * - Обнаружение ошибок с бейджами серьезности
 * - Проверку грамматики и орфографии
 * - Извлечение ключевых слов и навыков
 * - Сводку опыта
 * - Подсветку навыков (зеленый - совпавшие, красный - отсутствующие)
 * - Визуальный фидбек парсинга
 * - Интерфейс для исправления распарсенных данных
 */
const ResumeResultsPage: React.FC = () => {
  // Получение ID резюме из URL параметров
  const { id } = useParams<{ id: string }>();
  // Хук для навигации между страницами
  const navigate = useNavigate();
  // Хук для локализации интерфейса
  const { t } = useTranslation();
  // Состояние активной вкладки (0 - анализ, 1 - соответствие вакансиям, 2 - визуальный фидбек, 3 - редактор)
  const [activeTab, setActiveTab] = useState(0);

  // Состояния для загрузки данных
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resumeData, setResumeData] = useState<ResumeAnalysisData | null>(null);
  const [visualFeedback, setVisualFeedback] = useState<VisualParsingFeedbackType | null>(null);
  const [existingCorrections, setExistingCorrections] = useState<ParsingCorrectionResponse[]>([]);

  /**
   * Загрузка данных резюме и визуального фидбека
   */
  const fetchData = useCallback(async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      // Загружаем данные резюме
      const resumeResponse = await fetch(`/api/resumes/${id}`);
      if (!resumeResponse.ok) {
        throw new Error(`Failed to fetch resume: ${resumeResponse.statusText}`);
      }
      const data: ResumeAnalysisData = await resumeResponse.json();
      setResumeData(data);

      // Формируем визуальный фидбек на основе source_locations
      if (data.source_locations && data.source_locations.length > 0) {
        // Получаем существующие исправления для определения corrected_fields
        const correctionsResponse = await parsingCorrectionsClient.getCorrections(id);
        const corrections = correctionsResponse.data;
        setExistingCorrections(corrections);

        const correctedFields = corrections.map(c => c.field_name);

        setVisualFeedback({
          resume_id: id,
          source_locations: data.source_locations || [],
          total_fields: data.source_locations?.length || 0,
          corrected_fields: correctedFields,
        });
      } else {
        // Если source_locations нет, создаем пустой фидбек
        setVisualFeedback({
          resume_id: id,
          source_locations: [],
          total_fields: 0,
          corrected_fields: [],
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('results.error.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Обработчик переключения вкладок
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  /**
   * Обработчик создания исправления
   */
  const handleCorrectionCreated = useCallback((correction: ParsingCorrectionResponse) => {
    setExistingCorrections(prev => [...prev, correction]);
    // Обновляем visual feedback с новым списком исправленных полей
    if (visualFeedback) {
      setVisualFeedback({
        ...visualFeedback,
        corrected_fields: [...visualFeedback.corrected_fields, correction.field_name],
      });
    }
  }, [visualFeedback]);

  /**
   * Обработчик выбора поля для редактирования
   */
  const handleFieldSelect = useCallback((field: FieldSourceLocation | null) => {
    if (field) {
      // Переключаемся на вкладку редактора при выборе поля
      setActiveTab(3);
    }
  }, []);

  // Отображение состояния загрузки
  if (loading) {
    return (
      <PageTransition>
        <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h6" color="text.secondary">
            {t('results.loading.title', 'Loading resume data...')}
          </Typography>
        </Box>
      </PageTransition>
    );
  }

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

  // Отображение ошибки
  if (error) {
    return (
      <PageTransition>
        <Box sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
            {t('results.title', 'Resume Analysis Results')}
          </Typography>
          <Alert
            severity="error"
            action={
              <Button color="inherit" onClick={fetchData}>
                {t('results.error.retry', 'Retry')}
              </Button>
            }
          >
            {error}
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
            <Tab label={t('results.tabs.visualFeedback', 'Visual Feedback')} />
            <Tab label={t('results.tabs.editData', 'Edit Data')} />
          </Tabs>
        </Box>

        {/* Отображение контента в зависимости от активной вкладки */}
        {activeTab === 0 && <AnalysisResults resumeId={id} />}
        {activeTab === 1 && <VacancyMatchResults resumeId={id} />}

        {/* Вкладка визуального фидбека парсинга */}
        {activeTab === 2 && (
          <VisualParsingFeedback
            data={visualFeedback || { resume_id: id, source_locations: [], total_fields: 0, corrected_fields: [] }}
            sourceText={resumeData?.raw_text || ''}
            onFieldSelect={handleFieldSelect}
            loading={false}
            error={null}
          />
        )}

        {/* Вкладка редактора распарсенных данных */}
        {activeTab === 3 && resumeData && (
          <ParsedDataEditor
            resumeId={id}
            skills={resumeData.skills || []}
            education={resumeData.education || []}
            workHistory={resumeData.work_experience || []}
            languages={resumeData.languages || []}
            existingCorrections={existingCorrections}
            onCorrectionCreated={handleCorrectionCreated}
            readOnly={false}
            loading={false}
          />
        )}

        {/* Если нет данных резюме на вкладке редактора */}
        {activeTab === 3 && !resumeData && (
          <Alert severity="info">
            {t('results.noDataForEditing', 'No parsed data available for editing')}
          </Alert>
        )}
      </Box>
    </PageTransition>
  );
};

export default ResumeResultsPage;
export { ResumeResultsPage };
