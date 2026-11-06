import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/appStore';
import { api } from '../api/endpoints';
import { RMIHistoryChart } from '../components/charts/RMIHistoryChart';
import { DurationDistribution } from '../components/charts/DurationDistribution';
import { SymmetryChart } from '../components/charts/SymmetryChart';
import { SmoothnessChart } from '../components/charts/SmoothnessChart';
import { MetricCard } from '../components/common/MetricCard';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { Activity, Clock, ShieldCheck, Scale, AlertCircle } from 'lucide-react';
import { PersonalBaseline, BaselineComparisonResult } from '../types';

export const Analytics: React.FC = () => {
  const { currentUser, activeSession } = useAppStore();

  const [loading, setLoading] = useState(true);
  const [rmiHistory, setRmiHistory] = useState<any[]>([]);
  const [durationTrends, setDurationTrends] = useState<any[]>([]);
  const [symmetryTrends, setSymmetryTrends] = useState<any[]>([]);
  const [smoothnessTrends, setSmoothnessTrends] = useState<any[]>([]);
  const [baseline, setBaseline] = useState<PersonalBaseline | null>(null);
  const [comparison, setComparison] = useState<BaselineComparisonResult | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      if (!currentUser) return;
      setLoading(true);
      try {
        const [rmi, dur, sym, sm, b] = await Promise.all([
          api.getRMIHistory(currentUser.id),
          api.getDurationTrends(currentUser.id),
          api.getSymmetryTrends(currentUser.id),
          api.getSmoothnessTrends(currentUser.id),
          api.getUserBaseline(currentUser.id),
        ]);

        setRmiHistory(rmi);
        setDurationTrends(dur);
        setSymmetryTrends(sym);
        setSmoothnessTrends(sm);
        setBaseline(b);

        if (activeSession) {
          try {
            const comp = await api.getBaselineComparison(activeSession.id);
            setComparison(comp);
          } catch (_) {}
        }
      } catch (_) {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [currentUser, activeSession?.id]);

  if (loading) {
    return <LoadingSkeleton rows={6} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1f293d]">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Mobility & Recovery Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Statistical movement profiling & personal baseline comparison
          </p>
        </div>

        {/* Baseline status pill */}
        <div className="flex items-center gap-2">
          {baseline?.is_ready ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Personal Baseline Established ({baseline.sessions_used} sessions)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>
                Calibrating Baseline ({baseline?.sessions_used || 0}/3 sessions)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Row 1: Summary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Baseline Transition Time"
          value={baseline?.avg_transition_duration ? `${(baseline.avg_transition_duration / 1000).toFixed(2)}` : '—'}
          unit="sec"
          subValue={`± ${(baseline?.std_transition_duration ? baseline.std_transition_duration / 1000 : 0).toFixed(2)}s std dev`}
          icon={Clock}
          accentColor="sky"
        />
        <MetricCard
          label="Baseline Jerk Index"
          value={baseline?.avg_smoothness ? baseline.avg_smoothness.toFixed(2) : '—'}
          unit="jerk"
          subValue="Kinematic deceleration profile"
          icon={Activity}
          accentColor="emerald"
        />
        <MetricCard
          label="Baseline Angular Vel"
          value={baseline?.avg_angular_velocity ? baseline.avg_angular_velocity.toFixed(1) : '—'}
          unit="°/s"
          subValue="Rotational speed profile"
          icon={Scale}
          accentColor="amber"
        />
        <MetricCard
          label="Baseline Mobility Score"
          value={baseline?.avg_rmi ? Math.round(baseline.avg_rmi) : '—'}
          unit="pts"
          subValue="Rolling window aggregate"
          icon={ShieldCheck}
          accentColor="indigo"
        />
      </div>

      {/* Row 2: RMI History & Duration Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RMIHistoryChart data={rmiHistory} height={230} />
        <DurationDistribution data={durationTrends} height={230} />
      </div>

      {/* Row 3: Bilateral Turning Symmetry & Movement Smoothness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SymmetryChart data={symmetryTrends} height={230} />
        <SmoothnessChart data={smoothnessTrends} height={230} />
      </div>

      {/* Row 4: Personal Baseline Deviation Table */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Personal Baseline Deviation Profile
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluates session-specific measurements against individual standard deviations (z-scores)
            </p>
          </div>
          {comparison?.baseline_ready && (
            <span className="text-xs font-mono text-sky-400">
              Status: {comparison.overall_deviation}
            </span>
          )}
        </div>

        {!comparison || !comparison.baseline_ready || comparison.comparisons.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            <p>Insufficient baseline data to compute individual z-score deviations.</p>
            <p className="text-[11px] text-slate-600 mt-1">
              Complete at least 3 active sessions with purposeful movement events.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 uppercase font-mono text-[10px] border-b border-[#20293d]">
                <tr>
                  <th className="pb-3">Metric Name</th>
                  <th className="pb-3">Session Value</th>
                  <th className="pb-3">Personal Baseline</th>
                  <th className="pb-3">Std. Dev (σ)</th>
                  <th className="pb-3">Z-Score</th>
                  <th className="pb-3">Significance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b2336] text-slate-300">
                {comparison.comparisons.map((c, idx) => (
                  <tr key={idx} className="hover:bg-[#151c2c] transition-colors">
                    <td className="py-3 font-medium text-slate-200">{c.metric_name}</td>
                    <td className="py-3 font-mono font-bold text-white">{c.current_value}</td>
                    <td className="py-3 font-mono text-slate-400">{c.baseline_mean}</td>
                    <td className="py-3 font-mono text-slate-400">± {c.baseline_std}</td>
                    <td className="py-3 font-mono">
                      <span
                        className={`font-semibold ${
                          Math.abs(c.z_score) >= 1.5
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {c.z_score > 0 ? `+${c.z_score}` : c.z_score} σ
                      </span>
                    </td>
                    <td className="py-3">
                      {c.is_significant ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                          Notable Shift ({c.deviation_direction})
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                          Nominal
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
