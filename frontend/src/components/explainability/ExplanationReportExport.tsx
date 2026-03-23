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

  /**
   * Generate chart as base64 data URL for embedding
   */
  const generateFeatureContributionChart = (): string => {
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    // Sort features by contribution magnitude
    const sortedFeatures = [...explanationData.feature_explanations].sort(
      (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)
    );

    // Take top 10 features
    const topFeatures = sortedFeatures.slice(0, 10);

    const padding = 60;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    const barHeight = 30;
    const barSpacing = 10;

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Title
    ctx.fillStyle = '#2c3e50';
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Top Feature Contributions', canvas.width / 2, 30);

    // Find max absolute contribution for scaling
    const maxContribution = Math.max(
      ...topFeatures.map((f) => Math.abs(f.contribution))
    );

    // Draw bars
    topFeatures.forEach((feature, index) => {
      const y = padding + index * (barHeight + barSpacing);
      const barWidth = (Math.abs(feature.contribution) / maxContribution) * (chartWidth / 2);
      const color = feature.direction === 'positive' ? '#4caf50' : '#f44336';

      // Draw bar
      ctx.fillStyle = color;
      if (feature.contribution >= 0) {
        ctx.fillRect(canvas.width / 2, y, barWidth, barHeight);
      } else {
        ctx.fillRect(canvas.width / 2 - barWidth, y, barWidth, barHeight);
      }

      // Draw feature name
      ctx.fillStyle = '#2c3e50';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(
        feature.feature_name.substring(0, 25),
        canvas.width / 2 - 10,
        y + barHeight / 2 + 4
      );

      // Draw contribution value
      ctx.textAlign = 'left';
      ctx.fillStyle = color;
      ctx.font = 'bold 12px sans-serif';
      ctx.fillText(
        `${feature.contribution > 0 ? '+' : ''}${feature.contribution_percentage.toFixed(1)}%`,
        canvas.width / 2 + (feature.contribution >= 0 ? barWidth + 10 : -barWidth - 60),
        y + barHeight / 2 + 4
      );
    });

    // Draw center line
    ctx.strokeStyle = '#95a5a6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, padding);
    ctx.lineTo(canvas.width / 2, padding + topFeatures.length * (barHeight + barSpacing));
    ctx.stroke();

    return canvas.toDataURL('image/png');
  };

  /**
   * Generate confidence interval visualization chart
   */
  const generateConfidenceChart = (): string => {
    if (!explanationData.confidence_interval) return '';

    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    const padding = 60;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = 100;

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Title
    ctx.fillStyle = '#2c3e50';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Confidence Interval', canvas.width / 2, 30);

    const ci = explanationData.confidence_interval;
    const y = 80;

    // Draw scale line
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(canvas.width - padding, y);
    ctx.stroke();

    // Draw confidence interval bar
    const lowerX = padding + ci.lower_bound * chartWidth;
    const upperX = padding + ci.upper_bound * chartWidth;
    const scoreX = padding + (explanationData.rank_score / 100) * chartWidth;

    ctx.fillStyle = '#2196f3';
    ctx.globalAlpha = 0.3;
    ctx.fillRect(lowerX, y - 20, upperX - lowerX, 40);
    ctx.globalAlpha = 1;

    // Draw bounds
    ctx.strokeStyle = '#2196f3';
    ctx.lineWidth = 2;
    [lowerX, upperX].forEach((x) => {
      ctx.beginPath();
      ctx.moveTo(x, y - 25);
      ctx.lineTo(x, y + 25);
      ctx.stroke();
    });

    // Draw actual score marker
    ctx.fillStyle = getScoreColor(explanationData.rank_score);
    ctx.beginPath();
    ctx.arc(scoreX, y, 8, 0, Math.PI * 2);
    ctx.fill();

    // Labels
    ctx.fillStyle = '#2c3e50';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(ci.lower_bound * 100)}%`, lowerX, y + 45);
    ctx.fillText(`${Math.round(ci.upper_bound * 100)}%`, upperX, y + 45);
    ctx.fillText(`${Math.round(explanationData.rank_score)}%`, scoreX, y - 15);

    // Legend
    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#7f8c8d';
    ctx.fillText(
      `${ci.confidence_level * 100}% Confidence Interval`,
      canvas.width / 2,
      y + 70
    );

    return canvas.toDataURL('image/png');
  };

  /**
   * Generate score breakdown chart
   */
  const generateScoreChart = (): string => {
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 120;

    // Draw circular progress
    const score = explanationData.rank_score / 100;
    const color = getScoreColor(explanationData.rank_score);

    // Background circle
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.stroke();

    // Score arc
    ctx.strokeStyle = color;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, -Math.PI / 2, -Math.PI / 2 + score * Math.PI * 2);
    ctx.stroke();

    // Center text - score
    ctx.fillStyle = color;
    ctx.font = 'bold 64px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${Math.round(explanationData.rank_score)}`, centerX, centerY - 10);

    // Percentage symbol
    ctx.font = 'bold 24px sans-serif';
    ctx.fillText('%', centerX, centerY + 40);

    // Recommendation label below
    ctx.fillStyle = '#2c3e50';
    ctx.font = '16px sans-serif';
    ctx.fillText(
      getRecommendationLabel(explanationData.recommendation),
      centerX,
      centerY + radius + 40
    );

    return canvas.toDataURL('image/png');
  };

  const generateHTMLReport = (): string => {
    const timestamp = new Date().toLocaleString();
    const overallColor = getScoreColor(explanationData.rank_score);

    // Generate charts
    const featureChart = generateFeatureContributionChart();
    const confidenceChart = generateConfidenceChart();
    const scoreChart = generateScoreChart();

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

        /* Chart styling */
        .chart-container {
            margin: 20px 0;
            text-align: center;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            page-break-inside: avoid;
        }

        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }

        /* Page break controls for PDF */
        .page-break-before {
            page-break-before: always;
        }

        .page-break-after {
            page-break-after: always;
        }

        .no-page-break {
            page-break-inside: avoid;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
                max-width: 100%;
                padding: 20px;
            }

            .header {
                page-break-after: avoid;
            }

            .overall-score {
                page-break-inside: avoid;
                page-break-after: avoid;
            }

            .section {
                page-break-inside: avoid;
            }

            .section h2 {
                page-break-after: avoid;
            }

            .feature-item {
                page-break-inside: avoid;
            }

            .chart-container {
                page-break-inside: avoid;
            }

            /* Ensure charts fit on page */
            img {
                max-width: 100%;
                height: auto;
            }

            /* Optimize colors for print */
            .overall-score {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .feature-item.positive,
            .feature-item.negative {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
        }

        @media (max-width: 600px) {
            .strengths-weaknesses {
                grid-template-columns: 1fr;
            }

            .overall-score > div {
                flex-direction: column;
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

        <!-- Overall Score with Chart -->
        <div class="overall-score">
            <div style="display: flex; align-items: center; justify-content: center; gap: 40px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px; text-align: center;">
                    <div class="score">${Math.round(explanationData.rank_score)}%</div>
                    <div class="recommendation">${getRecommendationLabel(explanationData.recommendation)}</div>
                    <div style="font-size: 14px; color: #7f8c8d; margin-top: 10px;">
                        ${explanationData.rank_position ? `Position: #${explanationData.rank_position}` : 'Position not ranked'}
                    </div>
                </div>
                ${scoreChart ? `
                <div style="flex: 0 0 auto;">
                    <img src="${scoreChart}" alt="Score Visualization" style="max-width: 300px; height: auto;" />
                </div>
                ` : ''}
            </div>
        </div>

        <!-- Narrative Explanation -->
        <div class="narrative no-page-break">
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
                ${confidenceChart ? `
                <div style="margin-top: 20px; text-align: center;">
                    <img src="${confidenceChart}" alt="Confidence Interval Visualization" style="max-width: 100%; height: auto;" />
                </div>
                ` : ''}
            </div>
        </div>
        ` : ''}

        <!-- Feature Contributions -->
        <div class="section">
            <h2>🔍 Feature Contributions</h2>
            ${featureChart ? `
            <div style="margin-bottom: 30px; text-align: center; background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <img src="${featureChart}" alt="Feature Contributions Chart" style="max-width: 100%; height: auto;" />
            </div>
            ` : ''}
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
        <div class="section no-page-break">
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
        <div class="section page-break-before">
            <h2>📝 Influential Resume Sections</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                ${Object.entries(explanationData.highlight_sections).map(([section, content]) => `
                    <div style="margin-bottom: 15px;" class="no-page-break">
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 5px;">${section}</div>
                        <div style="font-size: 14px; color: #424242; line-height: 1.6; white-space: pre-wrap;">${content}</div>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}

        <!-- Metadata -->
        <div class="metadata no-page-break">
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
