import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

interface SymmetryChartProps {
  data: { session_id: string; left_rolls: number; right_rolls: number; symmetry_ratio: number }[];
  height?: number;
}

export const SymmetryChart: React.FC<SymmetryChartProps> = ({
  data,
  height = 240,
}) => {
  const chartData = data.map((d, idx) => ({
    session: `#${idx + 1}`,
    left: d.left_rolls,
    right: d.right_rolls,
    ratio: d.symmetry_ratio,
  }));

  return (
    <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Bilateral Turning Symmetry
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Left vs. right purposeful turning volume across sessions
          </p>
        </div>
      </div>

      <div style={{ height }} className="w-full">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            No symmetry records logged.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2538" />
              <XAxis dataKey="session" tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} stroke="#2a374f" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0d131f',
                  border: '1px solid #28364f',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              <Bar dataKey="left" name="Left Turns" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              <Bar dataKey="right" name="Right Turns" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
