// React для создания компонента
import React from 'react';
// React Router для навигации
import { Link } from 'react-router-dom';
// Компоненты Material UI для создания интерфейса
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  IconButton,
} from '@mui/material';
// Иконки Material UI
import {
  LocationOn,
  WorkOutline,
  BookmarkBorder,
  Bookmark,
  Schedule,
} from '@mui/icons-material';

/**
 * Интерфейс заявки на работу
 */
export interface JobApplication {
  /** Уникальный идентификатор заявки */
  id: string;
  /** Идентификатор вакансии */
  vacancy_id: string;
  /** Название должности */
  title: string;
  /** Описание вакансии */
  description?: string;
  /** Местоположение */
  location?: string;
  /** Формат работы */
  work_format?: 'remote' | 'office' | 'hybrid';
  /** Минимальный опыт в месяцах */
  min_experience_months?: number;
  /** Требуемые навыки */
  required_skills: string[];
  /** Статус заявки */
  status: string;
  /** Название этапа */
  stage_name?: string;
  /** Дата подачи заявки */
  applied_at: string;
  /** Оценка соответствия */
  match_score?: number;
}

/**
 * Свойства компонента ApplicationCard
 */
interface ApplicationCardProps {
  /** Данные заявки на работу */
  application: JobApplication;
  /** Сохранена ли вакансия */
  saved?: boolean;
  /** Обработчик сохранения */
  onSave?: () => void;
}

/**
 * Карточка заявки на работу
 *
 * Отображает информацию о заявке соискателя на вакансию, включая:
 * - Название должности и местоположение
 * - Статус заявки с цветовой индикацией
 * - Оценку соответствия (match score)
 * - Дату подачи
 * - Требуемые навыки
 * - Формат работы и опыт
 *
 * Компонент кликабелен и переходит на страницу вакансии.
 *
 * @example
 * ```tsx
 * <ApplicationCard
 *   application={applicationData}
 *   saved={true}
 *   onSave={() => console.log('Saved')}
 * />
 * ```
 */
export function ApplicationCard({ application, saved = false, onSave }: ApplicationCardProps) {
  // Максимальное количество навыков для отображения
  const maxSkillsToShow = 4;
  // Видимые навыки (первые N)
  const visibleSkills = application.required_skills.slice(0, maxSkillsToShow);
  // Количество оставшихся навыков
  const remainingSkillsCount = Math.max(0, application.required_skills.length - maxSkillsToShow);

  /**
   * Обработчик клика по закладке
   * Предотвращает переход по ссылке
   */
  const handleBookmarkClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSave?.();
  };

  /**
   * Форматирует дату в относительный формат
   * @param dateString - Дата в формате ISO
   * @returns Отформатированная строка даты
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  /**
   * Получает цвет чипа на основе статуса заявки
   * @param status - Статус заявки
   * @returns Цвет чипа Material UI
   */
  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'under_review':
        return 'info';
      case 'interview':
        return 'warning';
      case 'offered':
        return 'success';
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card
      component={Link}
      to={`/jobs/${application.vacancy_id}`}
      sx={{
        textDecoration: 'none',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s ease-out, box-shadow 0.2s ease-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        {/* Заголовок с названием, статусом и закладкой */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} color="text.primary" gutterBottom>
              {application.title}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
              {application.location && (
                <Stack direction="row" spacing={0.5} alignItems="center" color="text.secondary">
                  <LocationOn sx={{ fontSize: 16 }} />
                  <Typography variant="body2">{application.location}</Typography>
                </Stack>
              )}
            </Stack>
            <Stack direction="row" spacing={1} alignItems="center" color="text.secondary">
              <Schedule sx={{ fontSize: 16 }} />
              <Typography variant="body2">Applied {formatDate(application.applied_at)}</Typography>
            </Stack>
          </Box>
          <IconButton
            size="small"
            onClick={handleBookmarkClick}
            sx={{ ml: 1 }}
            aria-label={saved ? 'Remove from saved' : 'Save job'}
          >
            {saved ? <Bookmark color="primary" /> : <BookmarkBorder />}
          </IconButton>
        </Stack>

        {/* Чип статуса заявки с цветовой индикацией */}
        <Box sx={{ mb: 2 }}>
          <Chip
            label={application.stage_name || application.status}
            size="small"
            color={getStatusColor(application.status)}
            sx={{
              borderRadius: 1,
              fontSize: '0.75rem',
              height: 24,
              textTransform: 'capitalize',
            }}
          />
          {application.match_score !== undefined && (
            <Chip
              label={`${Math.round(application.match_score)}% match`}
              size="small"
              color="primary"
              variant="outlined"
              sx={{
                borderRadius: 1,
                fontSize: '0.75rem',
                height: 24,
                ml: 1,
              }}
            />
          )}
        </Box>

        {/* Описание, обрезанное до 2 строк */}
        {application.description && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {application.description}
          </Typography>
        )}

        {/* Формат работы и опыт */}
        {(application.work_format || application.min_experience_months) && (
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }} color="text.secondary">
            <WorkOutline sx={{ fontSize: 16 }} />
            <Typography variant="body2">
              {application.min_experience_months && application.min_experience_months > 0 && `${Math.floor(application.min_experience_months / 12)}+ years`}
              {application.work_format && ` • ${application.work_format}`}
            </Typography>
          </Stack>
        )}

        {/* Чипы навыков */}
        <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
          {visibleSkills.map((skill) => (
            <Chip
              key={skill}
              label={skill}
              size="small"
              variant="outlined"
              sx={{
                borderRadius: 1,
                fontSize: '0.75rem',
                height: 24,
              }}
            />
          ))}
          {remainingSkillsCount > 0 && (
            <Chip
              label={`+${remainingSkillsCount}`}
              size="small"
              variant="outlined"
              sx={{ borderRadius: 1, fontSize: '0.75rem', height: 24 }}
            />
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
