import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MovementEvent } from '../../types';
import { ArrowRight, ChevronRight, Gauge } from 'lucide-react';

interface MovementTimelineProps {
  movements: MovementEvent[];
  sessionId?: string;
}

const eventBadgeColors: Record<string, string> = {
  left_roll: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  right_roll: 'bg-teal-500/15 text-teal-300 border-teal-500/30',
  supine_to_sitting: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  sitting_to_supine: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  posture_transition: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  minor_adjustment: 'bg-slate-700/20 text-slate-400 border-slate-700/40',
  unclassified: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
};

export const MovementTimeline: React.FC<MovementTimelineProps> = ({
  movements,
  sessionId,
}) => {
  const navigate = useNavigate();

  return (
    <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d] flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Detected Movement Sequence
        </span>
        <span className="text-xs text-sky-400 font-mono font-bold">
          {movements.length} Event{movements.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 max-h-80 pr-1">
        {movements.length === 0 ? (
          <div className="h-32 flex flex-col items-center justify-center text-xs text-slate-500">
            <span>No movement events logged yet</span>
            <span className="text-[11px] text-slate-600 mt-1">
              Roll or trigger transitions to observe real-time classification
            </span>
          </div>
        ) : (
          movements.map((m, idx) => (
            <div
              key={m.id || idx}
              onClick={() => {
                if (sessionId) {
                  navigate(`/movement/${sessionId}/${m.id}`);
                }
              }}
              className="p-3 rounded-lg bg-[#0e1422] border border-[#1d273b] hover:border-sky-500/40 cursor-pointer transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-mono text-slate-400">
                  #{movements.length - idx}
                </span>

                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-medium uppercase px-2 py-0.5 rounded border ${
                        eventBadgeColors[m.event_type] || eventBadgeColors.unclassified
                      }`}
                    >
                      {m.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {(m.duration_ms / 1000).toFixed(2)}s
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                    <span>
                      {m.start_posture || 'supine'} → {m.end_posture || 'lateral'}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Gauge className="w-3 h-3 text-slate-400" />
                      {m.peak_angular_velocity.toFixed(0)}°/s peak
                    </span>
                  </div>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-sky-400 transition-colors" />
            </div>
          ))
        )}
      </div>
    </div>
  );
};
