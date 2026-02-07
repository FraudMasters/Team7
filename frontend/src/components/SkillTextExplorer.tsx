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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import styled from '@emotion/styled';

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

const StyledCard = styled(Card)`
  margin-bottom: ${({ theme }) => theme.spacing.sm};
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const HighlightBox = styled(Box)`
  padding: ${({ theme }) => theme.spacing.md};
  background-color: ${({ theme }) => theme.colors.background.paper};
  border-radius: ${({ theme }) => theme.spacing.md};
  border: 1px solid ${({ theme }) => theme.colors.divider};
  max-height: 600;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
`;

const SkillHighlight = styled('span')<{ matchType: string; confidence: number; theme: any }>`
  background-color: ${({ matchType, confidence }) => {
    switch (matchType) {
      case 'direct':
        return confidence >= 0.9 ? 'rgba(76, 175, 80, 0.3)' : 'rgba(76, 175, 80, 0.15)';
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
  }};
  border-bottom: 2px solid
    ${({ confidence, theme }) =>
      confidence >= 0.9
        ? theme.colors.success.main
        : confidence >= 0.7
        ? theme.colors.primary.main
        : confidence >= 0.5
        ? theme.colors.warning.main
        : theme.colors.error.main};
  padding: 2px 4px;
  margin: 0 2px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;

  &:hover {
    background-color: ${({ matchType, confidence }) => {
      let bg = '';
      switch (matchType) {
        case 'direct':
          bg = confidence >= 0.9 ? 'rgba(76, 175, 80, 0.3)' : 'rgba(76, 175, 80, 0.15)';
          break;
        case 'synonym':
          bg = 'rgba(33, 150, 243, 0.2)';
          break;
        default:
          bg = 'rgba(158, 158, 158, 0.2)';
      }
      return bg.replace('0.2', '0.4').replace('0.3', '0.5').replace('0.15', '0.3');
    }};
    transform: scale(1.05);
  }
`;

const getMatchTypeConfig = (matchType: string) => {
  switch (matchType) {
    case 'direct':
      return {
        label: 'Direct',
        iconName: 'check-circle',
        color: 'success' as const,
        description: 'Exact match found in resume',
      };
    case 'synonym':
      return {
        label: 'Synonym',
        iconName: 'languages',
        color: 'info' as const,
        description: 'Matched through known synonyms',
      };
    case 'fuzzy':
      return {
        label: 'Fuzzy',
        iconName: 'search',
        color: 'warning' as const,
        description: 'Partial match (typo or variation)',
      };
    case 'context':
      return {
        label: 'Context',
        iconName: 'brain',
        color: 'secondary' as const,
        description: 'Matched based on domain context',
      };
    case 'compound':
      return {
        label: 'Compound',
        iconName: 'wand-sparkles',
        color: 'primary' as const,
        description: 'Compound skill match',
      };
    case 'language_hierarchy':
      return {
        label: 'Hierarchy',
        iconName: 'brain',
        color: 'info' as const,
        description: 'Matched through language hierarchy',
      };
    default:
      return {
        label: 'Unknown',
        iconName: 'check-circle',
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
              <Typography css={{ fontWeight: 600 }}>
                {highlight.detail.skill}
              </Typography>
              <Typography>
                {matchConfig.label} match • {confidencePercent}% confidence
              </Typography>
              <Typography color="text.secondary">
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
      <Box css={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography css={{ ml: 2 }}>
          Loading resume text explorer...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" css={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!resumeText) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Typography color="text.secondary">
          No resume text available
        </Typography>
        <Typography color="text.secondary">
          Upload a resume to explore skill matches
        </Typography>
      </Box>
    );
  }

  return (
    <StyledCard>
      <CardContent>
        <Box
          css={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography fontWeight={600}>
            Resume Text Explorer
          </Typography>
          <Chip
            label={`${skillMatches.length} skills`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>

        <Divider css={{ mb: 2 }} />

        <Typography color="text.secondary" css={{ mb: 2 }}>
          Click on highlighted skills to see detailed match information
        </Typography>

        {/* Highlighted Text */}
        <HighlightBox>{renderHighlightedText()}</HighlightBox>

        {/* Skill Details Panel */}
        {selectedSkill && (
          <Collapse in={detailsExpanded}>
            <Paper
              elevation={2}
              css={{
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
                css={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                }}
              >
                <Typography fontWeight={600}>
                  {selectedSkill.skill}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => setDetailsExpanded(!detailsExpanded)}
                >
                  <Icon name={detailsExpanded ? 'chevron-up' : 'chevron-down'} />
                </IconButton>
              </Box>

              <Stack css={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1.5 }}>
                {(() => {
                  const matchConfig = getMatchTypeConfig(selectedSkill.match_type);
                  return (
                    <Chip
                      iconName={matchConfig.iconName}
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
                  css={{
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
                  <Typography color="text.secondary" css={{ mb: 1 }}>
                    Matched as: <strong>{selectedSkill.matched_as}</strong>
                  </Typography>
                )}

              {selectedSkill.locations && selectedSkill.locations.length > 0 && (
                <Box>
                  <Typography
                    color="text.secondary"
                    css={{ display: 'block', mb: 1, fontWeight: 500 }}
                  >
                    Found in {selectedSkill.locations.length} location{selectedSkill.locations.length > 1 ? 's' : ''}:
                  </Typography>
                  {selectedSkill.locations.map((location, idx) => (
                    <Box
                      key={idx}
                      css={{
                        p: 1,
                        mt: idx > 0 ? 0.5 : 0,
                        backgroundColor: 'grey.50',
                        borderRadius: 0.5,
                      }}
                    >
                      <Typography
                        css={{
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
        <Box css={{ mt: 2 }}>
          <Typography color="text.secondary" css={{ display: 'block', mb: 1, fontWeight: 500 }}>
            Highlight Legend:
          </Typography>
          <Stack css={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {(['direct', 'synonym', 'fuzzy', 'context', 'compound'] as const).map((type) => {
              const config = getMatchTypeConfig(type);
              return (
                <Chip
                  key={type}
                  iconName={config.iconName}
                  label={config.label}
                  size="small"
                  variant="outlined"
                  css={{ fontSize: '0.7rem', height: 22 }}
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
