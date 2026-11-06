import React from 'react';
import { Sparkles, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MobilityScoreProps {
  score?: number | null;
  previousScore?: number | null;
  components?: {
    duration?: number;
    smoothness?: number;
    velocity?: number;
    stability?: number;
    completion?: number;
    consistency?: number;
  } | null;
}

export const MobilityScore: React.FC<MobilityScoreProps> = ({
  score = 82,
  previousScore = 78,
  components = {
    duration: 88,
    smoothness: 82,
    velocity: 80,
    stability: 85,
    completion: 90,
    consistency: 76,
  },
}) => {
  const displayScore = score !== null && score !== undefined ? Math.round(score) : 0;
  const delta =
    previousScore !== null && score !== null && score !== undefined && previousScore !== undefined
      ? Math.round(score - previousScore)
      : null;

  // Circular gauge circumference for r=70 (2 * pi * 70 = 439.82)
  const radius = 70;
  const stroke = 8;
  const circumference = 2 * Math.PI * radius;
  const progress = (displayScore / 100) * circumference;

  let gaugeColor = '#38bdf8'; // sky
  if (displayScore < 50) gaugeColor = '#f87171'; // red
  else if (displayScore < 75) gaugeColor = '#fbbf24'; // yellow
  else gaugeColor = '#34d399'; // green

  return (
    <div className="p-6 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            ROLLIQ Mobility Index
          </span>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Experimental Engineering Score (0–100)
          </p>
        </div>
        <Sparkles className="w-4 h-4 text-sky-400" />
      </div>

      {/* Center Circular Progress Ring */}
      <div className="my-5 flex flex-col items-center justify-center relative">
        <div className="relative w-44 h-44 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90">
            {/* Background ring */}
            <circle
              cx="88"
              cy="88"
              r={radius}
              stroke="#1a2336"
              strokeWidth={stroke}
              fill="transparent"
            />
            {/* Value ring */}
            <circle
              cx="88"
              cy="88"
              r={radius}
              stroke={gaugeColor}
              strokeWidth={stroke}
              strokeDasharray={circumference}
              strokeDashoffset={circumference - progress}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
              fill="transparent"
            />
          </svg>

          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-4xl font-extrabold text-white font-mono tracking-tight">
              {displayScore}
            </span>
            <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider mt-0.5">
              Score Points
            </span>
          </div>
        </div>

        {/* Delta comparison badge */}
        {delta !== null && (
          <div className="mt-2 flex items-center gap-1.5 text-xs font-medium">
            {delta > 0 ? (
              <span className="flex items-center text-emerald-400">
                <TrendingUp className="w-3.5 h-3.5 mr-1" /> +{delta} pts vs last session
              </span>
            ) : delta < 0 ? (
              <span className="flex items-center text-rose-400">
                <TrendingDown className="w-3.5 h-3.5 mr-1" /> {delta} pts vs last session
              </span>
            ) : (
              <span className="flex items-center text-slate-400">
                <Minus className="w-3.5 h-3.5 mr-1" /> Neutral vs last session
              </span>
            )}
          </div>
        )}
      </div>

      {/* 6 Interpretable RMI Component bars */}
      {components && (
        <div className="space-y-2 border-t border-[#1c2538] pt-4">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider block">
            Metric Component Contributions
          </span>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
            {Object.entries(components).map(([key, val]) => (
              <div key={key}>
                <div className="flex justify-between text-slate-400 capitalize mb-1">
                  <span>{key}</span>
                  <span className="font-mono text-slate-200">{val ?? 0}%</span>
                </div>
                <div className="w-full bg-[#1b2336] h-1.5 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${Math.min(100, val ?? 0)}%` }}
                    className="h-full bg-sky-400 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
