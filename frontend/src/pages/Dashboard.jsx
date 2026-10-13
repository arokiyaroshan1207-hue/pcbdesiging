import React from 'react';
import { 
  Scan, AlertOctagon, CheckCircle2, TrendingUp, 
  Cpu, ArrowUpRight, Clock, ShieldCheck, Activity 
} from 'lucide-react';

export default function Dashboard({ 
  inspectionHistory = [], 
  onNavigateInspect, 
  healthInfo, 
  onSelectInspection,
  isCheckingHealth = false,
}) {
  // Aggregate telemetry from inspection history defensively
  const safeHistory = Array.isArray(inspectionHistory) ? inspectionHistory.filter(Boolean) : [];
  const totalInspections = safeHistory.length;
  const totalDefects = safeHistory.reduce((sum, item) => sum + (item?.summary?.total_defects || 0), 0);
  const passCount = safeHistory.filter((item) => Boolean(item?.summary?.pass_inspection)).length;
  const passRate = totalInspections > 0 ? Math.round((passCount / totalInspections) * 100) : 100;

  // Aggregate defect breakdown by class across all historical runs
  const defectAggregates = {
    'Open Circuit': 0,
    'Short Circuit': 0,
    'Mouse Bite': 0,
    'Spur': 0,
    'Spurious Copper': 0,
    'Missing Hole': 0,
  };

  safeHistory.forEach((item) => {
    if (item && item.summary && item.summary.defects_by_class) {
      Object.entries(item.summary.defects_by_class).forEach(([cls, count]) => {
        if (defectAggregates[cls] !== undefined) {
          defectAggregates[cls] += count;
        } else {
          defectAggregates[cls] = (defectAggregates[cls] || 0) + count;
        }
      });
    }
  });

  return (
    <div>
      {/* Header with Quick Inspection CTA */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Activity size={28} color="var(--color-accent)" />
            PCB Quality Assurance Dashboard
          </h1>
          <p className="page-subtitle">
            Real-time telemetry, automated defect analytics, and quality control metrics.
          </p>
        </div>

        <button className="btn btn-primary" onClick={onNavigateInspect}>
          <Scan size={18} />
          <span>New PCB Inspection</span>
        </button>
      </div>

      {/* Top 4 Industrial Metric Cards */}
      <div className="grid-4">
        <div className="metric-card cyan">
          <div>
            <span className="metric-label">Total Inspections</span>
            <div className="metric-value">{totalInspections}</div>
            <span className="metric-subtitle">Completed quality cycles</span>
          </div>
          <div className="metric-icon-box">
            <Scan size={24} color="var(--color-cyan)" />
          </div>
        </div>

        <div className="metric-card danger">
          <div>
            <span className="metric-label">Defects Identified</span>
            <div className="metric-value">{totalDefects}</div>
            <span className="metric-subtitle">Across all inspected units</span>
          </div>
          <div className="metric-icon-box">
            <AlertOctagon size={24} color="var(--color-danger)" />
          </div>
        </div>

        <div className="metric-card accent">
          <div>
            <span className="metric-label">Pass Yield Rate</span>
            <div className="metric-value">{passRate}%</div>
            <span className="metric-subtitle">{passCount} of {totalInspections || 1} units passed</span>
          </div>
          <div className="metric-icon-box">
            <ShieldCheck size={24} color="var(--color-accent)" />
          </div>
        </div>

        {/* AI Inference Engine Status Card */}
        {(() => {
          const isHealthy = healthInfo?.status === 'healthy';
          const isModelLoaded = isHealthy && healthInfo?.model_loaded === true;
          const isStandby = healthInfo?.status === 'offline';

          let engineTitle = 'Standby / Asleep';
          let engineSubtitle = 'Render free tier waking up';
          let cardColorClass = 'warning';
          let iconColor = 'var(--color-warning)';

          if (isCheckingHealth && !healthInfo) {
            engineTitle = 'Connecting...';
            engineSubtitle = 'Reaching backend server';
            cardColorClass = 'warning';
            iconColor = 'var(--color-warning)';
          } else if (isModelLoaded) {
            engineTitle = 'YOLOv8 Active';
            engineSubtitle = 'best.pt verified (6 classes)';
            cardColorClass = 'accent';
            iconColor = 'var(--color-accent)';
          } else if (isHealthy && healthInfo?.model_file_exists === false) {
            engineTitle = 'Weights Missing';
            engineSubtitle = 'best.pt missing on backend';
            cardColorClass = 'danger';
            iconColor = 'var(--color-danger)';
          } else if (isHealthy) {
            engineTitle = 'Engine Warming Up';
            engineSubtitle = 'Loading best.pt weights';
            cardColorClass = 'warning';
            iconColor = 'var(--color-warning)';
          } else if (isStandby) {
            engineTitle = 'Server Asleep';
            engineSubtitle = 'Waking up on Render (~50s)';
            cardColorClass = 'warning';
            iconColor = 'var(--color-warning)';
          }

          return (
            <div className={`metric-card ${cardColorClass}`}>
              <div>
                <span className="metric-label">AI Inference Engine</span>
                <div className="metric-value" style={{ fontSize: '1.25rem', marginTop: '0.5rem' }}>
                  {engineTitle}
                </div>
                <span className="metric-subtitle">
                  {engineSubtitle}
                </span>
              </div>
              <div className="metric-icon-box">
                <Cpu size={24} color={iconColor} />
              </div>
            </div>
          );
        })()}
      </div>

      {/* Defect Distribution Breakdown Cards */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">
            <TrendingUp size={18} color="var(--color-accent)" />
            Defect Class Distribution
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            YOLOv8 6-Class PCB Taxonomy
          </span>
        </div>

        <div className="grid-3" style={{ marginBottom: 0 }}>
          {Object.entries(defectAggregates).map(([className, count]) => {
            let tagColor = 'var(--color-accent)';
            if (className.includes('Short')) tagColor = 'var(--color-warning)';
            if (className.includes('Open')) tagColor = 'var(--color-danger)';
            if (className.includes('Mouse')) tagColor = 'var(--color-purple)';
            if (className.includes('Spur')) tagColor = 'var(--color-cyan)';

            return (
              <div 
                key={className}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {className}
                  </span>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Classified flaws
                  </div>
                </div>
                <div style={{ 
                  fontFamily: 'var(--font-mono)', 
                  fontSize: '1.5rem', 
                  fontWeight: 700, 
                  color: count > 0 ? tagColor : 'var(--text-muted)' 
                }}>
                  {count}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Inspection Activity Log Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Clock size={18} color="var(--color-accent)" />
            Recent Inspection Activity Log
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Showing {inspectionHistory.length} inspection events
          </span>
        </div>

        {inspectionHistory.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
            <Scan size={42} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
            <h4 style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>No Inspections Recorded Yet</h4>
            <p style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              Upload or capture a PCB image to run automated defect analysis.
            </p>
            <button className="btn btn-primary" onClick={onNavigateInspect}>
              Start First Inspection
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inspection ID</th>
                  <th>Timestamp</th>
                  <th>Image Source</th>
                  <th>Defects</th>
                  <th>Avg Confidence</th>
                  <th>Inference Latency</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {inspectionHistory.map((item) => {
                  const isPass = item.summary?.pass_inspection;
                  return (
                    <tr key={item.inspection_id}>
                      <td>
                        <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-cyan)' }}>
                          {item.inspection_id}
                        </code>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {new Date(item.timestamp).toLocaleString()}
                      </td>
                      <td>{item.original_filename}</td>
                      <td>
                        <strong style={{ color: isPass ? 'var(--color-accent)' : 'var(--color-danger)' }}>
                          {item.summary?.total_defects || 0}
                        </strong>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>
                        {item.summary?.average_confidence ? `${(item.summary.average_confidence * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {item.inference_time_ms} ms
                      </td>
                      <td>
                        <span className={`defect-tag ${isPass ? 'short' : 'open'}`} style={{
                          background: isPass ? 'rgba(0, 229, 153, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: isPass ? 'var(--color-accent)' : 'var(--color-danger)',
                          borderColor: isPass ? 'rgba(0, 229, 153, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                        }}>
                          {isPass ? 'PASS' : 'DEFECTIVE'}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn btn-secondary" 
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          onClick={() => onSelectInspection(item)}
                        >
                          Review Result
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
