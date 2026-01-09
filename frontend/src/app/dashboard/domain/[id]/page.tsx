'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { ElicitationChat } from '@/components/chat/ElicitationChat';
import { domainAPI } from '@/lib/api';
import type { Domain, ElicitationState } from '@/types';
import { Loader2, Play, FileText, Code } from 'lucide-react';
import Link from 'next/link';

type Tab = 'chat' | 'pddl' | 'plans';

export default function DomainPage() {
  const params = useParams();
  const domainId = params.id as string;

  const [domain, setDomain] = useState<Domain | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [elicitationState, setElicitationState] = useState<ElicitationState | null>(null);

  useEffect(() => {
    loadDomain();
  }, [domainId]);

  const loadDomain = async () => {
    try {
      const data = await domainAPI.get(domainId);
      setDomain(data);
    } catch (error) {
      console.error('Failed to load domain:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!domain) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-muted-foreground">Domain not found</p>
        <Link href="/dashboard" className="text-primary hover:underline mt-2">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const canGeneratePlan = elicitationState?.phase === 'complete' || !!domain.domain_pddl;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b bg-card">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{domain.name}</h1>
            {domain.description && (
              <p className="text-muted-foreground mt-1">{domain.description}</p>
            )}
          </div>
          {canGeneratePlan && (
            <Link
              href={`/dashboard/domain/${domainId}/plan`}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <Play className="h-4 w-4" />
              Generate Plan
            </Link>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-6">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${
              activeTab === 'chat'
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            }`}
          >
            <FileText className="h-4 w-4" />
            Define Domain
          </button>
          <button
            onClick={() => setActiveTab('pddl')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${
              activeTab === 'pddl'
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            }`}
          >
            <Code className="h-4 w-4" />
            PDDL
          </button>
          <button
            onClick={() => setActiveTab('plans')}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${
              activeTab === 'plans'
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            }`}
          >
            <Play className="h-4 w-4" />
            Plans
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <ElicitationChat
            domainId={domainId}
            onStateChange={setElicitationState}
          />
        )}

        {activeTab === 'pddl' && (
          <div className="p-6 h-full overflow-y-auto">
            {domain.domain_pddl ? (
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-2">Domain PDDL</h3>
                  <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                    {domain.domain_pddl}
                  </pre>
                </div>
                {domain.problem_pddl && (
                  <div>
                    <h3 className="font-semibold mb-2">Problem PDDL</h3>
                    <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                      {domain.problem_pddl}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-muted-foreground">
                  No PDDL generated yet
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Complete the domain definition chat to generate PDDL
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'plans' && (
          <div className="p-6 h-full overflow-y-auto">
            <div className="flex flex-col items-center justify-center h-full text-center">
              <p className="text-muted-foreground">
                No plans generated yet
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Complete the domain definition and click &quot;Generate Plan&quot;
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
