import React from 'react';
import { Cpu, LayoutDashboard, ScanEye, FileSpreadsheet, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, healthInfo, onRefreshHealth, isCheckingHealth }) {
  const isOnline = healthInfo?.status === 'healthy';
  const modelLoaded = healthInfo?.model_loaded === true;
  const isStandby = healthInfo?.status === 'offline';

  let statusText = 'CONNECTING...';
  let statusClass = 'connecting';
  let StatusIcon = AlertCircle;

  if (isCheckingHealth && !healthInfo) {
    statusText = 'WAKING UP SERVER...';
    statusClass = 'connecting';
  } else if (isOnline) {
    if (modelLoaded) {
      statusText = 'AI ENGINE READY';
      statusClass = 'online';
      StatusIcon = CheckCircle2;
    } else if (healthInfo?.model_file_exists === false) {
      statusText = 'WEIGHTS MISSING';
      statusClass = 'offline';
      StatusIcon = AlertCircle;
    } else {
      statusText = 'ENGINE INITIALIZING';
      statusClass = 'connecting';
      StatusIcon = AlertCircle;
    }
  } else if (isCheckingHealth) {
    statusText = 'RECONNECTING...';
    statusClass = 'connecting';
  } else if (isStandby || healthInfo?.error) {
    statusText = 'STANDBY (WAKING UP)';
    statusClass = 'standby';
    StatusIcon = AlertCircle;
  }

  const tooltipText = isOnline
    ? (healthInfo?.model_status_message || 'Backend operational & model ready')
    : (isStandby
        ? 'Backend is asleep on Render Free Tier. Waking up takes ~50s.'
        : 'Connecting to backend telemetry...');

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
        <div className="status-indicator" title={tooltipText}>
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
