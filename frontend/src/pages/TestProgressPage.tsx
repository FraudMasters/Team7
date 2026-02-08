import React, { useState, useEffect, useRef } from 'react';
import { Box, Container, Stack, Button, Typography, Card, CardContent } from '@mui/material';
import ProcessingProgressIndicator, {
  ProcessingProgressIndicatorHandle,
} from '@/components/ProcessingProgressIndicator';
import type { ResumeProgressStage } from '@/types/resume-progress';

/**
 * Test Progress Page
 *
 * Demonstrates the ProcessingProgressIndicator component with various states and configurations.
 */
const TestProgressPage: React.FC = () => {
  const [stage, setStage] = useState<ResumeProgressStage>('parsing');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Initializing...');
  const [isComplete, setIsComplete] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const indicatorRef = useRef<ProcessingProgressIndicatorHandle>(null);
  const simulationRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Reset all state
   */
  const handleReset = () => {
    setStage('parsing');
    setProgress(0);
    setMessage('Initializing...');
    setIsComplete(false);
    setHasError(false);
    setError(undefined);

    if (simulationRef.current) {
      clearInterval(simulationRef.current);
      simulationRef.current = null;
    }
  };

  /**
   * Simulate a successful processing flow
   */
  const handleSimulateSuccess = () => {
    handleReset();

    let currentProgress = 0;

    simulationRef.current = setInterval(() => {
      currentProgress += Math.random() * 15;

      if (currentProgress < 25) {
        setStage('parsing');
        setProgress(Math.min(currentProgress, 25));
        setMessage('Extracting text and metadata from resume...');
      } else if (currentProgress < 60) {
        setStage('analyzing');
        setProgress(Math.min(currentProgress, 60));
        setMessage('Running ML/NLP analysis and extracting insights...');
      } else if (currentProgress < 90) {
        setStage('ranking');
        setProgress(Math.min(currentProgress, 90));
        setMessage('Calculating match scores and rankings...');
      } else if (currentProgress >= 100) {
        setProgress(100);
        setStage('complete');
        setMessage('Resume processed successfully!');
        setIsComplete(true);

        if (simulationRef.current) {
          clearInterval(simulationRef.current);
          simulationRef.current = null;
        }
      } else {
        setProgress(currentProgress);
      }
    }, 800);
  };

  /**
   * Simulate an error during processing
   */
  const handleSimulateError = () => {
    handleReset();

    let currentProgress = 0;

    simulationRef.current = setInterval(() => {
      currentProgress += Math.random() * 10;

      if (currentProgress < 30) {
        setStage('parsing');
        setProgress(Math.min(currentProgress, 30));
        setMessage('Extracting text and metadata from resume...');
      } else if (currentProgress >= 40) {
        setStage('failed');
        setHasError(true);
        setError('Failed to parse resume file: Invalid file format');
        setMessage('');

        if (simulationRef.current) {
          clearInterval(simulationRef.current);
          simulationRef.current = null;
        }
      } else {
        setProgress(currentProgress);
      }
    }, 500);
  };

  /**
   * Test programmatic control via ref
   */
  const handleTestRefControl = () => {
    handleReset();

    setTimeout(() => {
      indicatorRef.current?.updateProgress({
        stage: 'parsing',
        progress: 10,
        message: 'Parsing resume...',
      });
    }, 500);

    setTimeout(() => {
      indicatorRef.current?.updateProgress({
        stage: 'analyzing',
        progress: 45,
        message: 'Analyzing skills and experience...',
      });
    }, 1500);

    setTimeout(() => {
      indicatorRef.current?.updateProgress({
        stage: 'ranking',
        progress: 80,
        message: 'Calculating match scores...',
      });
    }, 2500);

    setTimeout(() => {
      indicatorRef.current?.setComplete('Processing complete via ref control!');
    }, 3500);
  };

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (simulationRef.current) {
        clearInterval(simulationRef.current);
      }
    };
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        ProcessingProgressIndicator Test Page
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        This page demonstrates the ProcessingProgressIndicator component with various states
        and configurations.
      </Typography>

      <Stack spacing={4}>
        {/* Control Buttons */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Simulation Controls
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
              <Button variant="contained" color="primary" onClick={handleSimulateSuccess}>
                Simulate Success
              </Button>
              <Button variant="contained" color="error" onClick={handleSimulateError}>
                Simulate Error
              </Button>
              <Button variant="contained" color="info" onClick={handleTestRefControl}>
                Test Ref Control
              </Button>
              <Button variant="outlined" onClick={handleReset}>
                Reset
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Large Size Indicator */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Large Size (with Stepper)
            </Typography>
            <ProcessingProgressIndicator
              ref={indicatorRef}
              stage={stage}
              progress={progress}
              message={message}
              isComplete={isComplete}
              hasError={hasError}
              error={error}
              resumeId="test-resume-123"
              showStepper={true}
              title="Processing Resume"
              size="large"
            />
          </CardContent>
        </Card>

        {/* Medium Size Indicator */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Medium Size (default)
            </Typography>
            <ProcessingProgressIndicator
              stage="analyzing"
              progress={55}
              message="Analyzing skills and experience..."
              showStepper={true}
              size="medium"
            />
          </CardContent>
        </Card>

        {/* Small Size Indicator */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Small Size (without Stepper)
            </Typography>
            <ProcessingProgressIndicator
              stage="ranking"
              progress={80}
              message="Calculating match scores..."
              showStepper={false}
              size="small"
            />
          </CardContent>
        </Card>

        {/* Complete State */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Complete State
            </Typography>
            <ProcessingProgressIndicator
              stage="complete"
              progress={100}
              isComplete={true}
              message="Resume processed successfully!"
              resumeId="complete-resume-456"
              showStepper={false}
              size="medium"
            />
          </CardContent>
        </Card>

        {/* Error State */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Error State
            </Typography>
            <ProcessingProgressIndicator
              stage="failed"
              hasError={true}
              error="Failed to parse resume: Invalid file format"
              resumeId="error-resume-789"
              showStepper={false}
              size="medium"
            />
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default TestProgressPage;
