import React, { useState, useCallback, useRef, useEffect } from 'react';
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
  AlertTitle,
  Chip,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material';
import { config } from '@/config';
import {
  Upload as UploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  FolderOpen as FolderIcon,
  Close as CloseIcon,
  Pause as PauseIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Warning as WarningIcon,
  ContentCopy as DuplicateIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import ErrorBoundary from '@components/ErrorBoundary';

const API_URL = (window as any).env?.REACT_APP_API_URL || config.api.url;

// LocalStorage key for draft auto-save
const DRAFT_STORAGE_KEY = 'batch_upload_draft';

interface FileItem {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'cancelled' | 'duplicate';
  error?: string;
  progress?: number;
  abortController?: AbortController;
  // Duplicate info
  isDuplicate?: boolean;
  duplicateOf?: string;
  duplicateMatchType?: 'exact' | 'near';
  duplicateSimilarity?: number;
  resumeId?: string;
}

// Duplicate info from API response
interface DuplicateInfo {
  resume_id: string;
  filename: string;
  original_resume_id: string;
  match_type: 'exact' | 'near' | string;
  similarity_score: number;
  detection_timestamp?: string;
}

// Draft data structure (serializable for localStorage)
interface DraftData {
  notificationEmail: string;
  analyzeResumes: boolean;
  files: Array<{
    name: string;
    size: number;
    lastModified: number;
  }>;
  timestamp: number;
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
  // Duplicate info
  duplicates_detected?: number;
  duplicates?: DuplicateInfo[];
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
  const [hasDraft, setHasDraft] = useState(false);
  const [isPausing, setIsPausing] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [duplicates, setDuplicates] = useState<DuplicateInfo[]>([]);
  const [duplicatesDialog, setDuplicatesDialog] = useState(false);
  const [acceptingDuplicate, setAcceptingDuplicate] = useState<string | null>(null);
  const [rejectingDuplicate, setRejectingDuplicate] = useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Save draft to localStorage
  const saveDraft = useCallback(() => {
    try {
      const draftData: DraftData = {
        notificationEmail,
        analyzeResumes,
        files: files.map(f => ({
          name: f.file.name,
          size: f.file.size,
          lastModified: f.file.lastModified,
        })),
        timestamp: Date.now(),
      };
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draftData));
      setHasDraft(true);
    } catch (err) {
      // Silently fail if localStorage is full or unavailable
      console.warn('Failed to save draft:', err);
    }
  }, [notificationEmail, analyzeResumes, files]);

  // Load draft from localStorage
  const loadDraft = useCallback((): DraftData | null => {
    try {
      const stored = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (!stored) return null;
      const draft = JSON.parse(stored) as DraftData;
      // Check if draft is older than 24 hours
      const dayInMs = 24 * 60 * 60 * 1000;
      if (Date.now() - draft.timestamp > dayInMs) {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
        return null;
      }
      return draft;
    } catch (err) {
      console.warn('Failed to load draft:', err);
      return null;
    }
  }, []);

  // Clear draft from localStorage
  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      setHasDraft(false);
      setNotificationEmail('');
      setAnalyzeResumes(true);
      setFiles([]);
      setError(null);
      setSuccess('Draft cleared');
    } catch (err) {
      console.warn('Failed to clear draft:', err);
    }
  }, []);

  // Restore draft on mount
  React.useEffect(() => {
    const draft = loadDraft();
    if (draft && draft.files.length > 0) {
      // Note: We can't restore actual File objects, but we can restore form settings
      // and show a message that files need to be re-selected
      setNotificationEmail(draft.notificationEmail);
      setAnalyzeResumes(draft.analyzeResumes);
      setHasDraft(true);
      setSuccess(
        `Draft restored from ${new Date(draft.timestamp).toLocaleString()}. ` +
        `Please re-select your ${draft.files.length} file(s).`
      );
    }
  }, [loadDraft]);

  // Auto-save draft whenever form data changes
  React.useEffect(() => {
    if (!uploading && files.length > 0) {
      saveDraft();
    }
  }, [notificationEmail, analyzeResumes, files, uploading, saveDraft]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    const newFiles: FileItem[] = selectedFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending',
      progress: 0,
      abortController: new AbortController(),
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
      progress: 0,
      abortController: new AbortController(),
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setError(null);
  }, []);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const removeFile = (id: string) => {
    setFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.abortController) {
        file.abortController.abort();
      }
      return prev.filter((f) => f.id !== id);
    });
  };

  const cancelFileUpload = (id: string) => {
    setFiles((prev) =>
      prev.map((f) => {
        if (f.id === id && f.status === 'uploading') {
          if (f.abortController) {
            f.abortController.abort();
          }
          return { ...f, status: 'cancelled' as const, progress: 0 };
        }
        return f;
      })
    );
  };

  const clearAllFiles = () => {
    setFiles((prev) => {
      prev.forEach((f) => {
        if (f.abortController) {
          f.abortController.abort();
        }
      });
      return [];
    });
    setError(null);
  };

  const retryFailedUploads = async () => {
    const failedFiles = files.filter((f) => f.status === 'error' || f.status === 'cancelled');
    if (failedFiles.length === 0) {
      setError('No failed files to retry');
      return;
    }

    setUploading(true);
    setError(null);

    // Mark failed files as uploading and create new abort controllers
    setFiles((prev) =>
      prev.map((f) =>
        (f.status === 'error' || f.status === 'cancelled')
          ? { ...f, status: 'uploading' as const, error: undefined, progress: 0, abortController: new AbortController() }
          : f
      )
    );

    try {
      // Upload failed files in parallel with progress tracking
      const uploadPromises = failedFiles.map((fileItem) => uploadSingleFile(fileItem));
      const results = await Promise.all(uploadPromises);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failureCount = results.filter((r) => !r.success).length;

      // Update file statuses
      setFiles((prev) =>
        prev.map((f) => {
          const result = results.find((r) => r.id === f.id);
          if (!result) return f;
          if (result.success) {
            return { ...f, status: 'success' as const, progress: 100 };
          } else if (result.error === 'Cancelled') {
            return { ...f, status: 'cancelled' as const, progress: 0 };
          } else {
            return { ...f, status: 'error' as const, error: result.error || 'Upload failed', progress: 0 };
          }
        })
      );

      if (successCount > 0) {
        setSuccess(`Successfully retried ${successCount} file${successCount !== 1 ? 's' : ''}`);
      }

      if (failureCount > 0) {
        setError(`${failureCount} file(s) failed to retry`);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Retry failed';
      setError(errorMessage);
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'uploading' ? { ...f, status: 'error' as const, error: errorMessage, progress: 0 } : f
        )
      );
    } finally {
      setUploading(false);
    }
  };

  const uploadSingleFile = (fileItem: FileItem): Promise<{ id: string; success: boolean; error?: string }> => {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileItem.id ? { ...f, progress } : f
            )
          );
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          resolve({ id: fileItem.id, success: true });
        } else {
          resolve({ id: fileItem.id, success: false, error: `HTTP ${xhr.status}` });
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        resolve({ id: fileItem.id, success: false, error: 'Network error' });
      });

      // Handle abort
      xhr.addEventListener('abort', () => {
        resolve({ id: fileItem.id, success: false, error: 'Cancelled' });
      });

      // Prepare form data for this file
      const formData = new FormData();
      formData.append('files', fileItem.file);
      if (notificationEmail) {
        formData.append('notification_email', notificationEmail);
      }
      formData.append('analyze', analyzeResumes.toString());

      // Send request
      xhr.open('POST', `${API_URL}/api/batch/upload`);
      xhr.send(formData);
    });
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

    // Mark all files as uploading and reset progress
    setFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading' as const, progress: 0, error: undefined }))
    );

    try {
      // Upload files in parallel with individual progress tracking
      const uploadPromises = files
        .filter((f) => f.status !== 'cancelled')
        .map((fileItem) => uploadSingleFile(fileItem));

      const results = await Promise.all(uploadPromises);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failureCount = results.filter((r) => !r.success).length;

      // Update file statuses based on results
      setFiles((prev) =>
        prev.map((f) => {
          const result = results.find((r) => r.id === f.id);
          if (!result) return f;
          if (result.success) {
            return { ...f, status: 'success' as const, progress: 100 };
          } else if (result.error === 'Cancelled') {
            return { ...f, status: 'cancelled' as const, progress: 0 };
          } else {
            return { ...f, status: 'error' as const, error: result.error || 'Upload failed', progress: 0 };
          }
        })
      );

      if (successCount > 0) {
        // Create batch job for successful uploads
        const formData = new FormData();
        files
          .filter((f) => f.status !== 'cancelled' && f.status !== 'error')
          .forEach((fileItem) => {
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

        if (response.ok) {
          const result = await response.json();
          setCurrentBatch(result);

          // Handle duplicates from upload response
          if (result.duplicates_detected > 0 && result.duplicates) {
            setDuplicates(result.duplicates);
            setSuccess(
              `Batch upload started with ${result.total_files} files. ` +
              `${result.duplicates_detected} duplicate(s) detected.`
            );
          } else {
            setSuccess(`Batch upload started with ${result.total_files} files`);
          }

          startPolling(result.batch_id);
          // Clear draft after successful upload
          try {
            localStorage.removeItem(DRAFT_STORAGE_KEY);
            setHasDraft(false);
          } catch (err) {
            console.warn('Failed to clear draft after upload:', err);
          }
        } else {
          throw new Error(`Failed to create batch job: ${response.statusText}`);
        }
      }

      if (failureCount > 0) {
        setError(`${failureCount} file(s) failed to upload`);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'uploading' ? { ...f, status: 'error' as const, error: errorMessage, progress: 0 } : f
        )
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
              // Fetch duplicates if any were detected
              if (data.duplicates_detected && data.duplicates_detected > 0) {
                fetchDuplicates();
              }
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

  const exportBatchResults = async () => {
    if (!currentBatch) return;

    try {
      // Fetch results if not already loaded
      let resultsData = batchResults;
      if (!resultsData) {
        const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/results`);
        if (!response.ok) {
          throw new Error('Failed to fetch batch results');
        }
        resultsData = await response.json();
      }

      if (!resultsData) return;

      // Create CSV headers
      const headers = ['Filename', 'Status', 'Resume ID', 'Error'];

      // Create CSV rows
      const rows = resultsData.files?.map((file: any) => [
        file.filename || '',
        file.status || '',
        file.resume_id || '',
        file.error || '',
      ]) || [];

      // Combine headers and rows
      const csvContent = [
        headers.join(','),
        ...rows.map((row: string[]) =>
          row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
        ),
      ].join('\n');

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute('download', `batch-results-${currentBatch.batch_id}.csv`);
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);

      setSuccess('Batch results exported successfully');
    } catch (err) {
      console.error('Failed to export results:', err);
      setError('Failed to export batch results');
    }
  };

  const resetBatch = () => {
    setFiles([]);
    setCurrentBatch(null);
    setSuccess(null);
    setError(null);
    setBatchResults(null);
    setDuplicates([]);
    setDuplicatesDialog(false);
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
    // Clear draft when starting new batch
    try {
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      setHasDraft(false);
    } catch (err) {
      console.warn('Failed to clear draft:', err);
    }
  };

  // Pause batch processing
  const handlePauseBatch = async () => {
    if (!currentBatch) return;

    setIsPausing(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/pause`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentBatch((prev) => prev ? { ...prev, status: 'paused' } : null);
        setSuccess('Batch processing paused');
        // Stop polling while paused
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to pause batch');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to pause batch';
      setError(errorMessage);
    } finally {
      setIsPausing(false);
    }
  };

  // Resume batch processing
  const handleResumeBatch = async () => {
    if (!currentBatch) return;

    setIsResuming(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentBatch((prev) => prev ? { ...prev, status: 'processing' } : null);
        setSuccess('Batch processing resumed');
        // Restart polling
        startPolling(currentBatch.batch_id);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to resume batch');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resume batch';
      setError(errorMessage);
    } finally {
      setIsResuming(false);
    }
  };

  // Cancel batch processing
  const handleCancelBatch = async () => {
    if (!currentBatch) return;

    setIsCancelling(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentBatch((prev) => prev ? { ...prev, status: 'cancelled' } : null);
        setSuccess('Batch processing cancelled');
        // Stop polling
        if (pollInterval) {
          clearInterval(pollInterval);
          setPollInterval(null);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel batch');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel batch';
      setError(errorMessage);
    } finally {
      setIsCancelling(false);
    }
  };

  // Fetch duplicates for current batch
  const fetchDuplicates = async () => {
    if (!currentBatch) return;

    try {
      const response = await fetch(`${API_URL}/api/batch/${currentBatch.batch_id}/duplicates`);
      if (response.ok) {
        const data = await response.json();
        setDuplicates(data.duplicates || []);
        if (data.duplicates && data.duplicates.length > 0) {
          setDuplicatesDialog(true);
        }
      }
    } catch (err) {
      console.error('Failed to fetch duplicates:', err);
    }
  };

  // Accept duplicate (keep the duplicate resume)
  const handleAcceptDuplicate = async (duplicate: DuplicateInfo) => {
    setAcceptingDuplicate(duplicate.resume_id);
    setError(null);

    try {
      // Accept by keeping the resume - we could add an API endpoint for this
      // For now, we just remove it from the duplicates list to indicate it's been reviewed
      setDuplicates((prev) => prev.filter((d) => d.resume_id !== duplicate.resume_id));
      setSuccess(`Accepted duplicate: ${duplicate.filename}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to accept duplicate';
      setError(errorMessage);
    } finally {
      setAcceptingDuplicate(null);
    }
  };

  // Reject duplicate (delete the duplicate resume)
  const handleRejectDuplicate = async (duplicate: DuplicateInfo) => {
    setRejectingDuplicate(duplicate.resume_id);
    setError(null);

    try {
      // Delete the duplicate resume
      const response = await fetch(`${API_URL}/api/resumes/${duplicate.resume_id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setDuplicates((prev) => prev.filter((d) => d.resume_id !== duplicate.resume_id));
        setSuccess(`Rejected duplicate: ${duplicate.filename}`);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reject duplicate');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reject duplicate';
      setError(errorMessage);
    } finally {
      setRejectingDuplicate(null);
    }
  };

  // Accept all remaining duplicates
  const handleAcceptAllDuplicates = () => {
    setDuplicates([]);
    setSuccess('All duplicates accepted');
    setDuplicatesDialog(false);
  };

  // Reject all remaining duplicates
  const handleRejectAllDuplicates = async () => {
    setError(null);

    try {
      // Delete all duplicate resumes
      const deletePromises = duplicates.map((dup) =>
        fetch(`${API_URL}/api/resumes/${dup.resume_id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );

      await Promise.all(deletePromises);
      setDuplicates([]);
      setSuccess('All duplicates rejected');
      setDuplicatesDialog(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reject all duplicates';
      setError(errorMessage);
    }
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      // Abort any ongoing uploads
      files.forEach((f) => {
        if (f.abortController && f.status === 'uploading') {
          f.abortController.abort();
        }
      });
    };
  }, [pollInterval, files]);

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip size="small" label="Pending" color="default" />;
      case 'processing':
        return <Chip size="small" label="Processing" color="info" />;
      case 'paused':
        return <Chip size="small" label="Paused" color="warning" />;
      case 'cancelled':
        return <Chip size="small" label="Cancelled" color="default" />;
      case 'completed':
        return <Chip size="small" label="Completed" color="success" />;
      case 'failed':
        return <Chip size="small" label="Failed" color="error" />;
      case 'duplicate':
        return <Chip size="small" label="Duplicate" color="warning" />;
      default:
        return <Chip size="small" label={status} />;
    }
  };

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Batch upload page error:', error, errorInfo);
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', sm: 'center' },
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 2,
            mb: 1,
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom={false}>
            Batch Resume Upload
          </Typography>
          {hasDraft && (
            <Button
              variant="outlined"
              size="small"
              onClick={clearDraft}
              color="secondary"
              startIcon={<DeleteIcon />}
            >
              Clear Draft
            </Button>
          )}
        </Box>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Upload multiple resumes at once for analysis. Supports PDF and DOCX formats (max 100 files).
        </Typography>

        {error && (
          <Alert
            severity="error"
            sx={{ mb: 2 }}
            action={
              <Box
                sx={{
                  display: 'flex',
                  gap: 1,
                  alignItems: 'center',
                  flexWrap: { xs: 'wrap', sm: 'nowrap' },
                }}
              >
                <Button
                  size="small"
                  variant="contained"
                  color="primary"
                  onClick={retryFailedUploads}
                  disabled={uploading || files.filter((f) => f.status === 'error' || f.status === 'cancelled').length === 0}
                  sx={{ minHeight: 44 }}
                >
                  Retry Failed
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  color="secondary"
                  onClick={() => {
                    setFiles((prev) => prev.filter((f) => f.status !== 'error' && f.status !== 'cancelled'));
                    setError(null);
                  }}
                  disabled={uploading}
                  sx={{ minHeight: 44 }}
                >
                  Remove Failed
                </Button>
                <IconButton
                  size="small"
                  onClick={() => setError(null)}
                  disabled={uploading}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            }
          >
            <AlertTitle>Upload Error</AlertTitle>
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
            {/* Responsive Layout: Side-by-side on desktop, stacked on mobile */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  md: '1fr 1fr',
                },
                gap: 3,
              }}
            >
              {/* Left Column: Upload Zone and Options */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3,
                }}
              >
                {/* Drop Zone */}
                <Box
                  sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    borderRadius: 2,
                    p: { xs: 3, md: 4 },
                    textAlign: 'center',
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
                  <UploadIcon
                    sx={{
                      fontSize: { xs: 36, md: 48 },
                      color: 'primary.main',
                      mb: 2
                    }}
                  />
                  <Typography variant="h6" gutterBottom>
                    Drag & Drop Resume Files
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or click to browse (PDF, DOCX)
                  </Typography>
                </Box>

                {/* Options */}
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', md: 'row' },
                    gap: 2,
                    alignItems: { xs: 'stretch', md: 'center' },
                  }}
                >
                  <TextField
                    label="Notification Email (optional)"
                    type="email"
                    value={notificationEmail}
                    onChange={(e) => setNotificationEmail(e.target.value)}
                    disabled={uploading}
                    fullWidth
                    sx={{ minWidth: { xs: 'auto', md: 250 } }}
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
                    sx={{ minWidth: { xs: 'auto', md: 200 } }}
                  />
                </Box>
              </Box>

              {/* Right Column: File List */}
              {files.length > 0 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1">
                      {files.length} file{files.length !== 1 ? 's' : ''} selected
                    </Typography>
                    <Button onClick={clearAllFiles} disabled={uploading} size="small">
                      Clear All
                    </Button>
                  </Box>

                  {/* Overall Progress Indicator */}
                  {uploading && (
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Overall Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {files.filter((f) => f.status === 'success').length} / {files.length}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={
                          files.length > 0
                            ? files.reduce((sum, f) => sum + (f.progress || 0), 0) / files.length
                            : 0
                        }
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {Math.round(
                          files.length > 0
                            ? files.reduce((sum, f) => sum + (f.progress || 0), 0) / files.length
                            : 0
                        )}% Complete
                      </Typography>
                    </Box>
                  )}

                  <TableContainer
                    sx={{
                      flexGrow: 1,
                      maxHeight: { xs: 300, md: '100%' },
                      mb: 3,
                    }}
                  >
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Filename</TableCell>
                          <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Size</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {files.map((fileItem) => (
                          <React.Fragment key={fileItem.id}>
                            <TableRow
                              sx={{
                                bgcolor: fileItem.isDuplicate || fileItem.status === 'duplicate'
                                  ? 'warning.lighter'
                                  : 'inherit',
                              }}
                            >
                              <TableCell
                                sx={{
                                  maxWidth: { xs: 120, md: 200 },
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {fileItem.file.name}
                              </TableCell>
                              <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                                {(fileItem.file.size / 1024).toFixed(1)} KB
                              </TableCell>
                              <TableCell>
                                {fileItem.status === 'success' && !fileItem.isDuplicate && <CheckIcon color="success" fontSize="small" />}
                                {fileItem.status === 'success' && fileItem.isDuplicate && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <DuplicateIcon color="warning" fontSize="small" />
                                    <Typography variant="caption" color="warning.main">
                                      Duplicate
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'duplicate' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <DuplicateIcon color="warning" fontSize="small" />
                                    <Chip
                                      size="small"
                                      label={fileItem.duplicateMatchType === 'exact' ? 'Exact' : 'Similar'}
                                      color="warning"
                                      variant="outlined"
                                      sx={{ height: 20 }}
                                    />
                                  </Box>
                                )}
                                {fileItem.status === 'error' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <ErrorIcon color="error" fontSize="small" />
                                    <Typography
                                      variant="caption"
                                      color="error"
                                      sx={{
                                        maxWidth: { xs: 100, md: 200 },
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap',
                                      }}
                                    >
                                      {fileItem.error || 'Upload failed'}
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'cancelled' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <CloseIcon color="disabled" fontSize="small" />
                                    <Typography variant="caption" color="text.secondary">
                                      Cancelled
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'uploading' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
                                    <CircularProgress size={16} />
                                    <Typography variant="caption" color="text.secondary">
                                      {fileItem.progress || 0}%
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'pending' && <Chip size="small" label="Ready" />}
                              </TableCell>
                              <TableCell align="right">
                                {fileItem.status === 'uploading' && (
                                  <Tooltip title="Cancel upload">
                                    <IconButton
                                      onClick={() => cancelFileUpload(fileItem.id)}
                                      size="small"
                                      color="error"
                                      sx={{ minWidth: 44, minHeight: 44 }}
                                    >
                                      <CloseIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                )}
                                {fileItem.status === 'error' && (
                                  <IconButton
                                    onClick={() => {
                                      setFiles((prev) =>
                                        prev.map((f) =>
                                          f.id === fileItem.id
                                            ? { ...f, status: 'pending' as const, error: undefined }
                                            : f
                                        )
                                      );
                                      setError(null);
                                    }}
                                    disabled={uploading}
                                    size="small"
                                    color="primary"
                                    title="Retry this file"
                                    sx={{ minWidth: 44, minHeight: 44 }}
                                  >
                                    <RefreshIcon fontSize="small" />
                                  </IconButton>
                                )}
                                {fileItem.status === 'cancelled' && (
                                  <IconButton
                                    onClick={() => {
                                      setFiles((prev) =>
                                        prev.map((f) =>
                                          f.id === fileItem.id
                                            ? { ...f, status: 'pending' as const, error: undefined }
                                            : f
                                        )
                                      );
                                    }}
                                    disabled={uploading}
                                    size="small"
                                    color="primary"
                                    title="Retry this file"
                                    sx={{ minWidth: 44, minHeight: 44 }}
                                  >
                                    <RefreshIcon fontSize="small" />
                                  </IconButton>
                                )}
                                <IconButton
                                  onClick={() => removeFile(fileItem.id)}
                                  disabled={uploading && fileItem.status === 'uploading'}
                                  size="small"
                                  title="Remove file"
                                  sx={{ minWidth: 44, minHeight: 44 }}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                            {fileItem.status === 'uploading' && (
                              <TableRow>
                                <TableCell colSpan={4} sx={{ py: 0, px: 2 }}>
                                  <LinearProgress
                                    variant="determinate"
                                    value={fileItem.progress || 0}
                                    sx={{ height: 4, borderRadius: 2 }}
                                  />
                                </TableCell>
                              </TableRow>
                            )}
                          </React.Fragment>
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
                    sx={{ minHeight: 48 }}
                  >
                    {uploading ? 'Uploading...' : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
                  </Button>
                </Box>
              )}
            </Box>
          </Paper>
        ) : (
          <Paper sx={{ p: 3 }}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: { xs: 'flex-start', sm: 'center' },
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 2,
                mb: 3,
              }}
            >
              <Typography variant="h6">
                Batch Job: {currentBatch.batch_id.slice(0, 8)}...
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  gap: 1,
                  flexDirection: { xs: 'column', sm: 'row' },
                  width: { xs: '100%', sm: 'auto' },
                }}
              >
                {/* Pause button - visible during processing */}
                {currentBatch.status === 'processing' && (
                  <Tooltip title="Pause batch processing">
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={isPausing ? <CircularProgress size={20} color="inherit" /> : <PauseIcon />}
                      onClick={handlePauseBatch}
                      disabled={isPausing}
                      fullWidth={{ xs: true, sm: false }}
                      sx={{ minHeight: 44 }}
                    >
                      Pause
                    </Button>
                  </Tooltip>
                )}

                {/* Resume button - visible when paused */}
                {currentBatch.status === 'paused' && (
                  <Tooltip title="Resume batch processing">
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={isResuming ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
                      onClick={handleResumeBatch}
                      disabled={isResuming}
                      fullWidth={{ xs: true, sm: false }}
                      sx={{ minHeight: 44 }}
                    >
                      Resume
                    </Button>
                  </Tooltip>
                )}

                {/* Cancel button - visible during processing or paused */}
                {(currentBatch.status === 'processing' || currentBatch.status === 'paused') && (
                  <Tooltip title="Cancel batch processing">
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={isCancelling ? <CircularProgress size={20} color="inherit" /> : <StopIcon />}
                      onClick={handleCancelBatch}
                      disabled={isCancelling}
                      fullWidth={{ xs: true, sm: false }}
                      sx={{ minHeight: 44 }}
                    >
                      Cancel
                    </Button>
                  </Tooltip>
                )}

                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => fetchBatchResults()}
                  disabled={currentBatch.status !== 'completed'}
                  fullWidth={{ xs: true, sm: false }}
                  sx={{ minHeight: 44 }}
                >
                  View Results
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={exportBatchResults}
                  disabled={currentBatch.status !== 'completed'}
                  fullWidth={{ xs: true, sm: false }}
                  sx={{ minHeight: 44 }}
                >
                  Export CSV
                </Button>
                {/* Review Duplicates button - visible when batch has duplicates */}
                {((currentBatch.duplicates_detected && currentBatch.duplicates_detected > 0) || duplicates.length > 0) && (
                  <Tooltip title="Review detected duplicate resumes">
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<DuplicateIcon />}
                      onClick={() => setDuplicatesDialog(true)}
                      fullWidth={{ xs: true, sm: false }}
                      sx={{ minHeight: 44 }}
                    >
                      Review Duplicates ({duplicates.length || currentBatch.duplicates_detected})
                    </Button>
                  </Tooltip>
                )}
                <Button
                  onClick={resetBatch}
                  fullWidth={{ xs: true, sm: false }}
                  sx={{ minHeight: 44 }}
                >
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

            <Box
              sx={{
                mt: 3,
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(4, 1fr)',
                },
                gap: 2,
              }}
            >
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
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {duplicates.length || currentBatch.duplicates_detected || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Duplicates
                </Typography>
              </Paper>
            </Box>

            {/* Duplicate Alert - shows when batch completes with duplicates */}
            {currentBatch.status === 'completed' && (duplicates.length > 0 || (currentBatch.duplicates_detected && currentBatch.duplicates_detected > 0)) && (
              <Alert
                severity="warning"
                sx={{ mt: 2 }}
                action={
                  <Button
                    size="small"
                    variant="contained"
                    color="warning"
                    onClick={() => setDuplicatesDialog(true)}
                    sx={{ minHeight: 44 }}
                  >
                    Review Now
                  </Button>
                }
              >
                <AlertTitle>Duplicate Resumes Detected</AlertTitle>
                {duplicates.length || currentBatch.duplicates_detected} duplicate resume(s) were found in this batch.
                Please review them to decide whether to keep or reject each duplicate.
              </Alert>
            )}
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
            <Button
              onClick={exportBatchResults}
              startIcon={<DownloadIcon />}
              variant="contained"
              disabled={!batchResults || !batchResults.files || batchResults.files.length === 0}
            >
              Export CSV
            </Button>
            <Button onClick={() => setResultsDialog(false)}>Close</Button>
          </DialogActions>
        </Dialog>

        {/* Duplicates Review Dialog */}
        <Dialog
          open={duplicatesDialog}
          onClose={() => setDuplicatesDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="warning" />
              Review Duplicate Resumes
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="info" sx={{ mb: 2 }}>
              These resumes have been flagged as duplicates of existing resumes in your system.
              Review each one to decide whether to keep or reject them.
            </Alert>
            {duplicates.length === 0 ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <CheckIcon color="success" sx={{ fontSize: 48, mb: 1 }} />
                <Typography variant="body1" color="text.secondary">
                  All duplicates have been reviewed!
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Filename</TableCell>
                      <TableCell>Match Type</TableCell>
                      <TableCell>Similarity</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {duplicates.map((dup) => (
                      <TableRow
                        key={dup.resume_id}
                        sx={{
                          bgcolor: 'warning.lighter',
                          '&:hover': { bgcolor: 'warning.light' },
                        }}
                      >
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <DuplicateIcon color="warning" fontSize="small" />
                            <Typography variant="body2">{dup.filename}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={dup.match_type === 'exact' ? 'Exact Match' : 'Similar'}
                            color={dup.match_type === 'exact' ? 'warning' : 'default'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {Math.round((dup.similarity_score || 1) * 100)}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                            <Tooltip title="Keep this duplicate resume">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleAcceptDuplicate(dup)}
                                disabled={acceptingDuplicate === dup.resume_id || rejectingDuplicate === dup.resume_id}
                                sx={{ minWidth: 44, minHeight: 44 }}
                              >
                                {acceptingDuplicate === dup.resume_id ? (
                                  <CircularProgress size={20} color="inherit" />
                                ) : (
                                  <CheckIcon fontSize="small" />
                                )}
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete this duplicate resume">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRejectDuplicate(dup)}
                                disabled={acceptingDuplicate === dup.resume_id || rejectingDuplicate === dup.resume_id}
                                sx={{ minWidth: 44, minHeight: 44 }}
                              >
                                {rejectingDuplicate === dup.resume_id ? (
                                  <CircularProgress size={20} color="inherit" />
                                ) : (
                                  <DeleteIcon fontSize="small" />
                                )}
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </DialogContent>
          <DialogActions sx={{ justifyContent: 'space-between', px: 3 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {duplicates.length > 1 && (
                <>
                  <Button
                    variant="outlined"
                    color="success"
                    onClick={handleAcceptAllDuplicates}
                    startIcon={<CheckIcon />}
                    sx={{ minHeight: 44 }}
                  >
                    Accept All
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleRejectAllDuplicates}
                    startIcon={<DeleteIcon />}
                    sx={{ minHeight: 44 }}
                  >
                    Reject All
                  </Button>
                </>
              )}
            </Box>
            <Button onClick={() => setDuplicatesDialog(false)} sx={{ minHeight: 44 }}>
              Close
            </Button>
          </DialogActions>
        </Dialog>

        {/* Recent Batches */}
        <Paper sx={{ p: 3, mt: 3 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6">
              Recent Batches
            </Typography>
            <IconButton
              onClick={() => window.location.reload()}
              sx={{ minWidth: 44, minHeight: 44 }}
            >
              <RefreshIcon />
            </IconButton>
          </Box>
          <BatchList />
        </Paper>
      </Box>
    </Container>
    </ErrorBoundary>
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
