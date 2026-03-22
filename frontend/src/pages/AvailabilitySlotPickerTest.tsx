/**
 * Test page for AvailabilitySlotPicker component
 *
 * This page demonstrates and tests the AvailabilitySlotPicker functionality
 * with mock data for development purposes.
 */

import { useState } from 'react';
import { Box, Container, Typography, Paper, Button, Stack } from '@mui/material';
import { AvailabilitySlotPicker, AvailabilitySlot } from '../components/AvailabilitySlotPicker';

// Mock data for testing
const mockSlots: AvailabilitySlot[] = [
  // Today's slots
  {
    start_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
    end_time: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.95,
  },
  {
    start_time: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(), // 4 hours from now
    end_time: new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.85,
  },
  // Tomorrow's slots
  {
    start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow 9 AM
    end_time: new Date(Date.now() + 25 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.92,
  },
  {
    start_time: new Date(Date.now() + 28 * 60 * 60 * 1000).toISOString(), // Tomorrow 1 PM
    end_time: new Date(Date.now() + 29 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.78,
  },
  {
    start_time: new Date(Date.now() + 30 * 60 * 60 * 1000).toISOString(), // Tomorrow 3 PM
    end_time: new Date(Date.now() + 31 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.88,
  },
  // Day after tomorrow
  {
    start_time: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
    end_time: new Date(Date.now() + 49 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.95,
  },
  {
    start_time: new Date(Date.now() + 52 * 60 * 60 * 1000).toISOString(),
    end_time: new Date(Date.now() + 53 * 60 * 60 * 1000).toISOString(),
    available: true,
    confidence: 0.90,
  },
];

export function AvailabilitySlotPickerTest() {
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [bookingState, setBookingState] = useState<'idle' | 'booking' | 'success'>('idle');

  const handleSelectSlot = (slot: AvailabilitySlot) => {
    setSelectedSlot(slot);
    setBookingState('idle');
  };

  const handleBookInterview = () => {
    if (!selectedSlot) return;

    setBookingState('booking');

    // Simulate booking API call
    setTimeout(() => {
      setBookingState('success');
    }, 1500);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={2} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          AvailabilitySlotPicker Test Page
        </Typography>

        <Typography variant="body1" color="text.secondary" mb={4}>
          This page demonstrates the AvailabilitySlotPicker component with mock data.
        </Typography>

        <Box mb={4}>
          <AvailabilitySlotPicker
            slots={mockSlots}
            selectedSlot={selectedSlot}
            onSelectSlot={handleSelectSlot}
            durationMinutes={60}
          />
        </Box>

        <Stack direction="row" spacing={2} justifyContent="center">
          <Button
            variant="contained"
            size="large"
            disabled={!selectedSlot || bookingState !== 'idle'}
            onClick={handleBookInterview}
          >
            {bookingState === 'booking' ? 'Booking...' : 'Book Interview'}
          </Button>

          {selectedSlot && (
            <Button
              variant="outlined"
              size="large"
              onClick={() => setSelectedSlot(null)}
            >
              Clear Selection
            </Button>
          )}
        </Stack>

        {bookingState === 'success' && (
          <Box mt={3}>
            <Typography variant="h6" color="success.main" textAlign="center">
              ✓ Interview booked successfully!
            </Typography>
          </Box>
        )}

        {selectedSlot && (
          <Box mt={3} p={2} bgcolor="grey.100" borderRadius={1}>
            <Typography variant="body2" fontWeight="medium">
              Debug Info - Selected Slot:
            </Typography>
            <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem', mt: 1 }}>
              {JSON.stringify(selectedSlot, null, 2)}
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
}

export default AvailabilitySlotPickerTest;
