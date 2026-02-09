import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  CircularProgress,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Person as PersonIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { getUserProfile, updateUserProfile } from '@/api/preferences';
import type { UserProfileResponse, UserProfileUpdate } from '@/types/api';

/**
 * Form data for editing user profile
 */
interface ProfileFormData {
  name: string;
  email: string;
  role: string;
  avatar_url: string;
}

/**
 * Profile editor component props
 */
interface ProfileEditorProps {
  /** Optional callback when profile is updated */
  onProfileUpdate?: (profile: UserProfileResponse) => void;
}

/**
 * ProfileEditor Component
 *
 * Provides a comprehensive interface for editing user profile information. Features include:
 * - Edit name, email, role, and avatar URL
 * - Real-time validation
 * - Loading and error states
 * - Optimistic UI updates
 * - Avatar preview
 *
 * @example
 * ```tsx
 * <ProfileEditor
 *   onProfileUpdate={(profile) => console.log('Profile updated:', profile)}
 * />
 * ```
 */
const ProfileEditor: React.FC<ProfileEditorProps> = ({
  onProfileUpdate,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  // Profile state
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);

  // Form state
  const [formData, setFormData] = useState<ProfileFormData>({
    name: '',
    email: '',
    role: '',
    avatar_url: '',
  });

  /**
   * Fetch user profile from backend
   */
  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const result = await getUserProfile();
      setProfile(result);
      setFormData({
        name: result.name || '',
        email: result.email || '',
        role: result.role || '',
        avatar_url: result.avatar_url || '',
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load user profile';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  /**
   * Handle form input change
   */
  const handleInputChange = (field: keyof ProfileFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
    setSuccess(false);
  };

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    if (!formData.name.trim()) {
      setError('Name is required');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.role.trim()) {
      setError('Role is required');
      return false;
    }
    return true;
  };

  /**
   * Submit profile update
   */
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const updateData: UserProfileUpdate = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        role: formData.role.trim(),
        avatar_url: formData.avatar_url.trim() || undefined,
      };

      const updated = await updateUserProfile(updateData);

      // Optimistic update
      setProfile(updated);
      setSuccess(true);

      if (onProfileUpdate) {
        onProfileUpdate(updated);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update profile';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading profile...
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Profile Settings
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchProfile}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          Manage your personal information, including your name, email, role, and avatar. These details help personalize your experience.
        </Typography>

        {/* Success Message */}
        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            <AlertTitle>Success</AlertTitle>
            Profile updated successfully
          </Alert>
        )}

        {/* Error Message */}
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3 }}
            onClose={() => setError(null)}
          >
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Profile Form */}
      <Grid container spacing={3}>
        {/* Avatar Section */}
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Avatar
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 2,
                }}
              >
                <Avatar
                  src={formData.avatar_url || undefined}
                  sx={{
                    width: 120,
                    height: 120,
                    bgcolor: 'primary.main',
                    fontSize: '3rem',
                  }}
                >
                  {!formData.avatar_url && <PersonIcon />}
                </Avatar>
                <Typography variant="caption" color="text.secondary">
                  {formData.avatar_url
                    ? 'Custom avatar'
                    : 'Default avatar'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Form Fields */}
        <Grid item xs={12} md={8}>
          <Paper elevation={1} sx={{ p: 3 }}>
            <Stack spacing={3}>
              {/* Name Field */}
              <TextField
                label="Full Name"
                fullWidth
                required
                value={formData.name}
                onChange={handleInputChange('name')}
                placeholder="e.g., John Doe"
                disabled={submitting}
                helperText="Your full name as it appears in the system"
                InputProps={{
                  startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />

              {/* Email Field */}
              <TextField
                label="Email Address"
                fullWidth
                required
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                placeholder="e.g., john.doe@company.com"
                disabled={submitting}
                helperText="Your work email address for notifications"
              />

              {/* Role Field */}
              <TextField
                label="Role"
                fullWidth
                required
                value={formData.role}
                onChange={handleInputChange('role')}
                placeholder="e.g., Recruiter, Hiring Manager"
                disabled={submitting}
                helperText="Your role in the organization"
                select
                SelectProps={{
                  native: true,
                }}
              >
                <option value="">Select a role</option>
                <option value="recruiter">Recruiter</option>
                <option value="hiring_manager">Hiring Manager</option>
                <option value="hr_manager">HR Manager</option>
                <option value="admin">Administrator</option>
                <option value="other">Other</option>
              </TextField>

              {/* Avatar URL Field */}
              <TextField
                label="Avatar URL"
                fullWidth
                value={formData.avatar_url}
                onChange={handleInputChange('avatar_url')}
                placeholder="https://example.com/avatar.jpg"
                disabled={submitting}
                helperText="Optional: URL to your profile picture"
              />

              {/* Submit Button */}
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={submitting}
                  startIcon={submitting ? <CircularProgress size={16} /> : <SaveIcon />}
                  size="large"
                >
                  {submitting ? 'Saving...' : 'Save Changes'}
                </Button>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Current Profile Info */}
      {profile && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Current Profile Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Name
              </Typography>
              <Typography variant="body1">
                {profile.name || 'Not set'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Email
              </Typography>
              <Typography variant="body1">
                {profile.email || 'Not set'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Role
              </Typography>
              <Typography variant="body1">
                {profile.role || 'Not set'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Avatar URL
              </Typography>
              <Typography variant="body1" sx={{ wordBreak: 'break-all' }}>
                {profile.avatar_url || 'Not set'}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Stack>
  );
};

export default ProfileEditor;
