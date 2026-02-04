/**
 * TouchCarousel Demo Component
 *
 * This is a demonstration component showing how to use the TouchCarousel
 * component with candidate cards for mobile-friendly swiping.
 *
 * Usage:
 * Import and render this component in a page to see TouchCarousel in action.
 */

import React from 'react';
import { Box, Paper, Typography, Chip, Avatar } from '@mui/material';
import { Person as PersonIcon, Work as WorkIcon, Email as EmailIcon } from '@mui/icons-material';
import TouchCarousel from './TouchCarousel';

/**
 * Demo candidate data structure
 */
interface DemoCandidate {
  id: string;
  name: string;
  position: string;
  match: number;
  skills: string[];
  email: string;
  vacancy?: string;
}

/**
 * Demo candidates to display in the carousel
 */
const demoCandidates: DemoCandidate[] = [
  {
    id: '1',
    name: 'John Doe',
    position: 'Senior React Developer',
    match: 95,
    skills: ['React', 'TypeScript', 'Node.js', 'Material-UI'],
    email: 'john.doe@example.com',
    vacancy: 'Frontend Developer',
  },
  {
    id: '2',
    name: 'Jane Smith',
    position: 'Full Stack Engineer',
    match: 88,
    skills: ['React', 'Python', 'PostgreSQL', 'AWS'],
    email: 'jane.smith@example.com',
    vacancy: 'Full Stack Developer',
  },
  {
    id: '3',
    name: 'Bob Johnson',
    position: 'DevOps Engineer',
    match: 82,
    skills: ['Docker', 'Kubernetes', 'CI/CD', 'Terraform'],
    email: 'bob.johnson@example.com',
    vacancy: 'DevOps Specialist',
  },
  {
    id: '4',
    name: 'Alice Williams',
    position: 'UI/UX Designer',
    match: 91,
    skills: ['Figma', 'Adobe XD', 'Sketch', 'Prototyping'],
    email: 'alice.williams@example.com',
    vacancy: 'Product Designer',
  },
];

/**
 * Individual candidate card component
 */
const CandidateCard: React.FC<{ candidate: DemoCandidate }> = ({ candidate }) => (
  <Paper
    sx={{
      p: 3,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      mx: 1,
      bgcolor: 'background.paper',
      boxShadow: 3,
      borderRadius: 2,
    }}
  >
    {/* Avatar and Name */}
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Avatar
        sx={{
          bgcolor: 'primary.main',
          width: 56,
          height: 56,
          mr: 2,
        }}
      >
        <PersonIcon sx={{ fontSize: 32 }} />
      </Avatar>
      <Box>
        <Typography variant="h6" fontWeight={600}>
          {candidate.name}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {candidate.position}
        </Typography>
      </Box>
    </Box>

    {/* Match Percentage */}
    <Box sx={{ mb: 2 }}>
      <Chip
        label={`${candidate.match}% Match`}
        size="small"
        color={candidate.match >= 90 ? 'success' : candidate.match >= 80 ? 'warning' : 'default'}
        sx={{ mr: 1 }}
      />
    </Box>

    {/* Skills */}
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
        Skills:
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {candidate.skills.map((skill, index) => (
          <Chip
            key={index}
            label={skill}
            size="small"
            variant="outlined"
            sx={{ fontSize: '0.75rem' }}
          />
        ))}
      </Box>
    </Box>

    {/* Contact Info */}
    <Box sx={{ display: 'flex', alignItems: 'center', mt: 'auto', pt: 1 }}>
      <EmailIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
      <Typography variant="body2" color="text.secondary">
        {candidate.email}
      </Typography>
    </Box>

    {/* Vacancy */}
    {candidate.vacancy && (
      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
        <WorkIcon sx={{ fontSize: 16, mr: 1, color: 'text.secondary' }} />
        <Typography variant="body2" color="text.secondary">
          {candidate.vacancy}
        </Typography>
      </Box>
    )}
  </Paper>
);

/**
 * TouchCarousel Demo Component
 *
 * Demonstrates the TouchCarousel with candidate cards.
 * Swipe left/right on mobile to navigate through candidates.
 */
export const TouchCarouselDemo: React.FC = () => {
  return (
    <Box sx={{ width: '100%', maxWidth: 600, mx: 'auto', py: 4 }}>
      <Typography variant="h5" gutterBottom align="center">
        Touch Carousel Demo
      </Typography>
      <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
        Swipe left or right to navigate through candidate cards
      </Typography>

      {/* Basic TouchCarousel */}
      <TouchCarousel
        infinite={true}
        showDots={true}
        showArrows={true}
        enableSwipe={true}
        height={400}
        sx={{ mb: 4 }}
      >
        {demoCandidates.map((candidate) => (
          <CandidateCard key={candidate.id} candidate={candidate} />
        ))}
      </TouchCarousel>

      {/* Auto-play TouchCarousel */}
      <Typography variant="h6" gutterBottom align="center" sx={{ mt: 4 }}>
        Auto-Play Version (3 seconds)
      </Typography>
      <TouchCarousel
        infinite={true}
        autoPlay={true}
        autoPlayInterval={3000}
        showDots={true}
        showArrows={false}
        enableSwipe={true}
        height={400}
      >
        {demoCandidates.map((candidate) => (
          <CandidateCard key={candidate.id} candidate={candidate} />
        ))}
      </TouchCarousel>
    </Box>
  );
};

export default TouchCarouselDemo;
