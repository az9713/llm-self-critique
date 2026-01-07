import { Check, X, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PlanStep {
  index: number;
  action: string;
  status: 'pending' | 'executing' | 'valid' | 'invalid';
}

interface PlanStepsProps {
  steps: PlanStep[];
  currentStep?: number;
}

export function PlanSteps({ steps, currentStep }: PlanStepsProps) {
  return (
    <div className="space-y-2">
      {steps.map((step, idx) => (
        <div
          key={idx}
          className={cn(
            'flex items-center gap-3 p-3 rounded-md border',
            step.status === 'executing' && 'border-primary bg-primary/5',
            step.status === 'valid' && 'border-green-500/50 bg-green-50',
            step.status === 'invalid' && 'border-destructive/50 bg-destructive/5',
            step.status === 'pending' && 'border-border'
          )}
        >
          <div
            className={cn(
              'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
              step.status === 'executing' && 'bg-primary/10 text-primary',
              step.status === 'valid' && 'bg-green-100 text-green-600',
              step.status === 'invalid' && 'bg-destructive/10 text-destructive',
              step.status === 'pending' && 'bg-muted text-muted-foreground'
            )}
          >
            {step.status === 'pending' && <Clock className="h-4 w-4" />}
            {step.status === 'executing' && (
              <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            )}
            {step.status === 'valid' && <Check className="h-4 w-4" />}
            {step.status === 'invalid' && <X className="h-4 w-4" />}
          </div>

          <div className="flex-1">
            <div className="text-sm font-medium">Step {step.index + 1}</div>
            <div className="text-sm text-muted-foreground font-mono">
              {step.action}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
