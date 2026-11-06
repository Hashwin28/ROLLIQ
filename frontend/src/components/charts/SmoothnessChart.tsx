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

interface SmoothnessChartProps {
  data: { session_id: string; date: string; avg_smoothness: number }[];
  height?: number;
}

export const SmoothnessChart: React.FC<SmoothnessChartProps> = ({
  data,
  height = 240,
}) => {
  const chartData = data.map((d, idx) => ({
    session: `#${idx + 1}`,
    jerk: d.avg_smoothness,
  }));

  return (
    <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Movement Smoothness (Jerk Index)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized kinematic jerk. Lower values indicate smoother, coordinated transitions.
          </p>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            No smoothness records recorded.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="session" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" unit=" jerk" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Line
                type="monotone"
                dataKey="jerk"
                name="Jerk Metric"
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#f59e0b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
