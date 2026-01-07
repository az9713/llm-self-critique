/**
 * PDDL Validation API client
 */

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  message: string;
  location: string | null;
}

export interface ValidationResponse {
  valid: boolean;
  issues: ValidationIssue[];
  error_count: number;
  warning_count: number;
}

export interface FullValidationResponse {
  domain_valid: boolean;
  problem_valid: boolean;
  overall_valid: boolean;
  domain_issues: ValidationIssue[];
  problem_issues: ValidationIssue[];
  total_errors: number;
  total_warnings: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function validateDomain(domainPddl: string): Promise<ValidationResponse> {
  const response = await fetch(`${API_BASE}/api/validation/domain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ domain_pddl: domainPddl }),
  });

  if (!response.ok) {
    throw new Error(`Validation failed: ${response.statusText}`);
  }

  return response.json();
}

export async function validateProblem(
  problemPddl: string,
  domainPddl?: string
): Promise<ValidationResponse> {
  const response = await fetch(`${API_BASE}/api/validation/problem`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      problem_pddl: problemPddl,
      domain_pddl: domainPddl,
    }),
  });

  if (!response.ok) {
    throw new Error(`Validation failed: ${response.statusText}`);
  }

  return response.json();
}

export async function validateFull(
  domainPddl: string,
  problemPddl: string
): Promise<FullValidationResponse> {
  const response = await fetch(`${API_BASE}/api/validation/full`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      domain_pddl: domainPddl,
      problem_pddl: problemPddl,
    }),
  });

  if (!response.ok) {
    throw new Error(`Validation failed: ${response.statusText}`);
  }

  return response.json();
}
