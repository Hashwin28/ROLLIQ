import React, { ReactNode } from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  subValue?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendText?: string;
  accentColor?: 'sky' | 'emerald' | 'amber' | 'indigo' | 'rose';
  onClick?: () => void;
}

const colorMap = {
  sky: 'border-sky-500/20 text-sky-400 bg-sky-500/10 group-hover:border-sky-500/40',
  emerald: 'border-emerald-500/20 text-emerald-400 bg-emerald-500/10 group-hover:border-emerald-500/40',
  amber: 'border-amber-500/20 text-amber-400 bg-amber-500/10 group-hover:border-amber-500/40',
  indigo: 'border-indigo-500/20 text-indigo-400 bg-indigo-500/10 group-hover:border-indigo-500/40',
  rose: 'border-rose-500/20 text-rose-400 bg-rose-500/10 group-hover:border-rose-500/40',
};

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  subValue,
  icon: Icon,
  trend,
  trendText,
  accentColor = 'sky',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`group relative p-5 rounded-xl bg-[#121826] border border-[#20293d] hover:border-slate-600 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-lg' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
          {label}
        </span>
        {Icon && (
          <div
            className={`w-8 h-8 rounded-lg border flex items-center justify-center transition-colors ${colorMap[accentColor]}`}
          >
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {unit && <span className="text-xs text-slate-400 font-sans">{unit}</span>}
      </div>

      {(subValue || trendText) && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
          {trendText && (
            <span
              className={`font-semibold ${
                trend === 'up'
                  ? 'text-emerald-400'
                  : trend === 'down'
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }`}
            >
              {trendText}
            </span>
          )}
          {subValue && <span>{subValue}</span>}
        </div>
      )}
    </div>
  );
};
