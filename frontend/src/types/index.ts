// User types
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

// Domain types
export interface Domain {
  id: string;
  name: string;
  description: string;
  domain_pddl: string | null;
  problem_pddl: string | null;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  domain_id: string;
  messages: ChatMessage[];
  elicitation_state: ElicitationState;
  created_at: string;
}

export interface ElicitationState {
  phase: ElicitationPhase;
  domain_name: string | null;
  objects: string[];
  predicates: string[];
  actions: string[];
  initial_state: string[];
  goal_state: string[];
}

export type ElicitationPhase =
  | 'intro'
  | 'objects'
  | 'predicates'
  | 'actions'
  | 'initial'
  | 'goal'
  | 'review'
  | 'complete';

// Planning types
export interface PlanningSession {
  id: string;
  domain_id: string;
  status: SessionStatus;
  current_plan: string | null;
  final_verdict: Verdict | null;
  iteration_count: number;
  created_at: string;
  updated_at: string;
}

export type SessionStatus =
  | 'eliciting'
  | 'planning'
  | 'critiquing'
  | 'complete'
  | 'failed';

export type Verdict = 'correct' | 'wrong' | 'goal_not_reached';

export interface PlanIteration {
  id: string;
  session_id: string;
  iteration_number: number;
  plan: string;
  critique_results: CritiqueResult[];
  majority_verdict: Verdict;
  confidence: number;
  created_at: string;
}

export interface CritiqueResult {
  verdict: Verdict;
  step_traces: string[];
  error_reason: string | null;
}

export interface VoteResult {
  majority_verdict: Verdict;
  breakdown: Record<Verdict, number>;
  confidence: number;
  is_low_confidence: boolean;
}

// WebSocket event types
export type WSEventType =
  | 'started'
  | 'iteration_started'
  | 'generating_plan'
  | 'plan_generated'
  | 'critiquing'
  | 'critique_sample'
  | 'critique_complete'
  | 'iteration_complete'
  | 'completed'
  | 'error';

export interface WSEvent {
  type: WSEventType;
  data: Record<string, unknown>;
}
