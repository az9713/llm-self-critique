'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Library,
  Plus,
  Settings,
  LogOut,
  ChevronDown,
  ChevronRight,
  Folder,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Domain } from '@/types';

interface SidebarProps {
  domains: Domain[];
  onCreateDomain: () => void;
}

export function Sidebar({ domains, onCreateDomain }: SidebarProps) {
  const pathname = usePathname();
  const [domainsExpanded, setDomainsExpanded] = useState(true);

  return (
    <aside className="w-64 bg-card border-r h-screen flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b">
        <h1 className="text-lg font-bold">Self-Critique Planner</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <Link
          href="/dashboard"
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
            pathname === '/dashboard'
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted'
          )}
        >
          <Home className="h-4 w-4" />
          Dashboard
        </Link>

        {/* Domains Section */}
        <div className="pt-4">
          <button
            onClick={() => setDomainsExpanded(!domainsExpanded)}
            className="flex items-center gap-2 px-3 py-2 w-full text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            {domainsExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <Library className="h-4 w-4" />
            Domains
          </button>

          {domainsExpanded && (
            <div className="ml-4 mt-1 space-y-1">
              {domains.map((domain) => (
                <Link
                  key={domain.id}
                  href={`/dashboard/domain/${domain.id}`}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors',
                    pathname === `/dashboard/domain/${domain.id}`
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                >
                  <Folder className="h-4 w-4" />
                  <span className="truncate">{domain.name}</span>
                </Link>
              ))}

              <button
                onClick={onCreateDomain}
                className="flex items-center gap-2 px-3 py-2 w-full rounded-md text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                <Plus className="h-4 w-4" />
                New Domain
              </button>
            </div>
          )}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t space-y-2">
        <Link
          href="/dashboard/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-muted transition-colors"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
        <button className="flex items-center gap-3 px-3 py-2 rounded-md text-sm hover:bg-muted transition-colors w-full text-left text-muted-foreground">
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
