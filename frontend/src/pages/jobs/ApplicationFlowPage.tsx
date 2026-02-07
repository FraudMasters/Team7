// Импорт хуков React для управления состоянием
import { useState } from 'react';
// Импорт хука для получения параметров маршрута из URL
import { useParams } from 'react-router-dom';
// Импорт компонентов Material-UI
import {
  Container,      // Контейнер для ограничения ширины содержимого
  Paper,          // Бумажный компонент для создания карточки с тенями
  Typography,     // Компонент для отображения текста с различными стилями
  Stepper,        // Компонент пошагового индикатора
  Step,           // Отдельный шаг в Stepper
  StepLabel,      // Метка для шага
  Box,            // Универсальный контейнер для Flexbox и Grid布局
  TextField,      // Поле ввода текста
  Button,         // Кнопка
  Stack,          // Контейнер для расположения элементов с отступами
  CircularProgress, // Индикатор загрузки (крутящийся круг)
  Alert,          // Компонент для отображения предупреждений и сообщений
} from '@mui/material';
// Импорт кастомного хука для получения данных о вакансии
import { useJob } from '../../hooks/useJobs';
// Импорт компонента загрузки резюме
import ResumeUploader from '../../components/ResumeUploader';

// Массив этапов процесса подачи заявки
const steps = ['Upload Resume', 'Contact Info', 'Review', 'Submit'];

/**
 * Страница потока подачи заявки на вакансию
 * Многоэтапная форма: загрузка резюме -> контактная информация -> проверка -> отправка
 */
export function ApplicationFlowPage() {
  // Получение ID вакансии из параметров маршрута
  const { id } = useParams<{ id: string }>();
  // Получение данных о вакансии с помощью кастомного хука
  const { data: job, isLoading: jobLoading } = useJob(id || '');

  // Текущий активный этап процесса подачи заявки (0-3)
  const [activeStep, setActiveStep] = useState(0);
  // ID загруженного резюме
  const [resumeId, setResumeId] = useState<string | null>(null);
  // Данные формы контактной информации
  const [formData, setFormData] = useState({
    email: '',          // Email соискателя
    phone: '',          // Номер телефона
    coverLetter: '',    // Сопроводительное письмо
  });
  // Состояние отправки заявки
  const [submitting, setSubmitting] = useState(false);
  // Состояние ошибки
  const [error, setError] = useState<string | null>(null);

  /**
   * Обработчик завершения загрузки резюме
   * Сохраняет ID резюме и переходит к следующему этапу
   * @param id - ID загруженного резюме
   */
  const handleUploadComplete = (id: string) => {
    setResumeId(id);
    setActiveStep(1);
  };

  /**
   * Обработчик отправки заявки
   * Отправляет данные заявки на сервер
   */
  const handleSubmit = async () => {
    if (!resumeId || !id) return;

    setSubmitting(true);
    setError(null);

    try {
      // TODO: Реализовать фактический вызов API для отправки заявки
      await new Promise(resolve => setTimeout(resolve, 1000));
      setActiveStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  // Состояние загрузки данных о вакансии
  if (jobLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: { xs: 3, md: 5 } }}>
        {/* Заголовок страницы */}
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Apply for {job?.title}
        </Typography>

        {/* Индикатор прогресса по этапам */}
        <Stepper activeStep={activeStep} sx={{ my: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Основное содержимое с этапами */}
        <Box sx={{ mt: 4 }}>
          {/* Этап 1: Загрузка резюме */}
          {activeStep === 0 && (
            <Stack spacing={4}>
              <Typography variant="body1" color="text.secondary">
                Upload your resume and we'll match your skills to this position.
              </Typography>
              <ResumeUploader
                uploadUrl="http://localhost:8000/api/resumes/upload"
                onUploadComplete={handleUploadComplete}
                onUploadError={() => {}}
                onUploadStart={() => {}}
              />
            </Stack>
          )}

          {/* Этап 2: Контактная информация */}
          {activeStep === 1 && (
            <Stack spacing={4}>
              <Alert severity="success">
                Your resume has been analyzed! Please complete your details below.
              </Alert>

              {/* Поля формы */}
              <Stack spacing={3}>
                <TextField
                  label="Email"
                  type="email"
                  fullWidth
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
                <TextField
                  label="Phone"
                  type="tel"
                  fullWidth
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
                <TextField
                  label="Cover Letter (Optional)"
                  multiline
                  rows={6}
                  fullWidth
                  value={formData.coverLetter}
                  onChange={(e) => setFormData({ ...formData, coverLetter: e.target.value })}
                  placeholder="Tell us why you're a great fit..."
                />
              </Stack>

              {/* Кнопки навигации */}
              <Stack direction="row" spacing={2}>
                <Button onClick={() => setActiveStep(0)}>Back</Button>
                <Button
                  variant="contained"
                  onClick={() => setActiveStep(2)}
                  disabled={!formData.email}
                >
                  Review
                </Button>
              </Stack>
            </Stack>
          )}

          {/* Этап 3: Проверка данных */}
          {activeStep === 2 && (
            <Stack spacing={4}>
              <Typography variant="h6">Review Your Application</Typography>

              {/* Отображение email */}
              <Box>
                <Typography variant="body2" color="text.secondary">Email</Typography>
                <Typography>{formData.email}</Typography>
              </Box>

              {/* Отображение телефона (если указан) */}
              {formData.phone && (
                <Box>
                  <Typography variant="body2" color="text.secondary">Phone</Typography>
                  <Typography>{formData.phone}</Typography>
                </Box>
              )}

              {/* Отображение ошибки (если есть) */}
              {error && <Alert severity="error">{error}</Alert>}

              {/* Кнопки навигации */}
              <Stack direction="row" spacing={2}>
                <Button onClick={() => setActiveStep(1)}>Back</Button>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={submitting}
                  startIcon={submitting ? <CircularProgress size={16} /> : null}
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </Button>
              </Stack>
            </Stack>
          )}

          {/* Этап 4: Успешная отправка */}
          {activeStep === 3 && (
            <Stack spacing={4} alignItems="center" textAlign="center">
              <Typography variant="h5" fontWeight={700} color="success.main">
                Application Submitted!
              </Typography>
              <Typography variant="body1" color="text.secondary">
                We'll review your application and get back to you soon.
              </Typography>
              <Button variant="contained" href="/jobs">
                Browse More Jobs
              </Button>
            </Stack>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
