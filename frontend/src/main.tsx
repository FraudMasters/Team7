import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { LanguageProvider } from './contexts/LanguageContext';
import { ThemeProvider, useThemeContext } from './contexts/ThemeContext';
import App from './App';
import './index.css';
import './i18n'; // Initialize i18n

/**
 * Inner App Component that uses the theme context
 * This allows us to use useThemeContext inside the provider tree
 */
const AppWithTheme: React.FC = () => {
  const { theme } = useThemeContext();

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </MuiThemeProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LanguageProvider>
      <ThemeProvider>
        <AppWithTheme />
      </ThemeProvider>
    </LanguageProvider>
  </React.StrictMode>
);
