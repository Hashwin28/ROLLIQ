import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  History,
  Cpu,
  Users,
  Radio,
  ShieldAlert,
} from 'lucide-react';
import { useAppStore } from '../../store/appStore';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Live Monitor', path: '/monitor', icon: Activity },
  { name: 'Mobility Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Recovery Timeline', path: '/recovery', icon: History },
  { name: 'Device Manager', path: '/devices', icon: Cpu },
  { name: 'User Profiles', path: '/users', icon: Users },
];

export const Sidebar: React.FC = () => {
  const { simulationStatus, connectionStatus } = useAppStore();

  return (
    <aside className="w-64 bg-[#0d121f] border-r border-[#1f293d] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div>
        <div className="p-5 flex items-center gap-3 border-b border-[#1f293d]">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-400/30 flex items-center justify-center shadow-lg shadow-sky-500/10">
            <Radio className="w-5 h-5 text-sky-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-wider text-white">ROLLIQ</span>
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                PROTOTYPE
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Bed-Mobility & Recovery</p>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#161f33]'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-4 border-t border-[#1f293d] space-y-3">
        {/* Simulation Indicator Badge */}
        {simulationStatus.is_running ? (
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              <span className="text-xs font-semibold text-amber-300 uppercase">
                Simulating
              </span>
            </div>
            <span className="text-[11px] text-amber-200 font-mono">
              {simulationStatus.speed}x
            </span>
          </div>
        ) : (
          <div className="p-2.5 rounded-lg bg-[#161f33] border border-[#232f48] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-emerald-400' : 'bg-slate-500'
                }`}
              />
              <span className="text-xs text-slate-300">
                {connectionStatus === 'connected' ? 'Hardware Live' : 'Hardware Idle'}
              </span>
            </div>
            <span className="text-[10px] text-slate-500">50 Hz</span>
          </div>
        )}

        {/* Disclaimer */}
        <div className="flex items-start gap-2 text-[10.5px] text-slate-400 px-1 leading-tight">
          <ShieldAlert className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <span>Experimental engineering system. Not for medical diagnosis.</span>
        </div>
      </div>
    </aside>
  );
};
