import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckIcon,
  Psychology as AIIcon,
  Search as SearchIcon,
  AutoFixHigh as MagicIcon,
  Translate as SynonymIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

export interface SkillMatchDetail {
  skill: string;
  confidence: number;
  match_type: 'direct' | 'synonym' | 'fuzzy' | 'context' | 'compound' | 'language_hierarchy';
  matched_as?: string;
  locations?: Array<{
    text: string;
    start: number;
    end: number;
    context: string;
  }>;
}

interface SkillTextExplorerProps {
  resumeText: string;
  skillMatches: SkillMatchDetail[];
  loading?: boolean;
  error?: string | null;
}

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

const HighlightBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.spacing(1),
  border: `1px solid ${theme.palette.divider}`,
  maxHeight: 600,
  overflowY: 'auto',
  fontFamily: 'monospace',
  fontSize: '0.875rem',
  lineHeight: 1.6,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
}));

const SkillHighlight = styled('span')<{ matchType: string; confidence: number }>(
  ({ theme, matchType, confidence }) => {
    const getBackgroundColor = () => {
      switch (matchType) {
        case 'direct':
          return confidence >= 0.9
            ? 'rgba(76, 175, 80, 0.3)'
            : 'rgba(76, 175, 80, 0.15)';
        case 'synonym':
          return 'rgba(33, 150, 243, 0.2)';
        case 'fuzzy':
          return 'rgba(255, 152, 0, 0.2)';
        case 'context':
          return 'rgba(156, 39, 176, 0.2)';
        case 'compound':
          return 'rgba(63, 81, 181, 0.2)';
        case 'language_hierarchy':
          return 'rgba(0, 188, 212, 0.2)';
        default:
          return 'rgba(158, 158, 158, 0.2)';
      }
    };

    return {
      backgroundColor: getBackgroundColor(),
      borderBottom: `2px solid ${
        confidence >= 0.9
          ? theme.palette.success.main
          : confidence >= 0.7
          ? theme.palette.primary.main
          : confidence >= 0.5
          ? theme.palette.warning.main
          : theme.palette.error.main
      }`,
      padding: '2px 4px',
      margin: '0 2px',
      borderRadius: '3px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      fontWeight: 500,
      '&:hover': {
        backgroundColor: getBackgroundColor().replace('0.2', '0.4').replace('0.3', '0.5').replace('0.15', '0.3'),
        transform: 'scale(1.05)',
      },
    };
  }
);

const getMatchTypeConfig = (matchType: string) => {
  switch (matchType) {
    case 'direct':
      return {
        label: 'Direct',
        icon: <CheckIcon fontSize="small" />,
        color: 'success' as const,
        description: 'Exact match found in resume',
      };
    case 'synonym':
      return {
        label: 'Synonym',
        icon: <SynonymIcon fontSize="small" />,
        color: 'info' as const,
        description: 'Matched through known synonyms',
      };
    case 'fuzzy':
      return {
        label: 'Fuzzy',
        icon: <SearchIcon fontSize="small" />,
        color: 'warning' as const,
        description: 'Partial match (typo or variation)',
      };
    case 'context':
      return {
        label: 'Context',
        icon: <AIIcon fontSize="small" />,
        color: 'secondary' as const,
        description: 'Matched based on domain context',
      };
    case 'compound':
      return {
        label: 'Compound',
        icon: <MagicIcon fontSize="small" />,
        color: 'primary' as const,
        description: 'Compound skill match',
      };
    case 'language_hierarchy':
      return {
        label: 'Hierarchy',
        icon: <AIIcon fontSize="small" />,
        color: 'info' as const,
        description: 'Matched through language hierarchy',
      };
    default:
      return {
        label: 'Unknown',
        icon: <CheckIcon fontSize="small" />,
        color: 'default' as const,
        description: 'Unknown match type',
      };
  }
};

const SkillTextExplorer: React.FC<SkillTextExplorerProps> = ({
  resumeText,
  skillMatches,
  loading = false,
  error = null,
}) => {
  const [selectedSkill, setSelectedSkill] = useState<SkillMatchDetail | null>(null);
  const [detailsExpanded, setDetailsExpanded] = useState(true);

  const handleSkillClick = (skill: SkillMatchDetail) => {
    setSelectedSkill(skill);
    setDetailsExpanded(true);
  };

  const renderHighlightedText = () => {
    if (!resumeText || skillMatches.length === 0) {
      return <Typography color="text.secondary">{resumeText || 'No resume text available'}</Typography>;
    }

    // Create a map of all skill locations
    const allHighlights: Array<{ start: number; end: number; detail: SkillMatchDetail }> = [];

    skillMatches.forEach((skillDetail) => {
      if (skillDetail.locations) {
        skillDetail.locations.forEach((location) => {
          allHighlights.push({
            start: location.start,
            end: location.end,
            detail: skillDetail,
          });
        });
      }
    });

    // Sort by start position
    allHighlights.sort((a, b) => a.start - b.start);

    // Build the highlighted text
    const segments: React.ReactNode[] = [];
    let lastIndex = 0;

    allHighlights.forEach((highlight, index) => {
      // Add text before this highlight
      if (highlight.start > lastIndex) {
        segments.push(
          <span key={`text-${index}`}>
            {resumeText.substring(lastIndex, highlight.start)}
          </span>
        );
      }

      // Add the highlighted skill
      const matchConfig = getMatchTypeConfig(highlight.detail.match_type);
      const confidencePercent = Math.round(highlight.detail.confidence * 100);

      segments.push(
        <Tooltip
          key={`highlight-${index}`}
          title={
            <Box>
              <Typography variant="caption" display="block" fontWeight={600}>
                {highlight.detail.skill}
              </Typography>
              <Typography variant="caption" display="block">
                {matchConfig.label} match • {confidencePercent}% confidence
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                {matchConfig.description}
              </Typography>
            </Box>
          }
          arrow
          placement="top"
        >
          <SkillHighlight
            matchType={highlight.detail.match_type}
            confidence={highlight.detail.confidence}
            onClick={() => handleSkillClick(highlight.detail)}
          >
            {resumeText.substring(highlight.start, highlight.end)}
          </SkillHighlight>
        </Tooltip>
      );

      lastIndex = highlight.end;
    });

    // Add remaining text
    if (lastIndex < resumeText.length) {
      segments.push(
        <span key="text-end">{resumeText.substring(lastIndex)}</span>
      );
    }

    return segments;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading resume text explorer...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!resumeText) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No resume text available
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload a resume to explore skill matches
        </Typography>
      </Box>
    );
  }

  return (
    <StyledCard>
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            Resume Text Explorer
          </Typography>
          <Chip
            label={`${skillMatches.length} skills`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>

        <Divider sx={{ mb: 2 }} />

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Click on highlighted skills to see detailed match information
        </Typography>

        {/* Highlighted Text */}
        <HighlightBox>{renderHighlightedText()}</HighlightBox>

        {/* Skill Details Panel */}
        {selectedSkill && (
          <Collapse in={detailsExpanded}>
            <Paper
              elevation={2}
              sx={{
                mt: 2,
                p: 2,
                borderLeft: 4,
                borderLeftColor:
                  selectedSkill.confidence >= 0.9
                    ? 'success.main'
                    : selectedSkill.confidence >= 0.7
                    ? 'primary.main'
                    : selectedSkill.confidence >= 0.5
                    ? 'warning.main'
                    : 'error.main',
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                }}
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  {selectedSkill.skill}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => setDetailsExpanded(!detailsExpanded)}
                >
                  {detailsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>

              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
                {(() => {
                  const matchConfig = getMatchTypeConfig(selectedSkill.match_type);
                  return (
                    <Chip
                      icon={matchConfig.icon}
                      label={matchConfig.label}
                      size="small"
                      color={matchConfig.color}
                      variant="outlined"
                    />
                  );
                })()}

                <Chip
                  label={`${Math.round(selectedSkill.confidence * 100)}% confidence`}
                  size="small"
                  sx={{
                    fontWeight: 600,
                    backgroundColor:
                      selectedSkill.confidence >= 0.9
                        ? 'success.light'
                        : selectedSkill.confidence >= 0.7
                        ? 'primary.light'
                        : selectedSkill.confidence >= 0.5
                        ? 'warning.light'
                        : 'error.light',
                  }}
                />
              </Stack>

              {selectedSkill.matched_as &&
                selectedSkill.matched_as !== selectedSkill.skill && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Matched as: <strong>{selectedSkill.matched_as}</strong>
                  </Typography>
                )}

              {selectedSkill.locations && selectedSkill.locations.length > 0 && (
                <Box>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block', mb: 1, fontWeight: 500 }}
                  >
                    Found in {selectedSkill.locations.length} location{selectedSkill.locations.length > 1 ? 's' : ''}:
                  </Typography>
                  {selectedSkill.locations.map((location, idx) => (
                    <Box
                      key={idx}
                      sx={{
                        p: 1,
                        mt: idx > 0 ? 0.5 : 0,
                        backgroundColor: 'grey.50',
                        borderRadius: 0.5,
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          color: 'text.primary',
                          display: 'block',
                          lineHeight: 1.4,
                        }}
                      >
                        {location.context}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Paper>
          </Collapse>
        )}

        {/* Legend */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontWeight: 500 }}>
            Highlight Legend:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {(['direct', 'synonym', 'fuzzy', 'context', 'compound'] as const).map((type) => {
              const config = getMatchTypeConfig(type);
              return (
                <Chip
                  key={type}
                  icon={config.icon}
                  label={config.label}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 22 }}
                />
              );
            })}
          </Stack>
        </Box>
      </CardContent>
    </StyledCard>
  );
};

export default SkillTextExplorer;
