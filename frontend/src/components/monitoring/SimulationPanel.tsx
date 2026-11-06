import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, Radio, FastForward, Sliders } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { api } from '../../api/endpoints';
import { SimulationScenario } from '../../types';

export const SimulationPanel: React.FC = () => {
  const { currentUser, simulationStatus, dispatch } = useAppStore();
  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState('normal_rolling');
  const [speed, setSpeed] = useState(1.0);

  useEffect(() => {
    api.getSimulationScenarios().then(setScenarios).catch(() => {});
  }, []);

  const handleStartSim = async () => {
    if (!currentUser) return;
    try {
      const res = await api.startSimulation({
        user_id: currentUser.id,
        scenario: selectedScenario,
        speed,
      });
      dispatch({ type: 'SET_SIMULATION_STATUS', payload: res });
      // Fetch the created session
      if (res.session_id) {
        const s = await api.getSession(res.session_id);
        dispatch({ type: 'SET_ACTIVE_SESSION', payload: s });
      }
    } catch (_) {
      // ignore
    }
  };

  const handleStopSim = async () => {
    try {
      const res = await api.stopSimulation();
      dispatch({ type: 'SET_SIMULATION_STATUS', payload: res });
    } catch (_) {
      // ignore
    }
  };

  const handlePauseSim = async () => {
    try {
      const res = await api.pauseSimulation();
      dispatch({ type: 'SET_SIMULATION_STATUS', payload: res });
    } catch (_) {
      // ignore
    }
  };

  const handleResumeSim = async () => {
    try {
      const res = await api.resumeSimulation();
      dispatch({ type: 'SET_SIMULATION_STATUS', payload: res });
    } catch (_) {
      // ignore
    }
  };

  const handleScenarioChange = async (newScen: string) => {
    setSelectedScenario(newScen);
    if (simulationStatus.is_running) {
      try {
        const res = await api.changeScenario(newScen);
        dispatch({ type: 'SET_SIMULATION_STATUS', payload: res });
      } catch (_) {
        // ignore
      }
    }
  };

  const selectedDesc = scenarios.find((s) => s.name === selectedScenario)?.description;

  return (
    <div className="p-4 rounded-xl bg-[#141824] border border-amber-500/30 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-amber-400 animate-pulse" />
          <span className="text-xs font-bold text-amber-300 uppercase tracking-wider">
            Sensor Simulator
          </span>
        </div>
        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
          Demo Engine
        </span>
      </div>

      {/* Scenario selector */}
      <div>
        <label className="text-[11px] text-slate-400 block mb-1 font-medium">
          Movement Scenario
        </label>
        <select
          value={selectedScenario}
          onChange={(e) => handleScenarioChange(e.target.value)}
          className="w-full bg-[#0d121c] border border-[#232f48] rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
        >
          {scenarios.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name.replace(/_/g, ' ').toUpperCase()}
            </option>
          ))}
        </select>
        {selectedDesc && (
          <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed bg-[#0a0e1a]/60 p-2 rounded border border-[#1b2336]">
            {selectedDesc}
          </p>
        )}
      </div>

      {/* Speed Controls */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400 font-medium">Playback Rate</span>
        <div className="flex items-center gap-1">
          {[0.5, 1.0, 2.0, 5.0].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
                speed === s
                  ? 'bg-amber-500 text-slate-950 font-bold'
                  : 'bg-[#1b2234] text-slate-400 hover:text-slate-200'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Simulation Controls */}
      <div className="flex items-center gap-2 pt-1">
        {!simulationStatus.is_running ? (
          <button
            onClick={handleStartSim}
            className="flex-1 py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-md shadow-amber-500/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Start Simulation</span>
          </button>
        ) : (
          <>
            {simulationStatus.is_paused ? (
              <button
                onClick={handleResumeSim}
                className="flex-1 py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume</span>
              </button>
            ) : (
              <button
                onClick={handlePauseSim}
                className="flex-1 py-2 px-3 rounded-lg bg-[#252f44] hover:bg-[#2e3a54] text-amber-300 text-xs font-semibold flex items-center justify-center gap-2"
              >
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause</span>
              </button>
            )}

            <button
              onClick={handleStopSim}
              className="flex-1 py-2 px-3 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center justify-center gap-2"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};
