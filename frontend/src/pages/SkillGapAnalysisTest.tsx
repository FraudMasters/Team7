import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
} from '@mui/material';
import SkillGapAnalysis, {
  MissingSkillWithSuggestions,
} from '@components/SkillGapAnalysis';

const SkillGapAnalysisTest: React.FC = () => {
  // Test data - various missing skills with suggestions
  const testMissingSkills: MissingSkillWithSuggestions[] = [
    {
      skill: 'SQL',
      suggestions: [
        {
          skill: 'PostgreSQL',
          confidence: 0.85,
          reason: 'synonym',
        },
        {
          skill: 'MySQL',
          confidence: 0.82,
          reason: 'synonym',
        },
        {
          skill: 'MongoDB',
          confidence: 0.70,
          reason: 'same_category',
        },
      ],
    },
    {
      skill: 'React',
      suggestions: [
        {
          skill: 'ReactJS',
          confidence: 0.88,
          reason: 'fuzzy_match',
        },
        {
          skill: 'React.js',
          confidence: 0.86,
          reason: 'fuzzy_match',
        },
        {
          skill: 'Redux',
          confidence: 0.65,
          reason: 'related',
        },
      ],
    },
    {
      skill: 'AWS',
      suggestions: [
        {
          skill: 'Amazon Web Services',
          confidence: 0.90,
          reason: 'synonym',
        },
        {
          skill: 'Amazon EC2',
          confidence: 0.72,
          reason: 'same_category',
        },
      ],
    },
    {
      skill: 'Docker',
      suggestions: [
        {
          skill: 'Kubernetes',
          confidence: 0.68,
          reason: 'same_category',
        },
        {
          skill: 'Container',
          confidence: 0.62,
          reason: 'related',
        },
      ],
    },
    {
      skill: 'TypeScript',
      suggestions: [
        {
          skill: 'TS',
          confidence: 0.84,
          reason: 'synonym',
        },
        {
          skill: 'JavaScript',
          confidence: 0.60,
          reason: 'same_category',
        },
      ],
    },
    {
      skill: 'GraphQL',
      suggestions: [
        {
          skill: 'Graph QL',
          confidence: 0.75,
          reason: 'fuzzy_match',
        },
      ],
    },
    {
      skill: 'Python',
      suggestions: [
        {
          skill: 'Python 3',
          confidence: 0.92,
          reason: 'synonym',
        },
        {
          skill: 'Django',
          confidence: 0.66,
          reason: 'related',
        },
        {
          skill: 'Flask',
          confidence: 0.64,
          reason: 'related',
        },
      ],
    },
    {
      skill: 'Node.js',
      suggestions: [
        {
          skill: 'NodeJS',
          confidence: 0.89,
          reason: 'fuzzy_match',
        },
        {
          skill: 'Express',
          confidence: 0.67,
          reason: 'related',
        },
        {
          skill: 'Nest.js',
          confidence: 0.63,
          reason: 'related',
        },
      ],
    },
  ];

  // Test data - skills with no suggestions
  const noSuggestionsSkills: MissingSkillWithSuggestions[] = [
    {
      skill: 'COBOL',
      suggestions: [],
    },
    {
      skill: 'Fortran',
      suggestions: [],
    },
    {
      skill: 'Assembly Language',
      suggestions: [],
    },
  ];

  // Test data - high confidence suggestions
  const highConfidenceSuggestions: MissingSkillWithSuggestions[] = [
    {
      skill: 'JavaScript',
      suggestions: [
        {
          skill: 'JS',
          confidence: 0.95,
          reason: 'synonym',
        },
        {
          skill: 'ECMAScript',
          confidence: 0.88,
          reason: 'synonym',
        },
      ],
    },
    {
      skill: 'PostgreSQL',
      suggestions: [
        {
          skill: 'Postgres',
          confidence: 0.92,
          reason: 'synonym',
        },
      ],
    },
  ];

  // Test data - empty state
  const emptyMissingSkills: MissingSkillWithSuggestions[] = [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Skill Gap Analysis - Component Test
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Testing the SkillGapAnalysis component with various scenarios including
            missing skills with suggested alternatives
          </Typography>
        </Box>

        {/* Test Case 1: Full Analysis with Various Suggestion Types */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Mixed Missing Skills with Suggestions
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Showing missing skills with various suggestion types: synonym,
            same_category, related, and fuzzy_match
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={testMissingSkills} />
          </Box>
        </Paper>

        {/* Test Case 2: Skills with No Suggestions */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 2: Missing Skills with No Suggestions
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Skills that have no similar alternatives found in the resume
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={noSuggestionsSkills} />
          </Box>
        </Paper>

        {/* Test Case 3: High Confidence Suggestions */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 3: High Confidence Suggestions
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            All suggestions with 85%+ confidence (strong matches)
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis
              missingSkills={highConfidenceSuggestions}
              title="High Confidence Gap Analysis"
            />
          </Box>
        </Paper>

        {/* Test Case 4: Limited Display */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 4: Limited Display (Max 3)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Showing only first 3 of 8 missing skills
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={testMissingSkills} maxDisplay={3} />
          </Box>
        </Paper>

        {/* Test Case 5: Loading State */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 5: Loading State
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={[]} loading={true} />
          </Box>
        </Paper>

        {/* Test Case 6: Error State */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 6: Error State
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis
              missingSkills={[]}
              error="Failed to analyze skill gaps"
            />
          </Box>
        </Paper>

        {/* Test Case 7: Empty State (No Missing Skills) */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 7: Empty State (All Skills Matched)
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            When all required skills are found in the resume
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={emptyMissingSkills} />
          </Box>
        </Paper>

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" component="div">
            ✓ Shows missing required skills with warning styling<br />
            ✓ Displays suggested similar skills from resume<br />
            ✓ Visual distinction between missing and suggested skills<br />
            ✓ Suggestion reason badges (synonym, category, related, similar)<br />
            ✓ Confidence bars for each suggestion<br />
            ✓ Expandable/collapsible suggestion lists<br />
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

export default SkillGapAnalysisTest;
