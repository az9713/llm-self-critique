'use client';

import { ValidationIssue } from '@/hooks/useValidation';

interface ValidationErrorsProps {
  issues: ValidationIssue[];
  title?: string;
  showLocation?: boolean;
  className?: string;
}

export function ValidationErrors({
  issues,
  title,
  showLocation = true,
  className = '',
}: ValidationErrorsProps) {
  if (issues.length === 0) {
    return null;
  }

  const errors = issues.filter((i) => i.severity === 'error');
  const warnings = issues.filter((i) => i.severity === 'warning');
  const infos = issues.filter((i) => i.severity === 'info');

  return (
    <div className={`space-y-2 ${className}`}>
      {title && (
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {title}
        </h4>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="space-y-1">
          {errors.map((issue, index) => (
            <div
              key={`error-${index}`}
              className="flex items-start gap-2 rounded-md bg-red-50 dark:bg-red-900/20 px-3 py-2 text-sm"
            >
              <svg
                className="h-4 w-4 flex-shrink-0 text-red-500 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <span className="text-red-700 dark:text-red-300">{issue.message}</span>
                {showLocation && issue.location && (
                  <span className="ml-2 text-xs text-red-500 dark:text-red-400">
                    [{issue.location}]
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-1">
          {warnings.map((issue, index) => (
            <div
              key={`warning-${index}`}
              className="flex items-start gap-2 rounded-md bg-yellow-50 dark:bg-yellow-900/20 px-3 py-2 text-sm"
            >
              <svg
                className="h-4 w-4 flex-shrink-0 text-yellow-500 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <span className="text-yellow-700 dark:text-yellow-300">{issue.message}</span>
                {showLocation && issue.location && (
                  <span className="ml-2 text-xs text-yellow-600 dark:text-yellow-400">
                    [{issue.location}]
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      {infos.length > 0 && (
        <div className="space-y-1">
          {infos.map((issue, index) => (
            <div
              key={`info-${index}`}
              className="flex items-start gap-2 rounded-md bg-blue-50 dark:bg-blue-900/20 px-3 py-2 text-sm"
            >
              <svg
                className="h-4 w-4 flex-shrink-0 text-blue-500 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div className="flex-1">
                <span className="text-blue-700 dark:text-blue-300">{issue.message}</span>
                {showLocation && issue.location && (
                  <span className="ml-2 text-xs text-blue-500 dark:text-blue-400">
                    [{issue.location}]
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
