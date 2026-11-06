export type PostureType =
  | 'supine'
  | 'prone'
  | 'left_lateral'
  | 'right_lateral'
  | 'sitting'
  | 'unknown';

export type MovementEventType =
  | 'left_roll'
  | 'right_roll'
  | 'supine_to_sitting'
  | 'sitting_to_supine'
  | 'posture_transition'
  | 'minor_adjustment'
  | 'unclassified';

export interface User {
  id: string;
  display_name: string;
  age_group?: 'child' | 'adult' | 'elderly' | null;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  name: string;
  last_seen: string;
  firmware_version?: string | null;
  is_active: boolean;
  calibration_data?: Record<string, any> | null;
  created_at: string;
}

export interface MonitoringSession {
  id: string;
  user_id: string;
  device_id?: string | null;
  is_simulation: boolean;
  simulation_scenario?: string | null;
  status: 'active' | 'paused' | 'completed' | 'incomplete';
  started_at: string;
  ended_at?: string | null;
  total_movements: number;
  avg_transition_duration?: number | null;
  rmi_score?: number | null;
  notes?: string | null;
  metrics?: SessionMetrics | null;
}

export interface SensorReading {
  id?: number;
  session_id: string;
  timestamp_ms: number;
  ax: number;
  ay: number;
  az: number;
  gx: number;
  gy: number;
  gz: number;
  roll: number;
  pitch: number;
  signal_quality: number;
  packet_sequence: number;
}

export interface MovementEvent {
  id: string;
  session_id: string;
  event_type: MovementEventType;
  start_time_ms: number;
  end_time_ms: number;
  duration_ms: number;
  start_posture?: string | null;
  end_posture?: string | null;
  peak_angular_velocity: number;
  avg_angular_velocity: number;
  movement_smoothness: number;
  stability_after: number;
  confidence: number;
  classification_details?: Record<string, any> | null;
  sensor_data_start_idx?: number | null;
  sensor_data_end_idx?: number | null;
}

export interface MovementDetail extends MovementEvent {
  sensor_data: SensorReading[];
}

export interface SessionMetrics {
  id: string;
  session_id: string;
  total_movements: number;
  total_left_rolls: number;
  total_right_rolls: number;
  total_sit_transitions: number;
  avg_transition_duration_ms: number;
  median_transition_duration_ms: number;
  avg_angular_velocity: number;
  avg_smoothness: number;
  avg_stability: number;
  movement_symmetry: number;
  rmi_score: number;
  rmi_components?: {
    duration: number;
    smoothness: number;
    velocity: number;
    stability: number;
    completion: number;
    consistency: number;
  } | null;
  data_completeness: number;
  session_duration_ms: number;
}

export interface PersonalBaseline {
  id: string;
  user_id: string;
  sessions_used: number;
  avg_transition_duration: number;
  std_transition_duration: number;
  avg_angular_velocity: number;
  std_angular_velocity: number;
  avg_smoothness: number;
  std_smoothness: number;
  avg_stability: number;
  std_stability: number;
  avg_rmi: number;
  std_rmi: number;
  last_updated: string;
  is_ready: boolean;
  baseline_data?: {
    progress?: number;
    sessions_needed?: number;
    message?: string;
  } | null;
}

export interface BaselineComparison {
  metric_name: string;
  current_value: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  deviation_direction: string;
  is_significant: boolean;
}

export interface BaselineComparisonResult {
  user_id: string;
  session_id: string;
  baseline_ready: boolean;
  comparisons: BaselineComparison[];
  overall_deviation?: string | null;
}

export interface Alert {
  id: string;
  session_id?: string | null;
  user_id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'attention';
  title: string;
  message: string;
  measurement_value?: number | null;
  threshold_value?: number | null;
  is_read: boolean;
  created_at: string;
}

export interface SimulationScenario {
  name: string;
  description: string;
  estimated_duration_s: number;
}

export interface SimulationStatus {
  is_running: boolean;
  is_paused: boolean;
  scenario?: string | null;
  session_id?: string | null;
  speed: number;
  elapsed_ms: number;
  samples_generated: number;
}
