'use client';

import { useState, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';
import type { ChatMessage, ElicitationState } from '@/types';

export interface ChatWebSocketState {
  isConnected: boolean;
  isGenerating: boolean;
  messages: ChatMessage[];
  elicitationState: ElicitationState | null;
  sessionId: string | null;
  error: string | null;
}

export interface UseChatWebSocketOptions {
  domainId: string;
  onMessage?: (message: ChatMessage) => void;
  onStateChange?: (state: ElicitationState) => void;
}

export function useChatWebSocket({
  domainId,
  onMessage,
  onStateChange,
}: UseChatWebSocketOptions) {
  const [state, setState] = useState<ChatWebSocketState>({
    isConnected: false,
    isGenerating: false,
    messages: [],
    elicitationState: null,
    sessionId: null,
    error: null,
  });

  const handleWSMessage = useCallback(
    (message: WebSocketMessage) => {
      const { type, data } = message;

      switch (type) {
        case 'connected':
          setState((prev) => ({
            ...prev,
            isConnected: true,
            sessionId: data.session_id as string,
            elicitationState: data.state as ElicitationState,
          }));
          if (data.state) {
            onStateChange?.(data.state as ElicitationState);
          }
          break;

        case 'message':
          const chatMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: data.role as 'user' | 'assistant',
            content: data.content as string,
            timestamp: new Date().toISOString(),
          };
          setState((prev) => ({
            ...prev,
            messages: [...prev.messages, chatMessage],
            isGenerating: false,
          }));
          onMessage?.(chatMessage);
          break;

        case 'message_received':
          // User message was received
          const userMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content: data.content as string,
            timestamp: new Date().toISOString(),
          };
          setState((prev) => ({
            ...prev,
            messages: [...prev.messages, userMessage],
          }));
          break;

        case 'generating':
          setState((prev) => ({ ...prev, isGenerating: true }));
          break;

        case 'state_updated':
          const newState = data as unknown as ElicitationState;
          setState((prev) => ({
            ...prev,
            elicitationState: newState,
          }));
          onStateChange?.(newState);
          break;

        case 'state_reset':
          setState((prev) => ({
            ...prev,
            messages: [],
            elicitationState: data as unknown as ElicitationState,
          }));
          break;

        case 'error':
          setState((prev) => ({
            ...prev,
            error: data.message as string,
            isGenerating: false,
          }));
          break;
      }
    },
    [onMessage, onStateChange]
  );

  const {
    status: wsStatus,
    send,
    connect,
    disconnect,
    reconnectAttempts,
  } = useWebSocket({
    url: `/api/ws/chat/${domainId}`,
    onMessage: handleWSMessage,
    onOpen: () => {
      setState((prev) => ({ ...prev, isConnected: true, error: null }));
    },
    onClose: () => {
      setState((prev) => ({ ...prev, isConnected: false }));
    },
    onError: () => {
      setState((prev) => ({
        ...prev,
        error: 'Connection error',
        isConnected: false,
      }));
    },
  });

  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim()) return;

      send({
        type: 'message',
        content: content.trim(),
      });
    },
    [send]
  );

  const resetChat = useCallback(() => {
    send({ type: 'reset' });
  }, [send]);

  const getState = useCallback(() => {
    send({ type: 'get_state' });
  }, [send]);

  return {
    ...state,
    wsStatus,
    reconnectAttempts,
    sendMessage,
    resetChat,
    getState,
    connect,
    disconnect,
  };
}
