/**
 * Manual Test Suite for Utility Functions
 * Run with: node --loader ts-node/esm test-utils.ts
 */

import {
  formatBytes,
  formatDuration,
  formatBitrate,
  getFileExtension,
  getFileNameWithoutExtension,
  getResolutionName,
  formatDate,
  truncate,
  cn,
  clamp,
} from './lib/utils';

console.log('🧪 Testing Utility Functions\n');

// Test formatBytes
console.log('formatBytes tests:');
console.log('  0 bytes:', formatBytes(0)); // "0 Bytes"
console.log('  1024 bytes:', formatBytes(1024)); // "1 KB"
console.log('  1048576 bytes:', formatBytes(1048576)); // "1 MB"
console.log('  1073741824 bytes:', formatBytes(1073741824)); // "1 GB"

// Test formatDuration
console.log('\nformatDuration tests:');
console.log('  90 seconds:', formatDuration(90)); // "00:01:30"
console.log('  3661 seconds:', formatDuration(3661)); // "01:01:01"
console.log('  0 seconds:', formatDuration(0)); // "00:00:00"

// Test formatBitrate
console.log('\nformatBitrate tests:');
console.log('  1000 bps:', formatBitrate(1000)); // "1 Kbps"
console.log('  1000000 bps:', formatBitrate(1000000)); // "1 Mbps"
console.log('  5000000 bps:', formatBitrate(5000000)); // "5 Mbps"

// Test file name utilities
console.log('\nFile name utilities:');
const filename = 'movie.mkv';
console.log('  Extension of "movie.mkv":', getFileExtension(filename)); // ".mkv"
console.log('  Name without ext:', getFileNameWithoutExtension(filename)); // "movie"

// Test resolution names
console.log('\nResolution names:');
console.log('  1920x1080:', getResolutionName(1920, 1080)); // "Full HD"
console.log('  3840x2160:', getResolutionName(3840, 2160)); // "4K"
console.log('  1280x720:', getResolutionName(1280, 720)); // "HD"

// Test date formatting
console.log('\nDate formatting:');
const testDate = new Date('2024-01-15');
console.log('  2024-01-15:', formatDate(testDate));

// Test truncate
console.log('\nTruncate tests:');
console.log('  Short string:', truncate('Hello', 10)); // "Hello"
console.log('  Long string:', truncate('This is a very long string', 15)); // "This is a ve..."

// Test className utility
console.log('\nClassName utility:');
console.log('  cn("a", "b", false, "c"):', cn('a', 'b', false, 'c')); // "a b c"
console.log('  cn("btn", true && "active"):', cn('btn', true && 'active')); // "btn active"

// Test clamp
console.log('\nClamp tests:');
console.log('  clamp(5, 0, 10):', clamp(5, 0, 10)); // 5
console.log('  clamp(-5, 0, 10):', clamp(-5, 0, 10)); // 0
console.log('  clamp(15, 0, 10):', clamp(15, 0, 10)); // 10

console.log('\n✅ All utility tests completed!');
