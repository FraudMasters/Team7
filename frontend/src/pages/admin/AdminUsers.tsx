import { useState, useMemo } from 'react';
import {
  Container,
  Box,
  TextField,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

/**
 * User interface for admin user management
 */
interface User {
  id: string;
  email: string;
  name: string;
  role: 'JobSeeker' | 'Recruiter' | 'Admin';
  status: 'active' | 'inactive' | 'suspended';
  organization?: string;
  created_at: string;
  last_login?: string;
}

/**
 * Mock users data - TODO: Replace with actual API call when backend endpoint is available
 */
const MOCK_USERS: User[] = [
  {
    id: '1',
    email: 'admin@example.com',
    name: 'System Admin',
    role: 'Admin',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-02-05T10:30:00Z',
  },
  {
    id: '2',
    email: 'recruiter@example.com',
    name: 'John Recruiter',
    role: 'Recruiter',
    status: 'active',
    organization: 'Tech Corp',
    created_at: '2024-01-15T00:00:00Z',
    last_login: '2024-02-05T09:15:00Z',
  },
  {
    id: '3',
    email: 'jobseeker@example.com',
    name: 'Jane Candidate',
    role: 'JobSeeker',
    status: 'active',
    created_at: '2024-01-20T00:00:00Z',
    last_login: '2024-02-04T16:45:00Z',
  },
  {
    id: '4',
    email: 'inactive@example.com',
    name: 'Inactive User',
    role: 'JobSeeker',
    status: 'inactive',
    created_at: '2023-12-01T00:00:00Z',
  },
];

/**
 * Helper to get role color
 */
const getRoleColor = (role: string): 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (role) {
    case 'Admin':
      return 'error';
    case 'Recruiter':
      return 'primary';
    case 'JobSeeker':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * Helper to get status color
 */
const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
  switch (status) {
    case 'active':
      return 'success';
    case 'inactive':
      return 'default';
    case 'suspended':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Format date for display
 */
const formatDate = (dateString?: string): string => {
  if (!dateString) return 'Never';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * AdminUsers Page Component
 *
 * Provides user management interface for administrators:
 * - View all users with search and filter
 * - User status management (activate/deactivate/suspend)
 * - Role assignment and editing
 * - User deletion
 *
 * @example
 * ```tsx
 * <AdminUsers />
 * ```
 */
export function AdminUsers() {
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // TODO: Replace with actual API call when endpoint is available
  // const { data: usersData, isLoading, error, refetch } = useQuery({
  //   queryKey: ['admin-users'],
  //   queryFn: async () => {
  //     const response = await apiClient.get<{ users: User[] }>('/admin/users');
  //     return response.data;
  //   },
  // });

  // Using mock data for now
  const isLoading = false;
  const error = null;
  const usersData = { users: MOCK_USERS };

  /**
   * Filter users based on search term
   */
  const filteredUsers = useMemo(() => {
    const users = usersData?.users || [];
    if (!searchTerm) return users;

    const searchLower = searchTerm.toLowerCase();
    return users.filter(
      (user) =>
        user.name.toLowerCase().includes(searchLower) ||
        user.email.toLowerCase().includes(searchLower) ||
        user.role.toLowerCase().includes(searchLower) ||
        user.organization?.toLowerCase().includes(searchLower)
    );
  }, [usersData, searchTerm]);

  /**
   * Handle menu open
   */
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, user: User) => {
    setAnchorEl(event.currentTarget);
    setSelectedUser(user);
  };

  /**
   * Handle menu close
   */
  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedUser(null);
  };

  /**
   * Handle user action (placeholder)
   */
  const handleUserAction = (action: string) => {
    if (!selectedUser) return;

    // TODO: Implement actual API calls for user actions
    switch (action) {
      case 'edit':
        // Open edit dialog
        break;
      case 'activate':
        // Call API to activate user
        break;
      case 'deactivate':
        // Call API to deactivate user
        break;
      case 'suspend':
        // Call API to suspend user
        break;
      case 'delete':
        // Call API to delete user
        break;
    }
    handleMenuClose();
  };

  /**
   * Render loading state
   */
  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h6" color="text.secondary">
            Loading users...
          </Typography>
        </Box>
      </Container>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">
          <Typography variant="subtitle1" fontWeight={600}>
            Failed to load users
          </Typography>
          <Typography variant="body2">
            {(error as Error).message || 'An unexpected error occurred'}
          </Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          User Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage user accounts, roles, and permissions
        </Typography>
      </Box>

      {/* Search and Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <TextField
          placeholder="Search users by name, email, role..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ maxWidth: 400, flex: 1, minWidth: 250 }}
        />

        <Button
          variant="contained"
          startIcon={<AddIcon />}
          // TODO: Implement add user functionality
          onClick={() => {}}
        >
          Add User
        </Button>
      </Box>

      {/* Users Table */}
      <Paper elevation={1}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>User</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Role</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Organization</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Created</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>Last Login</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      {searchTerm ? 'No users found matching your search' : 'No users found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user) => (
                  <TableRow
                    key={user.id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      '&:hover': { bgcolor: 'action.selected' },
                    }}
                  >
                    {/* User Info */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {user.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {user.email}
                        </Typography>
                      </Box>
                    </TableCell>

                    {/* Role */}
                    <TableCell>
                      <Chip
                        label={user.role}
                        color={getRoleColor(user.role)}
                        size="small"
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>

                    {/* Organization */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {user.organization || '-'}
                      </Typography>
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      <Chip
                        label={user.status}
                        color={getStatusColor(user.status)}
                        size="small"
                        sx={{ fontWeight: 600, textTransform: 'capitalize' }}
                      />
                    </TableCell>

                    {/* Created Date */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(user.created_at)}
                      </Typography>
                    </TableCell>

                    {/* Last Login */}
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(user.last_login)}
                      </Typography>
                    </TableCell>

                    {/* Actions */}
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, user)}
                        aria-label="User actions"
                      >
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={() => handleUserAction('edit')}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit User
        </MenuItem>
        {selectedUser?.status === 'active' ? (
          <MenuItem onClick={() => handleUserAction('deactivate')}>
            <BlockIcon fontSize="small" sx={{ mr: 1 }} />
            Deactivate
          </MenuItem>
        ) : (
          <MenuItem onClick={() => handleUserAction('activate')}>
            <CheckCircleIcon fontSize="small" sx={{ mr: 1 }} />
            Activate
          </MenuItem>
        )}
        {selectedUser?.status === 'active' && (
          <MenuItem onClick={() => handleUserAction('suspend')} sx={{ color: 'error.main' }}>
            <BlockIcon fontSize="small" sx={{ mr: 1 }} />
            Suspend
          </MenuItem>
        )}
        <MenuItem onClick={() => handleUserAction('delete')} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete User
        </MenuItem>
      </Menu>

      {/* User Count Summary */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Showing {filteredUsers.length} of {usersData?.users.length || 0} users
        </Typography>
      </Box>
    </Container>
  );
}
