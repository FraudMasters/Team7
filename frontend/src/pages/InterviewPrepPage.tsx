import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Container } from '@/components/ui';
import InterviewPrepSheet from '@/components/InterviewPrepSheet';

/**
 * Interview Preparation Page
 *
 * Displays customized interview questions for a candidate based on their resume
 * and the job requirements. Shows technical, behavioral, situational, and
 * skill verification questions with the ability to add custom questions and
 * provide feedback.
 */
const InterviewPrepPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          Invalid interview preparation ID
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <InterviewPrepSheet prepId={id} />
      </Box>
    </Container>
  );
};

export default InterviewPrepPage;
