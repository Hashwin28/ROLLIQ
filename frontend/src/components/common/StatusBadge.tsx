import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const norm = status.toLowerCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (norm === 'active' || norm === 'connected' || norm === 'online') {
    colorClasses = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
  } else if (norm === 'paused' || norm === 'simulating' || norm === 'warning') {
    colorClasses = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
  } else if (norm === 'completed') {
    colorClasses = 'bg-sky-500/15 text-sky-300 border-sky-500/30';
  } else if (norm === 'incomplete' || norm === 'error' || norm === 'disconnected') {
    colorClasses = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border uppercase tracking-wider ${padding} ${colorClasses}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status.replace('_', ' ')}
    </span>
  );
};
