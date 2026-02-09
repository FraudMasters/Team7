import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import { profilesClient } from '@/api/profiles';
import type {
  JobSeekerProfile,
  JobSeekerProfileUpdate,
  JobSeekerStatus,
  ApiError,
} from '@/types/api';

/**
 * ProfileEditor Component Props
 */
interface ProfileEditorProps {
  /** Callback when profile is updated */
  onProfileUpdate?: (profile: JobSeekerProfile) => void;
  /** Whether to show the header section */
  showHeader?: boolean;
  /** Maximum length for bio field */
  bioMaxLength?: number;
}

/**
 * ProfileEditor Component
 *
 * Edit basic job seeker profile information:
 * - Contact information (phone, location)
 * - Professional summary (bio, current title/company)
 * - Online presence (LinkedIn, portfolio URLs)
 * - Career details (years of experience, industry)
 * - Job preferences (status, preferred locations, job types, expected salary)
 * - Supports both creating new profiles and updating existing ones
 * - Handles loading and error states gracefully
 *
 * @example
 * ```tsx
 * <ProfileEditor
 *   onProfileUpdate={(profile) => console.log('Profile updated:', profile)}
 * />
 *
 * <ProfileEditor
 *   showHeader={false}
 *   bioMaxLength={500}
 * />
 * ```
 */
const ProfileEditor: React.FC<ProfileEditorProps> = ({
  onProfileUpdate,
  showHeader = true,
  bioMaxLength = 2000,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [profile, setProfile] = useState<JobSeekerProfile | null>(null);

  // Form state
  const [phone, setPhone] = useState('');
  const [location, setLocation] = useState('');
  const [bio, setBio] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [yearsOfExperience, setYearsOfExperience] = useState('');
  const [currentTitle, setCurrentTitle] = useState('');
  const [currentCompany, setCurrentCompany] = useState('');
  const [industry, setIndustry] = useState('');
  const [jobSeekerStatus, setJobSeekerStatus] = useState<JobSeekerStatus | ''>('');
  const [preferredLocations, setPreferredLocations] = useState('');
  const [preferredJobTypes, setPreferredJobTypes] = useState('');
  const [expectedSalary, setExpectedSalary] = useState('');

  /**
   * Fetch the current user's profile
   */
  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await profilesClient.getMyProfile();
      setProfile(data);

      // Populate form fields with existing data
      setPhone(data.phone || '');
      setLocation(data.location || '');
      setBio(data.bio || '');
      setLinkedinUrl(data.linkedin_url || '');
      setPortfolioUrl(data.portfolio_url || '');
      setYearsOfExperience(data.years_of_experience?.toString() || '');
      setCurrentTitle(data.current_title || '');
      setCurrentCompany(data.current_company || '');
      setIndustry(data.industry || '');
      setJobSeekerStatus(data.job_seeker_status || '');
      setPreferredLocations(data.preferred_locations || '');
      setPreferredJobTypes(data.preferred_job_types || '');
      setExpectedSalary(data.expected_salary || '');
    } catch (err) {
      const apiError = err as ApiError;
      // Profile might not exist yet - that's okay, user will create it
      if (apiError.status === 404) {
        setProfile(null);
        setLoading(false);
        return;
      }
      setError(apiError.detail || 'Failed to load profile. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  /**
   * Handle form submission - create or update profile
   */
  const handleSubmit = useCallback(async () => {
    // Basic validation
    if (!phone.trim() && !location.trim() && !bio.trim() && !currentTitle.trim()) {
      setError('Please fill in at least one field.');
      return;
    }

    // Validate LinkedIn URL format if provided
    if (linkedinUrl.trim() && !isValidUrl(linkedinUrl)) {
      setError('Please enter a valid LinkedIn URL.');
      return;
    }

    // Validate portfolio URL format if provided
    if (portfolioUrl.trim() && !isValidUrl(portfolioUrl)) {
      setError('Please enter a valid portfolio URL.');
      return;
    }

    // Validate years of experience if provided
    const yearsExp = yearsOfExperience.trim() ? parseFloat(yearsOfExperience) : undefined;
    if (yearsExp !== undefined && (isNaN(yearsExp) || yearsExp < 0 || yearsExp > 100)) {
      setError('Years of experience must be between 0 and 100.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const updateData: JobSeekerProfileUpdate = {
        phone: phone.trim() || undefined,
        location: location.trim() || undefined,
        bio: bio.trim() || undefined,
        linkedin_url: linkedinUrl.trim() || undefined,
        portfolio_url: portfolioUrl.trim() || undefined,
        years_of_experience: yearsExp,
        current_title: currentTitle.trim() || undefined,
        current_company: currentCompany.trim() || undefined,
        industry: industry.trim() || undefined,
        job_seeker_status: jobSeekerStatus || undefined,
        preferred_locations: preferredLocations.trim() || undefined,
        preferred_job_types: preferredJobTypes.trim() || undefined,
        expected_salary: expectedSalary.trim() || undefined,
      };

      let updatedProfile: JobSeekerProfile;

      if (!profile) {
        // Create new profile
        updatedProfile = await profilesClient.createMyProfile(updateData);
        setProfile(updatedProfile);
      } else {
        // Update existing profile
        updatedProfile = await profilesClient.updateMyProfile(updateData);
        setProfile(updatedProfile);
      }

      setSuccessMessage(profile ? 'Profile updated successfully.' : 'Profile created successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      onProfileUpdate?.(updatedProfile);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to save profile. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [
    phone,
    location,
    bio,
    linkedinUrl,
    portfolioUrl,
    yearsOfExperience,
    currentTitle,
    currentCompany,
    industry,
    jobSeekerStatus,
    preferredLocations,
    preferredJobTypes,
    expectedSalary,
    profile,
    onProfileUpdate,
  ]);

  /**
   * Validate URL format
   */
  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url.startsWith('http') ? url : `https://${url}`);
      return true;
    } catch {
      return false;
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <CircularProgress size={40} sx={{ mb: 2 }} />
        <Typography variant="body2" color="secondary">
          Loading profile...
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={2}>
      {/* Header */}
      {showHeader && (
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={600}>
            Profile Information
          </Typography>
          {!profile && (
            <Typography variant="caption" color="secondary">
              Create your profile to get started
            </Typography>
          )}
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Profile Form */}
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={3}>
          {/* Contact Information */}
          <Box>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Contact Information
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Phone Number"
                  placeholder="+1 (555) 123-4567"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Location"
                  placeholder="San Francisco, CA"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Professional Summary */}
          <Box>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Professional Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Current Title"
                  placeholder="Senior Software Engineer"
                  value={currentTitle}
                  onChange={(e) => setCurrentTitle(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Current Company"
                  placeholder="Tech Corp"
                  value={currentCompany}
                  onChange={(e) => setCurrentCompany(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Industry"
                  placeholder="Technology / Software"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Years of Experience"
                  type="number"
                  placeholder="5"
                  value={yearsOfExperience}
                  onChange={(e) => setYearsOfExperience(e.target.value)}
                  disabled={submitting}
                  size="small"
                  inputProps={{ min: 0, max: 100, step: 0.5 }}
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Bio"
                  placeholder="Tell us about yourself, your background, and your career goals..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  disabled={submitting}
                  inputProps={{ maxLength: bioMaxLength }}
                  helperText={`${bio.length}/${bioMaxLength} characters`}
                />
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Online Presence */}
          <Box>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Online Presence
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="LinkedIn URL"
                  placeholder="https://linkedin.com/in/yourprofile"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Portfolio URL"
                  placeholder="https://yourportfolio.com"
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Job Preferences */}
          <Box>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Job Preferences
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Job Seeker Status</InputLabel>
                  <Select
                    value={jobSeekerStatus}
                    onChange={(e) => setJobSeekerStatus(e.target.value as JobSeekerStatus | '')}
                    label="Job Seeker Status"
                    disabled={submitting}
                  >
                    <MenuItem value="">Not specified</MenuItem>
                    <MenuItem value="actively_looking">Actively Looking</MenuItem>
                    <MenuItem value="open">Open to Opportunities</MenuItem>
                    <MenuItem value="not_looking">Not Looking</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Preferred Locations"
                  placeholder="San Francisco, Remote, New York"
                  value={preferredLocations}
                  onChange={(e) => setPreferredLocations(e.target.value)}
                  disabled={submitting}
                  size="small"
                  helperText="Separate multiple locations with commas"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Preferred Job Types"
                  placeholder="Full-time, Contract, Remote"
                  value={preferredJobTypes}
                  onChange={(e) => setPreferredJobTypes(e.target.value)}
                  disabled={submitting}
                  size="small"
                  helperText="Separate multiple types with commas"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Expected Salary"
                  placeholder="$120,000 - $150,000"
                  value={expectedSalary}
                  onChange={(e) => setExpectedSalary(e.target.value)}
                  disabled={submitting}
                  size="small"
                />
              </Grid>
            </Grid>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, pt: 1 }}>
            <Button
              variant="outlined"
              onClick={fetchProfile}
              disabled={submitting}
            >
              Reset
            </Button>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={16} /> : null}
            >
              {profile ? 'Update Profile' : 'Create Profile'}
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Stack>
  );
};

export default ProfileEditor;
