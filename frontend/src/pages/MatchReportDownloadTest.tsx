import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
  Divider,
} from '@/components/ui';
import MatchReportDownload from '@components/MatchReportDownload';

interface MatchedSkill {
  skill: string;
  confidence: number;
  match_type: 'direct' | 'synonym' | 'fuzzy' | 'context';
  location?: string;
}

interface MissingSkill {
  skill: string;
  suggested_alternatives?: string[];
}

const MatchReportDownloadTest: React.FC = () => {
  // Test data - comprehensive scenario
  const testMatchData = {
    resume_id: 'test-resume-123',
    vacancy_id: 'test-vacancy-456',
    vacancy_title: 'Senior Full Stack Developer',
    candidate_name: 'John Doe',
    overall_score: 82,
    keyword_score: 0.85,
    tfidf_score: 0.78,
    vector_score: 0.80,
    keyword_weight: 0.5,
    tfidf_weight: 0.3,
    vector_weight: 0.2,
    recommendation: 'good' as const,
    processing_time_ms: 145,
    generated_at: new Date().toISOString(),
    matched_skills: [
      {
        skill: 'React',
        confidence: 0.95,
        match_type: 'direct' as const,
        location: 'Work Experience - Senior Developer at Tech Corp (2020-Present)',
      },
      {
        skill: 'TypeScript',
        confidence: 0.92,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
      {
        skill: 'Node.js',
        confidence: 0.88,
        match_type: 'direct' as const,
        location: 'Work Experience - Full Stack Developer at StartupXYZ (2018-2020)',
      },
      {
        skill: 'Python',
        confidence: 0.85,
        match_type: 'synonym' as const,
        location: 'Skills Section',
      },
      {
        skill: 'SQL',
        confidence: 0.82,
        match_type: 'direct' as const,
        location: 'Projects Section - E-commerce Platform',
      },
      {
        skill: 'REST APIs',
        confidence: 0.90,
        match_type: 'context' as const,
        location: 'Work Experience - Senior Developer at Tech Corp',
      },
      {
        skill: 'Git',
        confidence: 0.95,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
      {
        skill: 'Docker',
        confidence: 0.78,
        match_type: 'synonym' as const,
        location: 'Projects Section',
      },
      {
        skill: 'AWS',
        confidence: 0.75,
        match_type: 'fuzzy' as const,
        location: 'Work Experience - Senior Developer',
      },
      {
        skill: 'MongoDB',
        confidence: 0.80,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
    ] as MatchedSkill[],
    missing_skills: [
      {
        skill: 'GraphQL',
        suggested_alternatives: ['REST APIs', 'API Design'],
      },
      {
        skill: 'Kubernetes',
        suggested_alternatives: ['Docker', 'Containerization'],
      },
      {
        skill: 'Redis',
        suggested_alternatives: ['MongoDB', 'Database Management'],
      },
    ] as MissingSkill[],
  };

  // Test data - excellent candidate
  const excellentCandidateData = {
    ...testMatchData,
    resume_id: 'excellent-resume-789',
    vacancy_id: 'test-vacancy-456',
    overall_score: 95,
    keyword_score: 0.98,
    tfidf_score: 0.95,
    vector_score: 0.92,
    recommendation: 'excellent' as const,
    matched_skills: [
      ...testMatchData.matched_skills,
      {
        skill: 'GraphQL',
        confidence: 0.90,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
      {
        skill: 'Kubernetes',
        confidence: 0.88,
        match_type: 'direct' as const,
        location: 'Certifications - AWS Certified DevOps Engineer',
      },
    ] as MatchedSkill[],
    missing_skills: [] as MissingSkill[],
  };

  // Test data - poor candidate
  const poorCandidateData = {
    ...testMatchData,
    resume_id: 'poor-resume-101',
    vacancy_id: 'test-vacancy-456',
    overall_score: 35,
    keyword_score: 0.30,
    tfidf_score: 0.25,
    vector_score: 0.40,
    candidate_name: 'Jane Smith',
    recommendation: 'poor' as const,
    matched_skills: [
      {
        skill: 'JavaScript',
        confidence: 0.70,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
      {
        skill: 'HTML',
        confidence: 0.85,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
      {
        skill: 'CSS',
        confidence: 0.82,
        match_type: 'direct' as const,
        location: 'Skills Section',
      },
    ] as MatchedSkill[],
    missing_skills: [
      {
        skill: 'React',
        suggested_alternatives: ['JavaScript', 'Frontend Frameworks'],
      },
      {
        skill: 'TypeScript',
        suggested_alternatives: ['JavaScript', 'Type Safety'],
      },
      {
        skill: 'Node.js',
        suggested_alternatives: ['JavaScript', 'Backend Development'],
      },
      {
        skill: 'Python',
        suggested_alternatives: [],
      },
      {
        skill: 'SQL',
        suggested_alternatives: [],
      },
      {
        skill: 'REST APIs',
        suggested_alternatives: [],
      },
      {
        skill: 'Git',
        suggested_alternatives: ['Version Control'],
      },
      {
        skill: 'Docker',
        suggested_alternatives: [],
      },
      {
        skill: 'AWS',
        suggested_alternatives: ['Cloud Computing'],
      },
      {
        skill: 'MongoDB',
        suggested_alternatives: [],
      },
      {
        skill: 'GraphQL',
        suggested_alternatives: [],
      },
      {
        skill: 'Kubernetes',
        suggested_alternatives: [],
      },
    ] as MissingSkill[],
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Match Report Download - Component Test
          </Typography>
          <Typography variant="body1" color="secondary">
            Testing the MatchReportDownload component with various candidate scenarios
          </Typography>
        </Box>

        {/* Test Case 1: Good Candidate (Typical Scenario) */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 1: Good Candidate (82% match)
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            This is a typical good match scenario with strong technical skills but some gaps in modern
            technologies like GraphQL and Kubernetes.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchReportDownload matchData={testMatchData} />
          </Box>
        </Paper>

        <Divider />

        {/* Test Case 2: Excellent Candidate */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 2: Excellent Candidate (95% match)
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            This represents an ideal candidate with all required skills and strong confidence scores
            across all matching algorithms.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchReportDownload matchData={excellentCandidateData} />
          </Box>
        </Paper>

        <Divider />

        {/* Test Case 3: Poor Candidate */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Test Case 3: Poor Candidate (35% match)
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            This represents a weak match with only basic frontend skills and many critical gaps in
            required technologies.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchReportDownload matchData={poorCandidateData} />
          </Box>
        </Paper>

        {/* Verification Checklist */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Verification Checklist:
          </Typography>
          <Typography variant="body2" as="div">
            ✓ Download button is visible<br />
            ✓ Clicking button triggers file download<br />
            ✓ Downloaded file contains match breakdown data<br />
            ✓ Report includes overall score and recommendation<br />
            ✓ Report shows score breakdown (Keyword, TF-IDF, Vector)<br />
            ✓ Report lists matched skills with confidence scores<br />
            ✓ Report lists missing skills with suggestions<br />
            ✓ Report includes metadata (IDs, processing time)<br />
            ✓ No console errors<br />
            ✓ HTML format is properly formatted and viewable in browser
          </Typography>
        </Paper>

        {/* Testing Instructions */}
        <Paper elevation={1} sx={{ p: 2, bgcolor: 'warning.50' }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Testing Instructions:
          </Typography>
          <Typography variant="body2" as="div">
            1. Click each "Download Match Report" button<br />
            2. Verify that an HTML file is downloaded<br />
            3. Open the downloaded file in a browser<br />
            4. Verify the report contains all match data<br />
            5. Check that formatting is correct and readable<br />
            6. Try printing the report to PDF (Ctrl+P / Cmd+P)
          </Typography>
        </Paper>
      </Stack>
    </Container>
  );
};

export default MatchReportDownloadTest;
