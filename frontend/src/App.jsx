import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import InspectPCB from './pages/InspectPCB';
import Reports from './pages/Reports';
import { getHealthStatus } from './services/api';

const STORAGE_KEY = 'pcb_sentinel_inspections_history';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [healthInfo, setHealthInfo] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);

  // Load inspection history from localStorage
  const [inspectionHistory, setInspectionHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (!saved) return [];
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
    } catch (e) {
      console.warn('Failed to parse localStorage history:', e);
      return [];
    }
  });

  // Save history to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(inspectionHistory));
    } catch (e) {
      console.warn('Failed to save inspection history to localStorage:', e);
    }
  }, [inspectionHistory]);

  // Query backend health
  const refreshHealth = useCallback(async () => {
    try {
      setIsCheckingHealth(true);
      const data = await getHealthStatus();
      setHealthInfo(data);
    } catch (err) {
      console.warn('Health check failed:', err);
      setHealthInfo({ status: 'offline', error: err.message, model_loaded: false });
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  // Adaptive polling: poll every 5s while waking up/offline, every 30s when healthy
  useEffect(() => {
    const pollInterval = healthInfo?.status === 'healthy' ? 30000 : 5000;
    const interval = setInterval(refreshHealth, pollInterval);
    return () => clearInterval(interval);
  }, [refreshHealth, healthInfo?.status]);

  const handleInspectionComplete = (result) => {
    setInspectionHistory((prev) => [result, ...prev]);
    // Refresh backend health in case model state updated
    refreshHealth();
  };

  const handleViewReport = (result) => {
    setSelectedReport(result);
    setActiveTab('reports');
  };

  const handleSelectHistoricalInspection = (item) => {
    setSelectedReport(item);
    setActiveTab('reports');
  };

  const isServerSleeping = !healthInfo || healthInfo?.status === 'offline';

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthInfo={healthInfo}
        onRefreshHealth={refreshHealth}
        isCheckingHealth={isCheckingHealth}
      />

      {/* Render Free-Tier Cold-Start Awareness Banner */}
      {isServerSleeping && (
        <div className="cold-start-banner">
          <div className="cold-start-content">
            <span className="cold-start-pulse"></span>
            <div>
              <strong>Cloud Backend Warming Up (Render Free Tier):</strong>{' '}
              <span>
                Free hosting instances sleep after 15 minutes of inactivity. Initial wake-up takes ~40-60 seconds.
                {isCheckingHealth ? ' Pinging server...' : ' Waiting for container boot.'}
              </span>
            </div>
          </div>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.78rem', padding: '0.3rem 0.75rem', whiteSpace: 'nowrap' }}
            onClick={refreshHealth}
            disabled={isCheckingHealth}
          >
            {isCheckingHealth ? 'Checking...' : 'Check Server'}
          </button>
        </div>
      )}

      <main className="main-content">
        {activeTab === 'dashboard' && (
          <Dashboard
            inspectionHistory={inspectionHistory}
            onNavigateInspect={() => setActiveTab('inspect')}
            healthInfo={healthInfo}
            isCheckingHealth={isCheckingHealth}
            onSelectInspection={handleSelectHistoricalInspection}
          />
        )}

        {activeTab === 'inspect' && (
          <InspectPCB
            healthInfo={healthInfo}
            isCheckingHealth={isCheckingHealth}
            onInspectionComplete={handleInspectionComplete}
            onViewReport={handleViewReport}
          />
        )}

        {activeTab === 'reports' && (
          <Reports
            inspectionHistory={inspectionHistory}
            selectedReport={selectedReport}
            onBackToDashboard={() => setActiveTab('dashboard')}
          />
        )}
      </main>
    </div>
  );
}
