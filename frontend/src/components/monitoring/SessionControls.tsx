import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, Clock } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { api } from '../../api/endpoints';

export const SessionControls: React.FC = () => {
  const { activeSession, currentUser, dispatch, simulationStatus } = useAppStore();
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let interval: any = null;
    if (activeSession && activeSession.status === 'active') {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(interval);
  }, [activeSession]);

  const handleStartHardwareSession = async () => {
    if (!currentUser) return;
    try {
      const newSession = await api.createSession({
        user_id: currentUser.id,
        is_simulation: false,
        device_id: 'ESP32-TORSO-NODE',
      });
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: newSession });
    } catch (_) {
      // ignore
    }
  };

  const handlePause = async () => {
    if (!activeSession) return;
    try {
      const updated = await api.updateSession(activeSession.id, { status: 'paused' });
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: updated });
    } catch (_) {
      // ignore
    }
  };

  const handleResume = async () => {
    if (!activeSession) return;
    try {
      const updated = await api.updateSession(activeSession.id, { status: 'active' });
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: updated });
    } catch (_) {
      // ignore
    }
  };

  const handleStop = async () => {
    if (!activeSession) return;
    try {
      if (simulationStatus.is_running) {
        await api.stopSimulation();
      }
      const updated = await api.completeSession(activeSession.id);
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: updated });
      dispatch({
        type: 'SET_SIMULATION_STATUS',
        payload: { ...simulationStatus, is_running: false },
      });
    } catch (_) {
      // ignore
    }
  };

  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d] flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Session Control
        </span>
        <div className="flex items-center gap-1.5 text-xs text-sky-400 font-mono">
          <Clock className="w-3.5 h-3.5" />
          <span>{formatTimer(elapsedSeconds)}</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {!activeSession ? (
          <button
            onClick={handleStartHardwareSession}
            className="flex-1 py-2 px-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-emerald-500/10"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Session</span>
          </button>
        ) : (
          <>
            {activeSession.status === 'active' ? (
              <button
                onClick={handlePause}
                className="flex-1 py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-amber-500/10"
              >
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={handleResume}
                className="flex-1 py-2 px-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-emerald-500/10"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume</span>
              </button>
            )}

            <button
              onClick={handleStop}
              className="flex-1 py-2 px-3 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center justify-center gap-2 transition-colors"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Finalize</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};
