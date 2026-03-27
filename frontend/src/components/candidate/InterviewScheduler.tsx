/**
 * Candidate Interview Scheduler Component
 *
 * Candidate-facing interface for self-scheduling interviews.
 * Shows a visual calendar with available time slots and allows booking.
 */

import { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Paper,
  Alert,
  CircularProgress,
  Grid2,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Event as EventIcon,
  AccessTime as TimeIcon,
  VideoCall as VideoIcon,
  Close as CloseIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addMonths,
  subMonths,
  format,
  isSameMonth,
  isSameDay,
  isToday,
  isBefore,
  startOfDay,
  parseISO,
  addMinutes,
} from 'date-fns';
import { interviewsClient } from '../../api/interviews';
import { calendarClient } from '../../api/calendar';

/**
 * Доступный временной слот для записи на интервью
 */
interface AvailableSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  recruiter_id: string;
  recruiter_name?: string;
}

/**
 * Запрос доступных слотов
 */
interface AvailableSlotsRequest {
  vacancy_id?: string;
  start_date: string;
  end_date: string;
}

/**
 * Ответ со списком доступных слотов
 */
interface AvailableSlotsResponse {
  slots: AvailableSlot[];
  total: number;
}

/**
 * Тип интервью
 */
type InterviewType = 'phone' | 'video' | 'onsite' | 'technical' | 'panel';

/**
 * Создание интервью (минимальные поля для кандидата)
 */
interface InterviewCreate {
  candidate_id: string;
  vacancy_id?: string;
  scheduled_start: string;
  duration_minutes: number;
  interview_type: InterviewType;
  title: string;
  participant_ids?: string[];
}

/**
 * Ответ с данными интервью
 */
interface InterviewResponse {
  id: string;
  candidate_id: string;
  vacancy_id?: string;
  scheduled_start: string;
  scheduled_end: string;
  duration_minutes: number;
  interview_type: InterviewType;
  title: string;
  status: string;
  meeting_link?: string;
  created_at: string;
}

interface InterviewSchedulerProps {
  /** ID кандидата */
  candidateId: string;
  /** ID вакансии (опционально) */
  vacancyId?: string;
  /** Callback при успешной записи */
  onSuccess?: (interview: InterviewResponse) => void;
  /** Callback при отмене */
  onCancel?: () => void;
  /** Открыт ли диалог (для контролируемого режима) */
  open?: boolean;
}

/**
 * Компонент для самостоятельной записи кандидата на интервью
 * с визуальным календарем и выбором доступных временных слотов
 */
export function InterviewScheduler({
  candidateId,
  vacancyId,
  onSuccess,
  onCancel,
  open: controlledOpen,
}: InterviewSchedulerProps) {
  const queryClient = useQueryClient();

  // Состояние диалога
  const [internalOpen, setInternalOpen] = useState(true);
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;

  // Состояние календаря
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<AvailableSlot | null>(null);

  // Получение доступных слотов для текущего месяца
  const startDate = startOfMonth(currentMonth);
  const endDate = endOfMonth(currentMonth);

  const {
    data: slotsData,
    isLoading: isLoadingSlots,
    error: slotsError,
  } = useQuery({
    queryKey: ['availableSlots', vacancyId, format(startDate, 'yyyy-MM-dd')],
    queryFn: async () => {
      // Здесь должен быть реальный API endpoint для получения доступных слотов
      // Пока используем mock данные для демонстрации
      const mockSlots: AvailableSlot[] = [];

      // Генерируем несколько доступных слотов на следующие 2 недели
      const now = new Date();
      for (let i = 1; i <= 14; i++) {
        const date = addDays(now, i);

        // Пропускаем выходные
        if (date.getDay() === 0 || date.getDay() === 6) continue;

        // Добавляем слоты в 10:00, 14:00, 16:00
        [10, 14, 16].forEach((hour) => {
          const slotStart = new Date(date);
          slotStart.setHours(hour, 0, 0, 0);

          mockSlots.push({
            start_time: slotStart.toISOString(),
            end_time: addMinutes(slotStart, 60).toISOString(),
            duration_minutes: 60,
            recruiter_id: 'recruiter-1',
            recruiter_name: 'HR Specialist',
          });
        });
      }

      return {
        slots: mockSlots,
        total: mockSlots.length,
      } as AvailableSlotsResponse;
    },
    enabled: open,
  });

  // Создание интервью
  const createMutation = useMutation({
    mutationFn: async (slot: AvailableSlot) => {
      const interviewData: InterviewCreate = {
        candidate_id: candidateId,
        vacancy_id: vacancyId,
        scheduled_start: slot.start_time,
        duration_minutes: slot.duration_minutes,
        interview_type: 'video',
        title: 'Interview',
        participant_ids: [slot.recruiter_id],
      };

      return await interviewsClient.createInterview(interviewData);
    },
    onSuccess: (interview) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['availableSlots'] });
      if (onSuccess) {
        onSuccess(interview);
      }
      handleClose();
    },
  });

  // Получение слотов для выбранной даты
  const slotsForSelectedDate = useMemo(() => {
    if (!selectedDate || !slotsData?.slots) return [];

    return slotsData.slots.filter((slot) => {
      const slotDate = parseISO(slot.start_time);
      return isSameDay(slotDate, selectedDate);
    });
  }, [selectedDate, slotsData]);

  // Получение дат с доступными слотами
  const datesWithSlots = useMemo(() => {
    if (!slotsData?.slots) return new Set<string>();

    const dates = new Set<string>();
    slotsData.slots.forEach((slot) => {
      const slotDate = parseISO(slot.start_time);
      dates.add(format(slotDate, 'yyyy-MM-dd'));
    });

    return dates;
  }, [slotsData]);

  // Генерация дней календаря
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    const days: Date[] = [];
    let day = startDate;

    while (day <= endDate) {
      days.push(day);
      day = addDays(day, 1);
    }

    return days;
  }, [currentMonth]);

  const handlePreviousMonth = () => {
    setCurrentMonth(subMonths(currentMonth, 1));
    setSelectedDate(null);
    setSelectedSlot(null);
  };

  const handleNextMonth = () => {
    setCurrentMonth(addMonths(currentMonth, 1));
    setSelectedDate(null);
    setSelectedSlot(null);
  };

  const handleDateClick = (date: Date) => {
    // Не позволяем выбирать прошлые даты
    if (isBefore(date, startOfDay(new Date()))) return;

    // Не позволяем выбирать даты без слотов
    const dateKey = format(date, 'yyyy-MM-dd');
    if (!datesWithSlots.has(dateKey)) return;

    setSelectedDate(date);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot: AvailableSlot) => {
    setSelectedSlot(slot);
  };

  const handleConfirmBooking = () => {
    if (!selectedSlot) return;
    createMutation.mutate(selectedSlot);
  };

  const handleClose = () => {
    setInternalOpen(false);
    if (onCancel) {
      onCancel();
    }
  };

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            <EventIcon color="primary" />
            <Typography variant="h6">Schedule Your Interview</Typography>
          </Stack>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Select a date and time that works best for you
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Календарь */}
          <Paper sx={{ p: 2 }}>
            {/* Заголовок календаря */}
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
              sx={{ mb: 2 }}
            >
              <IconButton onClick={handlePreviousMonth} size="small">
                <ChevronLeftIcon />
              </IconButton>
              <Typography variant="h6" fontWeight={600}>
                {format(currentMonth, 'MMMM yyyy')}
              </Typography>
              <IconButton onClick={handleNextMonth} size="small">
                <ChevronRightIcon />
              </IconButton>
            </Stack>

            {/* Дни недели */}
            <Grid2 container spacing={1} sx={{ mb: 1 }}>
              {weekDays.map((day) => (
                <Grid2 key={day} size={{ xs: 12 / 7 }}>
                  <Typography
                    variant="caption"
                    fontWeight={600}
                    color="text.secondary"
                    sx={{ textAlign: 'center', display: 'block' }}
                  >
                    {day}
                  </Typography>
                </Grid2>
              ))}
            </Grid2>

            {/* Дни месяца */}
            <Grid2 container spacing={1}>
              {calendarDays.map((day, index) => {
                const dateKey = format(day, 'yyyy-MM-dd');
                const hasSlots = datesWithSlots.has(dateKey);
                const isPast = isBefore(day, startOfDay(new Date()));
                const isCurrentMonth = isSameMonth(day, currentMonth);
                const isSelected = selectedDate && isSameDay(day, selectedDate);
                const isTodayDate = isToday(day);

                return (
                  <Grid2 key={index} size={{ xs: 12 / 7 }}>
                    <Box
                      onClick={() => handleDateClick(day)}
                      sx={{
                        aspectRatio: '1',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: 1,
                        cursor: hasSlots && !isPast ? 'pointer' : 'default',
                        bgcolor: isSelected
                          ? 'primary.main'
                          : isTodayDate
                          ? 'primary.light'
                          : 'transparent',
                        color: isSelected
                          ? 'primary.contrastText'
                          : !isCurrentMonth
                          ? 'text.disabled'
                          : isPast
                          ? 'text.disabled'
                          : 'text.primary',
                        border: hasSlots && !isPast ? '2px solid' : '1px solid',
                        borderColor: isSelected
                          ? 'primary.main'
                          : hasSlots && !isPast
                          ? 'success.main'
                          : 'divider',
                        fontWeight: isTodayDate ? 700 : 400,
                        opacity: !isCurrentMonth || isPast ? 0.5 : 1,
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: hasSlots && !isPast && !isSelected
                            ? 'action.hover'
                            : undefined,
                          transform: hasSlots && !isPast ? 'scale(1.05)' : undefined,
                        },
                      }}
                    >
                      <Typography variant="body2" fontWeight="inherit">
                        {format(day, 'd')}
                      </Typography>
                    </Box>
                  </Grid2>
                );
              })}
            </Grid2>

            {/* Легенда */}
            <Stack direction="row" spacing={2} sx={{ mt: 2 }} justifyContent="center">
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: 1,
                    border: '2px solid',
                    borderColor: 'success.main',
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Available
                </Typography>
              </Stack>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: 1,
                    bgcolor: 'primary.main',
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Selected
                </Typography>
              </Stack>
            </Stack>
          </Paper>

          {/* Доступные слоты для выбранной даты */}
          {selectedDate && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                Available Times for {format(selectedDate, 'MMMM d, yyyy')}
              </Typography>

              {isLoadingSlots ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress />
                </Box>
              ) : slotsForSelectedDate.length === 0 ? (
                <Alert severity="info">
                  No available time slots for this date. Please select another date.
                </Alert>
              ) : (
                <Grid2 container spacing={1}>
                  {slotsForSelectedDate.map((slot, index) => {
                    const startTime = parseISO(slot.start_time);
                    const isSelected = selectedSlot?.start_time === slot.start_time;

                    return (
                      <Grid2 key={index} size={{ xs: 6, sm: 4 }}>
                        <Button
                          fullWidth
                          variant={isSelected ? 'contained' : 'outlined'}
                          onClick={() => handleSlotSelect(slot)}
                          startIcon={<TimeIcon />}
                          sx={{
                            justifyContent: 'flex-start',
                            py: 1.5,
                            textTransform: 'none',
                          }}
                        >
                          <Stack spacing={0.5} alignItems="flex-start">
                            <Typography variant="body2" fontWeight={600}>
                              {format(startTime, 'h:mm a')}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {slot.duration_minutes} min
                            </Typography>
                          </Stack>
                        </Button>
                      </Grid2>
                    );
                  })}
                </Grid2>
              )}
            </Paper>
          )}

          {/* Детали выбранного слота */}
          {selectedSlot && (
            <Paper sx={{ p: 2, bgcolor: 'success.lighter', border: '1px solid', borderColor: 'success.main' }}>
              <Stack spacing={1}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <CheckIcon color="success" fontSize="small" />
                  <Typography variant="subtitle2" fontWeight={600}>
                    Interview Details
                  </Typography>
                </Stack>
                <Stack spacing={0.5}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <EventIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      {selectedDate && format(selectedDate, 'MMMM d, yyyy')} at{' '}
                      {format(parseISO(selectedSlot.start_time), 'h:mm a')}
                    </Typography>
                  </Stack>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <TimeIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      Duration: {selectedSlot.duration_minutes} minutes
                    </Typography>
                  </Stack>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <VideoIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      Video Interview
                    </Typography>
                  </Stack>
                  {selectedSlot.recruiter_name && (
                    <Typography variant="caption" color="text.secondary">
                      with {selectedSlot.recruiter_name}
                    </Typography>
                  )}
                </Stack>
              </Stack>
            </Paper>
          )}

          {/* Состояние загрузки */}
          {isLoadingSlots && !selectedDate && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Ошибка загрузки */}
          {slotsError && (
            <Alert severity="error">
              Failed to load available time slots. Please try again.
            </Alert>
          )}

          {/* Ошибка создания */}
          {createMutation.isError && (
            <Alert severity="error">
              Failed to schedule interview. Please try again.
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={createMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirmBooking}
          variant="contained"
          disabled={!selectedSlot || createMutation.isPending}
          startIcon={createMutation.isPending ? <CircularProgress size={16} /> : <CheckIcon />}
        >
          {createMutation.isPending ? 'Booking...' : 'Confirm Booking'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default InterviewScheduler;
