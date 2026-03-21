import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Divider,
  Alert,
  AlertTitle,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Warning as WarningIcon,
  ExpandMore as ExpandIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  SwapHoriz as SwapIcon,
  ContentCopy as CopyIcon,
  Difference as DiffIcon,
} from '@mui/icons-material';

/**
 * Тип конфликта поля
 */
type FieldType = 'simple' | 'text' | 'numeric' | 'contact' | 'list';

/**
 * Конфликтующее поле
 */
interface ConflictField {
  /** Имя поля */
  fieldName: string;
  /** Отображаемое имя поля на русском */
  displayName: string;
  /** Тип поля для правильного отображения */
  fieldType: FieldType;
  /** Значение из основного профиля */
  primaryValue: any;
  /** Значение из дубликата */
  duplicateValue: any;
  /** Рекомендуемое значение (опционально) */
  recommendedValue?: 'primary' | 'duplicate';
  /** Описание конфликта */
  description?: string;
}

/**
 * Решение конфликта
 */
interface ConflictResolution {
  /** Имя поля */
  fieldName: string;
  /** Выбранное значение: 'primary' или 'duplicate' */
  selectedValue: 'primary' | 'duplicate';
  /** Конечное значение */
  resolvedValue: any;
}

/**
 * ConflictResolutionPanel Component Props
 */
interface ConflictResolutionPanelProps {
  /** Список конфликтующих полей */
  conflicts: ConflictField[];
  /** Callback при изменении решений */
  onResolutionsChange?: (resolutions: ConflictResolution[]) => void;
  /** Callback при завершении разрешения всех конфликтов */
  onComplete?: (resolutions: ConflictResolution[]) => void;
  /** Показать кнопку "Завершить" */
  showCompleteButton?: boolean;
  /** Разрешить автоматическое принятие рекомендаций */
  allowAutoResolve?: boolean;
  /** Компактный режим отображения */
  compact?: boolean;
}

/**
 * Маппинг имен полей на русский язык
 */
const FIELD_DISPLAY_NAMES: Record<string, string> = {
  language: 'Язык резюме',
  vacancy_id: 'Вакансия',
  error_message: 'Сообщение об ошибке',
  raw_text: 'Текст резюме',
  total_experience_months: 'Общий опыт (месяцы)',
  quality_score: 'Оценка качества',
  contact_info: 'Контактная информация',
  email: 'Email',
  phone: 'Телефон',
  address: 'Адрес',
  skills: 'Навыки',
  keywords: 'Ключевые слова',
  education: 'Образование',
};

/**
 * Получить отображаемое имя поля
 */
const getFieldDisplayName = (fieldName: string): string => {
  return FIELD_DISPLAY_NAMES[fieldName] || fieldName;
};

/**
 * Определить тип поля
 */
const getFieldType = (value: any): FieldType => {
  if (value === null || value === undefined) return 'simple';
  if (typeof value === 'number') return 'numeric';
  if (Array.isArray(value)) return 'list';
  if (typeof value === 'object') return 'contact';
  if (typeof value === 'string' && value.length > 100) return 'text';
  return 'simple';
};

/**
 * Форматировать значение для отображения
 */
const formatValue = (value: any, fieldType: FieldType): string => {
  if (value === null || value === undefined || value === '') {
    return '(пусто)';
  }

  switch (fieldType) {
    case 'numeric':
      return String(value);
    case 'list':
      return Array.isArray(value) ? value.join(', ') : String(value);
    case 'contact':
      return typeof value === 'object'
        ? Object.entries(value)
            .filter(([_, v]) => v)
            .map(([k, v]) => `${getFieldDisplayName(k)}: ${v}`)
            .join(', ')
        : String(value);
    case 'text':
      return typeof value === 'string' && value.length > 200
        ? `${value.substring(0, 200)}...`
        : String(value);
    default:
      return String(value);
  }
};

/**
 * Получить цвет чипа для значения
 */
const getValueColor = (
  isSelected: boolean,
  isRecommended: boolean
): 'primary' | 'success' | 'default' => {
  if (isSelected) return 'primary';
  if (isRecommended) return 'success';
  return 'default';
};

/**
 * ConflictResolutionPanel Component
 *
 * Компонент для разрешения конфликтов данных при слиянии дубликатов профилей:
 * - Отображает список конфликтующих полей
 * - Показывает значения из обоих профилей
 * - Позволяет выбрать значение для каждого поля
 * - Визуально выделяет рекомендуемые значения
 * - Поддерживает различные типы полей (текст, числа, контакты, списки)
 * - Отслеживает прогресс разрешения конфликтов
 *
 * @example
 * ```tsx
 * <ConflictResolutionPanel
 *   conflicts={[
 *     {
 *       fieldName: 'language',
 *       displayName: 'Язык резюме',
 *       fieldType: 'simple',
 *       primaryValue: 'ru',
 *       duplicateValue: 'en',
 *       recommendedValue: 'primary'
 *     }
 *   ]}
 *   onResolutionsChange={(resolutions) => console.log(resolutions)}
 *   onComplete={(resolutions) => handleComplete(resolutions)}
 *   showCompleteButton
 * />
 * ```
 */
const ConflictResolutionPanel: React.FC<ConflictResolutionPanelProps> = ({
  conflicts,
  onResolutionsChange,
  onComplete,
  showCompleteButton = true,
  allowAutoResolve = true,
  compact = false,
}) => {
  const [resolutions, setResolutions] = useState<Map<string, ConflictResolution>>(new Map());
  const [expandedConflict, setExpandedConflict] = useState<string | false>(false);

  /**
   * Инициализация решений при изменении конфликтов
   */
  useEffect(() => {
    const initialResolutions = new Map<string, ConflictResolution>();
    conflicts.forEach((conflict) => {
      if (!resolutions.has(conflict.fieldName)) {
        const selectedValue = conflict.recommendedValue || 'primary';
        initialResolutions.set(conflict.fieldName, {
          fieldName: conflict.fieldName,
          selectedValue,
          resolvedValue:
            selectedValue === 'primary'
              ? conflict.primaryValue
              : conflict.duplicateValue,
        });
      }
    });
    setResolutions(initialResolutions);
  }, [conflicts]);

  /**
   * Обработка изменения решения для поля
   */
  const handleResolutionChange = useCallback(
    (conflict: ConflictField, selectedValue: 'primary' | 'duplicate') => {
      const newResolutions = new Map(resolutions);
      newResolutions.set(conflict.fieldName, {
        fieldName: conflict.fieldName,
        selectedValue,
        resolvedValue:
          selectedValue === 'primary' ? conflict.primaryValue : conflict.duplicateValue,
      });
      setResolutions(newResolutions);

      if (onResolutionsChange) {
        onResolutionsChange(Array.from(newResolutions.values()));
      }
    },
    [resolutions, onResolutionsChange]
  );

  /**
   * Автоматическое применение всех рекомендаций
   */
  const handleAutoResolve = useCallback(() => {
    const newResolutions = new Map<string, ConflictResolution>();
    conflicts.forEach((conflict) => {
      const selectedValue = conflict.recommendedValue || 'primary';
      newResolutions.set(conflict.fieldName, {
        fieldName: conflict.fieldName,
        selectedValue,
        resolvedValue:
          selectedValue === 'primary' ? conflict.primaryValue : conflict.duplicateValue,
      });
    });
    setResolutions(newResolutions);

    if (onResolutionsChange) {
      onResolutionsChange(Array.from(newResolutions.values()));
    }
  }, [conflicts, onResolutionsChange]);

  /**
   * Завершение разрешения конфликтов
   */
  const handleComplete = useCallback(() => {
    if (onComplete) {
      onComplete(Array.from(resolutions.values()));
    }
  }, [resolutions, onComplete]);

  /**
   * Обработка изменения раскрытого аккордеона
   */
  const handleAccordionChange = useCallback(
    (panel: string) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
      setExpandedConflict(isExpanded ? panel : false);
    },
    []
  );

  /**
   * Проверка, все ли конфликты разрешены
   */
  const allResolved = resolutions.size === conflicts.length;

  /**
   * Подсчет разрешенных конфликтов
   */
  const resolvedCount = resolutions.size;
  const totalCount = conflicts.length;

  /**
   * Рендер пустого состояния
   */
  if (conflicts.length === 0) {
    return (
      <Alert severity="success" icon={<CheckIcon />}>
        <AlertTitle>Конфликты отсутствуют</AlertTitle>
        <Typography variant="body2">
          Все поля совпадают или не требуют разрешения конфликтов. Можно продолжить слияние.
        </Typography>
      </Alert>
    );
  }

  /**
   * Рендер одного конфликтующего поля
   */
  const renderConflictField = (conflict: ConflictField) => {
    const resolution = resolutions.get(conflict.fieldName);
    const selectedValue = resolution?.selectedValue || 'primary';

    return (
      <Accordion
        key={conflict.fieldName}
        expanded={expandedConflict === conflict.fieldName}
        onChange={handleAccordionChange(conflict.fieldName)}
        elevation={1}
      >
        <AccordionSummary expandIcon={<ExpandIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
            <DiffIcon color="warning" />
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle1" fontWeight={600}>
                {conflict.displayName || getFieldDisplayName(conflict.fieldName)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {conflict.fieldType === 'text'
                  ? 'Текстовое поле'
                  : conflict.fieldType === 'numeric'
                  ? 'Числовое значение'
                  : conflict.fieldType === 'contact'
                  ? 'Контактная информация'
                  : conflict.fieldType === 'list'
                  ? 'Список значений'
                  : 'Простое поле'}
              </Typography>
            </Box>
            {resolution && (
              <Chip
                label={selectedValue === 'primary' ? 'Основной' : 'Дубликат'}
                color={getValueColor(
                  true,
                  conflict.recommendedValue === selectedValue
                )}
                size="small"
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            {conflict.description && (
              <Alert severity="info" icon={<InfoIcon />}>
                <Typography variant="body2">{conflict.description}</Typography>
              </Alert>
            )}

            <RadioGroup
              value={selectedValue}
              onChange={(e) =>
                handleResolutionChange(
                  conflict,
                  e.target.value as 'primary' | 'duplicate'
                )
              }
            >
              <Grid container spacing={2}>
                {/* Основной профиль */}
                <Grid item xs={12} md={6}>
                  <Card
                    variant="outlined"
                    sx={{
                      border: selectedValue === 'primary' ? 2 : 1,
                      borderColor:
                        selectedValue === 'primary'
                          ? 'primary.main'
                          : conflict.recommendedValue === 'primary'
                          ? 'success.main'
                          : 'divider',
                      bgcolor:
                        selectedValue === 'primary'
                          ? 'primary.50'
                          : 'background.paper',
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <FormControlLabel
                          value="primary"
                          control={<Radio />}
                          label={
                            <Typography variant="subtitle2" fontWeight={600}>
                              Основной профиль
                            </Typography>
                          }
                          sx={{ flex: 1 }}
                        />
                        {conflict.recommendedValue === 'primary' && (
                          <Chip
                            label="Рекомендуется"
                            color="success"
                            size="small"
                            icon={<CheckIcon />}
                          />
                        )}
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.primary"
                        sx={{
                          wordBreak: 'break-word',
                          whiteSpace: 'pre-wrap',
                          fontFamily:
                            conflict.fieldType === 'text'
                              ? 'monospace'
                              : 'inherit',
                        }}
                      >
                        {formatValue(conflict.primaryValue, conflict.fieldType)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Дубликат */}
                <Grid item xs={12} md={6}>
                  <Card
                    variant="outlined"
                    sx={{
                      border: selectedValue === 'duplicate' ? 2 : 1,
                      borderColor:
                        selectedValue === 'duplicate'
                          ? 'primary.main'
                          : conflict.recommendedValue === 'duplicate'
                          ? 'success.main'
                          : 'divider',
                      bgcolor:
                        selectedValue === 'duplicate'
                          ? 'primary.50'
                          : 'background.paper',
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <FormControlLabel
                          value="duplicate"
                          control={<Radio />}
                          label={
                            <Typography variant="subtitle2" fontWeight={600}>
                              Дубликат
                            </Typography>
                          }
                          sx={{ flex: 1 }}
                        />
                        {conflict.recommendedValue === 'duplicate' && (
                          <Chip
                            label="Рекомендуется"
                            color="success"
                            size="small"
                            icon={<CheckIcon />}
                          />
                        )}
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.primary"
                        sx={{
                          wordBreak: 'break-word',
                          whiteSpace: 'pre-wrap',
                          fontFamily:
                            conflict.fieldType === 'text'
                              ? 'monospace'
                              : 'inherit',
                        }}
                      >
                        {formatValue(conflict.duplicateValue, conflict.fieldType)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </RadioGroup>
          </Stack>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <Paper elevation={2} sx={{ p: compact ? 2 : 3 }}>
      <Stack spacing={3}>
        {/* Заголовок */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <WarningIcon color="warning" />
            <Typography variant="h6" fontWeight={600}>
              Разрешение конфликтов данных
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Обнаружены конфликтующие значения полей. Выберите, какие значения сохранить
            для каждого поля.
          </Typography>
        </Box>

        {/* Прогресс */}
        <Alert severity={allResolved ? 'success' : 'warning'}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" fontWeight={600}>
              Разрешено конфликтов: {resolvedCount} из {totalCount}
            </Typography>
            {allowAutoResolve && !allResolved && (
              <Button
                size="small"
                variant="outlined"
                startIcon={<CheckIcon />}
                onClick={handleAutoResolve}
              >
                Применить рекомендации
              </Button>
            )}
          </Box>
        </Alert>

        <Divider />

        {/* Список конфликтов */}
        <Stack spacing={1}>
          {conflicts.map((conflict) => renderConflictField(conflict))}
        </Stack>

        {/* Кнопка завершения */}
        {showCompleteButton && (
          <>
            <Divider />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleComplete}
                disabled={!allResolved}
                startIcon={<CheckIcon />}
              >
                Завершить разрешение
              </Button>
            </Box>
          </>
        )}
      </Stack>
    </Paper>
  );
};

export default ConflictResolutionPanel;
