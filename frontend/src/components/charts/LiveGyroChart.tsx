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

interface LiveGyroChartProps {
  data: SensorReading[];
  height?: number;
}

export const LiveGyroChart: React.FC<LiveGyroChartProps> = ({
  data,
  height = 200,
}) => {
  const chartData = data.slice(-80).map((d, idx) => ({
    time: (d.timestamp_ms / 1000).toFixed(1),
    index: idx,
    gx: d.gx,
    gy: d.gy,
    gz: d.gz,
  }));

  return (
    <div className="p-4 rounded-xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Angular Velocity (Gyroscope)
          </span>
          <span className="text-[10px] text-slate-500 font-mono">±250°/s Range</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1 text-purple-400">
            <span className="w-2 h-0.5 bg-purple-500 rounded-full" /> ωX (Roll)
          </span>
          <span className="flex items-center gap-1 text-amber-400">
            <span className="w-2 h-0.5 bg-amber-500 rounded-full" /> ωY (Pitch)
          </span>
          <span className="flex items-center gap-1 text-cyan-400">
            <span className="w-2 h-0.5 bg-cyan-500 rounded-full" /> ωZ (Yaw)
          </span>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            Awaiting gyroscope stream...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="index" hide />
              <YAxis
                domain={[-150, 150]}
                tick={{ fontSize: 10, fill: '#64748b' }}
                stroke="#2a374f"
                unit="°/s"
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
                dataKey="gx"
                stroke="#c084fc"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="gy"
                stroke="#fbbf24"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="gz"
                stroke="#22d3ee"
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
