import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
} from '@/components/ui';
import SkillDetailsWithConfidence, {
  SkillMatchDetail,
} from '@components/SkillDetailsWithConfidence';

const SkillDetailsWithConfidenceTest: React.FC = () => {
  // Test data - various match types and confidence levels
  const testSkills: SkillMatchDetail[] = [
    {
      skill: 'React',
      confidence: 1.0,
      match_type: 'direct',
      locations: [
        {
          text: 'React',
          start: 10,
          end: 15,
          context: 'Developed web applications using React and TypeScript',
        },
        {
          text: 'React',
          start: 45,
          end: 50,
          context: 'Built reusable React components for enterprise clients',
        },
      ],
    },
    {
      skill: 'TypeScript',
      confidence: 0.95,
      match_type: 'direct',
      matched_as: 'TypeScript',
      locations: [
        {
          text: 'TypeScript',
          start: 30,
          end: 40,
          context: 'Proficient in TypeScript for type-safe development',
        },
      ],
    },
    {
      skill: 'JavaScript',
      confidence: 0.9,
      match_type: 'synonym',
      matched_as: 'JS',
      locations: [
        {
          text: 'JS',
          start: 20,
          end: 22,
          context: 'Expert in modern JS (ES6+) and frameworks',
        },
      ],
    },
    {
      skill: 'Python',
      confidence: 0.85,
      match_type: 'direct',
      matched_as: 'Python',
      locations: [
        {
          text: 'Python',
          start: 15,
          end: 21,
          context: 'Python developer with 5 years of experience',
        },
      ],
    },
    {
      skill: 'Node.js',
      confidence: 0.75,
      match_type: 'fuzzy',
      matched_as: 'NodeJS',
      locations: [
        {
          text: 'NodeJS',
          start: 50,
          end: 56,
          context: 'Backend development with NodeJS and Express',
        },
      ],
    },
    {
      skill: 'PostgreSQL',
      confidence: 0.7,
      match_type: 'synonym',
      matched_as: 'Postgres',
      locations: [
        {
          text: 'Postgres',
          start: 75,
          end: 82,
          context: 'Database design with Postgres and MongoDB',
        },
      ],
    },
    {
      skill: 'AWS',
      confidence: 0.65,
      match_type: 'context',
      matched_as: 'Amazon Web Services',
      locations: [
        {
          text: 'Amazon Web Services',
          start: 100,
          end: 120,
          context: 'Cloud infrastructure on Amazon Web Services (AWS)',
        },
      ],
    },
    {
      skill: 'Docker',
      confidence: 0.6,
      match_type: 'direct',
      locations: [
        {
          text: 'Docker',
          start: 130,
          end: 136,
          context: 'Containerization using Docker and Kubernetes',
        },
      ],
    },
    {
      skill: 'MongoDB',
      confidence: 0.55,
      match_type: 'compound',
      matched_as: 'Mongo DB',
      locations: [
        {
          text: 'Mongo DB',
          start: 85,
          end: 93,
          context: 'NoSQL databases including Mongo DB and Redis',
        },
      ],
    },
    {
      skill: 'GraphQL',
      confidence: 0.5,
      match_type: 'fuzzy',
      matched_as: 'Graph QL',
      locations: [
        {
          text: 'Graph QL',
          start: 200,
          end: 208,
          context: 'API development with Graph QL and REST',
        },
      ],
    },
  ];

  // Test data - high confidence matches
  const highConfidenceSkills: SkillMatchDetail[] = [
    {
      skill: 'React',
      confidence: 1.0,
      match_type: 'direct',
      locations: [
        {
          text: 'React',
          start: 0,
          end: 5,
          context: 'Senior React Developer with extensive experience',
        },
      ],
    },
    {
      skill: 'TypeScript',
      confidence: 0.98,
      match_type: 'direct',
      locations: [
        {
          text: 'TypeScript',
          start: 40,
          end: 50,
          context: 'TypeScript expert for large-scale applications',
        },
      ],
    },
    {
      skill: 'Node.js',
      confidence: 0.95,
      match_type: 'direct',
      locations: [
        {
          text: 'Node.js',
          start: 80,
          end: 87,
          context: 'Full-stack Node.js development',
        },
      ],
    },
  ];

  // Test data - loading and error states
  const loadingTest = () => {
    return (
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Test Case 4: Loading State
        </Typography>
        <Box sx={{ mt: 2 }}>
          <SkillDetailsWithConfidence skills={[]} loading={true} />
        </Box>
      </Paper>
    );
  };

  const errorTest = () => {
    return (
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Test Case 5: Error State
        </Typography>
        <Box sx={{ mt: 2 }}>
          <SkillDetailsWithConfidence
            skills={[]}
            error="Failed to load skill details"
          />
        </Box>
      </Paper>
    );
  };

  const emptyTest = () => {
    return (
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Test Case 6: Empty State
        </Typography>
        <Box sx={{ mt: 2 }}>
          <SkillDetailsWithConfidence skills={[]} />
        </Box>
      </Paper>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Skill Details With Confidence - Component Test
          </Typography>
          <Typography variant="body1" color="secondary">
            Testing the SkillDetailsWithConfidence component with various match
            types and scenarios
          </Typography>
        </Box>

        {/* Test Case 1: Mixed Match Types */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Mixed Match Types and Confidence Levels
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Showing various match types: direct, synonym, fuzzy, context, and
            compound with different confidence scores
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillDetailsWithConfidence skills={testSkills} />
          </Box>
        </Paper>

        {/* Test Case 2: High Confidence Matches */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 2: High Confidence Matches
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            All matches with 90%+ confidence
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillDetailsWithConfidence
              skills={highConfidenceSkills}
              title="Top Matches"
            />
          </Box>
        </Paper>

        {/* Test Case 3: Limited Display */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 3: Limited Display (Max 5)
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Showing only first 5 of 10 skills
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillDetailsWithConfidence skills={testSkills} maxDisplay={5} />
          </Box>
        </Paper>

        {/* Test Case 4: Loading State */}
        {loadingTest()}

        {/* Test Case 5: Error State */}
        {errorTest()}

        {/* Test Case 6: Empty State */}
        {emptyTest()}

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" as="div">
            ✓ Component displays matched skills with confidence scores<br />
            ✓ Shows match type badges (direct, synonym, fuzzy, context)<br />
            ✓ Chips are color-coded by match type<br />
            ✓ Confidence bars show visual representation<br />
            ✓ Locations are displayed when available<br />
            ✓ Loading state works correctly<br />
            ✓ Error state works correctly<br />
            ✓ Empty state works correctly<br />
            ✓ No console errors
          </Typography>
        </Paper>
      </Stack>
    </Container>
  );
};

export default SkillDetailsWithConfidenceTest;
