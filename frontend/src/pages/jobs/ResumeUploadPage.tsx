import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Typography, Box, Paper, Stepper, Step, StepLabel } from '@mui/material';
import ResumeUploader from '@components/ResumeUploader';

/**
 * Шаг рабочего процесса загрузки
 * Upload workflow step
 */
type UploadStep = 'upload' | 'processing' | 'complete';

/**
 * Компонент страницы загрузки резюме
 * Resume Upload Page Component
 *
 * Предоставляет интерфейс загрузки резюме для кандидатов с поддержкой перетаскивания.
 * Provides the resume upload interface for candidates with drag-and-drop support.
 * Особенности упрощенного 3-шагового рабочего процесса:
 * Features a streamlined 3-step workflow:
 * 1. Загрузить резюме - Выберите или перетащите файл резюме
 *    Upload Resume - Select or drag-drop resume file
 * 2. Обработка - ИИ анализирует резюме
 *    Processing - AI analyzes the resume
 * 3. Просмотр результатов - Смотрите анализ и рейтинги
 *    View Results - See analysis and rankings
 *
 * При успешной загрузке перенаправляет на страницу результатов с ID резюме.
 * On successful upload, redirects to the results page with the resume ID.
 */
const ResumeUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [currentStep, setCurrentStep] = useState<UploadStep>('upload');

  /**
   * Обработка успешной загрузки путем перехода на страницу результатов
   * Handle successful upload by navigating to results page
   */
  const handleUploadComplete = (resumeId: string) => {
    setCurrentStep('complete');
    // Переход после небольшой задержки для показа шага завершения
    // Navigate after a brief delay to show the complete step
    setTimeout(() => {
      navigate(`/jobs/resume-results/${resumeId}`);
    }, 1000);
  };

  /**
   * Обработка ошибок загрузки (можно расширить логированием/уведомлениями)
   * Handle upload errors (could be expanded with error logging/toast)
   */
  const handleUploadError = (error: string) => {
    // Ошибка отображается в компоненте ResumeUploader
    // Error is displayed in the ResumeUploader component
    // Дополнительная обработка ошибок может быть добавлена здесь (например, toast-уведомления)
    // Additional error handling can be added here (e.g., toast notifications)
  };

  /**
   * Обработка начала загрузки для обновления индикатора шага
   * Handle upload start to update step indicator
   */
  const handleUploadStart = () => {
    setCurrentStep('processing');
  };

  // Определение шагов рабочего процесса
  // Define workflow steps
  const steps = [
    { label: t('upload.steps.upload'), key: 'upload' },
    { label: t('upload.steps.processing'), key: 'processing' },
    { label: t('upload.steps.results'), key: 'complete' },
  ];

  // Вычисление индекса активного шага
  // Calculate active step index
  const activeStep = steps.findIndex((step) => step.key === currentStep);

  return (
    <Box>
      {/* Заголовок страницы / Page Header */}
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('upload.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {t('upload.subtitle')}
      </Typography>

      {/* Индикатор прогресса шагов / Step Progress Indicator */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((step) => (
            <Step key={step.key}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Компонент загрузки / Upload Component */}
      <Paper elevation={1} sx={{ p: 4 }}>
        <ResumeUploader
          uploadUrl="http://localhost:8000/api/resumes/upload"
          onUploadComplete={handleUploadComplete}
          onUploadError={handleUploadError}
          onUploadStart={handleUploadStart}
        />
      </Paper>

      {/* Быстрая информация - упрощенная версия полных инструкций */}
      {/* Quick Info - Streamlined from full instructions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'primary.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.acceptedFormats')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            PDF, DOCX (Max 10MB)
          </Typography>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'success.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.processingTime')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('upload.whatHappensNext.timeline')}
          </Typography>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'info.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.whatsNext')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('upload.info.viewResults')}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default ResumeUploadPage;
export { ResumeUploadPage };
