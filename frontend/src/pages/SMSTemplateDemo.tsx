/**
 * SMS Template Demo Page
 *
 * Demonstration page for the SMSTemplateEditor component.
 * Shows character counting and segment calculation in action.
 */

import { useState } from 'react';
import { Container, Box, Typography, Paper, Button, Stack } from '@mui/material';
import { SMSTemplateEditor } from '../components/TemplateBuilder/SMSTemplateEditor';

export default function SMSTemplateDemo() {
  const [smsContent, setSmsContent] = useState(
    'Hi {{candidate_name}}, thank you for applying to {{job_title}} at {{company_name}}. We received your application and will review it shortly.'
  );

  const handleReset = () => {
    setSmsContent('');
  };

  const handleLoadSample = () => {
    setSmsContent(
      'Hi {{candidate_name}}, your interview for {{job_title}} is scheduled for {{interview_date}} at {{interview_time}}. ' +
      'Location: {{interview_location}}. Please arrive 10 minutes early. If you need to reschedule, contact {{recruiter_name}} at {{recruiter_email}}.'
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            SMS Template Editor Demo
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Test the SMS template editor with real-time character count and segment calculation.
          </Typography>
        </Paper>

        {/* Demo Actions */}
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={2}>
            <Button variant="outlined" onClick={handleReset}>
              Clear Content
            </Button>
            <Button variant="outlined" onClick={handleLoadSample}>
              Load Sample (Long Message)
            </Button>
          </Stack>
        </Paper>

        {/* SMS Template Editor */}
        <SMSTemplateEditor
          content={smsContent}
          onChange={setSmsContent}
          placeholder="Type your SMS message here..."
        />

        {/* Info Section */}
        <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
          <Typography variant="h6" gutterBottom>
            Testing Checklist:
          </Typography>
          <Stack component="ul" spacing={1} sx={{ pl: 2 }}>
            <Typography component="li" variant="body2">
              ✓ Character count displays and updates in real-time
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Segment count shows 1 for messages under 160 characters
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Segment count updates for messages over 160 characters (153 chars per segment)
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Progress bar reflects current character usage
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Warning appears for multi-segment messages
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Variable selector button allows inserting dynamic variables
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Encoding switches to UCS-2 when emojis are used (try adding 😊)
            </Typography>
            <Typography component="li" variant="body2">
              ✓ Characters remaining updates as you type
            </Typography>
          </Stack>
        </Paper>
      </Stack>
    </Container>
  );
}
