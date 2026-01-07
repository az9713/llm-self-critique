'use client';

import { useState, useCallback, useEffect } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';
import type { Verdict, CritiqueResult } from '@/types';

export interface PlanningIteration {
  number: number;
  plan: string;
  verdict: Verdict | null;
  confidence: number;
  errorReason: string | null;
  critiqueResults: CritiqueResult[];
}

export interface PlanningState {
  isRunning: boolean;
  status: 'idle' | 'planning' | 'critiquing' | 'complete' | 'failed';
  currentIteration: number;
  iterations: PlanningIteration[];
  finalPlan: string | null;
  finalVerdict: Verdict | null;
  error: string | null;
}

export interface UsePlanningWebSocketOptions {
  sessionId: string;
  onComplete?: (plan: string, verdict: Verdict) => void;
  onError?: (error: string) => void;
}

export function usePlanningWebSocket({
  sessionId,
  onComplete,
  onError,
}: UsePlanningWebSocketOptions) {
  const [state, setState] = useState<PlanningState>({
    isRunning: false,
    status: 'idle',
    currentIteration: 0,
    iterations: [],
    finalPlan: null,
    finalVerdict: null,
    error: null,
  });

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      const { type, data } = message;

      switch (type) {
        case 'started':
          setState((prev) => ({
            ...prev,
            isRunning: true,
            status: 'planning',
            iterations: [],
            error: null,
          }));
          break;

        case 'iteration_started':
          setState((prev) => ({
            ...prev,
            currentIteration: data.iteration as number,
            iterations: [
              ...prev.iterations,
              {
                number: data.iteration as number,
                plan: '',
                verdict: null,
                confidence: 0,
                errorReason: null,
                critiqueResults: [],
              },
            ],
          }));
          break;

        case 'generating_plan':
          setState((prev) => ({ ...prev, status: 'planning' }));
          break;

        case 'plan_generated':
          setState((prev) => ({
            ...prev,
            iterations: prev.iterations.map((iter) =>
              iter.number === prev.currentIteration
                ? { ...iter, plan: data.plan as string }
                : iter
            ),
          }));
          break;

        case 'critiquing':
          setState((prev) => ({ ...prev, status: 'critiquing' }));
          break;

        case 'critique_sample':
          setState((prev) => ({
            ...prev,
            iterations: prev.iterations.map((iter) =>
              iter.number === prev.currentIteration
                ? {
                    ...iter,
                    critiqueResults: [
                      ...iter.critiqueResults,
                      {
                        verdict: data.verdict as Verdict,
                        step_traces: [],
                        error_reason: null,
                      },
                    ],
                  }
                : iter
            ),
          }));
          break;

        case 'critique_complete':
          setState((prev) => ({
            ...prev,
            iterations: prev.iterations.map((iter) =>
              iter.number === prev.currentIteration
                ? {
                    ...iter,
                    verdict: data.majority_verdict as Verdict,
                    confidence: data.confidence as number,
                    errorReason: (data.best_error_reason as string) || null,
                  }
                : iter
            ),
          }));
          break;

        case 'iteration_complete':
          // Plan was invalid, will retry
          setState((prev) => ({ ...prev, status: 'planning' }));
          break;

        case 'completed':
          setState((prev) => ({
            ...prev,
            isRunning: false,
            status: 'complete',
            finalPlan: data.plan as string,
            finalVerdict: data.verdict as Verdict,
          }));
          onComplete?.(data.plan as string, data.verdict as Verdict);
          break;

        case 'error':
          setState((prev) => ({
            ...prev,
            isRunning: false,
            status: 'failed',
            error: data.message as string,
          }));
          onError?.(data.message as string);
          break;
      }
    },
    [onComplete, onError]
  );

  const { status: wsStatus, send, connect, disconnect } = useWebSocket({
    url: `/api/ws/plan/${sessionId}`,
    onMessage: handleMessage,
    autoConnect: false,
  });

  const startPlanning = useCallback(
    (domainPddl: string, problemPddl: string, options?: { maxIterations?: number }) => {
      setState((prev) => ({
        ...prev,
        isRunning: true,
        status: 'planning',
        iterations: [],
        finalPlan: null,
        finalVerdict: null,
        error: null,
      }));

      connect();

      // Send start message after connection
      setTimeout(() => {
        send({
          action: 'start',
          domain_pddl: domainPddl,
          problem_pddl: problemPddl,
          max_iterations: options?.maxIterations ?? 5,
        });
      }, 100);
    },
    [connect, send]
  );

  const stopPlanning = useCallback(() => {
    disconnect();
    setState((prev) => ({
      ...prev,
      isRunning: false,
      status: 'idle',
    }));
  }, [disconnect]);

  return {
    ...state,
    wsStatus,
    startPlanning,
    stopPlanning,
  };
}
