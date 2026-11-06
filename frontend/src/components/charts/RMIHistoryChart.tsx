import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface RMIHistoryChartProps {
  data: { date: string; rmi_score: number; total_movements: number }[];
  height?: number;
}

export const RMIHistoryChart: React.FC<RMIHistoryChartProps> = ({
  data,
  height = 240,
}) => {
  const chartData = data.map((d, idx) => ({
    session: `#${idx + 1}`,
    score: d.rmi_score,
    movements: d.total_movements,
    date: new Date(d.date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            ROLLIQ Mobility Index (RMI) History
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Experimental composite mobility score progression (0–100)
          </p>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            No historical session data available yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="rmiGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="session" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(val: any) => [`${val} pts`, 'RMI Score']}
                labelFormatter={(l, p) => `${p[0]?.payload?.date || l}`}
              />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#38bdf8"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#rmiGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
