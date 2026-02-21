# Testing Documentation

## Overview

This document describes the testing approach for the Scriptum v2.1 frontend.

## Test Files

### Manual Test Files

Located in `src/`:

1. **test-utils.ts** - Tests for utility functions
2. **test-errors.ts** - Tests for error classes

These files can be used for manual verification of functionality.

## Automated Tests

### TypeScript Compilation

Verify that all TypeScript code compiles without errors:

```bash
npx tsc --noEmit
```

Expected output: No errors (empty output)

## API Testing

### Backend Health Check

Test the backend API is running:

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "Scriptum Sync API",
  "version": "2.1-refactored",
  "architecture": "service-oriented"
}
```

### Frontend Health Check

Test the frontend dev server:

```bash
curl http://localhost:5173
```

Expected: HTML page with React root element

## Manual Testing Checklist

### 1. Dashboard Page (/)

- [ ] Page loads without errors
- [ ] Video file upload works
- [ ] File preview displays correctly
- [ ] "Analyze Video" button works
- [ ] Movie recognition triggers automatically
- [ ] MovieCard displays with poster and info
- [ ] VideoInfo shows analysis results
- [ ] Quick action buttons navigate correctly

### 2. Subtitle Search Page (/subtitles/search)

- [ ] Page loads without errors
- [ ] Search form accepts input
- [ ] Language dropdown works
- [ ] Search button triggers API call
- [ ] Results display in table
- [ ] Download buttons work
- [ ] Error messages display correctly
- [ ] Back to Dashboard navigation works

### 3. Translation Page (/translate)

- [ ] Page loads without errors
- [ ] Subtitle file upload works
- [ ] Source/target language selection works
- [ ] Tone selection (formal/casual/technical) works
- [ ] Preserve formatting checkbox works
- [ ] Validation prevents same source/target language
- [ ] Translate button works
- [ ] Progress bar displays during translation
- [ ] Download translated file works
- [ ] "Translate Another" button resets form

### 4. Sync Page (/sync)

- [ ] Page loads without errors
- [ ] Video file upload works
- [ ] Subtitle file upload works
- [ ] Whisper model selection works
- [ ] Language selection works
- [ ] Sync button disabled until both files uploaded
- [ ] Progress bar with steps displays
- [ ] Download synced file works
- [ ] "Sync Another" button resets form

### 5. Error Handling

- [ ] Network errors display user-friendly messages
- [ ] API errors show proper error alerts
- [ ] File validation works (size/type)
- [ ] Timeout errors handled gracefully
- [ ] 404 page displays for invalid routes

### 6. Navigation

- [ ] All navigation buttons work
- [ ] Back buttons return to correct pages
- [ ] Browser back/forward buttons work
- [ ] Direct URL access works for all routes

## Browser Testing

Recommended browsers to test:

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Console Errors

Check browser DevTools console for:

- No JavaScript errors
- No TypeScript compilation errors
- No React warnings
- No failed network requests (unless intentional)

## Performance Testing

### Lighthouse Audit

Run Lighthouse in Chrome DevTools:

1. Open DevTools (F12)
2. Go to Lighthouse tab
3. Run audit for Performance, Accessibility, Best Practices

Expected scores:
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+

### Network Throttling

Test with throttled network:

1. Open DevTools Network tab
2. Set throttling to "Slow 3G"
3. Verify loading states work correctly
4. Verify timeouts handle gracefully

## Component Testing

### Button Component

- [ ] All variants render (primary, secondary, danger, ghost)
- [ ] All sizes work (sm, md, lg)
- [ ] Loading state displays spinner
- [ ] Disabled state works
- [ ] onClick handler fires

### Card Component

- [ ] All variants render (default, outlined, elevated)
- [ ] Composition works (CardHeader, CardTitle, CardContent)
- [ ] Padding options work

### Alert Component

- [ ] All variants display (info, success, warning, error)
- [ ] Icons show correctly
- [ ] Close button works
- [ ] onClose handler fires

### FileUploader Component

- [ ] Drag and drop works
- [ ] Click to browse works
- [ ] File validation works
- [ ] Preview displays correctly
- [ ] Remove button works

## Error Class Testing

### ApiError

```typescript
const error = new ApiError('Not found', 404, '/api/test');
// Should have: message, statusCode, endpoint properties
```

### NetworkError

```typescript
const error = new NetworkError('Timeout', '/api/test');
// Should extend ApiError, indicate network issue
```

### ValidationError

```typescript
const error = new ValidationError('Invalid email', 'email', 'test@');
// Should have: message, field, value properties
```

### getErrorMessage()

```typescript
getErrorMessage(new ApiError('Error', 404));
// Should return: "Resource not found"

getErrorMessage(new ApiError('Error', 500));
// Should return: "Server error. Please try again later"
```

## Utility Function Testing

### formatBytes()

```typescript
formatBytes(1024) // "1 KB"
formatBytes(1048576) // "1 MB"
formatBytes(1073741824) // "1 GB"
```

### formatDuration()

```typescript
formatDuration(90) // "00:01:30"
formatDuration(3661) // "01:01:01"
```

### formatBitrate()

```typescript
formatBitrate(1000000) // "1 Mbps"
formatBitrate(5000000) // "5 Mbps"
```

## Regression Testing

After any code changes, verify:

1. TypeScript compilation: `npx tsc --noEmit`
2. Dev server starts: `npm run dev`
3. All pages load without errors
4. All navigation works
5. Backend API responds correctly

## Known Issues

None at this time.

## Future Testing Improvements

1. Add Jest for unit testing
2. Add React Testing Library for component tests
3. Add Cypress/Playwright for E2E tests
4. Add test coverage reporting
5. Add CI/CD pipeline tests
