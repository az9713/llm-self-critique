import type { Domain, ChatSession, PlanningSession, User } from '@/types';

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

interface BackendSessionInfo {
  session_id: string;
  phase: string;
  domain_name: string | null;
  completion_percentage: number;
  is_complete: boolean;
}

interface BackendChatResponse {
  session_id: string;
  message: string;
  phase: string;
  completion_percentage: number;
  is_complete: boolean;
}

export const chatAPI = {
  getSession: async (domainId: string): Promise<ChatSession> => {
    let sessionId = getSessionId(domainId);

    // If no session exists, create one
    if (!sessionId) {
      const newSession = await fetchAPI<BackendSessionInfo>('/chat/start', {
        method: 'POST',
      });
      sessionId = newSession.session_id;
      setSessionId(domainId, sessionId);

      return {
        id: sessionId,
        domain_id: domainId,
        messages: [],
        elicitation_state: {
          phase: newSession.phase,
          domain_name: newSession.domain_name,
          completion_percentage: newSession.completion_percentage,
          is_complete: newSession.is_complete,
        },
      };
    }

    // Try to get existing session
    try {
      const session = await fetchAPI<BackendSessionInfo>(`/chat/session/${sessionId}`);
      return {
        id: session.session_id,
        domain_id: domainId,
        messages: [], // Backend doesn't persist messages currently
        elicitation_state: {
          phase: session.phase,
          domain_name: session.domain_name,
          completion_percentage: session.completion_percentage,
          is_complete: session.is_complete,
        },
      };
    } catch {
      // Session expired/invalid, create new one
      clearSessionId(domainId);
      return chatAPI.getSession(domainId);
    }
  },

  sendMessage: async (domainId: string, message: string): Promise<{ response: string; state: ChatSession['elicitation_state'] }> => {
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
        phase: response.phase,
        domain_name: null,
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

  generate: (sessionId: string) =>
    fetchAPI<PlanningSession>(`/planning/sessions/${sessionId}/generate`, {
      method: 'POST',
    }),

  getIterations: (sessionId: string) =>
    fetchAPI<{ iterations: unknown[] }>(`/planning/sessions/${sessionId}/iterations`),
};

// WebSocket connection for streaming
export function createPlanningWebSocket(
  sessionId: string,
  onMessage: (event: { type: string; data: Record<string, unknown> }) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(
    `${protocol}//${window.location.host}/api/ws/planning/${sessionId}`
  );

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.error('Failed to parse WebSocket message:', event.data);
    }
  };

  ws.onerror = (event) => {
    console.error('WebSocket error:', event);
    onError?.(event);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}

export { APIError };
