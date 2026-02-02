import { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Card,
  CardContent,
  Chip,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Lightbulb as TipsIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Question as QuestionIcon,
  RecordVoiceOver as VoiceIcon,
  Psychology as MindIcon,
  Stars as StarsIcon,
} from '@mui/icons-material';
import { PageTransition } from '../../components/ui/PageTransition';

interface Tip {
  id: string;
  category: string;
  title: string;
  content: string[];
  icon: React.ReactElement;
}

interface Question {
  id: string;
  question: string;
  sampleAnswer: string;
  category: string;
}

const tips: Tip[] = [
  {
    id: '1',
    category: 'Preparation',
    title: 'Research the Company',
    icon: <MindIcon />,
    content: [
      'Review the company website, mission, and values',
      'Research recent news and press releases',
      'Understand their products/services and target market',
      'Look up your interviewers on LinkedIn',
      'Prepare questions to ask about the company culture and role',
    ],
  },
  {
    id: '2',
    category: 'Preparation',
    title: 'Practice Common Questions',
    icon: <QuestionIcon />,
    content: [
      'Tell me about yourself',
      'What are your greatest strengths and weaknesses?',
      'Why do you want to work here?',
      'Describe a challenging work situation and how you handled it',
      'Where do you see yourself in 5 years?',
    ],
  },
  {
    id: '3',
    category: 'During Interview',
    title: 'Make a Great First Impression',
    icon: <StarsIcon />,
    content: [
      'Arrive 10-15 minutes early',
      'Dress appropriately for the company culture',
      'Bring multiple copies of your resume',
      'Turn off your phone completely',
      'Greet everyone with a smile and firm handshake',
    ],
  },
  {
    id: '4',
    category: 'During Interview',
    title: 'Answer Effectively',
    icon: <VoiceIcon />,
    content: [
      'Use the STAR method (Situation, Task, Action, Result)',
      'Be specific and quantify your achievements',
      'Maintain eye contact and good posture',
      'Take time to think before answering',
      'Be honest about what you don\'t know',
    ],
  },
];

const commonQuestions: Question[] = [
  {
    id: '1',
    category: 'Behavioral',
    question: 'Tell me about a time you had to work with a difficult colleague.',
    sampleAnswer:
      'I once worked with a colleague who had a different communication style. I scheduled a one-on-one to understand their perspective and find common ground. We established clear expectations and regular check-ins, which improved our collaboration and project outcomes.',
  },
  {
    id: '2',
    category: 'Technical',
    question: 'How do you stay updated with the latest technologies?',
    sampleAnswer:
      'I follow industry blogs, attend meetups and conferences, contribute to open-source projects, and participate in online communities. I also allocate time each week for learning and experimenting with new tools.',
  },
  {
    id: '3',
    category: 'Behavioral',
    question: 'Describe a project where you had to learn a new skill quickly.',
    sampleAnswer:
      'In my previous role, we needed to migrate to a new framework. I took the initiative to learn it through online courses and built a prototype. I then trained team members and created documentation, resulting in a smooth transition.',
  },
  {
    id: '4',
    category: 'Leadership',
    question: 'How do you handle tight deadlines and pressure?',
    sampleAnswer:
      'I break down projects into smaller tasks, prioritize based on impact, and communicate early if deadlines seem unrealistic. I focus on delivering the most critical features first and maintain transparent communication with stakeholders.',
  },
];

export function InterviewTipsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', 'Preparation', 'During Interview', 'Follow-up'];

  const filteredTips =
    selectedCategory === 'All'
      ? tips
      : tips.filter((tip) => tip.category === selectedCategory);

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <TipsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Interview Preparation
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Expert tips and common questions to help you succeed
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Category Filter */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 4 }}>
          {categories.map((cat) => (
            <Chip
              key={cat}
              label={cat}
              onClick={() => setSelectedCategory(cat)}
              color={selectedCategory === cat ? 'primary' : 'default'}
              variant={selectedCategory === cat ? 'filled' : 'outlined'}
            />
          ))}
        </Box>

        <Grid container spacing={3}>
          {/* Tips */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Essential Tips
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filteredTips.map((tip) => (
                <Card key={tip.id} elevation={2}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Box
                        sx={{
                          width: 36,
                          height: 36,
                          borderRadius: '50%',
                          bgcolor: 'primary.100',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {tip.icon}
                      </Box>
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {tip.title}
                        </Typography>
                        <Chip label={tip.category} size="small" variant="outlined" />
                      </Box>
                    </Box>
                    <List dense>
                      {tip.content.map((item, idx) => (
                        <ListItem key={idx} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={item} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>

          {/* Common Questions */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Common Interview Questions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {commonQuestions.map((q) => (
                <Accordion key={q.id}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
                      <QuestionIcon color="primary" fontSize="small" />
                      <Typography variant="subtitle2" fontWeight={600}>
                        {q.question}
                      </Typography>
                    </Box>
                    <Chip label={q.category} size="small" variant="outlined" />
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      <strong>Sample Answer:</strong>
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {q.sampleAnswer}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>

            {/* Quick Tips Card */}
            <Paper sx={{ p: 3, mt: 3, bgcolor: 'primary.50' }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Quick Reminders
              </Typography>
              <Divider sx={{ my: 1 }} />
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Be authentic and honest" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Ask thoughtful questions" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Follow up with a thank you note" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Stay positive and confident" />
                </ListItem>
              </List>
            </Paper>
          </Grid>
        </Grid>

        {/* Mock Interview CTA */}
        <Paper sx={{ p: 4, mt: 4, textAlign: 'center', bgcolor: 'gradient.primary' }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Practice Makes Perfect
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Try a mock interview session to get personalized feedback
          </Typography>
          <Button variant="contained" size="large">
            Start Mock Interview
          </Button>
        </Paper>
      </Container>
    </PageTransition>
  );
}
