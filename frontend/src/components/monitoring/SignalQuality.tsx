import React from 'react';
import { Activity } from 'lucide-react';

interface SignalQualityProps {
  quality: number; // 0.0 to 1.0
  sampleRate?: number;
}

export const SignalQuality: React.FC<SignalQualityProps> = ({
  quality = 0.95,
  sampleRate = 50,
}) => {
  const bars = [0.2, 0.4, 0.6, 0.8, 1.0];
  const activeBars = bars.filter((b) => quality >= b).length;

  let color = 'text-emerald-400 bg-emerald-400';
  let label = 'Excellent';
  if (quality < 0.5) {
    color = 'text-rose-400 bg-rose-400';
    label = 'Degraded';
  } else if (quality < 0.75) {
    color = 'text-amber-400 bg-amber-400';
    label = 'Moderate';
  }

  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-[#121826] border border-[#20293d]">
      <div className="flex items-center gap-2.5">
        <Activity className="w-4 h-4 text-slate-400" />
        <div>
          <span className="text-xs font-medium text-slate-200">Signal Integrity</span>
          <p className="text-[10px] text-slate-400">{sampleRate} Hz Stream • {label}</p>
        </div>
      </div>

      <div className="flex items-end gap-1 h-5">
        {bars.map((threshold, idx) => (
          <div
            key={idx}
            style={{ height: `${(idx + 1) * 20}%` }}
            className={`w-1.5 rounded-sm transition-all duration-300 ${
              idx < activeBars ? color.split(' ')[1] : 'bg-slate-800'
            }`}
          />
        ))}
      </div>
    </div>
  );
};
