/**
 * Hiring Manager Interview Schedule Page
 *
 * Calendar view and interview scheduling page for hiring managers.
 * Shows upcoming interviews with calendar integration and allows
 * scheduling new interviews for candidates in the review queue.
 * Mobile-optimized for tablet access between meetings.
 */

import { useState, useMemo } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Stack,
  Grid,
  Button,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  Divider,
  Card,
  CardContent,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Event as EventIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  VideoCall as VideoIcon,
  LocationOn as LocationIcon,
  Add as AddIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon,
  Schedule as ScheduleIcon,
  Phone as PhoneIcon,
  Check as CheckIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { interviewsClient, type InterviewListFilters } from '../../api/interviews';
import { InterviewScheduler } from '../../components/InterviewScheduler';
import type { InterviewResponse, InterviewType, InterviewStatus } from '../../types/api';

/**
 * Interview status configuration with colors and labels
 */
const STATUS_CONFIG: Record<InterviewStatus, { label: string; color: 'success' | 'warning' | 'error' | 'info' | 'default' }> = {
  scheduled: { label: 'Scheduled', color: 'info' },
  confirmed: { label: 'Confirmed', color: 'success' },
  cancelled: { label: 'Cancelled', color: 'error' },
  completed: { label: 'Completed', color: 'default' },
  no_show: { label: 'No Show', color: 'error' },
  rescheduled: { label: 'Rescheduled', color: 'warning' },
};

/**
 * Interview type configuration with icons
 */
const TYPE_CONFIG: Record<InterviewType, { label: string; icon: React.ReactElement }> = {
  phone: { label: 'Phone', icon: <PhoneIcon fontSize="small" /> },
  video: { label: 'Video', icon: <VideoIcon fontSize="small" /> },
  onsite: { label: 'On-site', icon: <LocationIcon fontSize="small" /> },
  technical: { label: 'Technical', icon: <EventIcon fontSize="small" /> },
  panel: { label: 'Panel', icon: <PersonIcon fontSize="small" /> },
};

/**
 * Format date to readable string
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format time to readable string
 */
function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Get days in a month for calendar view
 */
function getDaysInMonth(year: number, month: number): (Date | null)[] {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startingDayOfWeek = firstDay.getDay();

  const days: (Date | null)[] = [];

  // Add empty slots for days before the first day of the month
  for (let i = 0; i < startingDayOfWeek; i++) {
    days.push(null);
  }

  // Add all days in the month
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(new Date(year, month, i));
  }

  return days;
}

/**
 * Check if two dates are the same day
 */
function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
}

/**
 * Hiring Manager Interview Schedule Page Component
 */
export function InterviewSchedulePage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Calendar state
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

  // Scheduler dialog state
  const [schedulerOpen, setSchedulerOpen] = useState(false);
  const [selectedInterview, setSelectedInterview] = useState<InterviewResponse | null>(null);

  // Current month/year for calendar
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth();

  // Calculate date range for the current month
  const monthStart = new Date(currentYear, currentMonth, 1);
  const monthEnd = new Date(currentYear, currentMonth + 1, 0);

  // Build query filters for the current month
  const queryFilters: InterviewListFilters = useMemo(() => ({
    start_date: monthStart.toISOString(),
    end_date: monthEnd.toISOString(),
    limit: 200,
  }), [monthStart, monthEnd]);

  // Fetch interviews for the current month
  const {
    data: interviewsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['interviews', 'hiring-manager', queryFilters],
    queryFn: async () => {
      return await interviewsClient.listInterviews(queryFilters);
    },
  });

  // Group interviews by date for calendar view
  const interviewsByDate = useMemo(() => {
    const grouped: Record<string, InterviewResponse[]> = {};

    if (interviewsData?.items) {
      interviewsData.items.forEach((interview) => {
        const dateKey = new Date(interview.scheduled_start).toDateString();
        if (!grouped[dateKey]) {
          grouped[dateKey] = [];
        }
        grouped[dateKey].push(interview);
      });
    }

    return grouped;
  }, [interviewsData]);

  // Get interviews for selected date
  const selectedDateInterviews = useMemo(() => {
    if (!selectedDate) return [];

    const dateKey = selectedDate.toDateString();
    const interviews = interviewsByDate[dateKey] || [];

    // Sort by time
    return [...interviews].sort((a, b) => {
      const timeA = new Date(a.scheduled_start).getTime();
      const timeB = new Date(b.scheduled_start).getTime();
      return timeA - timeB;
    });
  }, [selectedDate, interviewsByDate]);

  // Get upcoming interviews (next 7 days)
  const upcomingInterviews = useMemo(() => {
    if (!interviewsData?.items) return [];

    const now = new Date();
    const sevenDaysLater = new Date(now);
    sevenDaysLater.setDate(sevenDaysLater.getDate() + 7);

    return interviewsData.items
      .filter((interview) => {
        const interviewDate = new Date(interview.scheduled_start);
        return interviewDate >= now && interviewDate <= sevenDaysLater;
      })
      .sort((a, b) => new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime())
      .slice(0, 5);
  }, [interviewsData]);

  // Calendar navigation
  const handlePreviousMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  // Calendar days
  const calendarDays = useMemo(() => {
    return getDaysInMonth(currentYear, currentMonth);
  }, [currentYear, currentMonth]);

  // Week day headers
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Handle scheduling new interview
  const handleScheduleNew = () => {
    setSelectedInterview(null);
    setSchedulerOpen(true);
  };

  // Handle interview click
  const handleInterviewClick = (interview: InterviewResponse) => {
    setSelectedInterview(interview);
    setSchedulerOpen(true);
  };

  // Handle scheduler close
  const handleSchedulerClose = () => {
    setSchedulerOpen(false);
    setSelectedInterview(null);
    refetch();
  };

  // Stats for summary
  const stats = useMemo(() => {
    const today = new Date();
    const todayKey = today.toDateString();
    const todayInterviews = interviewsByDate[todayKey] || [];

    const scheduledCount = interviewsData?.items?.filter(
      (i) => i.status === 'scheduled' || i.status === 'confirmed'
    ).length || 0;

    return {
      todayCount: todayInterviews.length,
      scheduledCount,
      totalCount: interviewsData?.total || 0,
    };
  }, [interviewsData, interviewsByDate]);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          {t('hiringManagerSchedule.title', 'Interview Schedule')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('hiringManagerSchedule.subtitle', 'Manage your upcoming interviews and availability')}
        </Typography>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary.main" fontWeight={700}>
              {stats.todayCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('hiringManagerSchedule.stats.today', 'Today')}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="info.main" fontWeight={700}>
              {stats.scheduledCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('hiringManagerSchedule.stats.scheduled', 'Scheduled')}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main" fontWeight={700}>
              {stats.totalCount}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('hiringManagerSchedule.stats.thisMonth', 'This Month')}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
            }}
          >
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleScheduleNew}
              sx={{ minWidth: 44, minHeight: 44 }}
            >
              {t('hiringManagerSchedule.scheduleInterview', 'Schedule')}
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Calendar Section */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            {/* Calendar Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
              </Typography>
              <Stack direction="row" spacing={1}>
                <IconButton onClick={handleToday} size="small" title="Today">
                  <TodayIcon />
                </IconButton>
                <IconButton onClick={handlePreviousMonth} size="small">
                  <ChevronLeftIcon />
                </IconButton>
                <IconButton onClick={handleNextMonth} size="small">
                  <ChevronRightIcon />
                </IconButton>
              </Stack>
            </Box>

            {/* Week Day Headers */}
            <Grid container spacing={0.5} sx={{ mb: 1 }}>
              {weekDays.map((day) => (
                <Grid item xs={12 / 7} key={day}>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    align="center"
                    sx={{ display: 'block', fontWeight: 600 }}
                  >
                    {day}
                  </Typography>
                </Grid>
              ))}
            </Grid>

            {/* Calendar Days */}
            <Grid container spacing={0.5}>
              {calendarDays.map((date, index) => {
                if (!date) {
                  return <Grid item xs={12 / 7} key={`empty-${index}`} />;
                }

                const dateKey = date.toDateString();
                const dayInterviews = interviewsByDate[dateKey] || [];
                const isToday = isSameDay(date, new Date());
                const isSelected = selectedDate && isSameDay(date, selectedDate);
                const hasInterviews = dayInterviews.length > 0;

                return (
                  <Grid item xs={12 / 7} key={date.toISOString()}>
                    <Paper
                      sx={{
                        p: 0.5,
                        minHeight: { xs: 60, sm: 80 },
                        cursor: 'pointer',
                        bgcolor: isSelected ? 'primary.light' : isToday ? 'action.hover' : 'transparent',
                        border: isSelected ? 2 : isToday ? 1 : 0,
                        borderColor: isSelected ? 'primary.main' : isToday ? 'primary.light' : 'transparent',
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
                      }}
                      onClick={() => setSelectedDate(date)}
                    >
                      <Typography
                        variant="body2"
                        align="center"
                        fontWeight={isToday ? 700 : 400}
                        color={isToday ? 'primary.main' : 'text.primary'}
                      >
                        {date.getDate()}
                      </Typography>
                      {hasInterviews && (
                        <Box sx={{ mt: 0.5 }}>
                          {dayInterviews.slice(0, 3).map((interview, i) => (
                            <Box
                              key={interview.id}
                              sx={{
                                height: 4,
                                borderRadius: 2,
                                bgcolor: `${STATUS_CONFIG[interview.status]?.color}.main` || 'info.main',
                                mb: 0.25,
                              }}
                              title={`${interview.title} - ${formatTime(interview.scheduled_start)}`}
                            />
                          ))}
                          {dayInterviews.length > 3 && (
                            <Typography variant="caption" color="text.secondary">
                              +{dayInterviews.length - 3} more
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Paper>
                  </Grid>
                );
              })}
            </Grid>
          </Paper>
        </Grid>

        {/* Selected Date Details / Upcoming Section */}
        <Grid item xs={12} md={4}>
          <Stack spacing={2}>
            {/* Selected Date Interviews */}
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                {selectedDate
                  ? `${formatDate(selectedDate.toISOString())} Interviews`
                  : 'Select a Date'}
              </Typography>

              {isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : selectedDateInterviews.length === 0 ? (
                <Box sx={{ py: 4, textAlign: 'center' }}>
                  <EventIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    {t('hiringManagerSchedule.noInterviews', 'No interviews scheduled')}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={handleScheduleNew}
                    sx={{ mt: 2 }}
                  >
                    Schedule One
                  </Button>
                </Box>
              ) : (
                <Stack spacing={1.5}>
                  {selectedDateInterviews.map((interview) => {
                    const statusConfig = STATUS_CONFIG[interview.status];
                    const typeConfig = TYPE_CONFIG[interview.interview_type];

                    return (
                      <Card
                        key={interview.id}
                        sx={{
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          border: '1px solid',
                          borderColor: 'divider',
                          '&:hover': {
                            boxShadow: 2,
                            borderColor: 'primary.main',
                          },
                        }}
                        onClick={() => handleInterviewClick(interview)}
                      >
                        <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                            <Box sx={{ minWidth: 36 }}>
                              {typeConfig.icon}
                            </Box>
                            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                              <Typography
                                variant="subtitle2"
                                fontWeight={600}
                                noWrap
                                sx={{ fontSize: '0.875rem' }}
                              >
                                {interview.title}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                <TimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                                <Typography variant="caption" color="text.secondary">
                                  {formatTime(interview.scheduled_start)} -{' '}
                                  {formatTime(interview.scheduled_end)}
                                </Typography>
                              </Box>
                              <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                                <Chip
                                  label={typeConfig.label}
                                  size="small"
                                  variant="outlined"
                                  sx={{ height: 20, fontSize: '0.7rem' }}
                                />
                                <Chip
                                  label={statusConfig.label}
                                  size="small"
                                  color={statusConfig.color}
                                  sx={{ height: 20, fontSize: '0.7rem' }}
                                />
                              </Box>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    );
                  })}
                </Stack>
              )}
            </Paper>

            {/* Upcoming Interviews Summary */}
            {!isMobile && upcomingInterviews.length > 0 && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  {t('hiringManagerSchedule.upcoming', 'Upcoming This Week')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Stack spacing={1.5}>
                  {upcomingInterviews.map((interview) => (
                    <Box
                      key={interview.id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        py: 1,
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        '&:last-child': { borderBottom: 0 },
                      }}
                    >
                      <ScheduleIcon color="primary" fontSize="small" />
                      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                        <Typography variant="body2" fontWeight={500} noWrap>
                          {interview.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(interview.scheduled_start)} at{' '}
                          {formatTime(interview.scheduled_start)}
                        </Typography>
                      </Box>
                      <Chip
                        label={TYPE_CONFIG[interview.interview_type]?.label || interview.interview_type}
                        size="small"
                        variant="outlined"
                        sx={{ height: 24 }}
                      />
                    </Box>
                  ))}
                </Stack>
              </Paper>
            )}
          </Stack>
        </Grid>
      </Grid>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {t('hiringManagerSchedule.loadError', 'Failed to load interviews')}: {(error as Error).message}
          <Button size="small" onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {/* Interview Scheduler Dialog */}
      {schedulerOpen && (
        <InterviewScheduler
          candidateId={selectedInterview?.candidate_id || ''}
          candidateName={undefined}
          vacancyId={selectedInterview?.vacancy_id}
          onSuccess={() => {
            handleSchedulerClose();
          }}
          onCancel={handleSchedulerClose}
        />
      )}

      {/* Mobile Tip */}
      <Box sx={{ mt: 4, p: 2, bgcolor: 'info.lighter', borderRadius: 2 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>
            {t('hiringManagerSchedule.tip.icon', '💡')} {t('hiringManagerSchedule.tip.title', 'Tip:')}
          </strong>{' '}
          {t(
            'hiringManagerSchedule.tip.content',
            'Tap on a day to see scheduled interviews. Tap on an interview to view details or reschedule.'
          )}
        </Typography>
      </Box>
    </Container>
  );
}

export default InterviewSchedulePage;
