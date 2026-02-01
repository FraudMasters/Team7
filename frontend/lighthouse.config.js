module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:8080',
      ],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox',
        onlyCategories: ['performance', 'best-practices', 'accessibility', 'seo'],
        throttling: {
          rttMs: 40,
          throughputKbps: 10 * 1024,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0,
        },
        screenEmulation: {
          mobile: false,
          width: 1920,
          height: 1080,
          deviceScaleFactor: 1,
          disabled: false,
        },
        formFactor: 'desktop',
        throttlingMethod: 'devtools',
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.90, aggregationMethod: 'median' }],
        'categories:best-practices': ['error', { minScore: 0.90, aggregationMethod: 'median' }],
        'categories:accessibility': ['warn', { minScore: 0.90, aggregationMethod: 'median' }],
        'categories:seo': ['warn', { minScore: 0.80, aggregationMethod: 'median' }],

        // Performance budgets
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
        'speed-index': ['warn', { maxNumericValue: 3400 }],
        'interactive': ['error', { maxNumericValue: 3800 }],

        // Resource budgets
        'total-byte-weight': ['warn', { maxNumericValue: 1500000 }], // 1.5MB
        'resource-summary:script:size': ['warn', { maxNumericValue: 500000 }], // 500KB
        'resource-summary:stylesheet:size': ['warn', { maxNumericValue: 100000 }], // 100KB
        'resource-summary:image:size': ['warn', { maxNumericValue: 300000 }], // 300KB
        'resource-summary:font:size': ['warn', { maxNumericValue: 100000 }], // 100KB
        'resource-summary:total:size': ['warn', { maxNumericValue: 1500000 }], // 1.5MB

        // Best practices
        'redirects': ['warn', { maxLength: 0 }],
        'appcache-manifest': ['warn', { maxLength: 0 }],
        'doctype': ['error', { maxLength: 0 }],
        'response-code': ['error', { maxLength: 0 }],
        'errors-in-console': ['warn', { maxLength: 0 }],
        'no-vulnerable-libraries': ['warn', { maxLength: 0 }],
        'broken-links': ['warn', { maxLength: 0 }],

        // Accessibility
        'color-contrast': ['warn', { maxLength: 0 }],
        'image-alt': ['warn', { maxLength: 0 }],
        'label': ['warn', { maxLength: 0 }],
        'link-name': ['warn', { maxLength: 0 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
