import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Button,
  CircularProgress,
  Box,
  Tooltip,
  Alert,
  Paper,
  Typography,
  Stack,
} from '@mui/material';
import {
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  Description as HtmlIcon,
} from '@mui/icons-material';
import type {
  ExplainRankingResponse,
  FeatureExplanation,
  ConfidenceInterval,
} from '@/api/explainability';

export interface ExplanationReportExportProps {
  explanationData: ExplainRankingResponse;
  format?: 'html' | 'pdf';
  fileName?: string;
  onDownloadStart?: () => void;
  onDownloadComplete?: () => void;
  onDownloadError?: (error: string) => void;
}

const ExplanationReportExport: React.FC<ExplanationReportExportProps> = ({
  explanationData,
  format = 'html',
  fileName,
  onDownloadStart,
  onDownloadComplete,
  onDownloadError,
}) => {
  const { t } = useTranslation();
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 50) return '#ff9800';
    return '#f44336';
  };

  const getContributionColor = (direction: 'positive' | 'negative') => {
    return direction === 'positive' ? '#4caf50' : '#f44336';
  };

  const getRecommendationLabel = (recommendation: string) => {
    const key = `explainability.recommendation.${recommendation.toLowerCase()}`;
    return t(key, recommendation);
  };

  const generateHTMLReport = (): string => {
    const timestamp = new Date().toLocaleString();
    const overallColor = getScoreColor(explanationData.rank_score);

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Ranking Explanation - ${explanationData.candidate_name || 'Candidate'}</title>
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

        .narrative {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin-bottom: 30px;
        }

        .narrative .title {
            font-weight: 600;
            color: #1976d2;
            margin-bottom: 10px;
            font-size: 16px;
        }

        .narrative .text {
            color: #424242;
            line-height: 1.8;
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

        .confidence-interval {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .confidence-interval .range {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }

        .confidence-interval .level {
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }

        .feature-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .feature-item {
            border: 1px solid #ecf0f1;
            border-radius: 8px;
            padding: 15px;
            background: white;
        }

        .feature-item.positive {
            border-left: 4px solid #4caf50;
        }

        .feature-item.negative {
            border-left: 4px solid #f44336;
        }

        .feature-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .feature-name {
            font-weight: 600;
            color: #2c3e50;
            font-size: 16px;
        }

        .feature-contribution {
            font-weight: bold;
            font-size: 18px;
        }

        .feature-contribution.positive {
            color: #4caf50;
        }

        .feature-contribution.negative {
            color: #f44336;
        }

        .feature-description {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 5px;
        }

        .feature-value {
            font-size: 12px;
            color: #95a5a6;
        }

        .strengths-weaknesses {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .list-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }

        .list-section.strengths {
            border-left: 4px solid #4caf50;
        }

        .list-section.weaknesses {
            border-left: 4px solid #f44336;
        }

        .list-section h3 {
            font-size: 16px;
            margin-bottom: 15px;
            color: #2c3e50;
        }

        .list-section ul {
            list-style: none;
            padding: 0;
        }

        .list-section li {
            padding: 8px 12px;
            margin-bottom: 8px;
            background: white;
            border-radius: 4px;
            font-size: 14px;
            color: #424242;
        }

        .list-section.strengths li::before {
            content: "✓ ";
            color: #4caf50;
            font-weight: bold;
            margin-right: 5px;
        }

        .list-section.weaknesses li::before {
            content: "✗ ";
            color: #f44336;
            font-weight: bold;
            margin-right: 5px;
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
            .strengths-weaknesses {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 AI Ranking Explanation Report</h1>
            <div class="subtitle">Candidate: ${explanationData.candidate_name || 'Unknown'}</div>
            <div class="subtitle">Resume ID: ${explanationData.resume_id}</div>
            <div class="subtitle">Vacancy ID: ${explanationData.vacancy_id}</div>
            <div class="timestamp">Generated: ${timestamp}</div>
        </div>

        <!-- Overall Score -->
        <div class="overall-score">
            <div class="score">${Math.round(explanationData.rank_score)}%</div>
            <div class="recommendation">${getRecommendationLabel(explanationData.recommendation)}</div>
            <div style="font-size: 14px; color: #7f8c8d;">
                ${explanationData.rank_position ? `Position: #${explanationData.rank_position}` : 'Position not ranked'}
            </div>
        </div>

        <!-- Narrative Explanation -->
        <div class="narrative">
            <div class="title">💡 AI Explanation</div>
            <div class="text">${explanationData.narrative}</div>
        </div>

        <!-- Confidence Interval -->
        ${explanationData.confidence_interval ? `
        <div class="section">
            <h2>📈 Confidence Interval</h2>
            <div class="confidence-interval">
                <div class="range">
                    ${Math.round(explanationData.confidence_interval.lower_bound * 100)}% - ${Math.round(explanationData.confidence_interval.upper_bound * 100)}%
                </div>
                <div class="level">
                    ${explanationData.confidence_interval.confidence_level * 100}% confidence
                    <br>
                    ${explanationData.confidence_interval.interpretation}
                </div>
            </div>
        </div>
        ` : ''}

        <!-- Feature Contributions -->
        <div class="section">
            <h2>🔍 Feature Contributions</h2>
            <div class="feature-list">
                ${explanationData.feature_explanations.map((feature: FeatureExplanation) => `
                    <div class="feature-item ${feature.direction}">
                        <div class="feature-header">
                            <div class="feature-name">${feature.feature_name}</div>
                            <div class="feature-contribution ${feature.direction}">
                                ${feature.direction === 'positive' ? '+' : ''}${feature.contribution_percentage.toFixed(1)}%
                            </div>
                        </div>
                        <div class="feature-description">${feature.description}</div>
                        ${feature.value !== undefined ? `
                            <div class="feature-value">
                                Feature value: ${feature.value.toFixed(4)} | Contribution: ${feature.contribution.toFixed(4)}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- Strengths and Weaknesses -->
        <div class="section">
            <h2>💪 Strengths & Areas for Improvement</h2>
            <div class="strengths-weaknesses">
                <!-- Strengths -->
                <div class="list-section strengths">
                    <h3>✅ Key Strengths (${explanationData.strengths.length})</h3>
                    <ul>
                        ${explanationData.strengths.map(strength => `<li>${strength}</li>`).join('')}
                    </ul>
                </div>

                <!-- Weaknesses -->
                <div class="list-section weaknesses">
                    <h3>🔧 Areas for Improvement (${explanationData.weaknesses.length})</h3>
                    <ul>
                        ${explanationData.weaknesses.map(weakness => `<li>${weakness}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>

        <!-- Resume Section Highlights -->
        ${Object.keys(explanationData.highlight_sections).length > 0 ? `
        <div class="section">
            <h2>📝 Influential Resume Sections</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                ${Object.entries(explanationData.highlight_sections).map(([section, content]) => `
                    <div style="margin-bottom: 15px;">
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 5px;">${section}</div>
                        <div style="font-size: 14px; color: #424242; line-height: 1.6; white-space: pre-wrap;">${content}</div>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}

        <!-- Metadata -->
        <div class="metadata">
            <div class="row">
                <span><strong>Resume ID:</strong> ${explanationData.resume_id}</span>
                <span><strong>Vacancy ID:</strong> ${explanationData.vacancy_id}</span>
            </div>
            <div class="row">
                <span><strong>AI Provider:</strong> ${explanationData.provider}</span>
                <span><strong>Model:</strong> ${explanationData.model}</span>
            </div>
            <div class="row">
                <span><strong>Generated:</strong> ${new Date(explanationData.generated_at).toLocaleString()}</span>
            </div>
        </div>

        <!-- Footer -->
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ecf0f1; text-align: center; font-size: 12px; color: #95a5a6;">
            Generated by AgentHR ATS Explainability System<br>
            This report provides transparency into AI-driven ranking decisions
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

      // For PDF format, we would need to call the backend API
      // For now, we generate HTML which can be printed to PDF
      if (format === 'pdf') {
        // Try to use the backend API for PDF generation
        try {
          const response = await fetch(`${import.meta.env.VITE_API_URL ?? ''}/api/explainability/export/pdf`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              resume_id: explanationData.resume_id,
              vacancy_id: explanationData.vacancy_id,
              report_type: 'ranking_explanation',
            }),
          });

          if (response.ok) {
            const data = await response.json();
            if (data.success && data.download_url) {
              // Download the PDF from the provided URL
              const link = document.createElement('a');
              link.href = data.download_url;
              link.download = data.filename || `explanation-report-${explanationData.resume_id}.pdf`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);

              if (onDownloadComplete) {
                onDownloadComplete();
              }
              return;
            }
          }
        } catch (err) {
          // Fall back to HTML export if PDF generation fails
          console.warn('PDF generation failed, falling back to HTML export');
        }
      }

      // Create blob and download link for HTML
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      const defaultFileName = `explanation-report-${explanationData.resume_id}-${explanationData.vacancy_id}-${new Date().getTime()}.html`;
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
        <Tooltip title={t('explanationReportExport.title', 'Export Explanation Report')}>
          <Button
            variant="contained"
            color="primary"
            startIcon={generating ? <CircularProgress size={20} /> : <DownloadIcon />}
            onClick={handleDownload}
            disabled={generating}
            fullWidth
            size="large"
            sx={{ py: 1.5 }}
          >
            {generating
              ? t('explanationReportExport.generating', 'Generating report...')
              : t('explanationReportExport.exportButton', 'Export Explanation Report')}
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
            {t('explanationReportExport.reportContents', 'Report Contents: AI narrative explanation, feature contributions, confidence intervals, candidate strengths and weaknesses, and resume section highlights')}
          </Typography>
        </Paper>

        {/* Format Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {format === 'pdf' ? (
            <>
              <PdfIcon fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary">
                {t('explanationReportExport.formatPdf', 'Format: PDF (professional document)')}
              </Typography>
            </>
          ) : (
            <>
              <HtmlIcon fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary">
                {t('explanationReportExport.formatHtml', 'Format: HTML (viewable in any browser, can be printed to PDF)')}
              </Typography>
            </>
          )}
        </Box>
      </Stack>
    </Box>
  );
};

export default ExplanationReportExport;
export type { ExplanationReportExportProps };
