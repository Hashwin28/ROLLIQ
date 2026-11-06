import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { SensorReading } from '../../types';

interface LiveAccelChartProps {
  data: SensorReading[];
  height?: number;
}

export const LiveAccelChart: React.FC<LiveAccelChartProps> = ({
  data,
  height = 200,
}) => {
  // Format data for chart display
  const chartData = data.slice(-80).map((d, idx) => ({
    time: (d.timestamp_ms / 1000).toFixed(1),
    index: idx,
    ax: d.ax,
    ay: d.ay,
    az: d.az,
  }));

  return (
    <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Linear Acceleration (Tri-Axial)
          </span>
          <span className="text-[10px] text-slate-500 font-mono">±2g Dynamic Range</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1 text-rose-400">
            <span className="w-2 h-0.5 bg-rose-500 rounded-full" /> X (Roll)
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2 h-0.5 bg-emerald-500 rounded-full" /> Y (Pitch)
          </span>
          <span className="flex items-center gap-1 text-sky-400">
            <span className="w-2 h-0.5 bg-sky-500 rounded-full" /> Z (Gravity)
          </span>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            Awaiting accelerometer stream...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="index" hide />
              <YAxis
                domain={[-1.8, 1.8]}
                tick={{ fontSize: 10, fill: '#64748b' }}
                stroke="#2a374f"
                unit="g"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
                labelFormatter={(label) => `Sample #${label}`}
              />
              <Line
                type="monotone"
                dataKey="ax"
                stroke="#f43f5e"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="ay"
                stroke="#10b981"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="az"
                stroke="#38bdf8"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
