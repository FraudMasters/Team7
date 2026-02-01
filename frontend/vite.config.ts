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
    // Disable manualChunks to avoid circular dependency issues with emotion/mui
    // Vite's default chunking strategy is safer and works correctly
    rollupOptions: {
      output: {
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
