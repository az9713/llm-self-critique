'use client';

import { Wifi, WifiOff, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { WebSocketStatus } from '@/hooks';

interface ConnectionStatusProps {
  status: WebSocketStatus;
  reconnectAttempts?: number;
  maxReconnectAttempts?: number;
  showLabel?: boolean;
  className?: string;
}

export function ConnectionStatus({
  status,
  reconnectAttempts = 0,
  maxReconnectAttempts = 5,
  showLabel = true,
  className,
}: ConnectionStatusProps) {
  const getStatusInfo = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          label: 'Connected',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
        };
      case 'connecting':
        return {
          icon: Loader2,
          label: reconnectAttempts > 0
            ? `Reconnecting (${reconnectAttempts}/${maxReconnectAttempts})...`
            : 'Connecting...',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          animate: true,
        };
      case 'error':
        return {
          icon: AlertCircle,
          label: 'Connection Error',
          color: 'text-destructive',
          bgColor: 'bg-destructive/10',
        };
      case 'disconnected':
      default:
        return {
          icon: WifiOff,
          label: 'Disconnected',
          color: 'text-muted-foreground',
          bgColor: 'bg-muted',
        };
    }
  };

  const info = getStatusInfo();
  const Icon = info.icon;

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-2 py-1 rounded-md text-sm',
        info.bgColor,
        className
      )}
    >
      <Icon
        className={cn(
          'h-4 w-4',
          info.color,
          'animate' in info && info.animate && 'animate-spin'
        )}
      />
      {showLabel && (
        <span className={info.color}>{info.label}</span>
      )}
    </div>
  );
}
