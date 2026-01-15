/**
 * Security utilities for sanitizing user input
 */

/**
 * Sanitizes a reference ID to prevent path traversal attacks.
 * Only allows alphanumeric characters, hyphens, and underscores.
 * 
 * @param ref - The reference ID from user input
 * @returns Sanitized reference ID, or null if invalid
 */
export function sanitizeRef(ref: string | undefined | null): string | null {
  if (!ref || typeof ref !== 'string') {
    return null;
  }

  // Remove any path traversal sequences and non-alphanumeric chars (except - and _)
  const sanitized = ref.replace(/[^a-zA-Z0-9_-]/g, '');

  // Ensure it's not empty after sanitization and has reasonable length
  if (sanitized.length === 0 || sanitized.length > 50) {
    return null;
  }

  // Explicitly reject path traversal patterns
  if (sanitized.includes('..') || sanitized.includes('/') || sanitized.includes('\\')) {
    return null;
  }

  return sanitized;
}

/**
 * Sanitizes a filename to prevent path traversal attacks.
 * Only allows safe filename characters.
 * 
 * @param filename - The filename from user input
 * @returns Sanitized filename, or null if invalid
 */
export function sanitizeFilename(filename: string | undefined | null): string | null {
  if (!filename || typeof filename !== 'string') {
    return null;
  }

  // Remove path components - only keep the basename
  const basename = filename.split(/[/\\]/).pop() || '';

  // Remove any remaining dangerous characters, keep alphanumeric, dots, hyphens, underscores
  const sanitized = basename.replace(/[^a-zA-Z0-9._-]/g, '');

  // Ensure it's not empty, not a hidden file, and has reasonable length
  if (sanitized.length === 0 || sanitized.startsWith('.') || sanitized.length > 255) {
    return null;
  }

  // Reject files with multiple dots that might be trying to hide extensions
  const dotCount = (sanitized.match(/\./g) || []).length;
  if (dotCount > 2) {
    return null;
  }

  return sanitized;
}

/**
 * Sanitizes a file format extension to ensure it's an allowed type.
 * 
 * @param format - The file format extension
 * @param allowedFormats - Array of allowed format extensions
 * @returns Sanitized format, or null if invalid
 */
export function sanitizeFormat(
  format: string | undefined | null,
  allowedFormats: string[] = ['txt', 'json', 'png', 'jpeg', 'svg', 'pdf']
): string | null {
  if (!format || typeof format !== 'string') {
    return null;
  }

  const sanitized = format.toLowerCase().replace(/[^a-z]/g, '');

  if (!allowedFormats.includes(sanitized)) {
    return null;
  }

  return sanitized;
}

/**
 * Validates that a reference matches the expected format (numeric).
 * 
 * @param ref - The reference ID to validate
 * @returns true if valid, false otherwise
 */
export function isValidReference(ref: string | undefined | null): boolean {
  if (!ref || typeof ref !== 'string') {
    return false;
  }

  // Reference should be numeric and within expected range
  const numericRef = parseInt(ref, 10);
  return !isNaN(numericRef) && numericRef >= 10000 && numericRef <= 99999;
}
