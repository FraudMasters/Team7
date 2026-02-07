import React, { useState } from 'react';
import { Container, Typography, Box, Paper, Button, Stack, Divider } from '@/components/ui';
import LoadingSpinner from '@components/LoadingSpinner';

/**
 * LoadingSpinner Demo Page
 *
 * This page demonstrates all the different skeleton variants available
 * in the LoadingSpinner component for testing and verification.
 */
const LoadingSpinnerDemoPage: React.FC = () => {
  const [variant, setVariant] = useState<any>('spinner');
  const [count, setCount] = useState(3);

  const variants: Array<{ value: string; label: string; description: string }> = [
    { value: 'spinner', label: 'Spinner', description: 'Simple circular progress spinner' },
    { value: 'cards', label: 'Cards', description: 'Card-based grid layout skeleton' },
    { value: 'list', label: 'List', description: 'List items with avatars skeleton' },
    { value: 'table', label: 'Table', description: 'Table rows with header skeleton' },
    { value: 'form', label: 'Form', description: 'Form fields with labels skeleton' },
    { value: 'page', label: 'Page', description: 'Full page layout skeleton' },
    { value: 'upload', label: 'Upload', description: 'Resume upload workflow skeleton' },
    { value: 'analysis', label: 'Analysis', description: 'Analysis results workflow skeleton' },
    { value: 'vacancy-details', label: 'Vacancy Details', description: 'Vacancy details page skeleton' },
    { value: 'dashboard', label: 'Dashboard', description: 'Recruiter dashboard skeleton' },
    { value: 'candidate-search', label: 'Candidate Search', description: 'Candidate search workflow skeleton' },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          LoadingSpinner Component Demo
        </Typography>
        <Typography variant="body1" color="secondary">
          Visual verification of all skeleton variants
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start' }}>
        {/* Controls Sidebar */}
        <Paper sx={{ p: 3, minWidth: 280, position: 'sticky', top: 16 }}>
          <Typography variant="h6" gutterBottom>
            Select Variant
          </Typography>
          <Stack spacing={1} sx={{ mb: 3 }}>
            {variants.map((v) => (
              <Button
                key={v.value}
                variant={variant === v.value ? 'contained' : 'outlined'}
                onClick={() => setVariant(v.value)}
                fullWidth
                sx={{ justifyContent: 'flex-start', textTransform: 'none' }}
              >
                <Box sx={{ textAlign: 'left' }}>
                  <Typography variant="body2" fontWeight={500}>
                    {v.label}
                  </Typography>
                </Box>
              </Button>
            ))}
          </Stack>

          <Divider sx={{ mb: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Count (for list/cards/table/search)
          </Typography>
          <Stack direction="row" spacing={1}>
            {[1, 3, 5, 10].map((c) => (
              <Button
                key={c}
                variant={count === c ? 'contained' : 'outlined'}
                size="small"
                onClick={() => setCount(c)}
              >
                {c}
              </Button>
            ))}
          </Stack>

          <Divider sx={{ my: 2 }} />

          <Typography variant="caption" color="text.secondary">
            {variants.find((v) => v.value === variant)?.description}
          </Typography>
        </Paper>

        {/* Preview Area */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Preview: <strong>{variant}</strong>
            </Typography>
          </Paper>
          <Paper
            sx={{
              p: 0,
              minHeight: 400,
              bgcolor: 'background.paper',
              overflow: 'hidden',
            }}
          >
            <LoadingSpinner variant={variant} count={count} />
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default LoadingSpinnerDemoPage;
