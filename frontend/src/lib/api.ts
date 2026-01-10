import type { Domain, ChatSession, ChatMessage, PlanningSession, User, ElicitationState } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class APIError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// Domain API
export const domainAPI = {
  list: (workspaceId: string) =>
    fetchAPI<Domain[]>(`/domains?workspace_id=${workspaceId}`),

  get: (id: string) => fetchAPI<Domain>(`/domains/${id}`),

  create: (data: { name: string; description: string; workspace_id: string }) =>
    fetchAPI<Domain>('/domains', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Domain>) =>
    fetchAPI<Domain>(`/domains/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/domains/${id}`, { method: 'DELETE' }),
};

// Chat API - manages session-based elicitation
// Maps domain IDs to session IDs in localStorage
const getSessionId = (domainId: string): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(`chat_session_${domainId}`);
};

const setSessionId = (domainId: string, sessionId: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(`chat_session_${domainId}`, sessionId);
  }
};

const clearSessionId = (domainId: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(`chat_session_${domainId}`);
  }
};

interface BackendMessageInfo {
  role: string;
  content: string;
  timestamp: string;
}

interface BackendElicitationState {
  phase: string;
  domain_name: string | null;
  domain_description: string | null;
  objects: string[];
  predicates: string[];
  actions: Array<{ name: string; params?: string[]; preconditions?: string[]; effects?: string[] }>;
  initial_state: string[];
  goal_state: string[];
  messages: BackendMessageInfo[];
  created_at: string;
  updated_at: string;
}

interface BackendSessionInfo {
  session_id: string;
  phase: string;
  domain_name: string | null;
  domain_id: string | null;
  completion_percentage: number;
  is_complete: boolean;
  messages: BackendMessageInfo[];
  elicitation_state: BackendElicitationState | null;
}

interface BackendChatResponse {
  session_id: string;
  message: string;
  phase: string;
  completion_percentage: number;
  is_complete: boolean;
  domain_pddl: string | null;
  problem_pddl: string | null;
}

function convertMessages(messages: BackendMessageInfo[]): ChatMessage[] {
  return messages.map((m, index) => ({
    id: `msg-${index}-${m.timestamp}`,
    role: m.role as 'user' | 'assistant',
    content: m.content,
    timestamp: m.timestamp,
  }));
}

function convertElicitationState(backend: BackendElicitationState | null, fallbackPhase: string): ElicitationState {
  if (backend) {
    return {
      phase: backend.phase as ElicitationState['phase'],
      domain_name: backend.domain_name,
      objects: backend.objects || [],
      predicates: backend.predicates || [],
      actions: (backend.actions || []).map(a => typeof a === 'string' ? a : a.name),
      initial_state: backend.initial_state || [],
      goal_state: backend.goal_state || [],
    };
  }
  return {
    phase: fallbackPhase as ElicitationState['phase'],
    domain_name: null,
    objects: [],
    predicates: [],
    actions: [],
    initial_state: [],
    goal_state: [],
  };
}

export const chatAPI = {
  getSession: async (domainId: string): Promise<ChatSession> => {
    let sessionId = getSessionId(domainId);

    // If no session exists, create one linked to the domain
    if (!sessionId) {
      const newSession = await fetchAPI<BackendSessionInfo>('/chat/start', {
        method: 'POST',
        body: JSON.stringify({ domain_id: domainId }),
      });
      sessionId = newSession.session_id;
      setSessionId(domainId, sessionId);

      return {
        id: sessionId,
        domain_id: domainId,
        messages: convertMessages(newSession.messages),
        elicitation_state: convertElicitationState(newSession.elicitation_state, newSession.phase),
        created_at: new Date().toISOString(),
      };
    }

    // Try to get existing session
    try {
      const session = await fetchAPI<BackendSessionInfo>(`/chat/session/${sessionId}`);
      return {
        id: session.session_id,
        domain_id: domainId,
        messages: convertMessages(session.messages),
        elicitation_state: convertElicitationState(session.elicitation_state, session.phase),
        created_at: new Date().toISOString(),
      };
    } catch {
      // Session expired/invalid, create new one
      clearSessionId(domainId);
      return chatAPI.getSession(domainId);
    }
  },

  sendMessage: async (domainId: string, message: string): Promise<{ response: string; state: ElicitationState }> => {
    let sessionId = getSessionId(domainId);

    // Create session if needed
    if (!sessionId) {
      const session = await chatAPI.getSession(domainId);
      sessionId = session.id;
    }

    const response = await fetchAPI<BackendChatResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    return {
      response: response.message,
      state: {
        phase: response.phase as ElicitationState['phase'],
        domain_name: null,
        objects: [],
        predicates: [],
        actions: [],
        initial_state: [],
        goal_state: [],
        completion_percentage: response.completion_percentage,
        is_complete: response.is_complete,
      },
    };
  },

  reset: async (domainId: string): Promise<ChatSession> => {
    // Clear old session and create new one
    clearSessionId(domainId);
    return chatAPI.getSession(domainId);
  },

  generatePddl: async (domainId: string): Promise<{ domain_pddl: string; problem_pddl: string; saved_to_domain: boolean }> => {
    const sessionId = getSessionId(domainId);
    if (!sessionId) {
      throw new Error('No active session for this domain');
    }

    return fetchAPI<{ domain_pddl: string; problem_pddl: string; saved_to_domain: boolean }>(
      `/chat/session/${sessionId}/generate-pddl`,
      { method: 'POST' }
    );
  },
};

// Planning API
export const planningAPI = {
  list: (domainId: string) =>
    fetchAPI<PlanningSession[]>(`/planning/sessions?domain_id=${domainId}`),

  get: (id: string) => fetchAPI<PlanningSession>(`/planning/sessions/${id}`),

  create: (domainId: string) =>
    fetchAPI<PlanningSession>('/planning/sessions', {
      method: 'POST',
      body: JSON.stringify({ domain_id: domainId }),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/planning/sessions/${id}`, { method: 'DELETE' }),
};

// User API
export const userAPI = {
  me: () => fetchAPI<User>('/users/me'),
};

// WebSocket helpers
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface PlanningWSEvent {
  type: string;
  data: Record<string, unknown>;
}

export async function createPlanningWebSocket(
  sessionId: string,
  domainId: string,
  onMessage: (event: PlanningWSEvent) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): Promise<WebSocket | null> {
  // Fetch PDDL data BEFORE opening WebSocket
  let domainPddl: string;
  let problemPddl: string;

  try {
    const domain = await domainAPI.get(domainId);
    if (!domain.domain_pddl || !domain.problem_pddl) {
      onError?.(new Event('No PDDL available for this domain. Complete domain definition first.'));
      return null;
    }
    domainPddl = domain.domain_pddl;
    problemPddl = domain.problem_pddl;
  } catch (e) {
    console.error('Failed to load PDDL:', e);
    onError?.(new Event('Failed to load domain PDDL'));
    return null;
  }

  // Now open WebSocket with data ready to send
  const ws = new WebSocket(`${WS_BASE}/ws/plan/${sessionId}`);

  ws.onopen = () => {
    // Send start message immediately - data is already loaded
    ws.send(JSON.stringify({
      action: 'start',
      domain_pddl: domainPddl,
      problem_pddl: problemPddl,
    }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as PlanningWSEvent;
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError?.(error);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}
