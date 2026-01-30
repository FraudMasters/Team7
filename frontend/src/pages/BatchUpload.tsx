import React, { useState, useCallback } from 'react';
import {
  Typography,
  Box,
  Paper,
  Container,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Chip,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  FolderOpen as FolderIcon,
} from '@mui/icons-material';

const API_URL = (window as any).env?.REACT_APP_API_URL || 'http://localhost:8000';

interface FileItem {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface BatchJob {
  batch_id: string;
  status: string;
  total_files: number;
  processed_files: number;
  failed_files: number;
  progress_percentage: number;
  created_at?: string;
  completed_at?: string;
  error_message?: string;
}

/**
 * Batch Upload Page Component
 *
 * Page for uploading multiple resumes in batch.
 */
const BatchUploadPage: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [notificationEmail, setNotificationEmail] = useState('');
  const [analyzeResumes, setAnalyzeResumes] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [currentBatch, setCurrentBatch] = useState<BatchJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pollInterval, setPollInterval] = useState<number | null>(null);
  const [resultsDialog, setResultsDialog] = useState(false);
  const [batchResults, setBatchResults] = useState<any>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    const newFiles: FileItem[] = selectedFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setError(null);
    if (event.target) {
      event.target.value = '';
    }
  };

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files).filter(
      (file) => {
        const ext = file.name.split('.').pop()?.toLowerCase();
        return ext === 'pdf' || ext === 'docx';
      }
    );
    if (droppedFiles.length === 0) {
      setError('Only PDF and DOCX files are allowed');
      return;
    }
    const newFiles: FileItem[] = droppedFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setError(null);
  }, []);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const clearAllFiles = () => {
    setFiles([]);
    setError(null);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setCurrentBatch(null);

    // Mark all files as uploading
    setFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading' as const }))
    );

    try {
      const formData = new FormData();
      files.forEach((fileItem) => {
        formData.append('files', fileItem.file);
      });
      if (notificationEmail) {
        formData.append('notification_email', notificationEmail);
      }
      formData.append('analyze', analyzeResumes.toString());

      const response = await fetch(`${API_URL}/api/batch/upload`, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();

      // Mark all files as success
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'success' as const }))
      );

      setCurrentBatch(result);
      setSuccess(`Batch upload started with ${result.total_files} files`);

      // Start polling for status
      startPolling(result.batch_id);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'error' as const, error: errorMessage }))
      );
    } finally {
      setUploading(false);
    }
  };

  const startPolling = (batchId: string) => {
    const poll = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/batch/${batchId}`);
        if (response.ok) {
          const data: BatchJob = await response.json();
          setCurrentBatch(data);

          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(poll);
            setPollInterval(null);
            if (data.status === 'completed') {
              setSuccess('Batch processing completed!');
            } else {
              setError(data.error_message || 'Batch processing failed');
            }
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);

    setPollInterval(poll);
  };

  const fetchBatchResults = async () => {
    if (!currentBatch) return;

    try {
      const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/results`);
      if (response.ok) {
        const data = await response.json();
        setBatchResults(data);
        setResultsDialog(true);
      }
    } catch (err) {
      console.error('Failed to fetch results:', err);
    }
  };

  const resetBatch = () => {
    setFiles([]);
    setCurrentBatch(null);
    setSuccess(null);
    setError(null);
    setBatchResults(null);
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip size="small" label="Pending" color="default" />;
      case 'processing':
        return <Chip size="small" label="Processing" color="info" />;
      case 'completed':
        return <Chip size="small" label="Completed" color="success" />;
      case 'failed':
        return <Chip size="small" label="Failed" color="error" />;
      default:
        return <Chip size="small" label={status} />;
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Batch Resume Upload
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Upload multiple resumes at once for analysis. Supports PDF and DOCX formats (max 100 files).
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {!currentBatch ? (
          <Paper sx={{ p: 3 }}>
            {/* Drop Zone */}
            <Box
              sx={{
                border: '2px dashed',
                borderColor: 'divider',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                mb: 3,
                cursor: 'pointer',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                },
              }}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drag & Drop Resume Files
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to browse (PDF, DOCX)
              </Typography>
            </Box>

            {/* Options */}
            <Box sx={{ mb: 3, display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              <TextField
                label="Notification Email (optional)"
                type="email"
                value={notificationEmail}
                onChange={(e) => setNotificationEmail(e.target.value)}
                disabled={uploading}
                sx={{ minWidth: 250 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={analyzeResumes}
                    onChange={(e) => setAnalyzeResumes(e.target.checked)}
                    disabled={uploading}
                  />
                }
                label="Analyze resumes after upload"
              />
            </Box>

            {/* File List */}
            {files.length > 0 && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="subtitle1">
                    {files.length} file{files.length !== 1 ? 's' : ''} selected
                  </Typography>
                  <Button onClick={clearAllFiles} disabled={uploading} size="small">
                    Clear All
                  </Button>
                </Box>

                <TableContainer sx={{ mb: 3, maxHeight: 300 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Filename</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {files.map((fileItem) => (
                        <TableRow key={fileItem.id}>
                          <TableCell>{fileItem.file.name}</TableCell>
                          <TableCell>
                            {(fileItem.file.size / 1024).toFixed(1)} KB
                          </TableCell>
                          <TableCell>
                            {fileItem.status === 'success' && <CheckIcon color="success" fontSize="small" />}
                            {fileItem.status === 'error' && <ErrorIcon color="error" fontSize="small" />}
                            {fileItem.status === 'uploading' && <CircularProgress size={16} />}
                            {fileItem.status === 'pending' && <Chip size="small" label="Ready" />}
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              onClick={() => removeFile(fileItem.id)}
                              disabled={uploading}
                              size="small"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Button
                  variant="contained"
                  size="large"
                  onClick={handleUpload}
                  disabled={uploading || files.length === 0}
                  startIcon={uploading ? undefined : <UploadIcon />}
                  fullWidth
                >
                  {uploading ? 'Uploading...' : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
                </Button>
              </>
            )}
          </Paper>
        ) : (
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Batch Job: {currentBatch.batch_id.slice(0, 8)}...
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => fetchBatchResults()}
                  disabled={currentBatch.status !== 'completed'}
                >
                  View Results
                </Button>
                <Button onClick={resetBatch}>
                  New Batch
                </Button>
              </Box>
            </Box>

            {getStatusChip(currentBatch.status)}

            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Progress: {currentBatch.processed_files} / {currentBatch.total_files} files
              </Typography>
              <LinearProgress
                variant="determinate"
                value={currentBatch.progress_percentage}
                sx={{ height: 10, borderRadius: 5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {currentBatch.progress_percentage}% Complete
              </Typography>
            </Box>

            {currentBatch.error_message && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {currentBatch.error_message}
              </Alert>
            )}

            <Box sx={{ mt: 3, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {currentBatch.total_files}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Files
                </Typography>
              </Paper>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {currentBatch.processed_files}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Processed
                </Typography>
              </Paper>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {currentBatch.failed_files}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Failed
                </Typography>
              </Paper>
            </Box>
          </Paper>
        )}

        {/* Results Dialog */}
        <Dialog open={resultsDialog} onClose={() => setResultsDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Batch Results</DialogTitle>
          <DialogContent>
            {batchResults && (
              <>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2">
                    Status: {getStatusChip(batchResults.status)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {batchResults.successful} successful, {batchResults.failed} failed
                  </Typography>
                </Box>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Filename</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {batchResults.files?.map((file: any) => (
                        <TableRow key={file.resume_id}>
                          <TableCell>{file.filename}</TableCell>
                          <TableCell>{getStatusChip(file.status)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setResultsDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>

        {/* Recent Batches */}
        <Paper sx={{ p: 3, mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Recent Batches
            </Typography>
            <IconButton onClick={() => window.location.reload()}>
              <RefreshIcon />
            </IconButton>
          </Box>
          <BatchList />
        </Paper>
      </Box>
    </Container>
  );
};

const BatchList: React.FC = () => {
  const [batches, setBatches] = React.useState<BatchJob[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_URL}/api/batch/`)
      .then((res) => res.json())
      .then((data) => {
        setBatches(data.batches || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch batches:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (batches.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" align="center" sx={{ p: 3 }}>
        No batches yet. Upload some resumes to get started.
      </Typography>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Batch ID</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Created</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {batches.map((batch) => (
            <TableRow key={batch.batch_id}>
              <TableCell>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {batch.batch_id.slice(0, 8)}...
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  size="small"
                  label={batch.status}
                  color={
                    batch.status === 'completed'
                      ? 'success'
                      : batch.status === 'failed'
                      ? 'error'
                      : batch.status === 'processing'
                      ? 'info'
                      : 'default'
                  }
                />
              </TableCell>
              <TableCell>
                <LinearProgress
                  variant="determinate"
                  value={batch.progress_percentage}
                  sx={{ width: 80 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {batch.processed_files}/{batch.total_files}
                </Typography>
              </TableCell>
              <TableCell>
                {batch.created_at
                  ? new Date(batch.created_at).toLocaleString()
                  : '-'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default BatchUploadPage;
