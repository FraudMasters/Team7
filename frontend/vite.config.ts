import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

/**
 * Vite Configuration with Performance Optimizations
 *
 * Performance Optimizations:
 * 1. Granular Code Splitting - Dependencies split into smaller chunks for better caching
 *    - React core, React Router, MUI components separated
 *    - Heavy libraries (DnD, date-fns) isolated to route-specific chunks
 *    - Reduces initial bundle size and enables parallel loading
 *
 * 2. Asset Optimization:
 *    - assetsInlineLimit: 4KB - Small assets inlined as base64 to reduce requests
 *    - chunkSizeWarningLimit: 500KB - Warns about large bundles
 *    - Organized asset output by type (js, css, images, fonts)
 *
 * 3. CSS Code Splitting - Enabled for better caching of per-component CSS
 *
 * 4. Tree Shaking & Minification:
 *    - Terser minification with console.log removal in production
 *    - Dead code elimination via Rollup
 *
 * 5. Dependency Optimization - Pre-bundles dependencies for faster dev server startup
 *
 * Expected Results:
 * - Initial bundle < 500KB
 * - Faster page loads via granular chunking
 * - Better caching strategy for vendor libraries
 * - Reduced number of HTTP requests
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@api': path.resolve(__dirname, './src/api'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@i18n': path.resolve(__dirname, './src/i18n'),
      '@pages': path.resolve(__dirname, './src/pages'),
    },
  },
  server: {
    port: 5173,
    host: true,
    strictPort: false,
    open: true,
    proxy: {
      // Proxy API requests to backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy health checks
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Optimize chunk sizes for faster initial load
    rollupOptions: {
      output: {
        // More granular chunk splitting for better caching and parallel loading
        manualChunks: (id) => {
          // React core - rarely changes, good for caching
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/')) {
            return 'react-core';
          }
          // React Router - separate for route lazy loading
          if (id.includes('node_modules/react-router/')) {
            return 'react-router';
          }
          // Material UI - split into smaller chunks
          if (id.includes('node_modules/@mui/material/')) {
            // Split heavy components
            if (id.includes('@mui/material/Grid') || id.includes('@mui/material/Container')) {
              return 'mui-layout';
            }
            if (id.includes('@mui/material/Table') || id.includes('@mui/material/DataGrid')) {
              return 'mui-table';
            }
            return 'mui-core';
          }
          // MUI Icons - very large, keep separate
          if (id.includes('node_modules/@mui/icons-material/')) {
            return 'mui-icons';
          }
          // Emotion (CSS-in-JS) - separate for better caching
          if (id.includes('node_modules/@emotion/')) {
            return 'emotion';
          }
          // API client - small, rarely changes
          if (id.includes('node_modules/axios/')) {
            return 'api-client';
          }
          // DnD library - only used on workflow page
          if (id.includes('node_modules/@hello-pangea/dnd/')) {
            return 'dnd-library';
          }
          // Date utilities - only used where dates are needed
          if (id.includes('node_modules/date-fns/')) {
            return 'date-utils';
          }
          // i18n - rarely changes
          if (id.includes('node_modules/i18next/')) {
            return 'i18n';
          }
          // Other node_modules
          if (id.includes('node_modules/')) {
            return 'vendor';
          }
        },
        // Optimize chunk file names for better caching
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || '';
          if (name.endsWith('.css')) {
            return 'assets/css/[name]-[hash][extname]';
          }
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(name)) {
            return 'assets/images/[name]-[hash][extname]';
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(name)) {
            return 'assets/fonts/[name]-[hash][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
    // Asset size limits - warn if files are too large
    assetsInlineLimit: 4096, // 4KB - inline small assets as base64
    chunkSizeWarningLimit: 500, // Warn if chunks exceed 500KB
    // CSS code splitting
    cssCodeSplit: true,
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
      },
      format: {
        comments: false,
      },
    },
  },
  // Optimize dependencies for faster dev server startup
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
      '@emotion/react',
      '@emotion/styled',
      'axios',
      'i18next',
      'i18next-browser-languagedetector',
    ],
  },
  // Preview server configuration
  preview: {
    port: 4173,
    host: true,
    strictPort: false,
    open: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
    coverage: {
      provider: 'c8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
    },
  },
});
