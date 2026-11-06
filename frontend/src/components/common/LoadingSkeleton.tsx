import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 4 }) => {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-6 bg-[#172033] rounded-lg w-1/3" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-14 bg-[#141b2a] rounded-xl border border-[#1f293d]" />
      ))}
    </div>
  );
};
