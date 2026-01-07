import type { Domain, ChatSession, PlanningSession, User } from '@/types';

const API_BASE = '/api';

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

// Chat API
export const chatAPI = {
  getSession: (domainId: string) =>
    fetchAPI<ChatSession>(`/chat/${domainId}`),

  sendMessage: (domainId: string, message: string) =>
    fetchAPI<{ response: string; state: ChatSession['elicitation_state'] }>(
      `/chat/${domainId}/message`,
      {
        method: 'POST',
        body: JSON.stringify({ message }),
      }
    ),

  reset: (domainId: string) =>
    fetchAPI<ChatSession>(`/chat/${domainId}/reset`, { method: 'POST' }),
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
