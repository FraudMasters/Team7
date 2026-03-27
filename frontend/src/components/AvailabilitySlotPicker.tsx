/**
 * Availability Slot Picker Component
 *
 * Displays available interview time slots in a calendar grid format.
 * Allows candidates to select a time slot for self-scheduling.
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Paper,
  Chip,
  Grid2,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  AccessTime as TimeIcon,
  Event as EventIcon,
  Check as CheckIcon,
} from '@mui/icons-material';

export interface AvailabilitySlot {
  start_time: string;
  end_time: string;
  available: boolean;
  confidence: number;
}

interface AvailabilitySlotPickerProps {
  slots: AvailabilitySlot[];
  loading?: boolean;
  error?: string | null;
  onSelectSlot: (slot: AvailabilitySlot) => void;
  selectedSlot?: AvailabilitySlot | null;
  durationMinutes?: number;
}

export function AvailabilitySlotPicker({
  slots,
  loading = false,
  error = null,
  onSelectSlot,
  selectedSlot = null,
  durationMinutes = 60,
}: AvailabilitySlotPickerProps) {
  // Group slots by date for calendar grid display
  const slotsByDate = slots.reduce((acc, slot) => {
    if (!slot.available) return acc;

    const date = new Date(slot.start_time);
    const dateKey = date.toISOString().split('T')[0];

    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(slot);
    return acc;
  }, {} as Record<string, AvailabilitySlot[]>);

  // Sort dates
  const sortedDates = Object.keys(slotsByDate).sort();

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Check if it's today or tomorrow
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    }

    // Otherwise return formatted date
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const isSlotSelected = (slot: AvailabilitySlot): boolean => {
    if (!selectedSlot) return false;
    return slot.start_time === selectedSlot.start_time &&
           slot.end_time === selectedSlot.end_time;
  };

  const handleSlotClick = (slot: AvailabilitySlot) => {
    onSelectSlot(slot);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" py={8}>
        <Stack spacing={2} alignItems="center">
          <CircularProgress size={48} />
          <Typography variant="body1" color="text.secondary">
            Loading available time slots...
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  if (sortedDates.length === 0) {
    return (
      <Alert severity="info" sx={{ my: 2 }}>
        No available time slots found. Please contact the recruiter for more options.
      </Alert>
    );
  }

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1} mb={3}>
        <EventIcon color="primary" />
        <Typography variant="h6">
          Select an Available Time Slot
        </Typography>
      </Stack>

      <Typography variant="body2" color="text.secondary" mb={3}>
        Duration: {durationMinutes} minutes
      </Typography>

      <Stack spacing={3}>
        {sortedDates.map((dateKey) => {
          const dateSlots = slotsByDate[dateKey];

          return (
            <Box key={dateKey}>
              <Typography
                variant="subtitle1"
                fontWeight="medium"
                mb={1.5}
                sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
              >
                <EventIcon fontSize="small" color="action" />
                {formatDate(dateKey)}
              </Typography>

              <Grid2 container spacing={1.5}>
                {dateSlots.map((slot, index) => {
                  const selected = isSlotSelected(slot);
                  const confidenceLevel =
                    slot.confidence >= 0.9 ? 'high' :
                    slot.confidence >= 0.7 ? 'medium' : 'low';

                  return (
                    <Grid2 key={index} size={{ xs: 6, sm: 4, md: 3 }}>
                      <Paper
                        elevation={selected ? 4 : 1}
                        sx={{
                          p: 2,
                          cursor: 'pointer',
                          border: selected ? 2 : 0,
                          borderColor: 'primary.main',
                          bgcolor: selected ? 'primary.50' : 'background.paper',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            elevation: 3,
                            transform: 'translateY(-2px)',
                            bgcolor: selected ? 'primary.100' : 'action.hover',
                          },
                          position: 'relative',
                        }}
                        onClick={() => handleSlotClick(slot)}
                      >
                        <Stack spacing={1} alignItems="center">
                          {selected && (
                            <Box
                              sx={{
                                position: 'absolute',
                                top: 8,
                                right: 8,
                                bgcolor: 'primary.main',
                                borderRadius: '50%',
                                width: 24,
                                height: 24,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                              }}
                            >
                              <CheckIcon sx={{ color: 'white', fontSize: 16 }} />
                            </Box>
                          )}

                          <TimeIcon
                            color={selected ? 'primary' : 'action'}
                            fontSize="small"
                          />

                          <Typography
                            variant="body1"
                            fontWeight={selected ? 'bold' : 'medium'}
                            color={selected ? 'primary.main' : 'text.primary'}
                          >
                            {formatTime(slot.start_time)}
                          </Typography>

                          {confidenceLevel !== 'high' && (
                            <Chip
                              label={confidenceLevel}
                              size="small"
                              color={confidenceLevel === 'medium' ? 'warning' : 'default'}
                              sx={{ fontSize: '0.7rem', height: 18 }}
                            />
                          )}
                        </Stack>
                      </Paper>
                    </Grid2>
                  );
                })}
              </Grid2>
            </Box>
          );
        })}
      </Stack>

      {selectedSlot && (
        <Alert severity="success" sx={{ mt: 3 }}>
          Selected: {formatDate(selectedSlot.start_time.split('T')[0])} at{' '}
          {formatTime(selectedSlot.start_time)}
        </Alert>
      )}
    </Box>
  );
}

export default AvailabilitySlotPicker;
