'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { chatAPI } from '@/lib/api';
import type { ChatMessage as ChatMessageType, ElicitationState } from '@/types';
import { Loader2, RotateCcw } from 'lucide-react';

interface ElicitationChatProps {
  domainId: string;
  onStateChange?: (state: ElicitationState) => void;
}

export function ElicitationChat({ domainId, onStateChange }: ElicitationChatProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [state, setState] = useState<ElicitationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSession();
  }, [domainId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSession = async () => {
    setLoading(true);
    try {
      const session = await chatAPI.getSession(domainId);
      setMessages(session.messages);
      setState(session.elicitation_state);
      onStateChange?.(session.elicitation_state);
    } catch (error) {
      console.error('Failed to load chat session:', error);
      // Start with empty state if session doesn't exist
      setMessages([]);
      setState(null);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (content: string) => {
    // Optimistically add user message
    const userMessage: ChatMessageType = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const { response, state: newState } = await chatAPI.sendMessage(
        domainId,
        content
      );

      // Add assistant response
      const assistantMessage: ChatMessageType = {
        id: `resp-${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setState(newState);
      onStateChange?.(newState);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      const errorMessage: ChatMessageType = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleReset = async () => {
    try {
      const session = await chatAPI.reset(domainId);
      setMessages(session.messages);
      setState(session.elicitation_state);
      onStateChange?.(session.elicitation_state);
    } catch (error) {
      console.error('Failed to reset session:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isComplete = state?.phase === 'complete';

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div>
          <h2 className="font-semibold">Domain Definition</h2>
          <p className="text-sm text-muted-foreground">
            {state?.phase === 'complete'
              ? 'Domain definition complete'
              : `Current phase: ${state?.phase || 'intro'}`}
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-3 py-1.5 text-sm border rounded-md hover:bg-muted transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
          Reset
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <p className="text-muted-foreground mb-2">
              No messages yet
            </p>
            <p className="text-sm text-muted-foreground">
              Start by describing your planning domain. The assistant will guide
              you through defining objects, actions, and goals.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={sending || isComplete}
        placeholder={
          isComplete
            ? 'Domain definition is complete'
            : sending
            ? 'Sending...'
            : 'Describe your planning domain...'
        }
      />
    </div>
  );
}
