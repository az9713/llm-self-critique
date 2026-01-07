'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  validateDomain,
  validateProblem,
  validateFull,
  ValidationResponse,
  FullValidationResponse,
  ValidationIssue,
} from '@/lib/validation-api';

export type { ValidationIssue, ValidationResponse, FullValidationResponse };

export interface UseValidationOptions {
  debounceMs?: number;
  validateOnChange?: boolean;
}

export interface UseValidationReturn {
  isValidating: boolean;
  result: ValidationResponse | null;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  validate: () => Promise<ValidationResponse | null>;
  clearResult: () => void;
}

export interface UseFullValidationReturn {
  isValidating: boolean;
  result: FullValidationResponse | null;
  domainErrors: ValidationIssue[];
  domainWarnings: ValidationIssue[];
  problemErrors: ValidationIssue[];
  problemWarnings: ValidationIssue[];
  validate: () => Promise<FullValidationResponse | null>;
  clearResult: () => void;
}

export function useDomainValidation(
  domainPddl: string,
  options: UseValidationOptions = {}
): UseValidationReturn {
  const { debounceMs = 500, validateOnChange = false } = options;

  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<ValidationResponse | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const validate = useCallback(async (): Promise<ValidationResponse | null> => {
    if (!domainPddl.trim()) {
      setResult(null);
      return null;
    }

    setIsValidating(true);
    try {
      const validationResult = await validateDomain(domainPddl);
      setResult(validationResult);
      return validationResult;
    } catch (error) {
      console.error('Domain validation error:', error);
      return null;
    } finally {
      setIsValidating(false);
    }
  }, [domainPddl]);

  const clearResult = useCallback(() => {
    setResult(null);
  }, []);

  // Auto-validate on change with debounce
  useEffect(() => {
    if (!validateOnChange) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (domainPddl.trim()) {
      debounceRef.current = setTimeout(() => {
        validate();
      }, debounceMs);
    } else {
      setResult(null);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [domainPddl, debounceMs, validateOnChange, validate]);

  const errors = result?.issues.filter((i) => i.severity === 'error') || [];
  const warnings = result?.issues.filter((i) => i.severity === 'warning') || [];

  return {
    isValidating,
    result,
    errors,
    warnings,
    validate,
    clearResult,
  };
}

export function useProblemValidation(
  problemPddl: string,
  domainPddl?: string,
  options: UseValidationOptions = {}
): UseValidationReturn {
  const { debounceMs = 500, validateOnChange = false } = options;

  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<ValidationResponse | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const validate = useCallback(async (): Promise<ValidationResponse | null> => {
    if (!problemPddl.trim()) {
      setResult(null);
      return null;
    }

    setIsValidating(true);
    try {
      const validationResult = await validateProblem(problemPddl, domainPddl);
      setResult(validationResult);
      return validationResult;
    } catch (error) {
      console.error('Problem validation error:', error);
      return null;
    } finally {
      setIsValidating(false);
    }
  }, [problemPddl, domainPddl]);

  const clearResult = useCallback(() => {
    setResult(null);
  }, []);

  // Auto-validate on change with debounce
  useEffect(() => {
    if (!validateOnChange) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (problemPddl.trim()) {
      debounceRef.current = setTimeout(() => {
        validate();
      }, debounceMs);
    } else {
      setResult(null);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [problemPddl, domainPddl, debounceMs, validateOnChange, validate]);

  const errors = result?.issues.filter((i) => i.severity === 'error') || [];
  const warnings = result?.issues.filter((i) => i.severity === 'warning') || [];

  return {
    isValidating,
    result,
    errors,
    warnings,
    validate,
    clearResult,
  };
}

export function useFullValidation(
  domainPddl: string,
  problemPddl: string,
  options: UseValidationOptions = {}
): UseFullValidationReturn {
  const { debounceMs = 500, validateOnChange = false } = options;

  const [isValidating, setIsValidating] = useState(false);
  const [result, setResult] = useState<FullValidationResponse | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const validate = useCallback(async (): Promise<FullValidationResponse | null> => {
    if (!domainPddl.trim() || !problemPddl.trim()) {
      setResult(null);
      return null;
    }

    setIsValidating(true);
    try {
      const validationResult = await validateFull(domainPddl, problemPddl);
      setResult(validationResult);
      return validationResult;
    } catch (error) {
      console.error('Full validation error:', error);
      return null;
    } finally {
      setIsValidating(false);
    }
  }, [domainPddl, problemPddl]);

  const clearResult = useCallback(() => {
    setResult(null);
  }, []);

  // Auto-validate on change with debounce
  useEffect(() => {
    if (!validateOnChange) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (domainPddl.trim() && problemPddl.trim()) {
      debounceRef.current = setTimeout(() => {
        validate();
      }, debounceMs);
    } else {
      setResult(null);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [domainPddl, problemPddl, debounceMs, validateOnChange, validate]);

  const domainErrors = result?.domain_issues.filter((i) => i.severity === 'error') || [];
  const domainWarnings = result?.domain_issues.filter((i) => i.severity === 'warning') || [];
  const problemErrors = result?.problem_issues.filter((i) => i.severity === 'error') || [];
  const problemWarnings = result?.problem_issues.filter((i) => i.severity === 'warning') || [];

  return {
    isValidating,
    result,
    domainErrors,
    domainWarnings,
    problemErrors,
    problemWarnings,
    validate,
    clearResult,
  };
}
