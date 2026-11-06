import React, { useEffect } from 'react';
import { useAppStore } from '../store/appStore';
import { SensorWebSocket } from '../api/websocket';
import { PostureIndicator } from '../components/monitoring/PostureIndicator';
import { SignalQuality } from '../components/monitoring/SignalQuality';
import { SessionControls } from '../components/monitoring/SessionControls';
import { SimulationPanel } from '../components/monitoring/SimulationPanel';
import { LiveAccelChart } from '../components/charts/LiveAccelChart';
import { LiveGyroChart } from '../components/charts/LiveGyroChart';
import { MovementTimeline } from '../components/charts/MovementTimeline';
import { PostureType } from '../types';

export const LiveMonitoring: React.FC = () => {
  const {
    activeSession,
    livePosture,
    postureConfidence,
    sensorBuffer,
    recentMovements,
    simulationStatus,
    dispatch,
  } = useAppStore();

  // Connect WebSocket when session is active
  useEffect(() => {
    if (!activeSession) return;

    const ws = new SensorWebSocket(activeSession.id);
    ws.connect();

    const unsubscribe = ws.subscribe((msg: any) => {
      if (msg.type === 'sensor_data' && Array.isArray(msg.readings)) {
        dispatch({ type: 'APPEND_SENSOR_DATA', payload: msg.readings });
      } else if (msg.type === 'posture_update') {
        dispatch({
          type: 'SET_POSTURE',
          payload: {
            posture: msg.posture as PostureType,
            confidence: msg.confidence,
          },
        });
      } else if (msg.type === 'movement_event' && msg.movement) {
        dispatch({ type: 'ADD_MOVEMENT_EVENT', payload: msg.movement });
      } else if (msg.type === 'alert' && msg.alert) {
        dispatch({ type: 'ADD_ALERT', payload: msg.alert });
      }
    });

    return () => {
      unsubscribe();
      ws.disconnect();
    };
  }, [activeSession?.id]);

  return (
    <div className="space-y-6">
      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1f293d]">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Live Postural Telemetry
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time 50 Hz kinematic streaming & edge event classification
          </p>
        </div>

        <div className="flex items-center gap-3">
          {simulationStatus.is_running ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              <span>Simulated Stream Active ({simulationStatus.speed}x)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Edge Telemetry Ready</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Grid: Left Controls (1 col) + Right Real-time Waveforms (2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Posture visualizer, Signal quality, Session & Simulator controls */}
        <div className="space-y-4">
          <PostureIndicator
            posture={livePosture}
            confidence={postureConfidence}
          />
          <SignalQuality
            quality={sensorBuffer.length > 0 ? sensorBuffer[sensorBuffer.length - 1].signal_quality : 0.95}
            sampleRate={50}
          />
          <SessionControls />
          <SimulationPanel />
        </div>

        {/* Right Column: Live Accel & Gyro charts + Movement sequence */}
        <div className="lg:col-span-2 space-y-4">
          <LiveAccelChart data={sensorBuffer} height={210} />
          <LiveGyroChart data={sensorBuffer} height={210} />

          {/* Movement sequence timeline */}
          <div className="pt-2">
            <MovementTimeline
              movements={recentMovements}
              sessionId={activeSession?.id}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
