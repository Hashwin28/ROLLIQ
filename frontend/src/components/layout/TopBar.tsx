import React, { useState } from 'react';
import {
  Bell,
  User as UserIcon,
  Wifi,
  WifiOff,
  Radio,
  Play,
  Square,
  ChevronDown,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import { api } from '../../api/endpoints';

export const TopBar: React.FC = () => {
  const {
    currentUser,
    users,
    activeSession,
    alerts,
    connectionStatus,
    simulationStatus,
    dispatch,
  } = useAppStore();

  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const unreadAlerts = alerts.filter((a) => !a.is_read).length;

  const handleStopSession = async () => {
    if (activeSession) {
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
    }
  };

  return (
    <header className="h-16 bg-[#0a0e1a]/80 backdrop-blur-md border-b border-[#1f293d] px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Active Session Status */}
      <div className="flex items-center gap-4">
        {activeSession ? (
          <div className="flex items-center gap-3 bg-[#131b2e] border border-sky-500/30 rounded-full px-3.5 py-1.5 shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <div className="flex items-center gap-2 text-xs">
              <span className="font-semibold text-slate-200">
                Session Active
              </span>
              <span className="text-slate-400 font-mono text-[11px]">
                {activeSession.is_simulation ? '(Simulated)' : '(Hardware)'}
              </span>
            </div>
            <button
              onClick={handleStopSession}
              className="ml-2 text-rose-400 hover:text-rose-300 p-1 hover:bg-rose-500/10 rounded-full transition-colors"
              title="Stop and finalize session"
            >
              <Square className="w-3.5 h-3.5 fill-rose-400" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-[#121826] border border-[#1f293d] rounded-full px-3 py-1">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            <span>Ready for session</span>
          </div>
        )}
      </div>

      {/* Right controls: Hardware state, Alerts, User Profile */}
      <div className="flex items-center gap-4">
        {/* Hardware Status Pill */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${
            simulationStatus.is_running
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              : connectionStatus === 'connected'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-slate-800/40 border-slate-700/50 text-slate-400'
          }`}
        >
          {simulationStatus.is_running ? (
            <>
              <Radio className="w-3.5 h-3.5 animate-pulse text-amber-400" />
              <span>Sim Mode</span>
            </>
          ) : connectionStatus === 'connected' ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-emerald-400" />
              <span>ESP32 Node Online</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-slate-500" />
              <span>Sensor Standby</span>
            </>
          )}
        </div>

        {/* Alerts Bell */}
        <div className="relative">
          <div className="w-9 h-9 rounded-lg bg-[#141b2a] border border-[#232e44] flex items-center justify-center text-slate-300 hover:text-white cursor-pointer hover:border-slate-500 transition-colors">
            <Bell className="w-4 h-4" />
            {unreadAlerts > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-[10px] font-bold text-black rounded-full flex items-center justify-center shadow-md">
                {unreadAlerts}
              </span>
            )}
          </div>
        </div>

        {/* User Switcher */}
        <div className="relative">
          <button
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-[#141b2a] border border-[#232e44] hover:border-slate-500 text-slate-200 transition-colors"
          >
            <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center text-xs font-bold">
              {currentUser?.display_name.charAt(0) || 'U'}
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold leading-none text-slate-200">
                {currentUser?.display_name || 'Select User'}
              </p>
              <p className="text-[10px] text-slate-400 capitalize">
                {currentUser?.age_group || 'Subject'}
              </p>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* User selector dropdown menu */}
          {userDropdownOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-[#141b2a] border border-[#232e44] rounded-xl shadow-2xl py-1 z-50">
              <div className="px-3 py-1.5 border-b border-[#232e44] text-[11px] font-semibold uppercase text-slate-400">
                Switch Subject
              </div>
              {users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => {
                    dispatch({ type: 'SET_CURRENT_USER', payload: u });
                    setUserDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-sky-500/10 ${
                    u.id === currentUser?.id ? 'text-sky-400 font-semibold bg-sky-500/5' : 'text-slate-300'
                  }`}
                >
                  <span>{u.display_name}</span>
                  <span className="text-[10px] text-slate-400 capitalize">{u.age_group}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
