/**
 * Manual Test Suite for Error Classes
 */

import {
  ApiError,
  NetworkError,
  ValidationError,
  FileProcessingError,
  getErrorMessage,
} from './lib/errors';

console.log('🧪 Testing Error Classes\n');

// Test ApiError
console.log('ApiError tests:');
const apiError = new ApiError('Not found', 404, '/api/users');
console.log('  Message:', apiError.message); // "Not found"
console.log('  Status Code:', apiError.statusCode); // 404
console.log('  Endpoint:', apiError.endpoint); // "/api/users"
console.log('  Name:', apiError.name); // "ApiError"

// Test NetworkError
console.log('\nNetworkError tests:');
const networkError = new NetworkError('Connection timeout', '/api/data');
console.log('  Message:', networkError.message); // "Connection timeout"
console.log('  Endpoint:', networkError.endpoint); // "/api/data"
console.log('  Name:', networkError.name); // "NetworkError"

// Test ValidationError
console.log('\nValidationError tests:');
const validationError = new ValidationError('Invalid email', 'email', 'test@');
console.log('  Message:', validationError.message); // "Invalid email"
console.log('  Field:', validationError.field); // "email"
console.log('  Value:', validationError.value); // "test@"
console.log('  Name:', validationError.name); // "ValidationError"

// Test FileProcessingError
console.log('\nFileProcessingError tests:');
const fileError = new FileProcessingError(
  'Invalid format',
  'video.mkv',
  'conversion'
);
console.log('  Message:', fileError.message); // "Invalid format"
console.log('  Filename:', fileError.filename); // "video.mkv"
console.log('  Operation:', fileError.operation); // "conversion"
console.log('  Name:', fileError.name); // "FileProcessingError"

// Test getErrorMessage
console.log('\ngetErrorMessage tests:');
const apiErr = new ApiError('Resource not found', 404);
console.log('  404 ApiError:', getErrorMessage(apiErr)); // "Resource not found"

const serverErr = new ApiError('Internal error', 500);
console.log('  500 ApiError:', getErrorMessage(serverErr)); // "Server error. Please try again later"

const netErr = new NetworkError('Timeout');
console.log('  NetworkError:', getErrorMessage(netErr)); // "Network connection failed..."

const stdErr = new Error('Generic error');
console.log('  Standard Error:', getErrorMessage(stdErr)); // "Generic error"

const unknownErr = 'String error';
console.log('  Unknown error:', getErrorMessage(unknownErr)); // "An unexpected error occurred"

console.log('\n✅ All error tests completed!');
