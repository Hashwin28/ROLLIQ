import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface DurationDistributionProps {
  data: { session_id: string; date: string; avg_duration_ms: number; median_duration_ms: number }[];
  height?: number;
}

export const DurationDistribution: React.FC<DurationDistributionProps> = ({
  data,
  height = 240,
}) => {
  const chartData = data.map((d, idx) => ({
    session: `#${idx + 1}`,
    avg_s: (d.avg_duration_ms / 1000).toFixed(2),
    median_s: (d.median_duration_ms / 1000).toFixed(2),
  }));

  return (
    <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Transition Duration Distribution
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Average and median bed-mobility transition times in seconds
          </p>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            No session duration data available.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="session" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" unit="s" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="avg_s" name="Mean Duration" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="median_s" name="Median Duration" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
