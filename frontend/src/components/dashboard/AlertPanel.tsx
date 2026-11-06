import React from 'react';
import { Alert } from '../../types';
import { ShieldAlert, AlertTriangle, Info, Check } from 'lucide-react';
import { api } from '../../api/endpoints';
import { useAppStore } from '../../store/appStore';

interface AlertPanelProps {
  alerts: Alert[];
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  const { dispatch } = useAppStore();

  const handleMarkRead = async (id: string) => {
    try {
      await api.markAlertRead(id);
      dispatch({ type: 'MARK_ALERT_READ', payload: id });
    } catch (_) {
      // ignore
    }
  };

  const severityIcons = {
    attention: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
    warning: <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />,
    info: <Info className="w-4 h-4 text-sky-400 shrink-0" />,
  };

  return (
    <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">System Notifications</h3>
          <p className="text-xs text-slate-400 mt-0.5">Telemetry and postural health notices</p>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {alerts.filter((a) => !a.is_read).length} unread
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2.5 max-h-80 pr-1">
        {alerts.length === 0 ? (
          <div className="h-32 flex flex-col items-center justify-center text-xs text-slate-500">
            <span>No alerts recorded</span>
            <span className="text-[11px] text-slate-600 mt-0.5">Operating within normal parameters</span>
          </div>
        ) : (
          alerts.slice(0, 10).map((a) => (
            <div
              key={a.id}
              className={`p-3 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                a.is_read
                  ? 'bg-[#0f1523]/60 border-[#1c2538] opacity-60'
                  : 'bg-[#151d2e] border-sky-500/20'
              }`}
            >
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5">{severityIcons[a.severity] || severityIcons.info}</div>
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">{a.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{a.message}</p>
                  <span className="text-[10px] text-slate-400 font-mono mt-1 block">
                    {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>

              {!a.is_read && (
                <button
                  onClick={() => handleMarkRead(a.id)}
                  title="Mark read"
                  className="p-1 rounded-md hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
