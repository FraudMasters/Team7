import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { apiClient } from '../../api/client';

const MotionPaper = motion(Paper);

interface ResumeUploadProps {
  onUploadComplete: (resumeId: string) => void;
}

export function ResumeUpload({ onUploadComplete }: ResumeUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadedFile(file);
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onUploadComplete(response.data.id);
      setUploadedFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
      setUploadedFile(null);
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: uploading,
  });

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <MotionPaper
        {...getRootProps()}
        component="div"
        whileHover={{ scale: uploading ? 1 : 1.01 }}
        whileTap={{ scale: uploading ? 1 : 0.99 }}
        sx={{
          p: 6,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: uploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
        }}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <Stack spacing={2} alignItems="center">
            <CircularProgress size={48} />
            <Typography>Uploading and analyzing...</Typography>
          </Stack>
        ) : uploadedFile ? (
          <Stack spacing={2} alignItems="center">
            <DescriptionIcon sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h6">{uploadedFile.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              Ready to analyze
            </Typography>
          </Stack>
        ) : (
          <Stack spacing={3} alignItems="center">
            <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6" gutterBottom>
                Upload Your Resume
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Drag and drop or click to browse
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              PDF, DOCX • Max 10MB
            </Typography>
          </Stack>
        )}
      </MotionPaper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
