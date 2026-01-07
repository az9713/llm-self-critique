'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { CreateDomainDialog } from '@/components/domains/CreateDomainDialog';
import { domainAPI } from '@/lib/api';
import type { Domain } from '@/types';

// Mock workspace ID for now - would come from auth context
const WORKSPACE_ID = '00000000-0000-0000-0000-000000000001';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      const data = await domainAPI.list(WORKSPACE_ID);
      setDomains(data);
    } catch (error) {
      console.error('Failed to load domains:', error);
      // Use empty array if API fails (backend not running)
      setDomains([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDomain = async (data: {
    name: string;
    description: string;
  }) => {
    const newDomain = await domainAPI.create({
      ...data,
      workspace_id: WORKSPACE_ID,
    });
    setDomains([...domains, newDomain]);
  };

  return (
    <div className="flex h-screen">
      <Sidebar
        domains={loading ? [] : domains}
        onCreateDomain={() => setShowCreateDialog(true)}
      />
      <main className="flex-1 overflow-auto bg-muted/30">
        {children}
      </main>
      <CreateDomainDialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        onSubmit={handleCreateDomain}
      />
    </div>
  );
}
