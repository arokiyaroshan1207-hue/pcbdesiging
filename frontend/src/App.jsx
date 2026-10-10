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
      return saved ? JSON.parse(saved) : [];
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
    // Re-check health every 30 seconds
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, [refreshHealth]);

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

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthInfo={healthInfo}
        onRefreshHealth={refreshHealth}
        isCheckingHealth={isCheckingHealth}
      />

      <main className="main-content">
        {activeTab === 'dashboard' && (
          <Dashboard
            inspectionHistory={inspectionHistory}
            onNavigateInspect={() => setActiveTab('inspect')}
            healthInfo={healthInfo}
            onSelectInspection={handleSelectHistoricalInspection}
          />
        )}

        {activeTab === 'inspect' && (
          <InspectPCB
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
