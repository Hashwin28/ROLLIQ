import React from 'react';
import { motion } from 'framer-motion';
import { PostureType } from '../../types';

interface PostureIndicatorProps {
  posture: PostureType;
  confidence: number;
}

const postureConfig: Record<
  PostureType,
  { label: string; color: string; border: string; bg: string; rotation: number; pitchTilt: number }
> = {
  supine: {
    label: 'Supine (Back)',
    color: 'text-sky-400',
    border: 'border-sky-500/40',
    bg: 'bg-sky-500/10',
    rotation: 0,
    pitchTilt: 0,
  },
  left_lateral: {
    label: 'Left Lateral',
    color: 'text-cyan-400',
    border: 'border-cyan-500/40',
    bg: 'bg-cyan-500/10',
    rotation: -90,
    pitchTilt: 0,
  },
  right_lateral: {
    label: 'Right Lateral',
    color: 'text-teal-400',
    border: 'border-teal-500/40',
    bg: 'bg-teal-500/10',
    rotation: 90,
    pitchTilt: 0,
  },
  sitting: {
    label: 'Sitting Upright',
    color: 'text-emerald-400',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-500/10',
    rotation: 0,
    pitchTilt: -45,
  },
  prone: {
    label: 'Prone (Stomach)',
    color: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/10',
    rotation: 180,
    pitchTilt: 0,
  },
  unknown: {
    label: 'Transitional / Unknown',
    color: 'text-slate-400',
    border: 'border-slate-600',
    bg: 'bg-slate-800/20',
    rotation: 0,
    pitchTilt: 0,
  },
};

export const PostureIndicator: React.FC<PostureIndicatorProps> = ({
  posture = 'supine',
  confidence = 0.9,
}) => {
  const current = postureConfig[posture] || postureConfig.unknown;

  return (
    <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-[#121826] border border-[#20293d] relative overflow-hidden">
      {/* Background radial glow */}
      <div
        className={`absolute w-36 h-36 rounded-full blur-3xl opacity-20 pointer-events-none ${
          posture === 'supine'
            ? 'bg-sky-500'
            : posture === 'left_lateral' || posture === 'right_lateral'
            ? 'bg-cyan-500'
            : posture === 'sitting'
            ? 'bg-emerald-500'
            : 'bg-amber-500'
        }`}
      />

      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-4">
        Torso Orientation State
      </span>

      {/* Anatomical Torso Silhouette Visualization */}
      <div className="relative w-44 h-44 flex items-center justify-center">
        {/* Outer Circular Confidence Gauge */}
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="88"
            cy="88"
            r="80"
            stroke="currentColor"
            strokeWidth="4"
            className="text-slate-800"
            fill="transparent"
          />
          <circle
            cx="88"
            cy="88"
            r="80"
            stroke="currentColor"
            strokeWidth="4"
            strokeDasharray={502}
            strokeDashoffset={502 - 502 * Math.min(1, Math.max(0, confidence))}
            strokeLinecap="round"
            className={`transition-all duration-500 ${current.color}`}
            fill="transparent"
          />
        </svg>

        {/* Center Stylized Abstract Body & Torso IMU Representation */}
        <motion.div
          animate={{
            rotate: current.rotation,
            scale: posture === 'sitting' ? 1.08 : 1.0,
          }}
          transition={{ type: 'spring', stiffness: 120, damping: 15 }}
          className={`absolute w-24 h-28 rounded-2xl border-2 flex flex-col items-center justify-center shadow-lg transition-colors duration-300 ${current.bg} ${current.border}`}
        >
          {/* Head indicator */}
          <div className="w-6 h-6 rounded-full border border-current opacity-80 mb-1" />

          {/* Torso IMU Sensor Chip icon */}
          <div className="w-12 h-14 rounded-lg bg-[#0a0e1a]/80 border border-current/40 flex flex-col items-center justify-center p-1">
            <span className="text-[9px] font-mono font-bold tracking-tighter text-slate-300">
              MPU
            </span>
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping mt-1" />
          </div>

          {/* Orientation Arrow */}
          <div className="w-0.5 h-3 bg-current mt-1 opacity-70" />
        </motion.div>
      </div>

      {/* Posture Name & Confidence Label */}
      <div className="mt-4 text-center">
        <h4 className={`text-base font-bold tracking-tight ${current.color}`}>
          {current.label}
        </h4>
        <p className="text-xs text-slate-400 mt-0.5 font-mono">
          Confidence: {(confidence * 100).toFixed(0)}%
        </p>
      </div>
    </div>
  );
};
