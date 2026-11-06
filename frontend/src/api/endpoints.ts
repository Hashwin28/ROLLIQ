import { apiRequest } from './client';
import {
  User,
  Device,
  MonitoringSession,
  MovementEvent,
  MovementDetail,
  SensorReading,
  SessionMetrics,
  PersonalBaseline,
  BaselineComparisonResult,
  Alert,
  SimulationScenario,
  SimulationStatus,
} from '../types';

export const api = {
  // Users
  getUsers: () => apiRequest<User[]>('/api/users'),
  getUser: (id: string) => apiRequest<User>(`/api/users/${id}`),
  createUser: (data: { display_name: string; age_group?: string }) =>
    apiRequest<User>('/api/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getUserBaseline: (userId: string) =>
    apiRequest<PersonalBaseline | null>(`/api/users/${userId}/baseline`),
  getUserSummary: (userId: string) =>
    apiRequest<any>(`/api/users/${userId}/summary`),

  // Sessions
  getSessions: (params?: { user_id?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.user_id) query.append('user_id', params.user_id);
    if (params?.status) query.append('status', params.status);
    return apiRequest<MonitoringSession[]>(`/api/sessions?${query.toString()}`);
  },
  getSession: (id: string) => apiRequest<MonitoringSession>(`/api/sessions/${id}`),
  createSession: (data: {
    user_id: string;
    device_id?: string;
    is_simulation?: boolean;
    simulation_scenario?: string;
    notes?: string;
  }) =>
    apiRequest<MonitoringSession>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateSession: (id: string, data: { status?: string; notes?: string }) =>
    apiRequest<MonitoringSession>(`/api/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteSession: (id: string) =>
    apiRequest<void>(`/api/sessions/${id}`, { method: 'DELETE' }),
  completeSession: (id: string) =>
    apiRequest<MonitoringSession>(`/api/sessions/${id}/complete`, {
      method: 'POST',
    }),

  // Movements & Sensor Data
  getSessionMovements: (sessionId: string) =>
    apiRequest<MovementEvent[]>(`/api/sessions/${sessionId}/movements`),
  getMovementDetail: (sessionId: string, movementId: string) =>
    apiRequest<MovementDetail>(
      `/api/sessions/${sessionId}/movements/${movementId}`
    ),
  getSessionSensorData: (
    sessionId: string,
    params?: { from_ms?: number; to_ms?: number; limit?: number }
  ) => {
    const query = new URLSearchParams();
    if (params?.from_ms !== undefined)
      query.append('from_ms', params.from_ms.toString());
    if (params?.to_ms !== undefined)
      query.append('to_ms', params.to_ms.toString());
    if (params?.limit) query.append('limit', params.limit.toString());
    return apiRequest<SensorReading[]>(
      `/api/sessions/${sessionId}/sensor-data?${query.toString()}`
    );
  },
  getLatestReadings: (sessionId: string, limit = 200) =>
    apiRequest<SensorReading[]>(
      `/api/sensor/latest/${sessionId}?limit=${limit}`
    ),

  // Devices
  getDevices: () => apiRequest<Device[]>('/api/devices'),
  getDevice: (id: string) => apiRequest<Device>(`/api/devices/${id}`),
  registerDevice: (data: {
    id: string;
    name: string;
    firmware_version?: string;
  }) =>
    apiRequest<Device>('/api/devices', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getDeviceStatus: (id: string) =>
    apiRequest<any>(`/api/devices/${id}/status`),
  calibrateDevice: (
    id: string,
    data: {
      accel_offsets: Record<string, number>;
      gyro_offsets: Record<string, number>;
    }
  ) =>
    apiRequest<any>(`/api/devices/${id}/calibrate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Analytics
  getRMIHistory: (userId: string) =>
    apiRequest<any[]>(`/api/analytics/rmi-history/${userId}`),
  getMovementDistribution: (userId: string) =>
    apiRequest<any[]>(`/api/analytics/movement-distribution/${userId}`),
  getDurationTrends: (userId: string) =>
    apiRequest<any[]>(`/api/analytics/duration-trends/${userId}`),
  getSymmetryTrends: (userId: string) =>
    apiRequest<any[]>(`/api/analytics/symmetry/${userId}`),
  getSmoothnessTrends: (userId: string) =>
    apiRequest<any[]>(`/api/analytics/smoothness-trends/${userId}`),
  getBaselineComparison: (sessionId: string) =>
    apiRequest<BaselineComparisonResult>(
      `/api/analytics/baseline-comparison/${sessionId}`
    ),
  compareSessions: (sessionA: string, sessionB: string) =>
    apiRequest<any>(
      `/api/analytics/session-comparison?session_a_id=${sessionA}&session_b_id=${sessionB}`
    ),

  // Alerts
  getAlerts: (params?: { user_id?: string; unread_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.user_id) query.append('user_id', params.user_id);
    if (params?.unread_only) query.append('unread_only', 'true');
    return apiRequest<Alert[]>(`/api/alerts?${query.toString()}`);
  },
  markAlertRead: (id: string) =>
    apiRequest<Alert>(`/api/alerts/${id}/read`, { method: 'PATCH' }),

  // Simulation
  getSimulationScenarios: () =>
    apiRequest<SimulationScenario[]>('/api/simulation/scenarios'),
  getSimulationStatus: () =>
    apiRequest<SimulationStatus>('/api/simulation/status'),
  startSimulation: (data: {
    user_id: string;
    scenario?: string;
    speed?: number;
  }) =>
    apiRequest<SimulationStatus>('/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  stopSimulation: () =>
    apiRequest<SimulationStatus>('/api/simulation/stop', { method: 'POST' }),
  pauseSimulation: () =>
    apiRequest<SimulationStatus>('/api/simulation/pause', { method: 'POST' }),
  resumeSimulation: () =>
    apiRequest<SimulationStatus>('/api/simulation/resume', { method: 'POST' }),
  changeScenario: (scenario: string) =>
    apiRequest<SimulationStatus>('/api/simulation/scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),
};
