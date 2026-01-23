import React from 'react';
import { Box, Container } from '@mui/material';
import { useParams } from 'react-router-dom';
import { JobComparison } from '@components/JobComparison';

/**
 * Compare Page Component
 *
 * Displays comprehensive job comparison analysis between a resume and vacancy,
 * showing matched/missing skills, match percentage, and experience verification.
 */
const ComparePage: React.FC = () => {
  const { resumeId, vacancyId } = useParams<{ resumeId: string; vacancyId: string }>();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box>
        <JobComparison resumeId={resumeId || ''} vacancyId={vacancyId || ''} />
      </Box>
    </Container>
  );
};

export default ComparePage;
