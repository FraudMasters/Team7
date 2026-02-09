import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
// Импорт компонентов MUI Material
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Paper,
  BottomNavigation,
  BottomNavigationAction,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery,
  useTheme,
  IconButton,
  Collapse,
  CircularProgress,
  Backdrop,
  Fade,
} from '@mui/material';
// Импорт иконок MUI
import {
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
  Description as DescriptionIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  Lightbulb as TipsIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Recommend as RecommendIcon,
  School as LearningIcon,
  Assessment as AssessmentIcon,
  Menu as MenuIcon,
  AttachMoney as SalaryIcon,
} from '@mui/icons-material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import { useAuthContext } from '@/contexts/AuthContext';

// Интерфейс элемента навигации
interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
  children?: NavItem[];
}

// Интерфейс секции навигации
interface NavSection {
  title?: string;
  items: NavItem[];
}

// Конфигурация секций навигации для соискателя
const navSections: NavSection[] = [
  {
    items: [
      { label: 'Find Jobs', path: '/jobs', icon: <SearchIcon /> },
    ],
  },
  {
    title: 'Jobs',
    items: [
      { label: 'Browse', path: '/jobs', icon: <WorkIcon /> },
      { label: 'Recommended', path: '/jobs/recommended', icon: <RecommendIcon /> },
      { label: 'Saved', path: '/jobs/saved', icon: <BookmarkIcon /> },
      { label: 'Applications', path: '/jobs/applications', icon: <DescriptionIcon /> },
    ],
  },
  {
    title: 'Career',
    items: [
      { label: 'Skill Assessment', path: '/jobs/assessment', icon: <AssessmentIcon /> },
      { label: 'Learning', path: '/jobs/learning', icon: <LearningIcon /> },
      { label: 'Salary Calculator', path: '/jobs/salary', icon: <SalaryIcon /> },
      { label: 'Interview Tips', path: '/jobs/tips', icon: <TipsIcon /> },
    ],
  },
  {
    title: 'Account',
    items: [
      { label: 'Profile', path: '/profile', icon: <PersonIcon /> },
      { label: 'Resume', path: '/jobs/upload', icon: <DescriptionIcon /> },
      { label: 'Job Alerts', path: '/jobs/alerts', icon: <NotificationsIcon /> },
      { label: 'Settings', path: '/jobs/settings', icon: <SettingsIcon /> },
    ],
  },
];

// Элементы нижней навигации для мобильных устройств
const bottomNavItems: NavItem[] = [
  { label: 'Jobs', path: '/jobs', icon: <WorkIcon /> },
  { label: 'Saved', path: '/jobs/saved', icon: <BookmarkIcon /> },
  { label: 'Applications', path: '/jobs/applications', icon: <DescriptionIcon /> },
  { label: 'Profile', path: '/profile', icon: <PersonIcon /> },
];

// Ширина боковой панели навигации
const DRAWER_WIDTH = 280;

// Основной компонент макета для соискателя
const JobSeekerLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { isInitialized } = useAuthContext();
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Jobs: true,
    Career: false,
    Account: false,
  });
  // State for transition animation
  const [transitionKey, setTransitionKey] = useState(location.pathname);

  // Обновление активной вкладки на основе текущего маршрута (нижняя навигация)
  useEffect(() => {
    const index = bottomNavItems.findIndex((item) =>
      location.pathname === item.path || location.pathname.startsWith(item.path + '/')
    );
    if (index >= 0) {
      setBottomNavValue(index);
    }
  }, [location.pathname]);

  // Trigger transition animation on route change
  useEffect(() => {
    setTransitionKey(location.pathname);
  }, [location.pathname]);

  // Обработчик изменения нижней навигации
  const handleBottomNavChange = (_event: React.SyntheticEvent, newValue: number) => {
    setBottomNavValue(newValue);
    navigate(bottomNavItems[newValue].path);
  };

  // Обработчик открытия/закрытия мобильного меню
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // Обработчик переключения секции навигации
  const handleSectionToggle = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // Содержимое боковой панели навигации
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Логотип */}
      <Box
        sx={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          px: 3,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="h6"
          role="heading"
          aria-level={1}
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          AgentHR
        </Typography>
      </Box>

      {/* Секции навигации */}
      <nav aria-label="Основная навигация">
        <List sx={{ px: 2, py: 2 }} role="menubar">
          {navSections.map((section, sectionIdx) => (
            <Box key={section.title || sectionIdx}>
              {section.title && (
                <>
                  <ListItem
                    disablePadding
                    sx={{ mt: sectionIdx > 0 ? 2 : 0, mb: 1 }}
                    role="none"
                  >
                    <ListItemButton
                      onClick={() => handleSectionToggle(section.title!)}
                      sx={{
                        borderRadius: 2,
                        px: 2,
                        py: 1,
                        '&:hover': { backgroundColor: 'action.hover' },
                      }}
                    >
                      <ListItemText
                        primary={section.title}
                        sx={{
                          '& .MuiTypography-root': {
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: 0.5,
                            color: 'text.secondary',
                          },
                        }}
                      />
                      {expandedSections[section.title!] ? <ExpandLess /> : <ExpandMore />}
                    </ListItemButton>
                  </ListItem>
                </>
              )}

              <Collapse in={!section.title || expandedSections[section.title!]} timeout="auto" unmountOnExit>
                {section.items.map((item) => {
                  const isActive = location.pathname === item.path ||
                    (item.path !== '/jobs' && location.pathname.startsWith(item.path + '/'));

                  return (
                    <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }} role="none">
                      <ListItemButton
                        role="menuitem"
                        aria-current={isActive ? 'page' : undefined}
                        onClick={() => {
                          navigate(item.path);
                          if (isMobile) setMobileOpen(false);
                        }}
                        sx={{
                          borderRadius: 2,
                          px: 2,
                          py: 1,
                          backgroundColor: isActive ? 'action.selected' : 'transparent',
                          '&:hover': {
                            backgroundColor: isActive ? 'action.selected' : 'action.hover',
                          },
                        }}
                      >
                        <ListItemIcon
                          sx={{
                            minWidth: 40,
                            color: isActive ? 'primary.main' : 'text.primary',
                          }}
                          aria-hidden="true"
                        >
                          {item.icon}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.label}
                          sx={{
                            '& .MuiTypography-root': {
                              fontWeight: isActive ? 600 : 500,
                              fontSize: '0.875rem',
                            },
                          }}
                        />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </Collapse>

              {sectionIdx < navSections.length - 1 && (
                <Divider sx={{ my: 1, mx: 2 }} />
              )}
            </Box>
          ))}
        </List>
      </nav>
    </Box>
  );

  /**
   * Show loading state during initial auth check
   */
  if (!isInitialized) {
    return (
      <Backdrop
        sx={{
          color: 'primary.main',
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: 'background.default',
        }}
        open
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <CircularProgress size={48} thickness={4} />
          <Typography variant="body1" color="text.secondary">
            Loading...
          </Typography>
        </Box>
      </Backdrop>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Ссылка для пропуска к основному содержимому (для пользователей клавиатуры) */}
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          top: 0,
          zIndex: 9999,
          '&:focus': {
            left: '10px',
            top: '10px',
            bgcolor: 'primary.main',
            color: 'white',
            p: 2,
            borderRadius: 1,
          },
        }}
      >
        Skip to main content
      </Box>

      {/* Фиксированная верхняя панель */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ justifyContent: { xs: 'center', md: 'space-between' } }}>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
            <Typography
              variant="h6"
              component="h1"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AgentHR
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              color="inherit"
              onClick={() => navigate('/jobs/alerts')}
              aria-label="Job alerts"
              sx={{ display: { xs: 'none', md: 'flex' } }}
            >
              <NotificationsIcon />
            </IconButton>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
              sx={{ display: { xs: 'flex', md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Боковая панель для десктопа */}
      <Box
        component="nav"
        sx={{
          width: { md: DRAWER_WIDTH },
          flexShrink: { md: 0 },
          display: { xs: 'none', md: 'block' },
        }}
        aria-label="Job seeker sidebar navigation"
      >
        <Drawer
          variant="permanent"
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      {/* Мобильное выдвижное меню */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: DRAWER_WIDTH,
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Основной контент */}
      <Box
        component="main"
        id="main-content"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          bgcolor: 'background.default',
          pb: { xs: 7, md: 0 }, // Padding for bottom navigation on mobile
        }}
        tabIndex={-1}
      >
        <Fade in timeout={{ enter: 300, exit: 200 }} key={transitionKey}>
          <Box>
            <Outlet />
          </Box>
        </Fade>
      </Box>

      {/* Нижняя навигация (только для мобильных устройств) */}
      <Paper
        component="nav"
        aria-label="Mobile navigation"
        sx={{
          display: { xs: 'block', md: 'none' },
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          elevation: 3,
          borderRadius: 0,
          zIndex: (theme) => theme.zIndex.appBar - 1,
        }}
      >
        <BottomNavigation
          value={bottomNavValue}
          onChange={handleBottomNavChange}
          aria-label="Job seeker navigation"
          showLabels
        >
          {bottomNavItems.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              icon={item.icon}
              aria-current={bottomNavValue === index ? 'page' : undefined}
            />
          ))}
        </BottomNavigation>
      </Paper>
    </Box>
  );
};

export default JobSeekerLayout;
