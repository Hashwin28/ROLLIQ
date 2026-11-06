import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import {
  User,
  MonitoringSession,
  PostureType,
  MovementEvent,
  SensorReading,
  Alert,
  SimulationStatus,
} from '../types';
import { api } from '../api/endpoints';

interface AppState {
  currentUser: User | null;
  users: User[];
  activeSession: MonitoringSession | null;
  livePosture: PostureType;
  postureConfidence: number;
  sensorBuffer: SensorReading[];
  recentMovements: MovementEvent[];
  alerts: Alert[];
  simulationStatus: SimulationStatus;
  connectionStatus: 'connected' | 'disconnected' | 'simulating';
}

type Action =
  | { type: 'SET_USERS'; payload: User[] }
  | { type: 'SET_CURRENT_USER'; payload: User | null }
  | { type: 'SET_ACTIVE_SESSION'; payload: MonitoringSession | null }
  | { type: 'SET_POSTURE'; payload: { posture: PostureType; confidence: number } }
  | { type: 'APPEND_SENSOR_DATA'; payload: SensorReading[] }
  | { type: 'ADD_MOVEMENT_EVENT'; payload: MovementEvent }
  | { type: 'SET_ALERTS'; payload: Alert[] }
  | { type: 'ADD_ALERT'; payload: Alert }
  | { type: 'MARK_ALERT_READ'; payload: string }
  | { type: 'SET_SIMULATION_STATUS'; payload: SimulationStatus }
  | { type: 'SET_CONNECTION_STATUS'; payload: 'connected' | 'disconnected' | 'simulating' }
  | { type: 'CLEAR_SENSOR_BUFFER' };

const initialState: AppState = {
  currentUser: null,
  users: [],
  activeSession: null,
  livePosture: 'supine',
  postureConfidence: 0.95,
  sensorBuffer: [],
  recentMovements: [],
  alerts: [],
  simulationStatus: {
    is_running: false,
    is_paused: false,
    speed: 1.0,
    elapsed_ms: 0,
    samples_generated: 0,
  },
  connectionStatus: 'disconnected',
};

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_USERS':
      return { ...state, users: action.payload };
    case 'SET_CURRENT_USER':
      return { ...state, currentUser: action.payload };
    case 'SET_ACTIVE_SESSION':
      return { ...state, activeSession: action.payload };
    case 'SET_POSTURE':
      return {
        ...state,
        livePosture: action.payload.posture,
        postureConfidence: action.payload.confidence,
      };
    case 'APPEND_SENSOR_DATA': {
      // Keep a rolling buffer of 150 points for responsive 50Hz charts
      const nextBuffer = [...state.sensorBuffer, ...action.payload].slice(-150);
      return { ...state, sensorBuffer: nextBuffer };
    }
    case 'ADD_MOVEMENT_EVENT':
      return {
        ...state,
        recentMovements: [action.payload, ...state.recentMovements].slice(0, 50),
      };
    case 'SET_ALERTS':
      return { ...state, alerts: action.payload };
    case 'ADD_ALERT':
      return {
        ...state,
        alerts: [action.payload, ...state.alerts.filter((a) => a.id !== action.payload.id)],
      };
    case 'MARK_ALERT_READ':
      return {
        ...state,
        alerts: state.alerts.map((a) =>
          a.id === action.payload ? { ...a, is_read: true } : a
        ),
      };
    case 'SET_SIMULATION_STATUS':
      return {
        ...state,
        simulationStatus: action.payload,
        connectionStatus: action.payload.is_running ? 'simulating' : state.connectionStatus,
      };
    case 'SET_CONNECTION_STATUS':
      return { ...state, connectionStatus: action.payload };
    case 'CLEAR_SENSOR_BUFFER':
      return { ...state, sensorBuffer: [], recentMovements: [] };
    default:
      return state;
  }
}

interface AppContextValue extends AppState {
  dispatch: React.Dispatch<Action>;
  refreshUsers: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  refreshSimulationStatus: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | null>(null);

export const AppStoreProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const refreshUsers = async () => {
    try {
      const uList = await api.getUsers();
      dispatch({ type: 'SET_USERS', payload: uList });
      if (uList.length > 0 && !state.currentUser) {
        dispatch({ type: 'SET_CURRENT_USER', payload: uList[0] });
      }
    } catch (_) {
      // initial load error
    }
  };

  const refreshAlerts = async () => {
    try {
      const aList = await api.getAlerts();
      dispatch({ type: 'SET_ALERTS', payload: aList });
    } catch (_) {
      // ignore
    }
  };

  const refreshSimulationStatus = async () => {
    try {
      const s = await api.getSimulationStatus();
      dispatch({ type: 'SET_SIMULATION_STATUS', payload: s });
    } catch (_) {
      // ignore
    }
  };

  useEffect(() => {
    refreshUsers();
    refreshAlerts();
    refreshSimulationStatus();
  }, []);

  return (
    <AppContext.Provider
      value={{
        ...state,
        dispatch,
        refreshUsers,
        refreshAlerts,
        refreshSimulationStatus,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export function useAppStore() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppStoreProvider');
  }
  return context;
}
