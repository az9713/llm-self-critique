'use client';

import { ValidationResponse, FullValidationResponse } from '@/hooks/useValidation';

interface ValidationSummaryProps {
  result: ValidationResponse | FullValidationResponse | null;
  isValidating?: boolean;
  className?: string;
}

function isFullValidation(
  result: ValidationResponse | FullValidationResponse
): result is FullValidationResponse {
  return 'overall_valid' in result;
}

export function ValidationSummary({
  result,
  isValidating = false,
  className = '',
}: ValidationSummaryProps) {
  if (isValidating) {
    return (
      <div className={`flex items-center gap-2 text-sm text-gray-500 ${className}`}>
        <svg
          className="h-4 w-4 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span>Validating...</span>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const isValid = isFullValidation(result) ? result.overall_valid : result.valid;
  const errorCount = isFullValidation(result)
    ? result.total_errors
    : result.error_count;
  const warningCount = isFullValidation(result)
    ? result.total_warnings
    : result.warning_count;

  return (
    <div className={`flex items-center gap-3 text-sm ${className}`}>
      {/* Valid/Invalid badge */}
      {isValid ? (
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 dark:bg-green-900/30 px-2.5 py-0.5 text-green-700 dark:text-green-300">
          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          Valid
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 rounded-full bg-red-100 dark:bg-red-900/30 px-2.5 py-0.5 text-red-700 dark:text-red-300">
          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          Invalid
        </span>
      )}

      {/* Error count */}
      {errorCount > 0 && (
        <span className="text-red-600 dark:text-red-400">
          {errorCount} error{errorCount !== 1 ? 's' : ''}
        </span>
      )}

      {/* Warning count */}
      {warningCount > 0 && (
        <span className="text-yellow-600 dark:text-yellow-400">
          {warningCount} warning{warningCount !== 1 ? 's' : ''}
        </span>
      )}

      {/* Full validation specific info */}
      {isFullValidation(result) && (
        <span className="text-gray-500 dark:text-gray-400">
          (Domain: {result.domain_valid ? 'OK' : 'errors'}, Problem:{' '}
          {result.problem_valid ? 'OK' : 'errors'})
        </span>
      )}
    </div>
  );
}
