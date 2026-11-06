import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppStoreProvider } from './store/appStore';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { Analytics } from './pages/Analytics';
import { RecoveryTimeline } from './pages/RecoveryTimeline';
import { MovementDetail } from './pages/MovementDetail';
import { DeviceManagement } from './pages/DeviceManagement';
import { UserProfiles } from './pages/UserProfiles';

export function App() {
  return (
    <AppStoreProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/monitor" element={<LiveMonitoring />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/recovery" element={<RecoveryTimeline />} />
            <Route path="/movement/:sessionId/:movementId" element={<MovementDetail />} />
            <Route path="/devices" element={<DeviceManagement />} />
            <Route path="/users" element={<UserProfiles />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppStoreProvider>
  );
}

export default App;
