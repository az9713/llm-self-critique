'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PlanningView } from '@/components/planning/PlanningView';
import { planningAPI, domainAPI } from '@/lib/api';
import type { PlanningSession, Domain } from '@/types';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function PlanPage() {
  const params = useParams();
  const router = useRouter();
  const domainId = params.id as string;

  const [domain, setDomain] = useState<Domain | null>(null);
  const [session, setSession] = useState<PlanningSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [domainId]);

  const loadData = async () => {
    try {
      // Load domain
      const domainData = await domainAPI.get(domainId);
      setDomain(domainData);

      // Check for existing sessions or create new one
      const sessions = await planningAPI.list(domainId);

      if (sessions.length > 0) {
        // Use most recent session
        setSession(sessions[sessions.length - 1]);
      } else {
        // Create new session
        const newSession = await planningAPI.create(domainId);
        setSession(newSession);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load planning session');
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

  if (error || !domain) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-destructive">{error || 'Domain not found'}</p>
        <Link href="/dashboard" className="text-primary hover:underline mt-2">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b bg-card">
        <div className="flex items-center gap-4 mb-4">
          <Link
            href={`/dashboard/domain/${domainId}`}
            className="p-2 hover:bg-muted rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Plan Generation</h1>
            <p className="text-muted-foreground">{domain.name}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {session ? (
          <PlanningView
            session={session}
            domainId={domainId}
            onSessionUpdate={setSession}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Creating planning session...</p>
          </div>
        )}
      </div>
    </div>
  );
}
