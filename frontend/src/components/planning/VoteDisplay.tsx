import { Check, X, AlertTriangle, Vote } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { VoteResult, Verdict } from '@/types';

interface VoteDisplayProps {
  voteResult: VoteResult;
}

export function VoteDisplay({ voteResult }: VoteDisplayProps) {
  const { majority_verdict, breakdown, confidence, is_low_confidence } = voteResult;

  const getVerdictIcon = (verdict: Verdict) => {
    switch (verdict) {
      case 'correct':
        return <Check className="h-4 w-4" />;
      case 'wrong':
        return <X className="h-4 w-4" />;
      case 'goal_not_reached':
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const getVerdictLabel = (verdict: Verdict) => {
    switch (verdict) {
      case 'correct':
        return 'Valid';
      case 'wrong':
        return 'Invalid';
      case 'goal_not_reached':
        return 'Goal Not Reached';
    }
  };

  const getVerdictColor = (verdict: Verdict, isMain: boolean = false) => {
    const baseColors = {
      correct: isMain ? 'bg-green-500' : 'bg-green-200',
      wrong: isMain ? 'bg-destructive' : 'bg-destructive/30',
      goal_not_reached: isMain ? 'bg-yellow-500' : 'bg-yellow-200',
    };
    return baseColors[verdict];
  };

  const totalVotes = Object.values(breakdown).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-card border rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Vote className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Self-Consistency Voting</h3>
      </div>

      {/* Result summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-md text-white',
              getVerdictColor(majority_verdict, true)
            )}
          >
            {getVerdictIcon(majority_verdict)}
            <span className="font-medium">
              {getVerdictLabel(majority_verdict)}
            </span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-lg font-bold">
            {Math.round(confidence * 100)}%
          </div>
          <div className="text-xs text-muted-foreground">confidence</div>
        </div>
      </div>

      {/* Low confidence warning */}
      {is_low_confidence && (
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          <span>Low confidence - consider reviewing the critiques manually</span>
        </div>
      )}

      {/* Vote breakdown */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-muted-foreground">
          Vote Distribution ({totalVotes} samples)
        </div>

        {/* Visual bar */}
        <div className="flex h-4 rounded-full overflow-hidden">
          {(['correct', 'wrong', 'goal_not_reached'] as Verdict[]).map(
            (verdict) => {
              const count = breakdown[verdict] || 0;
              if (count === 0) return null;
              const percentage = (count / totalVotes) * 100;
              return (
                <div
                  key={verdict}
                  className={cn(
                    'transition-all',
                    getVerdictColor(verdict, verdict === majority_verdict)
                  )}
                  style={{ width: `${percentage}%` }}
                />
              );
            }
          )}
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm">
          {(['correct', 'wrong', 'goal_not_reached'] as Verdict[]).map(
            (verdict) => {
              const count = breakdown[verdict] || 0;
              if (count === 0) return null;
              return (
                <div key={verdict} className="flex items-center gap-2">
                  <div
                    className={cn(
                      'w-3 h-3 rounded-full',
                      getVerdictColor(verdict, verdict === majority_verdict)
                    )}
                  />
                  <span className="text-muted-foreground">
                    {getVerdictLabel(verdict)}: {count}
                  </span>
                </div>
              );
            }
          )}
        </div>
      </div>
    </div>
  );
}
