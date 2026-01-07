'use client';

import { useState, useEffect, useCallback } from 'react';
import { IterationCard } from './IterationCard';
import { createPlanningWebSocket, planningAPI } from '@/lib/api';
import type { PlanningSession, Verdict } from '@/types';
import { Loader2, Play, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Iteration {
  number: number;
  plan: string;
  verdict: Verdict | null;
  confidence: number;
  errorReason: string | null;
  critiqueResults: Array<{
    verdict: Verdict;
    step_traces: string[];
    error_reason: string | null;
  }>;
}

interface PlanningViewProps {
  session: PlanningSession;
  domainId: string;
  onSessionUpdate?: (session: PlanningSession) => void;
}

export function PlanningView({
  session,
  domainId,
  onSessionUpdate,
}: PlanningViewProps) {
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [currentIteration, setCurrentIteration] = useState<number>(0);
  const [status, setStatus] = useState<string>(session.status);
  const [isRunning, setIsRunning] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const handleWSMessage = useCallback(
    (event: { type: string; data: Record<string, unknown> }) => {
      switch (event.type) {
        case 'started':
          setStatus('planning');
          setIterations([]);
          break;

        case 'iteration_started':
          setCurrentIteration(event.data.iteration as number);
          setIterations((prev) => [
            ...prev,
            {
              number: event.data.iteration as number,
              plan: '',
              verdict: null,
              confidence: 0,
              errorReason: null,
              critiqueResults: [],
            },
          ]);
          break;

        case 'plan_generated':
          setIterations((prev) =>
            prev.map((iter) =>
              iter.number === currentIteration
                ? { ...iter, plan: event.data.plan as string }
                : iter
            )
          );
          break;

        case 'critique_sample':
          setIterations((prev) =>
            prev.map((iter) =>
              iter.number === currentIteration
                ? {
                    ...iter,
                    critiqueResults: [
                      ...iter.critiqueResults,
                      event.data.result as Iteration['critiqueResults'][0],
                    ],
                  }
                : iter
            )
          );
          break;

        case 'critique_complete':
          setIterations((prev) =>
            prev.map((iter) =>
              iter.number === currentIteration
                ? {
                    ...iter,
                    verdict: event.data.majority_verdict as Verdict,
                    confidence: event.data.confidence as number,
                    errorReason: event.data.best_error_reason as string | null,
                  }
                : iter
            )
          );
          break;

        case 'completed':
          setStatus('complete');
          setIsRunning(false);
          break;

        case 'error':
          setStatus('failed');
          setIsRunning(false);
          break;
      }
    },
    [currentIteration]
  );

  const startPlanning = async () => {
    setIsRunning(true);
    setIterations([]);
    setStatus('planning');

    // Connect WebSocket
    const websocket = createPlanningWebSocket(
      session.id,
      handleWSMessage,
      () => {
        setIsRunning(false);
        setStatus('failed');
      },
      () => {
        setIsRunning(false);
      }
    );

    setWs(websocket);
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      ws?.close();
    };
  }, [ws]);

  const getStatusIcon = () => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      case 'planning':
      case 'critiquing':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
      default:
        return <AlertCircle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'complete':
        return 'Plan Validated';
      case 'failed':
        return 'Planning Failed';
      case 'planning':
        return 'Generating Plan...';
      case 'critiquing':
        return 'Critiquing Plan...';
      default:
        return 'Ready to Plan';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <span className="font-medium">{getStatusText()}</span>
        </div>

        {!isRunning && status !== 'complete' && (
          <button
            onClick={startPlanning}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Play className="h-4 w-4" />
            {iterations.length > 0 ? 'Retry' : 'Start Planning'}
          </button>
        )}
      </div>

      {/* Iterations */}
      {iterations.length > 0 ? (
        <div className="space-y-4">
          {iterations.map((iteration) => (
            <IterationCard
              key={iteration.number}
              iterationNumber={iteration.number}
              plan={iteration.plan}
              verdict={iteration.verdict}
              confidence={iteration.confidence}
              isActive={isRunning && iteration.number === currentIteration}
              errorReason={iteration.errorReason}
              critiqueResults={iteration.critiqueResults}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            Click &quot;Start Planning&quot; to generate and validate a plan
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            The AI will iteratively generate plans and critique them until valid
          </p>
        </div>
      )}
    </div>
  );
}
