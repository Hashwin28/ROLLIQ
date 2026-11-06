import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  User as UserIcon,
  Clock,
  Radio,
  Sparkles,
  RotateCcw,
  Zap,
  TrendingUp,
} from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { api } from '../api/endpoints';
import { MetricCard } from '../components/common/MetricCard';
import { PostureIndicator } from '../components/monitoring/PostureIndicator';
import { LiveAccelChart } from '../components/charts/LiveAccelChart';
import { LiveGyroChart } from '../components/charts/LiveGyroChart';
import { MovementTimeline } from '../components/charts/MovementTimeline';
import { MobilityScore } from '../components/dashboard/MobilityScore';
import { AlertPanel } from '../components/dashboard/AlertPanel';
import { MonitoringSession, MovementEvent } from '../types';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentUser,
    activeSession,
    livePosture,
    postureConfidence,
    sensorBuffer,
    recentMovements,
    alerts,
    simulationStatus,
    connectionStatus,
    dispatch,
  } = useAppStore();

  const [recentSessions, setRecentSessions] = useState<MonitoringSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        if (currentUser) {
          const sessions = await api.getSessions({ user_id: currentUser.id });
          setRecentSessions(sessions.slice(0, 5));
        }
      } catch (_) {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentUser]);

  // Compute stats
  const totalCompletedMovements = activeSession?.total_movements || recentMovements.length;
  const currentRmi = activeSession?.rmi_score || 82;
  const prevSessionRmi = recentSessions.length > 1 ? recentSessions[1].rmi_score : 78;

  return (
    <div className="space-y-6">
      {/* Top Welcome & Mode Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#121826] border border-[#20293d] p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Clinical Telemetry Overview
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30 font-medium">
              Live Edge Monitor
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Subject: <strong className="text-slate-200">{currentUser?.display_name || 'Primary User'}</strong>{' '}
            • Age Group: <span className="capitalize">{currentUser?.age_group || 'adult'}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/monitor')}
            className="px-4 py-2 text-xs font-bold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors shadow-md shadow-sky-500/20 flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            <span>Open Live Monitor</span>
          </button>
        </div>
      </div>

      {/* Row 1: High-Level Core Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Detected Posture"
          value={livePosture.replace('_', ' ').toUpperCase()}
          subValue={`${Math.round(postureConfidence * 100)}% Match`}
          icon={RotateCcw}
          accentColor="sky"
        />
        <MetricCard
          label="Completed Transitions"
          value={totalCompletedMovements}
          unit="events"
          subValue="Purposeful repositioning"
          icon={Zap}
          accentColor="emerald"
        />
        <MetricCard
          label="Mobility Index"
          value={currentRmi}
          unit="pts"
          trend="up"
          trendText="+4 pts"
          subValue="vs. user baseline"
          icon={Sparkles}
          accentColor="amber"
        />
        <MetricCard
          label="Telemetry Stream"
          value={simulationStatus.is_running ? 'SIMULATED' : connectionStatus === 'connected' ? 'HARDWARE' : 'STANDBY'}
          subValue={simulationStatus.is_running ? `${simulationStatus.speed}x speed` : '50 Hz MPU6050'}
          icon={Radio}
          accentColor={simulationStatus.is_running ? 'amber' : 'indigo'}
        />
      </div>

      {/* Row 2: Live Charts & RMI Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 cols: Live Waveforms */}
        <div className="lg:col-span-2 space-y-4">
          <LiveAccelChart data={sensorBuffer} height={190} />
          <LiveGyroChart data={sensorBuffer} height={190} />
        </div>

        {/* Right col: RMI Score Gauge & Posture state */}
        <div className="space-y-4">
          <MobilityScore
            score={currentRmi}
            previousScore={prevSessionRmi}
            components={{
              duration: 86,
              smoothness: 82,
              velocity: 80,
              stability: 85,
              completion: 90,
              consistency: 78,
            }}
          />
        </div>
      </div>

      {/* Row 3: Movement Event Sequence & System Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MovementTimeline
            movements={recentMovements}
            sessionId={activeSession?.id}
          />
        </div>
        <div>
          <AlertPanel alerts={alerts} />
        </div>
      </div>

      {/* Row 4: Recent Sessions History */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-200">
            Recent Monitoring Sessions
          </h3>
          <button
            onClick={() => navigate('/recovery')}
            className="text-xs text-sky-400 hover:text-sky-300 font-medium"
          >
            View Recovery Timeline →
          </button>
        </div>

        {recentSessions.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No completed monitoring sessions logged yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 uppercase font-mono text-[10px] border-b border-[#20293d]">
                <tr>
                  <th className="pb-3">Session Date</th>
                  <th className="pb-3">Mode</th>
                  <th className="pb-3">Transitions</th>
                  <th className="pb-3">Avg Duration</th>
                  <th className="pb-3">RMI Score</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b2336] text-slate-300">
                {recentSessions.map((s) => (
                  <tr
                    key={s.id}
                    onClick={() => navigate('/recovery')}
                    className="hover:bg-[#151c2c] cursor-pointer transition-colors"
                  >
                    <td className="py-3 font-mono">
                      {new Date(s.started_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3">
                      <span className="font-mono text-[11px] text-slate-400">
                        {s.is_simulation ? 'Simulated' : 'Hardware'}
                      </span>
                    </td>
                    <td className="py-3 font-mono">{s.total_movements}</td>
                    <td className="py-3 font-mono">
                      {s.avg_transition_duration ? `${(s.avg_transition_duration / 1000).toFixed(2)}s` : '—'}
                    </td>
                    <td className="py-3 font-mono font-bold text-sky-400">
                      {s.rmi_score ? `${s.rmi_score} pts` : '—'}
                    </td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                        {s.status}
                      </span>
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
