import { Check, X, AlertTriangle, ChevronDown, ChevronRight, Brain } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { CritiqueResult, Verdict } from '@/types';

interface CritiqueTraceProps {
  critiqueResults: CritiqueResult[];
  planSteps: string[];
}

export function CritiqueTrace({ critiqueResults, planSteps }: CritiqueTraceProps) {
  const [expandedSample, setExpandedSample] = useState<number | null>(0);

  const getVerdictIcon = (verdict: Verdict) => {
    switch (verdict) {
      case 'correct':
        return <Check className="h-4 w-4 text-green-600" />;
      case 'wrong':
        return <X className="h-4 w-4 text-destructive" />;
      case 'goal_not_reached':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getVerdictBg = (verdict: Verdict) => {
    switch (verdict) {
      case 'correct':
        return 'bg-green-50 border-green-200';
      case 'wrong':
        return 'bg-destructive/5 border-destructive/20';
      case 'goal_not_reached':
        return 'bg-yellow-50 border-yellow-200';
    }
  };

  if (critiqueResults.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Brain className="h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">
          No critique traces yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Brain className="h-4 w-4" />
        <span>{critiqueResults.length} critique samples</span>
      </div>

      {critiqueResults.map((critique, idx) => (
        <div
          key={idx}
          className={cn('border rounded-lg overflow-hidden', getVerdictBg(critique.verdict))}
        >
          {/* Sample header */}
          <button
            onClick={() =>
              setExpandedSample(expandedSample === idx ? null : idx)
            }
            className="w-full flex items-center justify-between p-3 hover:bg-black/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              {expandedSample === idx ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="font-medium text-sm">Sample {idx + 1}</span>
            </div>
            <div className="flex items-center gap-2">
              {getVerdictIcon(critique.verdict)}
              <span className="text-sm capitalize">
                {critique.verdict.replace('_', ' ')}
              </span>
            </div>
          </button>

          {/* Trace content */}
          {expandedSample === idx && (
            <div className="border-t p-4 bg-white/50 space-y-4">
              {/* Step-by-step traces */}
              <div>
                <h4 className="text-sm font-medium mb-2">Step-by-Step Analysis</h4>
                <div className="space-y-2">
                  {critique.step_traces.map((trace, stepIdx) => (
                    <div
                      key={stepIdx}
                      className="flex gap-3 p-3 bg-muted/50 rounded-md"
                    >
                      <div className="flex-shrink-0 w-6 h-6 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs font-medium">
                        {stepIdx + 1}
                      </div>
                      <div className="flex-1">
                        {planSteps[stepIdx] && (
                          <div className="text-sm font-mono text-muted-foreground mb-1">
                            {planSteps[stepIdx]}
                          </div>
                        )}
                        <div className="text-sm">{trace}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Error reason if any */}
              {critique.error_reason && (
                <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
                  <h4 className="text-sm font-medium text-destructive mb-1">
                    Error Identified
                  </h4>
                  <p className="text-sm text-destructive/90">
                    {critique.error_reason}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
