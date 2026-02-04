// PWA configuration for vite-plugin-pwa
// This configuration enables Progressive Web App capabilities including:
// - Service worker with workbox for caching strategies
// - Web app manifest for install-to-homescreen
// - Offline support for cached assets

import { defineConfig } from 'vite-plugin-pwa';

export const pwaConfig = defineConfig({
  registerType: 'autoUpdate', // Automatically update service worker when new version available

  // Web app manifest configuration
  manifest: {
    name: 'Resume Analysis Platform',
    short_name: 'ResumeAI',
    description: 'AI-powered resume analysis platform for recruiters and job seekers',
    theme_color: '#1976d2', // Material-UI primary blue
    background_color: '#ffffff',
    display: 'standalone', // Run as standalone app (not in browser)
    orientation: 'portrait-primary', // Lock to portrait on mobile
    scope: '/',
    start_url: '/',
    icons: [
      {
        src: '/icon-192x192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any maskable' // Maskable for adaptive icons on Android
      },
      {
        src: '/icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any maskable'
      }
    ],
    categories: ['business', 'productivity', 'utilities'],
    shortcuts: [
      {
        name: 'Search Candidates',
        short_name: 'Search',
        description: 'Search and filter candidates',
        url: '/recruiter/search',
        icons: [{ src: '/icon-192x192.png', sizes: '192x192' }]
      },
      {
        name: 'My Resumes',
        short_name: 'Resumes',
        description: 'View analyzed resumes',
        url: '/recruiter/resumes',
        icons: [{ src: '/icon-192x192.png', sizes: '192x192' }]
      }
    ]
  },

  // Workbox configuration for service worker
  workbox: {
    // Glob patterns for precaching (static assets to cache immediately)
    globPatterns: [
      '**/*.{js,css,html,ico,png,svg,woff2}'
    ],
    // Don't cache these routes (use network-first or network-only)
    navigateFallback: null, // Let the app handle 404s
    navigateFallbackDenylist: [/^\/api/, /^\/health/], // Don't fallback for API routes

    // Runtime caching strategies for different resource types
    runtimeCaching: [
      // API calls - Network First with offline fallback
      {
        urlPattern: /^https?:\/\/.*\/api\/.*/i,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 5 * 60 // 5 minutes
          },
          networkTimeoutSeconds: 10, // Fall back to cache after 10s
          cacheableResponse: {
            statuses: [0, 200]
          }
        }
      },
      // Images - Cache First with long expiration
      {
        urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'image-cache',
          expiration: {
            maxEntries: 60,
            maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
          }
        }
      },
      // Fonts - Cache First with very long expiration
      {
        urlPattern: /\.(?:woff2?|eot|ttf|otf)$/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'font-cache',
          expiration: {
            maxEntries: 20,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
          }
        }
      },
      // JavaScript and CSS - Stale While Revalidate
      {
        urlPattern: /\.(?:js|css)$/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'static-resources',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 7 * 24 * 60 * 60 // 7 days
          }
        }
      }
    ]
  },

  // Service worker configuration
  // Don't register service worker on development
  disableForProcess: ['development'] ?? [],

  // Dev options
  devOptions: {
    enabled: false, // Disable PWA in development
    navigateFallback: false
  }
});

export default pwaConfig;
