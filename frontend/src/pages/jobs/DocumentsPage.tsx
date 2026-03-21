import { useState } from 'react';
// MUI компоненты для UI
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Stack,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Card,
  CardContent,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
// Иконки MUI
import {
  Search as SearchIcon,
  Description as DocumentIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  CloudUpload as UploadIcon,
} from '@mui/icons-material';
// Хуки для получения данных
import { useDocuments } from '../../hooks/useDocuments';
// Компоненты
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';
import DocumentUploader from '../../components/candidate/DocumentUploader';

export function DocumentsPage() {
  // Состояние для поискового запроса
  const [searchTerm, setSearchTerm] = useState('');
  // Состояние для фильтрации по типу документа
  const [filters, setFilters] = useState<{
    document_type?: string;
  }>({});
  // Состояние для отображения секции загрузки
  const [showUploader, setShowUploader] = useState(false);

  // Получаем данные о документах
  const { data, isLoading, error, refetch } = useDocuments(filters);

  // Фильтрация документов по поиску
  const filteredDocuments = data?.documents.filter((document) => {
    // Проверка соответствия поисковому запросу
    const matchesSearch =
      searchTerm === '' ||
      document.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      document.description?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesSearch;
  }) ?? [];

  // Функция для подсчета документов по типу
  const getTypeCount = (type: string) => {
    return data?.documents.filter((doc) => doc.document_type === type).length ?? 0;
  };

  // Функция для получения названия типа документа
  const getDocumentTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      CERTIFICATE: 'Certificate',
      DIPLOMA: 'Diploma',
      REFERENCE: 'Reference Letter',
      PORTFOLIO: 'Portfolio',
      TRANSCRIPT: 'Transcript',
      OTHER: 'Other',
    };
    return labels[type] || type;
  };

  // Функция для получения цвета чипа по типу документа
  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'info' | 'error' | 'default'> = {
      CERTIFICATE: 'success',
      DIPLOMA: 'primary',
      REFERENCE: 'info',
      PORTFOLIO: 'secondary',
      TRANSCRIPT: 'warning',
      OTHER: 'default',
    };
    return colors[type] || 'default';
  };

  // Функция для форматирования даты
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Обработчик успешной загрузки
  const handleUploadComplete = (documentId: string) => {
    // Обновляем список документов
    refetch();
    // Скрываем форму загрузки
    setShowUploader(false);
  };

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            My Documents
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your uploaded documents, certificates, and portfolios
          </Typography>
        </Box>

        {/* Секция загрузки документа */}
        {showUploader ? (
          <Paper sx={{ p: 3, mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Upload New Document
              </Typography>
              <IconButton onClick={() => setShowUploader(false)} size="small">
                <DeleteIcon />
              </IconButton>
            </Box>
            <DocumentUploader
              showDocumentTypeSelector={true}
              onUploadComplete={handleUploadComplete}
            />
          </Paper>
        ) : (
          <Paper
            sx={{
              p: 3,
              mb: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
              cursor: 'pointer',
              border: '2px dashed',
              borderColor: 'divider',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
            onClick={() => setShowUploader(true)}
          >
            <UploadIcon color="primary" sx={{ fontSize: 32 }} />
            <Typography variant="h6" color="primary">
              Upload New Document
            </Typography>
          </Paper>
        )}

        {/* Поиск и фильтры */}
        <Paper
          sx={{
            p: 2,
            mb: 4,
            display: 'flex',
            gap: 2,
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <TextField
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={filters.document_type || ''}
              label="Type"
              onChange={(e) => setFilters({ ...filters, document_type: e.target.value || undefined })}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="CERTIFICATE">Certificate</MenuItem>
              <MenuItem value="DIPLOMA">Diploma</MenuItem>
              <MenuItem value="REFERENCE">Reference</MenuItem>
              <MenuItem value="PORTFOLIO">Portfolio</MenuItem>
              <MenuItem value="TRANSCRIPT">Transcript</MenuItem>
              <MenuItem value="OTHER">Other</MenuItem>
            </Select>
          </FormControl>
          {/* Отображение общего количества документов */}
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
            <DocumentIcon color="primary" />
            <Typography variant="body2" color="text.secondary">
              {data?.total || 0} total
            </Typography>
          </Box>
        </Paper>

        {/* Сводка по типам */}
        {data && data.documents.length > 0 && (
          <Paper sx={{ p: 2, mb: 4 }}>
            <Stack direction="row" spacing={2} flexWrap="wrap">
              <Typography variant="body2" color="text.secondary">
                Summary:
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 80 }}>
                Certificates: {getTypeCount('CERTIFICATE')}
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 70 }}>
                Diplomas: {getTypeCount('DIPLOMA')}
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 80 }}>
                References: {getTypeCount('REFERENCE')}
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 70 }}>
                Portfolios: {getTypeCount('PORTFOLIO')}
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 80 }}>
                Transcripts: {getTypeCount('TRANSCRIPT')}
              </Typography>
              <Typography variant="body2" sx={{ minWidth: 50 }}>
                Other: {getTypeCount('OTHER')}
              </Typography>
            </Stack>
          </Paper>
        )}

        {/* Состояния загрузки, ошибки, пустого списка и список документов */}
        {isLoading ? (
          <LoadingState message="Loading documents..." />
        ) : error ? (
          <ErrorState
            title="Error"
            message="Failed to load documents. Please try again later."
            onRetry={() => window.location.reload()}
          />
        ) : filteredDocuments.length === 0 ? (
          // Пустое состояние - нет документов
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <DocumentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {searchTerm || filters.document_type ? 'No documents match your search' : 'No documents yet'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {searchTerm || filters.document_type
                ? 'Try adjusting your search terms'
                : 'Upload your first document to get started'}
            </Typography>
            {!searchTerm && !filters.document_type && (
              <Typography
                variant="body2"
                color="primary"
                sx={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => setShowUploader(true)}
              >
                Upload Document
              </Typography>
            )}
          </Paper>
        ) : (
          // Список документов
          <Grid container spacing={2}>
            {filteredDocuments.map((document, index) => (
              <Grid item xs={12} key={document.id}>
                <Box
                  sx={{
                    animation: `fadeInUp 0.5s ease-out ${index * 50}ms both`,
                    '@keyframes fadeInUp': {
                      '0%': {
                        opacity: 0,
                        transform: 'translateY(20px)',
                      },
                      '100%': {
                        opacity: 1,
                        transform: 'translateY(0)',
                      },
                    },
                  }}
                >
                  <Card
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      p: 2,
                      '&:hover': {
                        boxShadow: 3,
                      },
                    }}
                  >
                    <DocumentIcon sx={{ fontSize: 48, color: 'primary.main', mr: 2 }} />
                    <CardContent sx={{ flex: 1, py: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6" fontWeight={600}>
                          {document.filename}
                        </Typography>
                        <Chip
                          label={getDocumentTypeLabel(document.document_type)}
                          color={getDocumentTypeColor(document.document_type)}
                          size="small"
                        />
                      </Box>
                      {document.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {document.description}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={2} divider={<Divider orientation="vertical" flexItem />}>
                        <Typography variant="caption" color="text.secondary">
                          Type: {document.content_type}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Uploaded: {formatDate(document.created_at)}
                        </Typography>
                      </Stack>
                    </CardContent>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton color="primary" size="small" title="Download">
                        <DownloadIcon />
                      </IconButton>
                      <IconButton color="error" size="small" title="Delete">
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Card>
                </Box>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </PageTransition>
  );
}
