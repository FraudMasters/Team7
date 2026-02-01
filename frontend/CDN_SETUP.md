# CDN Configuration Guide

This document explains how the CDN (Content Delivery Network) is configured for the AgentHR frontend application.

## Overview

The frontend is configured to work with two CDN options:
1. **Vercel** (Recommended) - Automatic CDN with edge deployment
2. **Cloudflare** - Manual configuration with cache invalidation
3. **AWS CloudFront** - Alternative option (configuration similar to Cloudflare)

## Local Development CDN Proxy

For testing CDN behavior locally, a Docker Compose service is included:

```bash
# Start the CDN proxy
docker-compose up cdn_proxy

# Access via CDN proxy
open http://localhost:8080
```

The local CDN proxy simulates:
- Static asset caching
- Gzip compression
- Cache control headers
- API proxying

## Production Deployment

### Vercel (Recommended)

#### Setup

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Link your project:
```bash
cd frontend
vercel link
```

3. Set environment variables in Vercel dashboard:
   - `VITE_API_URL`: Your backend API URL

4. Deploy:
```bash
vercel --prod
```

#### Features

- Automatic edge deployment
- Global CDN with 300+ PoPs
- HTTPS on all domains
- Automatic HTTP/2 and HTTP/3
- Intelligent caching with cache headers
- Built-in analytics

#### Caching Strategy

Static assets are cached aggressively:
- JavaScript/CSS bundles: 1 year, immutable
- Images/fonts: 1 year, immutable
- HTML: No cache (s-maxage for CDN only)

### Cloudflare

#### Setup

1. Add your domain to Cloudflare
2. Configure DNS to point to your origin server
3. Enable **Caching Level: Standard**
4. Configure **Browser Cache TTL: 1 year**

#### Page Rules

Create page rules for optimal caching:

```
*agenthr.com/assets/*
- Cache Level: Cache Everything
- Edge Cache TTL: 1 year
- Browser Cache TTL: 1 year

*agenthr.com/*.js
- Cache Level: Cache Everything
- Edge Cache TTL: 1 year

*agenthr.com/*.css
- Cache Level: Cache Everything
- Edge Cache TTL: 1 year

*agenthr.com/api/*
- Cache Level: Ignore (pass through)
- Bypass Cache on Cookie: true
```

#### Cache Invalidation

Automatic cache invalidation is configured in `.github/workflows/deploy.yml`:

```yaml
- name: Purge Cloudflare cache
  uses: jakejarvis/cloudflare-purge-action@master
  env:
    CLOUDFLARE_ZONE: ${{ secrets.CLOUDFLARE_ZONE_ID }}
    CLOUDFLARE_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

### AWS CloudFront

#### Setup

1. Create a CloudFront distribution
2. Set origin domain to your backend server
3. Configure cache behaviors:
   - **Path Pattern**: `/assets/*`
   - **TTL**: 31536000 seconds (1 year)
   - **Compress**: Yes
   - **Forward Cookies**: None

4. Configure default cache behavior:
   - **TTL**: 86400 seconds (1 day)
   - **Compress**: Yes

#### Cache Invalidation

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/assets/*" "/*.js" "/*.css"
```

## Build Optimizations

The `vite.config.ts` is configured for optimal CDN delivery:

### Code Splitting

```typescript
manualChunks: (id) => {
  if (id.includes('react')) return 'react-vendor';
  if (id.includes('@mui')) return 'mui-vendor';
  if (id.includes('axios')) return 'api-vendor';
  if (id.includes('react-window')) return 'ui-vendor';
}
```

Benefits:
- **react-vendor**: Rarely changes, cached for long periods
- **mui-vendor**: Updates independently from app code
- **api-vendor**: Separated for better control
- **ui-vendor**: Performance libraries grouped together

### Asset Naming

```typescript
chunkFileNames: 'assets/[name]-[hash].js'
entryFileNames: 'assets/[name]-[hash].js'
assetFileNames: (assetInfo) => {
  if (assetInfo.name?.endsWith('.css')) return 'assets/styles-[hash].[ext]';
  if (/\.(png|jpe?g|gif|svg)$/.test(assetInfo.name || '')) return 'assets/images-[hash].[ext]';
  if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || '')) return 'assets/fonts-[hash].[ext]';
}
```

- **Hash-based naming**: Content hash changes when file changes
- **Separate folders**: Better organization and cache control
- **Immutable assets**: Long cache times for hashed assets

### Minification

```typescript
terserOptions: {
  compress: {
    drop_console: true,
    drop_debugger: true,
    pure_funcs: ['console.log'],
  },
}
```

Production builds:
- Remove console.log statements
- Remove debugger statements
- Reduce bundle size

## Monitoring and Analytics

### Vercel Analytics

Automatic deployment metrics:
- Build time
- Bundle size
- Edge function invocations
- Real user monitoring (RUM)

### Cloudflare Analytics

Available in Cloudflare dashboard:
- Bandwidth saved by cache
- Cache hit rate
- Geographic distribution
- Edge response times

### Performance Monitoring

Monitor CDN performance:

```bash
# Check cache hit rate
curl -I https://agenthr.com/assets/react-vendor-abc123.js
# Look for: X-Cache: HIT

# Check CDN edge location
curl -I https://agenthr.com/
# Look for: CF-Cache-Status, CF-Ray, CF-IPCountry
```

## Troubleshooting

### Cache Not Updating

1. **Verify build hash changed:**
```bash
ls -l dist/assets/
```

2. **Clear CDN cache manually:**
   - Vercel: `vercel deploy --prebuilt` (automatic)
   - Cloudflare: Caching → Configuration → Purge Everything
   - CloudFront: Create invalidation

3. **Verify browser cache:**
   - Open DevTools → Network tab
   - Disable cache checkbox
   - Hard refresh (Cmd+Shift+R)

### Assets 404

1. Check `vercel.json` routes configuration
2. Verify build output directory
3. Check case sensitivity in filenames

### API Requests Not Working

1. Verify CORS headers on backend
2. Check API proxy configuration
3. Ensure environment variables are set

## Best Practices

1. **Use immutable caching**: Hash-based filenames never change content
2. **Version API endpoints**: `/api/v1/` for better cache control
3. **Compress responses**: Gzip/Brotli enabled by default
4. **Monitor cache hit rates**: Target > 90% for static assets
5. **Test edge cases**: International users, slow networks
6. **Set proper TTLs**: Long for assets, short for HTML
7. **Use CDN for images**: Optimize and serve from CDN
8. **Prefetch critical assets**: Use `<link rel="preload">`

## Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| First Contentful Paint | < 1.5s | TBD |
| Largest Contentful Paint | < 2.5s | TBD |
| Time to Interactive | < 3.5s | TBD |
| Cumulative Layout Shift | < 0.1 | TBD |
| Cache Hit Rate | > 90% | TBD |

Run Lighthouse CI to measure:
```bash
npm run lighthouse
```

## Additional Resources

- [Vercel Caching Documentation](https://vercel.com/docs/concepts/edge-network/caching)
- [Cloudflare Caching Tutorial](https://developers.cloudflare.com/cache/)
- [AWS CloudFront Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/)
- [Web.dev Performance Guide](https://web.dev/fast/)
