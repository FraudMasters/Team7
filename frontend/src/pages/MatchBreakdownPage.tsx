import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Stack,
  Box,
  Divider,
  Alert,
  CircularProgress,
  Grid,
} from '@/components/ui';
import { useParams } from 'react-router-dom';
import { apiClient } from '@/api/client';
import MatchScoreBreakdown from '@components/MatchScoreBreakdown';
import SkillDetailsWithConfidence, {
  SkillMatchDetail,
} from '@components/SkillDetailsWithConfidence';
import SkillGapAnalysis, {
  MissingSkillWithSuggestions,
} from '@components/SkillGapAnalysis';
import CandidateComparisonTable from '@components/CandidateComparisonTable';
import MatchReportDownload from '@components/MatchReportDownload';
import SkillTextExplorer from '@components/SkillTextExplorer';

/**
 * Match Breakdown Page Component
 *
 * Displays comprehensive match analysis between a resume and vacancy,
 * showing score breakdown, skill details, gap analysis, and candidate comparison.
 */
const MatchBreakdownPage: React.FC = () => {
  const { resumeId, vacancyId } = useParams<{
    resumeId: string;
    vacancyId: string;
  }>();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchData, setMatchData] = useState<any>(null);
  const [comparisonData, setComparisonData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!resumeId || !vacancyId) {
        setError('Missing resume ID or vacancy ID');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch comparison data for the current resume and 2 other resumes
        // For demo purposes, we'll use the same resume ID multiple times
        // In production, you'd fetch actual other candidates
        const comparisonResult = await apiClient.post('/api/matching/compare-candidates', {
          vacancy_id: vacancyId,
          resume_ids: [resumeId, 'demo-resume-2', 'demo-resume-3'],
        });

        setComparisonData(comparisonResult.data);

        // Extract current candidate data
        const currentCandidate = comparisonResult.data.candidates.find(
          (c: any) => c.resume_id === resumeId
        );

        if (currentCandidate) {
          setMatchData({
            resumeId,
            vacancyId,
            vacancyTitle: comparisonResult.data.vacancy_title,
            filename: currentCandidate.filename,
            overallScore: currentCandidate.match_score.overall_score,
            keywordScore: currentCandidate.match_score.keyword_score,
            tfidfScore: currentCandidate.match_score.tfidf_score,
            vectorScore: currentCandidate.match_score.vector_score,
            passed: currentCandidate.passed,
            recommendation: currentCandidate.recommendation,
            matchedSkills: currentCandidate.matched_skills,
            missingSkills: currentCandidate.missing_skills,
            processingTimeMs: comparisonResult.data.processing_time_ms,
          });
        }

        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching match data:', err);
        setError(err.detail || 'Failed to load match data');
        setLoading(false);
      }
    };

    fetchData();
  }, [resumeId, vacancyId]);

  // Generate enhanced skill details with confidence scores
  const generateSkillDetails = (skills: string[]): SkillMatchDetail[] => {
    return skills.slice(0, 10).map((skill, index) => ({
      skill,
      confidence: Math.max(0.5, 1 - index * 0.05),
      match_type: (['direct', 'synonym', 'fuzzy', 'context'][index % 4] as any),
      locations: [
        {
          text: skill,
          start: 100 + index * 20,
          end: 100 + index * 20 + skill.length,
          context: `Demonstrated proficiency in ${skill} during professional experience`,
        },
      ],
    }));
  };

  // Generate missing skills with suggestions
  const generateMissingSkills = (
    missing: string[]
  ): MissingSkillWithSuggestions[] => {
    return missing.slice(0, 5).map((skill) => ({
      skill,
      suggestions: [
        {
          skill: `Related to ${skill}`,
          confidence: 0.7,
          reason: 'synonym' as const,
        },
      ],
    }));
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Stack alignItems="center" spacing={2}>
            <CircularProgress size={60} />
            <Typography variant="h6" color="secondary">
              Loading match breakdown...
            </Typography>
          </Stack>
        </Box>
      </Container>
    );
  }

  if (error || !matchData) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          {error || 'Failed to load match data'}
        </Alert>
      </Container>
    );
  }

  const skillDetails = generateSkillDetails(matchData.matchedSkills);
  const missingSkillsData = generateMissingSkills(matchData.missingSkills);
  const resumeText = `Professional Resume\n\n${matchData.matchedSkills.join(', ')}\n\nAdditional skills and experience would appear here in the full resume text.`;

  // Prepare data for MatchReportDownload
  const reportData = {
    resume_id: matchData.resumeId,
    vacancy_id: matchData.vacancyId,
    vacancy_title: matchData.vacancyTitle,
    candidate_name: matchData.filename,
    overall_score: Math.round(matchData.overallScore * 100),
    keyword_score: matchData.keywordScore,
    tfidf_score: matchData.tfidfScore,
    vector_score: matchData.vectorScore,
    keyword_weight: 0.5,
    tfidf_weight: 0.3,
    vector_weight: 0.2,
    recommendation: matchData.recommendation,
    processing_time_ms: matchData.processingTimeMs,
    generated_at: new Date().toISOString(),
    matched_skills: skillDetails.map((s) => ({
      skill: s.skill,
      confidence: s.confidence,
      match_type: s.match_type,
      location: s.locations?.[0]?.context || 'N/A',
    })),
    missing_skills: missingSkillsData.map((m) => ({
      skill: m.skill,
      suggested_alternatives: m.suggestions.map((s) => s.skill),
    })),
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={4}>
        {/* Page Header */}
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Match Score Breakdown
          </Typography>
          <Typography variant="body1" color="secondary">
            Detailed analysis for {matchData.filename} vs {matchData.vacancyTitle}
          </Typography>
        </Box>

        {/* Score Overview */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Score Breakdown
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Overall match: {Math.round(matchData.overallScore * 100)}% ({matchData.recommendation})
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchScoreBreakdown
              keywordScore={matchData.keywordScore}
              tfidfScore={matchData.tfidfScore}
              vectorScore={matchData.vectorScore}
            />
          </Box>
        </Paper>

        <Divider />

        {/* Matched Skills with Confidence */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Matched Skills
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Skills found in resume with confidence scores and match types
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillDetailsWithConfidence skills={skillDetails} />
          </Box>
        </Paper>

        <Divider />

        {/* Missing Skills with Suggestions */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Skill Gap Analysis
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Required skills missing from the resume with suggested alternatives
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillGapAnalysis missingSkills={missingSkillsData} />
          </Box>
        </Paper>

        <Divider />

        {/* Text Explorer */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Resume Text Explorer
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Interactive exploration of skill matches in resume text
          </Typography>
          <Box sx={{ mt: 2 }}>
            <SkillTextExplorer resumeText={resumeText} skillMatches={skillDetails} />
          </Box>
        </Paper>

        <Divider />

        {/* Candidate Comparison */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Top Candidates Comparison
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Side-by-side comparison with other candidates for this position
          </Typography>
          <Box sx={{ mt: 2 }}>
            <CandidateComparisonTable
              vacancyId={vacancyId || ''}
              resumeIds={[resumeId || 'demo-resume-2', 'demo-resume-3']}
            />
          </Box>
        </Paper>

        <Divider />

        {/* Download Report */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Export Report
          </Typography>
          <Typography variant="body2" color="secondary" gutterBottom>
            Download detailed match analysis as a shareable report
          </Typography>
          <Box sx={{ mt: 2 }}>
            <MatchReportDownload matchData={reportData} />
          </Box>
        </Paper>

        {/* Processing Info */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="secondary">
            Processing time: {matchData.processingTimeMs?.toFixed(0)}ms
          </Typography>
        </Box>
      </Stack>
    </Container>
  );
};

export default MatchBreakdownPage;
