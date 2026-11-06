import React, { useEffect, useState } from 'react';
import { api } from '../api/endpoints';
import { Device } from '../types';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import {
  Cpu,
  Wifi,
  Radio,
  Sliders,
  CheckCircle2,
  RefreshCw,
  Plus,
  Activity,
  HardDrive,
} from 'lucide-react';

export const DeviceManagement: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [calibrating, setCalibrating] = useState(false);
  const [calibSuccess, setCalibSuccess] = useState(false);

  useEffect(() => {
    loadDevices();
  }, []);

  async function loadDevices() {
    setLoading(true);
    try {
      const data = await api.getDevices();
      setDevices(data);
    } catch (_) {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  const handleRegisterNode = async () => {
    try {
      const newDev = await api.registerDevice({
        id: `ESP32-TORSO-${Math.floor(1000 + Math.random() * 9000)}`,
        name: 'ESP32 NodeMCU (30-pin) + MPU6050',
        firmware_version: 'v1.0.4-firmware',
      });
      setDevices([newDev, ...devices]);
    } catch (_) {
      // ignore
    }
  };

  const handleCalibrate = async (devId: string) => {
    setCalibrating(true);
    setCalibSuccess(false);
    try {
      await api.calibrateDevice(devId, {
        accel_offsets: { x: 0.012, y: -0.008, z: 0.045 },
        gyro_offsets: { x: -0.42, y: 0.18, z: 0.05 },
      });
      setCalibSuccess(true);
      await loadDevices();
    } catch (_) {
      // ignore
    } finally {
      setCalibrating(false);
    }
  };

  if (loading) {
    return <LoadingSkeleton rows={4} />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1f293d]">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Device & Sensor Node Management
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            ESP32 NodeMCU (30-pin) and MPU6050 calibration & hardware health
          </p>
        </div>

        <button
          onClick={handleRegisterNode}
          className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 transition-colors flex items-center gap-2 shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Register Hardware Node</span>
        </button>
      </div>

      {/* Hardware Node Specifications & Wiring Reference */}
      <div className="p-5 rounded-2xl bg-[#121826] border border-[#20293d]">
        <div className="flex items-center gap-2 mb-3">
          <Cpu className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Hardware Architecture & Pin Configuration
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-xl bg-[#0e1422] border border-[#1d273b]">
            <span className="text-slate-400 block text-[11px]">Microcontroller</span>
            <span className="font-mono font-bold text-white mt-1 block">ESP32 30-Pin NodeMCU</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">240 MHz Dual-Core • Wi-Fi 802.11b/g/n</span>
          </div>

          <div className="p-3 rounded-xl bg-[#0e1422] border border-[#1d273b]">
            <span className="text-slate-400 block text-[11px]">IMU Sensor</span>
            <span className="font-mono font-bold text-white mt-1 block">MPU6050 6-Axis</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">±2g Accel • ±250°/s Gyro</span>
          </div>

          <div className="p-3 rounded-xl bg-[#0e1422] border border-[#1d273b]">
            <span className="text-slate-400 block text-[11px]">I2C Wiring</span>
            <span className="font-mono font-bold text-white mt-1 block">SDA: GPIO 21 • SCL: GPIO 22</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">VCC: 3.3V • GND: GND</span>
          </div>

          <div className="p-3 rounded-xl bg-[#0e1422] border border-[#1d273b]">
            <span className="text-slate-400 block text-[11px]">Sampling Protocol</span>
            <span className="font-mono font-bold text-white mt-1 block">50 Hz Fixed Sampling</span>
            <span className="text-[10px] text-slate-500 mt-0.5 block">HTTP Batching + WebSocket Live</span>
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="space-y-4">
        {devices.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 bg-[#121826] rounded-2xl border border-[#20293d]">
            No physical hardware devices registered yet. Click 'Register Hardware Node' to link an ESP32 unit.
          </div>
        ) : (
          devices.map((d) => (
            <div
              key={d.id}
              className="p-5 rounded-2xl bg-[#121826] border border-[#20293d] flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                  <HardDrive className="w-5 h-5" />
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-white">{d.name}</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                      Active
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 mt-1 font-mono flex items-center gap-3">
                    <span>Node ID: {d.id}</span>
                    <span>•</span>
                    <span>Firmware: {d.firmware_version || 'v1.0.4'}</span>
                    <span>•</span>
                    <span>
                      Last Seen:{' '}
                      {new Date(d.last_seen).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>
                  </p>

                  {d.calibration_data && (
                    <div className="mt-2 text-[11px] text-slate-400 font-mono bg-[#0d121c] p-2 rounded border border-[#1b2538] flex items-center gap-3">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Calibration Bias Corrected: Zero-g offset saved.</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions: Calibrate sensor */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleCalibrate(d.id)}
                  disabled={calibrating}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#182236] hover:bg-[#202d48] text-sky-400 border border-sky-500/30 transition-colors flex items-center gap-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${calibrating ? 'animate-spin' : ''}`} />
                  <span>{calibrating ? 'Calibrating...' : 'Calibrate Offsets'}</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
