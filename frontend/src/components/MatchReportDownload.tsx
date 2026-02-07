import React, { useState } from 'react';
import {
  Button,
  CircularProgress,
  Box,
  Tooltip,
  Alert,
  Paper,
  Typography,
  Stack,
  Chip,
  LinearProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

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

interface MatchReportData {
  resume_id: string;
  vacancy_id: string;
  vacancy_title: string;
  candidate_name?: string;
  overall_score: number;
  keyword_score: number;
  tfidf_score: number;
  vector_score: number;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  matched_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  recommendation?: 'excellent' | 'good' | 'maybe' | 'poor';
  processing_time_ms?: number;
  generated_at?: string;
}

interface MatchReportDownloadProps {
  matchData: MatchReportData;
  format?: 'html' | 'pdf';
  fileName?: string;
  onDownloadStart?: () => void;
  onDownloadComplete?: () => void;
  onDownloadError?: (error: string) => void;
}

const MatchReportDownload: React.FC<MatchReportDownloadProps> = ({
  matchData,
  format = 'html',
  fileName,
  onDownloadStart,
  onDownloadComplete,
  onDownloadError,
}) => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendationLabel = (rec?: string) => {
    switch (rec) {
      case 'excellent':
        return 'Excellent Candidate';
      case 'good':
        return 'Good Candidate';
      case 'maybe':
        return 'Possible Match';
      case 'poor':
        return 'Weak Match';
      default:
        return 'Not Evaluated';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 50) return '#ff9800';
    return '#f44336';
  };

  const getMatchTypeLabel = (type: string) => {
    switch (type) {
      case 'direct':
        return 'Direct Match';
      case 'synonym':
        return 'Synonym';
      case 'fuzzy':
        return 'Fuzzy Match';
      case 'context':
        return 'Contextual';
      default:
        return type;
    }
  };

  const generateHTMLReport = (): string => {
    const timestamp = new Date().toLocaleString();
    const overallColor = getScoreColor(matchData.overall_score);
    const keywordColor = getScoreColor(matchData.keyword_score * 100);
    const tfidfColor = getScoreColor(matchData.tfidf_score * 100);
    const vectorColor = getScoreColor(matchData.vector_score * 100);

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Match Report - ${matchData.vacancy_title}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .header {
            border-bottom: 3px solid ${overallColor};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 32px;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .header .subtitle {
            font-size: 16px;
            color: #7f8c8d;
            margin-bottom: 5px;
        }

        .header .timestamp {
            font-size: 12px;
            color: #95a5a6;
        }

        .overall-score {
            background: linear-gradient(135deg, ${overallColor}22 0%, ${overallColor}44 100%);
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 30px;
            border: 2px solid ${overallColor};
        }

        .overall-score .score {
            font-size: 64px;
            font-weight: bold;
            color: ${overallColor};
            margin-bottom: 10px;
        }

        .overall-score .recommendation {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .section {
            margin-bottom: 30px;
        }

        .section h2 {
            font-size: 20px;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }

        .score-breakdown {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }

        .score-card {
            border: 1px solid #ecf0f1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }

        .score-card .title {
            font-size: 14px;
            font-weight: 600;
            color: #7f8c8d;
            margin-bottom: 10px;
        }

        .score-card .score {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .score-card .weight {
            font-size: 12px;
            color: #95a5a6;
        }

        .score-card.keyword { border-color: ${keywordColor}; }
        .score-card.keyword .score { color: ${keywordColor}; }

        .score-card.tfidf { border-color: ${tfidfColor}; }
        .score-card.tfidf .score { color: ${tfidfColor}; }

        .score-card.vector { border-color: ${vectorColor}; }
        .score-card.vector .score { color: ${vectorColor}; }

        .skills-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .skill-list {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }

        .skill-list.matched {
            border-left: 4px solid #4caf50;
        }

        .skill-list.missing {
            border-left: 4px solid #f44336;
        }

        .skill-list h3 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #2c3e50;
        }

        .skill-item {
            background: white;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            border: 1px solid #ecf0f1;
        }

        .skill-item .name {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 4px;
        }

        .skill-item .details {
            font-size: 12px;
            color: #7f8c8d;
            display: flex;
            justify-content: space-between;
        }

        .skill-item .confidence {
            color: #27ae60;
        }

        .skill-item .match-type {
            background: #ecf0f1;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10px;
        }

        .missing-skill {
            background: #ffebee;
            border-left: 3px solid #f44336;
        }

        .missing-skill .suggestions {
            font-size: 11px;
            color: #e74c3c;
            margin-top: 4px;
        }

        .metadata {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-size: 12px;
            color: #7f8c8d;
        }

        .metadata .row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
            }
        }

        @media (max-width: 600px) {
            .score-breakdown {
                grid-template-columns: 1fr;
            }
            .skills-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Candidate Match Report</h1>
            <div class="subtitle">${matchData.vacancy_title}</div>
            <div class="subtitle">Candidate: ${matchData.candidate_name || 'Unknown'}</div>
            <div class="timestamp">Generated: ${timestamp}</div>
        </div>

        <!-- Overall Score -->
        <div class="overall-score">
            <div class="score">${Math.round(matchData.overall_score)}%</div>
            <div class="recommendation">${getRecommendationLabel(matchData.recommendation)}</div>
            <div style="font-size: 14px; color: #7f8c8d;">
                Overall Match Score
            </div>
        </div>

        <!-- Score Breakdown -->
        <div class="section">
            <h2>🔍 Score Breakdown</h2>
            <div class="score-breakdown">
                <div class="score-card keyword">
                    <div class="title">Keyword Matching</div>
                    <div class="score">${Math.round(matchData.keyword_score * 100)}%</div>
                    <div class="weight">Weight: ${matchData.keyword_weight * 100}%</div>
                </div>
                <div class="score-card tfidf">
                    <div class="title">TF-IDF Weighting</div>
                    <div class="score">${Math.round(matchData.tfidf_score * 100)}%</div>
                    <div class="weight">Weight: ${matchData.tfidf_weight * 100}%</div>
                </div>
                <div class="score-card vector">
                    <div class="title">Semantic Similarity</div>
                    <div class="score">${Math.round(matchData.vector_score * 100)}%</div>
                    <div class="weight">Weight: ${matchData.vector_weight * 100}%</div>
                </div>
            </div>
        </div>

        <!-- Skills Analysis -->
        <div class="section">
            <h2>💡 Skills Analysis</h2>
            <div class="skills-grid">
                <!-- Matched Skills -->
                <div class="skill-list matched">
                    <h3>✅ Matched Skills (${matchData.matched_skills.length})</h3>
                    ${matchData.matched_skills.map(skill => `
                        <div class="skill-item">
                            <div class="name">${skill.skill}</div>
                            <div class="details">
                                <span class="confidence">Confidence: ${Math.round(skill.confidence * 100)}%</span>
                                <span class="match-type">${getMatchTypeLabel(skill.match_type)}</span>
                            </div>
                            ${skill.location ? `<div style="font-size: 11px; color: #95a5a6; margin-top: 4px;">📍 ${skill.location}</div>` : ''}
                        </div>
                    `).join('')}
                </div>

                <!-- Missing Skills -->
                <div class="skill-list missing">
                    <h3>❌ Missing Skills (${matchData.missing_skills.length})</h3>
                    ${matchData.missing_skills.map(skill => `
                        <div class="skill-item missing-skill">
                            <div class="name">${skill.skill}</div>
                            ${skill.suggested_alternatives && skill.suggested_alternatives.length > 0 ? `
                                <div class="suggestions">
                                    💡 Suggested: ${skill.suggested_alternatives.join(', ')}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>

        <!-- Metadata -->
        <div class="metadata">
            <div class="row">
                <span><strong>Resume ID:</strong> ${matchData.resume_id}</span>
                <span><strong>Vacancy ID:</strong> ${matchData.vacancy_id}</span>
            </div>
            <div class="row">
                <span><strong>Processing Time:</strong> ${matchData.processing_time_ms || 'N/A'}ms</span>
                <span><strong>Algorithm:</strong> Unified Matcher v1</span>
            </div>
        </div>

        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ecf0f1; text-align: center; font-size: 12px; color: #95a5a6;">
            Generated by AgentHR ATS Matching System<br>
            For questions about this report, contact your system administrator
        </div>
    </div>
</body>
</html>
    `.trim();
  };

  const handleDownload = async () => {
    setGenerating(true);
    setError(null);

    try {
      if (onDownloadStart) {
        onDownloadStart();
      }

      // Generate HTML content
      const htmlContent = generateHTMLReport();

      // Create blob and download link
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      const defaultFileName = `match-report-${matchData.resume_id}-${matchData.vacancy_id}-${new Date().getTime()}.html`;
      link.download = fileName || defaultFileName;

      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up
      URL.revokeObjectURL(url);

      if (onDownloadComplete) {
        onDownloadComplete();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate report';
      setError(errorMessage);
      if (onDownloadError) {
        onDownloadError(errorMessage);
      }
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Box>
      <Stack spacing={2}>
        {/* Download Button */}
        <Tooltip title={`Download ${format.toUpperCase()} report`}>
          <Button
            variant="contained"
            color="primary"
            startIcon={generating ? <CircularProgress size={20} /> : <Icon name="download" />}
            onClick={handleDownload}
            disabled={generating}
            fullWidth
            size="large"
            sx={{ py: 1.5 }}
          >
            {generating ? 'Generating Report...' : 'Download Match Report'}
          </Button>
        </Tooltip>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Info Section */}
        <Paper elevation={0} sx={{ p: 2, bgcolor: 'info.50' }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Report Contents:</strong> Overall score, detailed score breakdown,
            matched skills with confidence scores, missing skills with suggestions,
            and processing metadata
          </Typography>
        </Paper>

        {/* Format Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Icon name="file-text" fontSize="small" color="action" />
          <Typography variant="caption" color="text.secondary">
            Format: HTML (viewable in any browser, can be printed to PDF)
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
};

export default MatchReportDownload;
