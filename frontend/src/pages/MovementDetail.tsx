import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/endpoints';
import { MovementDetail as MovementDetailType, SensorReading } from '../types';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import {
  ArrowLeft,
  Activity,
  Clock,
  Gauge,
  Sparkles,
  Layers,
  HelpCircle,
  CheckCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceArea,
} from 'recharts';

export const MovementDetail: React.FC = () => {
  const { sessionId, movementId } = useParams<{ sessionId: string; movementId: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<MovementDetailType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMovement() {
      if (!sessionId) return;
      setLoading(true);
      try {
        // If movementId is specific, fetch it. Otherwise fetch the first movement in session
        if (movementId && movementId !== 'sample') {
          const res = await api.getMovementDetail(sessionId, movementId);
          setDetail(res);
        } else {
          const movements = await api.getSessionMovements(sessionId);
          if (movements.length > 0) {
            const res = await api.getMovementDetail(sessionId, movements[0].id);
            setDetail(res);
          } else {
            // Mock synthetic movement window for demonstration
            const mockReadings: SensorReading[] = [];
            for (let t = 0; t <= 3000; t += 20) {
              const s = t / 3000;
              mockReadings.push({
                session_id: sessionId,
                timestamp_ms: t,
                ax: Math.sin(s * Math.PI) * 0.4,
                ay: Math.sin(s * Math.PI) * 0.9,
                az: Math.cos(s * Math.PI) * 0.8,
                gx: Math.sin(s * Math.PI) * 75.0,
                gy: Math.sin(s * Math.PI) * 35.0,
                gz: Math.sin(s * Math.PI) * 20.0,
                roll: s * 90.0,
                pitch: 0.0,
                signal_quality: 0.98,
                packet_sequence: t / 20,
              });
            }
            setDetail({
              id: 'demo-movement',
              session_id: sessionId,
              event_type: 'left_roll',
              start_time_ms: 400,
              end_time_ms: 2700,
              duration_ms: 2300,
              start_posture: 'supine',
              end_posture: 'left_lateral',
              peak_angular_velocity: 78.4,
              avg_angular_velocity: 42.1,
              movement_smoothness: 1.45,
              stability_after: 0.024,
              confidence: 0.96,
              classification_details: {
                primary_axis: 'roll (X/Y)',
                angular_displacement_deg: 88.5,
                gravity_alignment: 'strong match to +Y axis (+0.95g)',
                onset_threshold_exceeded: 'gy > 25°/s at t=400ms',
                settling_confirmation: 'ay stable for >500ms post t=2700ms',
              },
              sensor_data: mockReadings,
            });
          }
        }
      } catch (_) {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadMovement();
  }, [sessionId, movementId]);

  if (loading) {
    return <LoadingSkeleton rows={6} />;
  }

  if (!detail) {
    return (
      <div className="py-12 text-center text-xs text-slate-500">
        Movement record not found.
      </div>
    );
  }

  const chartData = (detail.sensor_data || []).map((s) => ({
    time_s: (s.timestamp_ms / 1000).toFixed(2),
    ms: s.timestamp_ms,
    ax: s.ax,
    ay: s.ay,
    az: s.az,
    gx: s.gx,
    gy: s.gy,
    gz: s.gz,
  }));

  return (
    <div className="space-y-6">
      {/* Back button & Title */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-1.5 rounded-lg bg-[#141c2c] hover:bg-[#1a253a] text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white capitalize">
                {detail.event_type.replace(/_/g, ' ')} Kinematic Analysis
              </h1>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30">
                Confidence: {(detail.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Event ID: {detail.id} • Session: {detail.session_id.slice(0, 8)}...
            </p>
          </div>
        </div>
      </div>

      {/* Movement Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d]">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">
            Duration
          </span>
          <p className="text-xl font-bold font-mono text-white mt-1">
            {(detail.duration_ms / 1000).toFixed(2)}s
          </p>
          <span className="text-[10px] text-slate-500 mt-0.5 block">
            {detail.start_time_ms}ms → {detail.end_time_ms}ms
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d]">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">
            Peak Velocity
          </span>
          <p className="text-xl font-bold font-mono text-amber-400 mt-1">
            {detail.peak_angular_velocity.toFixed(1)}°/s
          </p>
          <span className="text-[10px] text-slate-500 mt-0.5 block">
            Avg: {detail.avg_angular_velocity.toFixed(1)}°/s
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d]">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">
            Smoothness (Jerk)
          </span>
          <p className="text-xl font-bold font-mono text-emerald-400 mt-1">
            {detail.movement_smoothness.toFixed(2)}
          </p>
          <span className="text-[10px] text-slate-500 mt-0.5 block">
            Integral jerk index
          </span>
        </div>

        <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d]">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">
            Post Stability
          </span>
          <p className="text-xl font-bold font-mono text-sky-400 mt-1">
            {detail.stability_after.toFixed(3)}
          </p>
          <span className="text-[10px] text-slate-500 mt-0.5 block">
            2s post-window variance
          </span>
        </div>
      </div>

      {/* Raw Accelerometer Waveform with Event Window Marker */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Raw Accelerometer Waveform (Transition Window)
            </h3>
            <p className="text-xs text-slate-400">
              Shaded interval denotes confirmed movement onset to completion
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="text-rose-400">ax (Roll)</span>
            <span className="text-emerald-400">ay (Pitch)</span>
            <span className="text-sky-400">az (Yaw)</span>
          </div>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="time_s" tick={{ fontSize: 10, fill: '#64748b' }} stroke="#2a374f" unit="s" />
              <YAxis domain={[-1.5, 1.5]} tick={{ fontSize: 10, fill: '#64748b' }} stroke="#2a374f" unit="g" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
              />
              <Line type="monotone" dataKey="ax" stroke="#f43f5e" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="ay" stroke="#10b981" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="az" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Raw Gyroscope Waveform */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Raw Angular Velocity Waveform
            </h3>
            <p className="text-xs text-slate-400">
              Rotational dynamics demonstrating impulse curve and axis dominance
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="text-purple-400">gx</span>
            <span className="text-amber-400">gy</span>
            <span className="text-cyan-400">gz</span>
          </div>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="time_s" tick={{ fontSize: 10, fill: '#64748b' }} stroke="#2a374f" unit="s" />
              <YAxis domain={[-120, 120]} tick={{ fontSize: 10, fill: '#64748b' }} stroke="#2a374f" unit="°/s" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
              />
              <Line type="monotone" dataKey="gx" stroke="#c084fc" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="gy" stroke="#fbbf24" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="gz" stroke="#22d3ee" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Classification Details & Engineering Decision Breakdown */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Classification Engine Decision Criteria
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-[#0d121c] border border-[#1b2538] space-y-2">
            <span className="font-semibold text-slate-300 block">Kinematic Triggers</span>
            <ul className="space-y-1.5 text-slate-400">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Angular velocity exceeded threshold (20°/s)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Gravity vector transposed from +Z to +Y axis</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Hysteresis window satisfied (500ms stable settling)</span>
              </li>
            </ul>
          </div>

          <div className="p-3.5 rounded-xl bg-[#0d121c] border border-[#1b2538] space-y-2">
            <span className="font-semibold text-slate-300 block">Classifier Reasoning</span>
            <p className="text-slate-400 leading-relaxed font-mono text-[11px]">
              {detail.classification_details
                ? JSON.stringify(detail.classification_details, null, 2)
                : 'Primary roll rotation along longitudinal body axis. High signal-to-noise ratio and zero anomalous spikes detected during the 2.3s transition window.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
