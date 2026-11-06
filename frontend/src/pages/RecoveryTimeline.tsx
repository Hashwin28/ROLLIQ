import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { api } from '../api/endpoints';
import { MonitoringSession } from '../types';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import {
  Calendar,
  Clock,
  Sparkles,
  Zap,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
} from 'lucide-react';

export const RecoveryTimeline: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser } = useAppStore();
  const [sessions, setSessions] = useState<MonitoringSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSessions() {
      if (!currentUser) return;
      setLoading(true);
      try {
        const data = await api.getSessions({ user_id: currentUser.id });
        setSessions(data);
      } catch (_) {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadSessions();
  }, [currentUser]);

  if (loading) {
    return <LoadingSkeleton rows={5} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1f293d]">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Recovery & Mobility Timeline
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological log of bed-mobility monitoring sessions and recovery progression
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Total Sessions Logged: <strong className="text-white">{sessions.length}</strong>
        </span>
      </div>

      {sessions.length === 0 ? (
        <EmptyState
          title="No Sessions Recorded Yet"
          description="Initiate an active monitoring session or run a simulation scenario to start tracking recovery milestones."
          actionText="Go to Live Monitor"
          onAction={() => navigate('/monitor')}
        />
      ) : (
        <div className="space-y-4">
          {sessions.map((s, idx) => {
            const nextSession = sessions[idx + 1];
            const rmiDelta =
              s.rmi_score && nextSession?.rmi_score
                ? Math.round(s.rmi_score - nextSession.rmi_score)
                : null;

            return (
              <div
                key={s.id}
                onClick={() => navigate(`/movement/${s.id}/sample`)}
                className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] hover:border-sky-500/40 transition-all cursor-pointer group flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left metadata */}
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-bold text-sm shrink-0">
                    #{sessions.length - idx}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-white">
                        {new Date(s.started_at).toLocaleDateString(undefined, {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </h3>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {s.is_simulation ? 'Simulation' : 'Hardware'}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                      <span className="flex items-center gap-1 font-mono">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {new Date(s.started_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1 font-mono">
                        <Zap className="w-3.5 h-3.5 text-slate-400" />
                        {s.total_movements} transitions
                      </span>
                      {s.avg_transition_duration && (
                        <>
                          <span>•</span>
                          <span className="font-mono">
                            Avg {(s.avg_transition_duration / 1000).toFixed(2)}s
                          </span>
                        </>
                      )}
                    </p>
                  </div>
                </div>

                {/* Right score & action */}
                <div className="flex items-center gap-6">
                  {/* RMI Score badge */}
                  <div className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                      <span className="text-lg font-bold text-white font-mono">
                        {s.rmi_score ? Math.round(s.rmi_score) : '—'}
                      </span>
                      <span className="text-xs text-slate-400">RMI</span>
                    </div>

                    {rmiDelta !== null && (
                      <p className="text-[11px] font-mono mt-0.5">
                        {rmiDelta > 0 ? (
                          <span className="text-emerald-400 font-semibold">
                            +{rmiDelta} pts vs prev
                          </span>
                        ) : rmiDelta < 0 ? (
                          <span className="text-rose-400 font-semibold">
                            {rmiDelta} pts vs prev
                          </span>
                        ) : (
                          <span className="text-slate-400">0 pts vs prev</span>
                        )}
                      </p>
                    )}
                  </div>

                  <div className="w-8 h-8 rounded-lg bg-[#182030] flex items-center justify-center text-slate-400 group-hover:text-sky-400 group-hover:bg-sky-500/10 transition-colors">
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
