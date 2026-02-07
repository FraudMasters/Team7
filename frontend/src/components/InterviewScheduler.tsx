/**
 * Interview Scheduler Component
 *
 * Schedule interviews for candidates with date/time selection, interviewer assignment,
 * and calendar integration.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Paper,
  Alert,
  CircularProgress,
  Grid2,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Event as EventIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  VideoCall as VideoIcon,
  LocationOn as LocationIcon,
  Close as CloseIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewsClient } from '../api/interviews';
import { calendarClient } from '../api/calendar';
import type {
  InterviewCreate,
  InterviewType,
  InterviewResponse,
  InterviewerAvailability,
} from '../types/api';

interface InterviewSchedulerProps {
  candidateId: string;
  candidateName?: string;
  vacancyId?: string;
  onSuccess?: (interview: InterviewResponse) => void;
  onCancel?: () => void;
}

const INTERVIEW_TYPES: { value: InterviewType; label: string; icon: React.ReactElement }[] = [
  { value: 'phone', label: 'Phone Screen', icon: <EventIcon fontSize="small" /> },
  { value: 'video', label: 'Video Interview', icon: <VideoIcon fontSize="small" /> },
  { value: 'onsite', label: 'On-site Interview', icon: <LocationIcon fontSize="small" /> },
  { value: 'technical', label: 'Technical Assessment', icon: <EventIcon fontSize="small" /> },
  { value: 'panel', label: 'Panel Interview', icon: <PersonIcon fontSize="small" /> },
];

const DURATION_OPTIONS = [30, 45, 60, 75, 90, 120];

export function InterviewScheduler({
  candidateId,
  candidateName,
  vacancyId,
  onSuccess,
  onCancel,
}: InterviewSchedulerProps) {
  const queryClient = useQueryClient();

  // Form state
  const [open, setOpen] = useState(true);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [interviewType, setInterviewType] = useState<InterviewType>('video');
  const [date, setDate] = useState<Date | null>(null);
  const [time, setTime] = useState<Date | null>(null);
  const [duration, setDuration] = useState(60);
  const [location, setLocation] = useState('');
  const [meetingLink, setMeetingLink] = useState('');
  const [meetingRoom, setMeetingRoom] = useState('');
  const [selectedInterviewers, setSelectedInterviewers] = useState<string[]>([]);
  const [availabilityStatus, setAvailabilityStatus] = useState<InterviewerAvailability[]>([]);
  const [checkingAvailability, setCheckingAvailability] = useState(false);

  // Create interview mutation
  const createMutation = useMutation({
    mutationFn: async (data: InterviewCreate) => {
      return await interviewsClient.createInterview(data);
    },
    onSuccess: (interview) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidateId, 'interviews'] });
      if (onSuccess) {
        onSuccess(interview);
      }
      handleClose();
    },
  });

  // Check availability mutation
  const checkAvailabilityMutation = useMutation({
    mutationFn: async (interviewerIds: string[]) => {
      if (!date || !time) {
        throw new Error('Date and time must be selected to check availability');
      }

      const scheduledStart = new Date(date);
      const timeHours = time.getHours();
      const timeMinutes = time.getMinutes();
      scheduledStart.setHours(timeHours, timeMinutes, 0, 0);

      return await calendarClient.checkAvailability({
        interviewer_ids: interviewerIds,
        start_time: scheduledStart.toISOString(),
        duration_minutes: duration,
      });
    },
    onSuccess: (response) => {
      setAvailabilityStatus(response.interviewers || []);
      setCheckingAvailability(false);
    },
    onError: () => {
      setCheckingAvailability(false);
    },
  });

  const handleClose = () => {
    setOpen(false);
    if (onCancel) {
      onCancel();
    }
  };

  const handleCheckAvailability = () => {
    if (selectedInterviewers.length === 0) {
      return;
    }

    setCheckingAvailability(true);
    checkAvailabilityMutation.mutate(selectedInterviewers);
  };

  const handleSubmit = () => {
    if (!title.trim() || !date || !time) {
      return;
    }

    const scheduledStart = new Date(date);
    const timeHours = time.getHours();
    const timeMinutes = time.getMinutes();
    scheduledStart.setHours(timeHours, timeMinutes, 0, 0);

    const interviewData: InterviewCreate = {
      candidate_id: candidateId,
      vacancy_id: vacancyId,
      scheduled_start: scheduledStart.toISOString(),
      duration_minutes: duration,
      interview_type: interviewType,
      title: title.trim(),
      description: description.trim() || undefined,
      location: location.trim() || undefined,
      meeting_link: meetingLink.trim() || undefined,
      meeting_room: meetingRoom.trim() || undefined,
      participant_ids: selectedInterviewers.length > 0 ? selectedInterviewers : undefined,
    };

    createMutation.mutate(interviewData);
  };

  const isFormValid = title.trim() && date && time;
  const allInterviewersAvailable = availabilityStatus.length > 0 &&
    availabilityStatus.every((i) => i.is_available);

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            <EventIcon color="primary" />
            <Typography variant="h6">Schedule Interview</Typography>
          </Stack>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
        {candidateName && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Candidate: {candidateName}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Title */}
          <TextField
            fullWidth
            label="Interview Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Technical Interview - Round 1"
            required
            autoFocus
            slotProps={{
              input: {
                'aria-label': 'Interview title',
              },
            }}
          />

          {/* Interview Type */}
          <FormControl fullWidth required>
            <InputLabel id="interview-type-label">Interview Type</InputLabel>
            <Select
              labelId="interview-type-label"
              value={interviewType}
              label="Interview Type"
              onChange={(e) => setInterviewType(e.target.value as InterviewType)}
            >
              {INTERVIEW_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    {type.icon}
                    <span>{type.label}</span>
                  </Stack>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Date and Time */}
          <Grid2 container spacing={2}>
            <Grid2 size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="date"
                label="Date"
                value={date}
                onChange={(e) => setDate(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
                required
                slotProps={{
                  input: {
                    'aria-label': 'Interview date',
                  },
                }}
              />
            </Grid2>
            <Grid2 size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                type="time"
                label="Time"
                value={time}
                onChange={(e) => setTime(e.target.value ? new Date(`1970-01-01T${e.target.value}`) : null)}
                InputLabelProps={{ shrink: true }}
                required
                slotProps={{
                  input: {
                    'aria-label': 'Interview time',
                  },
                }}
              />
            </Grid2>
          </Grid2>

          {/* Duration */}
          <FormControl fullWidth required>
            <InputLabel id="duration-label">Duration</InputLabel>
            <Select
              labelId="duration-label"
              value={duration}
              label="Duration"
              onChange={(e) => setDuration(Number(e.target.value))}
            >
              {DURATION_OPTIONS.map((mins) => (
                <MenuItem key={mins} value={mins}>
                  {mins} minutes
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Description */}
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description (Optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add interview details, preparation notes, or agenda..."
            slotProps={{
              input: {
                'aria-label': 'Interview description',
              },
            }}
          />

          {/* Location (for onsite interviews) */}
          {(interviewType === 'onsite' || interviewType === 'panel') && (
            <TextField
              fullWidth
              label="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., Building A, Room 301"
              slotProps={{
                inputProps: {
                  startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                },
                input: {
                  'aria-label': 'Interview location',
                },
              }}
            />
          )}

          {/* Meeting Link (for video interviews) */}
          {interviewType === 'video' && (
            <TextField
              fullWidth
              label="Meeting Link"
              value={meetingLink}
              onChange={(e) => setMeetingLink(e.target.value)}
              placeholder="https://meet.google.com/xxx-xxxx-xxx"
              slotProps={{
                inputProps: {
                  startAdornment: <VideoIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                },
                input: {
                  'aria-label': 'Video meeting link',
                },
              }}
            />
          )}

          {/* Meeting Room (optional) */}
          <TextField
            fullWidth
            label="Meeting Room (Optional)"
            value={meetingRoom}
            onChange={(e) => setMeetingRoom(e.target.value)}
            placeholder="e.g., Conference Room B"
            slotProps={{
              input: {
                'aria-label': 'Meeting room',
              },
            }}
          />

          {/* Interviewers Section */}
          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <PersonIcon color="primary" />
                <Typography variant="subtitle1">Interviewers</Typography>
              </Stack>
              {selectedInterviewers.length > 0 && (
                <Button
                  size="small"
                  onClick={handleCheckAvailability}
                  disabled={checkingAvailability || !date || !time}
                  startIcon={<TimeIcon />}
                >
                  {checkingAvailability ? 'Checking...' : 'Check Availability'}
                </Button>
              )}
            </Stack>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add interviewers by entering their recruiter IDs
            </Typography>

            <TextField
              fullWidth
              label="Add Interviewer (Recruiter ID)"
              placeholder="Enter recruiter ID and press Enter"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  const target = e.target as HTMLInputElement;
                  const recruiterId = target.value.trim();
                  if (recruiterId && !selectedInterviewers.includes(recruiterId)) {
                    setSelectedInterviewers([...selectedInterviewers, recruiterId]);
                    target.value = '';
                    setAvailabilityStatus([]);
                  }
                }
              }}
              slotProps={{
                input: {
                  'aria-label': 'Add interviewer',
                },
              }}
            />

            {/* Selected Interviewers */}
            {selectedInterviewers.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Selected Interviewers
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap" useFlexGap>
                  {selectedInterviewers.map((id) => {
                    const availability = availabilityStatus.find((a) => a.recruiter_id === id);
                    return (
                      <Chip
                        key={id}
                        label={id}
                        onDelete={() => {
                          setSelectedInterviewers(selectedInterviewers.filter((i) => i !== id));
                          setAvailabilityStatus(availabilityStatus.filter((a) => a.recruiter_id !== id));
                        }}
                        color={availability?.is_available ? 'success' : 'default'}
                        icon={availability?.is_available ? <CheckIcon /> : undefined}
                        size="small"
                      />
                    );
                  })}
                </Stack>
              </Box>
            )}

            {/* Availability Status */}
            {availabilityStatus.length > 0 && (
              <Alert
                severity={allInterviewersAvailable ? 'success' : 'warning'}
                sx={{ mt: 2 }}
              >
                {allInterviewersAvailable
                  ? 'All selected interviewers are available at this time.'
                  : 'Some interviewers may have conflicts. Please review before scheduling.'}
              </Alert>
            )}
          </Paper>

          {/* Error Display */}
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
          onClick={handleSubmit}
          variant="contained"
          disabled={!isFormValid || createMutation.isPending}
          startIcon={createMutation.isPending ? <CircularProgress size={16} /> : <EventIcon />}
        >
          {createMutation.isPending ? 'Scheduling...' : 'Schedule Interview'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default InterviewScheduler;
