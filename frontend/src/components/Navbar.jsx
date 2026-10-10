import React from 'react';
import { Cpu, LayoutDashboard, ScanEye, FileSpreadsheet, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, healthInfo, onRefreshHealth, isCheckingHealth }) {
  const isOnline = healthInfo?.status === 'healthy';
  const modelLoaded = healthInfo?.model_loaded === true;

  let statusText = 'CONNECTING...';
  let statusClass = 'offline';
  let StatusIcon = AlertCircle;

  if (isOnline) {
    if (modelLoaded) {
      statusText = 'AI ENGINE READY';
      statusClass = 'online';
      StatusIcon = CheckCircle2;
    } else {
      statusText = 'WEIGHTS MISSING';
      statusClass = 'offline';
      StatusIcon = AlertCircle;
    }
  } else if (healthInfo?.error) {
    statusText = 'BACKEND OFFLINE';
    statusClass = 'offline';
    StatusIcon = AlertCircle;
  }

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <div className="brand-icon-wrapper">
          <Cpu size={24} />
        </div>
        <div>
          <span>PCB SENTINEL</span>
          <span className="brand-badge">YOLOv8 QA</span>
        </div>
      </div>

      <div className="nav-links">
        <button
          className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </button>

        <button
          className={`nav-link ${activeTab === 'inspect' ? 'active' : ''}`}
          onClick={() => setActiveTab('inspect')}
        >
          <ScanEye size={18} />
          <span>Inspect PCB</span>
        </button>

        <button
          className={`nav-link ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileSpreadsheet size={18} />
          <span>Reports</span>
        </button>
      </div>

      <div className="nav-status">
        <div className="status-indicator" title={healthInfo?.model_status_message || 'Backend telemetry'}>
          <span className={`status-dot ${statusClass}`}></span>
          <span style={{ fontWeight: 600 }}>{statusText}</span>
        </div>

        <button
          className="btn btn-secondary"
          style={{ padding: '0.4rem 0.6rem' }}
          onClick={onRefreshHealth}
          title="Refresh Backend Telemetry"
          disabled={isCheckingHealth}
        >
          <RefreshCw size={14} className={isCheckingHealth ? 'spin' : ''} />
        </button>
      </div>
    </nav>
  );
}
