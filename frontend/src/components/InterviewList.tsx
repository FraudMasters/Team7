/**
 * Interview List Component
 *
 * Displays a filterable list of interviews with candidate details,
 * scheduling information, and participant lists. Supports filtering
 * by status, date range, candidate, and vacancy.
 */

import { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Stack,
  Grid2,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Event as EventIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  VideoCall as VideoIcon,
  LocationOn as LocationIcon,
  Phone as PhoneIcon,
  Business as BusinessIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { interviewsClient, type InterviewListFilters } from '../api/interviews';
import type {
  InterviewResponse,
  InterviewStatus,
  InterviewType,
} from '../types/api';

interface InterviewListProps {
  candidateId?: string;
  vacancyId?: string;
  interviewerId?: string;
  status?: InterviewStatus;
  onInterviewClick?: (interview: InterviewResponse) => void;
  autoRefresh?: boolean;
}

/**
 * Interview status configuration with colors and labels
 */
const STATUS_CONFIG: Record<
  InterviewStatus,
  { label: string; color: 'success' | 'warning' | 'error' | 'info' | 'default' }
> = {
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
const TYPE_CONFIG: Record<
  InterviewType,
  { label: string; icon: React.ReactElement }
> = {
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
    year: 'numeric',
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

export function InterviewList({
  candidateId,
  vacancyId,
  interviewerId,
  status: propStatus,
  onInterviewClick,
  autoRefresh = true,
}: InterviewListProps) {
  // Filter state
  const [statusFilter, setStatusFilter] = useState<InterviewStatus | 'all'>(
    propStatus ?? 'all'
  );
  const [typeFilter, setTypeFilter] = useState<InterviewType | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Build query filters
  const queryFilters = useMemo<InterviewListFilters>(() => {
    const filters: InterviewListFilters = {
      skip: 0,
      limit: 100,
    };

    if (candidateId) filters.candidate_id = candidateId;
    if (vacancyId) filters.vacancy_id = vacancyId;
    if (interviewerId) filters.interviewer_id = interviewerId;
    if (statusFilter !== 'all') filters.status = statusFilter;

    return filters;
  }, [candidateId, vacancyId, interviewerId, statusFilter]);

  // Fetch interviews
  const {
    data: interviewsData,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['interviews', queryFilters],
    queryFn: async () => {
      return await interviewsClient.listInterviews(queryFilters);
    },
    enabled: autoRefresh,
    refetchInterval: autoRefresh ? 60000 : false, // Refresh every minute if enabled
  });

  // Filter interviews based on client-side filters
  const filteredInterviews = useMemo(() => {
    if (!interviewsData?.items) return [];

    return interviewsData.items.filter((interview) => {
      // Type filter
      if (typeFilter !== 'all' && interview.interview_type !== typeFilter) {
        return false;
      }

      // Date range filter
      if (startDate) {
        const interviewDate = new Date(interview.scheduled_start);
        const filterStartDate = new Date(startDate);
        if (interviewDate < filterStartDate) {
          return false;
        }
      }

      if (endDate) {
        const interviewDate = new Date(interview.scheduled_start);
        const filterEndDate = new Date(endDate);
        filterEndDate.setHours(23, 59, 59);
        if (interviewDate > filterEndDate) {
          return false;
        }
      }

      // Search term filter (title, candidate name, location)
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const titleMatch = interview.title.toLowerCase().includes(searchLower);
        const locationMatch =
          interview.location?.toLowerCase().includes(searchLower);
        const descriptionMatch =
          interview.description?.toLowerCase().includes(searchLower);

        if (!titleMatch && !locationMatch && !descriptionMatch) {
          return false;
        }
      }

      return true;
    });
  }, [interviewsData, typeFilter, startDate, endDate, searchTerm]);

  // Sort interviews by date (nearest first)
  const sortedInterviews = useMemo(() => {
    return [...filteredInterviews].sort((a, b) => {
      const dateA = new Date(a.scheduled_start).getTime();
      const dateB = new Date(b.scheduled_start).getTime();
      return dateA - dateB;
    });
  }, [filteredInterviews]);

  const handleRefresh = () => {
    refetch();
  };

  const handleClearFilters = () => {
    setStatusFilter(propStatus ?? 'all');
    setTypeFilter('all');
    setSearchTerm('');
    setStartDate('');
    setEndDate('');
  };

  const hasActiveFilters =
    statusFilter !== 'all' ||
    typeFilter !== 'all' ||
    searchTerm ||
    startDate ||
    endDate;

  // Render loading state
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 400,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Paper sx={{ p: 3, bgcolor: 'error.main', color: 'error.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          Failed to load interviews
        </Typography>
        <Typography variant="body2">
          {(error as Error).message || 'An unknown error occurred'}
        </Typography>
        <Button
          variant="outlined"
          color="inherit"
          onClick={handleRefresh}
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Filters Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <FilterIcon sx={{ mr: 1 }} />
          <Typography variant="h6" fontWeight={600}>
            Filters
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton onClick={handleRefresh} disabled={isRefetching}>
            <RefreshIcon />
          </IconButton>
        </Box>

        <Grid2 container spacing={2}>
          {/* Status Filter */}
          <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) =>
                  setStatusFilter(e.target.value as InterviewStatus | 'all')
                }
              >
                <MenuItem value="all">All Statuses</MenuItem>
                {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                  <MenuItem key={value} value={value}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid2>

          {/* Type Filter */}
          <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                label="Type"
                onChange={(e) =>
                  setTypeFilter(e.target.value as InterviewType | 'all')
                }
              >
                <MenuItem value="all">All Types</MenuItem>
                {Object.entries(TYPE_CONFIG).map(([value, config]) => (
                  <MenuItem key={value} value={value}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid2>

          {/* Search */}
          <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              placeholder="Title, location..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Grid2>

          {/* Clear Filters */}
          <Grid2 size={{ xs: 12, sm: 6, md: 3 }}>
            <Button
              fullWidth
              variant="outlined"
              onClick={handleClearFilters}
              disabled={!hasActiveFilters}
            >
              Clear Filters
            </Button>
          </Grid2>

          {/* Date Range */}
          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="From Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid2>

          <Grid2 size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="To Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid2>
        </Grid2>
      </Paper>

      {/* Results Summary */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Showing {sortedInterviews.length} of {interviewsData?.total || 0}{' '}
          interviews
        </Typography>
      </Box>

      {/* Interview List */}
      {sortedInterviews.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', bgcolor: 'action.hover' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {hasActiveFilters
              ? 'No interviews match your filters'
              : 'No interviews scheduled'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {hasActiveFilters
              ? 'Try adjusting your filter criteria'
              : 'Schedule your first interview to get started'}
          </Typography>
        </Paper>
      ) : (
        <Stack spacing={2}>
          {sortedInterviews.map((interview) => {
            const statusConfig = STATUS_CONFIG[interview.status];
            const typeConfig = TYPE_CONFIG[interview.interview_type];

            return (
              <Paper
                key={interview.id}
                sx={{
                  p: 2,
                  cursor: onInterviewClick ? 'pointer' : 'default',
                  transition: 'all 0.2s',
                  border: '2px solid transparent',
                  '&:hover': onInterviewClick
                    ? {
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                        borderColor: 'primary.main',
                      }
                    : {},
                }}
                onClick={() =>
                  onInterviewClick ? onInterviewClick(interview) : undefined
                }
                tabIndex={0}
                aria-label={`Interview: ${interview.title}`}
              >
                {/* Header Row */}
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    mb: 1.5,
                  }}
                >
                  <Box sx={{ flexGrow: 1 }}>
                    <Box
                      sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}
                    >
                      <EventIcon
                        sx={{
                          mr: 1,
                          color: 'primary.main',
                          fontSize: { xs: 18, sm: 20 },
                        }}
                      />
                      <Typography
                        variant="h6"
                        fontWeight={600}
                        sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                      >
                        {interview.title}
                      </Typography>
                    </Box>

                    {/* Type and Status Chips */}
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Chip
                        icon={typeConfig.icon}
                        label={typeConfig.label}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={statusConfig.label}
                        size="small"
                        color={statusConfig.color}
                      />
                      <Chip
                        label={`${interview.duration_minutes} min`}
                        size="small"
                        variant="outlined"
                        icon={<TimeIcon fontSize="small" />}
                      />
                    </Box>
                  </Box>
                </Box>

                {/* Date and Time */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mb: 1,
                    flexWrap: 'wrap',
                    gap: 2,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <EventIcon
                      sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(interview.scheduled_start)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimeIcon
                      sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {formatTime(interview.scheduled_start)} -{' '}
                      {formatTime(interview.scheduled_end)}
                    </Typography>
                  </Box>
                </Box>

                {/* Location or Meeting Link */}
                {(interview.location || interview.meeting_link) && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    {interview.location ? (
                      <>
                        <LocationIcon
                          sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {interview.location}
                        </Typography>
                      </>
                    ) : interview.meeting_link ? (
                      <>
                        <VideoIcon
                          sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }}
                        />
                        <Typography
                          variant="body2"
                          color="primary"
                          component="a"
                          href={interview.meeting_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            textDecoration: 'none',
                            '&:hover': { textDecoration: 'underline' },
                          }}
                        >
                          Join Meeting
                        </Typography>
                      </>
                    ) : null}
                  </Box>
                )}

                {/* Meeting Room */}
                {interview.meeting_room && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <BusinessIcon
                      sx={{ mr: 0.5, fontSize: 16, color: 'text.secondary' }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      Room: {interview.meeting_room}
                    </Typography>
                  </Box>
                )}

                {/* Participants */}
                {interview.participants && interview.participants.length > 0 && (
                  <Box sx={{ mt: 1.5 }}>
                    <Divider sx={{ mb: 1 }} />
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: 0.5,
                      }}
                    >
                      <PersonIcon
                        sx={{ fontSize: 16, color: 'text.secondary', mr: 0.5 }}
                      />
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mr: 1 }}
                      >
                        {interview.participants.length} participant
                        {interview.participants.length !== 1 ? 's' : ''}:
                      </Typography>
                      {interview.participants.map((participant) => (
                        <Chip
                          key={participant.id}
                          label={participant.role.replace(/_/g, ' ')}
                          size="small"
                          variant="outlined"
                          sx={{
                            fontSize: '0.7rem',
                            height: 20,
                            borderColor:
                              participant.status === 'accepted'
                                ? 'success.main'
                                : participant.status === 'declined'
                                ? 'error.main'
                                : 'divider',
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* Calendar Sync Status */}
                {interview.calendar_event_id && (
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={`Synced with ${interview.calendar_provider || 'calendar'}`}
                      size="small"
                      color="success"
                      icon={<CheckIcon fontSize="small" />}
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                )}
              </Paper>
            );
          })}
        </Stack>
      )}
    </Box>
  );
}

export default InterviewList;
