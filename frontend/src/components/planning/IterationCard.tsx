import { Check, X, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { CritiqueTrace } from './CritiqueTrace';
import { VoteDisplay } from './VoteDisplay';
import type { Verdict, CritiqueResult, VoteResult } from '@/types';

interface IterationCardProps {
  iterationNumber: number;
  plan: string;
  verdict: Verdict | null;
  confidence: number;
  isActive: boolean;
  errorReason?: string | null;
  critiqueResults?: CritiqueResult[];
}

export function IterationCard({
  iterationNumber,
  plan,
  verdict,
  confidence,
  isActive,
  errorReason,
  critiqueResults = [],
}: IterationCardProps) {
  const [expanded, setExpanded] = useState(isActive);

  const getVerdictIcon = () => {
    if (!verdict) return null;
    switch (verdict) {
      case 'correct':
        return <Check className="h-4 w-4 text-green-600" />;
      case 'wrong':
        return <X className="h-4 w-4 text-destructive" />;
      case 'goal_not_reached':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getVerdictText = () => {
    if (!verdict) return 'Processing...';
    switch (verdict) {
      case 'correct':
        return 'Valid';
      case 'wrong':
        return 'Invalid';
      case 'goal_not_reached':
        return 'Goal Not Reached';
    }
  };

  const getVerdictColor = () => {
    if (!verdict) return 'bg-muted';
    switch (verdict) {
      case 'correct':
        return 'bg-green-100 text-green-800';
      case 'wrong':
        return 'bg-destructive/10 text-destructive';
      case 'goal_not_reached':
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  // Parse plan into steps
  const planSteps = plan
    ? plan
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => line.trim())
    : [];

  // Calculate vote result from critique results
  const voteResult: VoteResult | null = useMemo(() => {
    if (critiqueResults.length === 0 || !verdict) return null;

    const breakdown: Record<Verdict, number> = {
      correct: 0,
      wrong: 0,
      goal_not_reached: 0,
    };

    for (const result of critiqueResults) {
      breakdown[result.verdict]++;
    }

    return {
      majority_verdict: verdict,
      breakdown,
      confidence,
      is_low_confidence: confidence < 0.8,
    };
  }, [critiqueResults, verdict, confidence]);

  return (
    <div
      className={cn(
        'border rounded-lg overflow-hidden',
        isActive && 'border-primary shadow-sm'
      )}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-card hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium">Iteration {iterationNumber}</span>
          {isActive && !verdict && (
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          )}
        </div>

        <div className="flex items-center gap-3">
          {verdict && (
            <>
              <span className="text-sm text-muted-foreground">
                Confidence: {Math.round(confidence * 100)}%
              </span>
              <div
                className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded-md text-sm',
                  getVerdictColor()
                )}
              >
                {getVerdictIcon()}
                {getVerdictText()}
              </div>
            </>
          )}
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4 border-t space-y-4">
          {/* Plan */}
          <div>
            <h4 className="text-sm font-medium mb-2">Plan</h4>
            {planSteps.length > 0 ? (
              <div className="bg-muted rounded-md p-3 space-y-1">
                {planSteps.map((step, idx) => (
                  <div key={idx} className="flex gap-2 text-sm font-mono">
                    <span className="text-muted-foreground w-6">{idx + 1}.</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Generating plan...
              </p>
            )}
          </div>

          {/* Vote display */}
          {voteResult && (
            <VoteDisplay voteResult={voteResult} />
          )}

          {/* Error reason if any */}
          {errorReason && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
              <h4 className="text-sm font-medium text-destructive mb-1">
                Issue Found
              </h4>
              <p className="text-sm text-destructive/90">{errorReason}</p>
            </div>
          )}

          {/* Critique traces */}
          {critiqueResults.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Critique Analysis</h4>
              <CritiqueTrace
                critiqueResults={critiqueResults}
                planSteps={planSteps}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
