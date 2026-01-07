import { Plus, Sparkles, Target, Brain } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="p-8">
      <div className="max-w-4xl">
        <h1 className="text-3xl font-bold mb-2">Welcome to Self-Critique Planner</h1>
        <p className="text-muted-foreground mb-8">
          Create AI-powered plans with automatic verification and critique.
        </p>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-card rounded-lg border p-6 hover:border-primary/50 transition-colors">
            <Plus className="h-8 w-8 text-primary mb-4" />
            <h3 className="font-semibold mb-2">New Domain</h3>
            <p className="text-sm text-muted-foreground">
              Define a new planning domain for your problem space.
            </p>
          </div>

          <div className="bg-card rounded-lg border p-6 hover:border-primary/50 transition-colors">
            <Target className="h-8 w-8 text-primary mb-4" />
            <h3 className="font-semibold mb-2">Generate Plan</h3>
            <p className="text-sm text-muted-foreground">
              Create a verified plan using AI-powered critique.
            </p>
          </div>

          <div className="bg-card rounded-lg border p-6 hover:border-primary/50 transition-colors">
            <Brain className="h-8 w-8 text-primary mb-4" />
            <h3 className="font-semibold mb-2">Review Critiques</h3>
            <p className="text-sm text-muted-foreground">
              Examine step-by-step verification traces.
            </p>
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-card rounded-lg border p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">How It Works</h2>
          </div>

          <ol className="space-y-4">
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-medium">
                1
              </span>
              <div>
                <h3 className="font-medium">Define Your Domain</h3>
                <p className="text-sm text-muted-foreground">
                  Describe your planning problem in natural language. No PDDL
                  knowledge required.
                </p>
              </div>
            </li>

            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-medium">
                2
              </span>
              <div>
                <h3 className="font-medium">AI Generates a Plan</h3>
                <p className="text-sm text-muted-foreground">
                  Our AI creates a step-by-step plan to achieve your goals.
                </p>
              </div>
            </li>

            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-medium">
                3
              </span>
              <div>
                <h3 className="font-medium">Self-Critique Verification</h3>
                <p className="text-sm text-muted-foreground">
                  The AI critiques its own plan, checking each step for
                  correctness using self-consistency voting.
                </p>
              </div>
            </li>

            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-medium">
                4
              </span>
              <div>
                <h3 className="font-medium">Iterative Refinement</h3>
                <p className="text-sm text-muted-foreground">
                  If issues are found, the plan is refined until validated or
                  maximum iterations reached.
                </p>
              </div>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}
