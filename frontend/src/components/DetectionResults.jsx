import React, { useState } from 'react';
import { 
  CheckCircle, AlertTriangle, Download, ArrowLeft, 
  Layers, Maximize2, FileText, Clock, Hash, Percent,
  FileDown, RefreshCw
} from 'lucide-react';
import { resolveResultImageUrl, downloadInspectionPDF } from '../services/api';

export default function DetectionResults({ 
  result, 
  originalPreviewUrl, 
  onReset, 
  onViewReport 
}) {
  const [activeView, setActiveView] = useState('annotated'); // 'annotated' | 'original' | 'split'
  const [selectedDefect, setSelectedDefect] = useState(null);
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);

  if (!result) return null;

  const {
    inspection_id,
    timestamp,
    original_filename,
    image_width,
    image_height,
    annotated_image_url,
    annotated_image_filename,
    inference_time_ms,
    detections,
    summary,
  } = result;

  const fullAnnotatedUrl = resolveResultImageUrl(annotated_image_url);
  const isPass = summary.pass_inspection;

  const downloadAnnotatedImage = async () => {
    try {
      const response = await fetch(fullAnnotatedUrl);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `annotated_${original_filename || 'pcb_result.jpg'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error('Failed to download annotated image:', err);
      window.open(fullAnnotatedUrl, '_blank');
    }
  };

  const handleDownloadPDF = async () => {
    try {
      setIsDownloadingPDF(true);
      await downloadInspectionPDF(result);
    } catch (err) {
      console.error('Failed to generate PDF:', err);
      alert('Failed to generate PDF report from server. Please consult backend logs.');
    } finally {
      setIsDownloadingPDF(false);
    }
  };

  return (
    <div>
      {/* Top Action Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <button className="btn btn-secondary" onClick={onReset}>
          <ArrowLeft size={16} />
          <span>New Inspection</span>
        </button>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={downloadAnnotatedImage}>
            <Download size={16} />
            <span>Download Image</span>
          </button>
          <button className="btn btn-primary" onClick={handleDownloadPDF} disabled={isDownloadingPDF}>
            {isDownloadingPDF ? <RefreshCw size={16} className="spin" /> : <FileDown size={16} />}
            <span>Download PDF Report</span>
          </button>
          {onViewReport && (
            <button className="btn btn-secondary" onClick={() => onViewReport(result)}>
              <FileText size={16} />
              <span>View Certificate</span>
            </button>
          )}
        </div>
      </div>

      {/* Industrial Inspection Status Banner */}
      <div className={`metric-card ${isPass ? 'accent' : 'danger'}`} style={{ marginBottom: '1.5rem', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ 
            background: isPass ? 'rgba(0, 229, 153, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${isPass ? 'rgba(0, 229, 153, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            color: isPass ? 'var(--color-accent)' : 'var(--color-danger)'
          }}>
            {isPass ? <CheckCircle size={32} /> : <AlertTriangle size={32} />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ 
                fontSize: '1.5rem', 
                fontWeight: 700, 
                color: isPass ? 'var(--color-accent)' : 'var(--color-danger)' 
              }}>
                {isPass ? 'QC INSPECTION PASSED: DEFECT-FREE' : `DEFECTIVE PCB: ${summary.total_defects} ANOMALIES DETECTED`}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.85rem', flexWrap: 'wrap' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Hash size={14} /> ID: <code style={{ color: 'var(--text-primary)' }}>{inspection_id}</code>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Clock size={14} /> Latency: <strong style={{ color: 'var(--color-cyan)' }}>{inference_time_ms} ms</strong>
              </span>
              <span>Dimensions: {image_width} × {image_height} px</span>
              <span>File: {original_filename}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Visual Inspector + Telemetry Cards */}
      <div className="grid-2" style={{ gridTemplateColumns: '1.25fr 0.75fr', alignItems: 'start' }}>
        
        {/* Left Column: Visual Viewport with Mode Switcher */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Layers size={18} color="var(--color-accent)" />
              Optical Inspection Viewport
            </h3>
            <div style={{ display: 'flex', gap: '0.35rem', background: 'var(--bg-surface)', padding: '0.25rem', borderRadius: 'var(--radius-sm)' }}>
              <button 
                className={`btn btn-secondary`} 
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', background: activeView === 'annotated' ? 'var(--bg-surface-elevated)' : 'transparent', borderColor: 'transparent' }}
                onClick={() => setActiveView('annotated')}
              >
                Annotated Overlay
              </button>
              <button 
                className={`btn btn-secondary`} 
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', background: activeView === 'original' ? 'var(--bg-surface-elevated)' : 'transparent', borderColor: 'transparent' }}
                onClick={() => setActiveView('original')}
              >
                Original Raw Image
              </button>
            </div>
          </div>

          <div className="preview-container" style={{ minHeight: '440px', background: '#020617' }}>
            {activeView === 'annotated' ? (
              <img 
                src={fullAnnotatedUrl} 
                alt="YOLOv8 Annotated Defect Map" 
                className="preview-image"
                style={{ cursor: 'zoom-in' }}
                onClick={() => window.open(fullAnnotatedUrl, '_blank')}
              />
            ) : (
              <img 
                src={originalPreviewUrl} 
                alt="Raw PCB Capture" 
                className="preview-image"
              />
            )}
          </div>
          <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Click image to open high-resolution view in new tab</span>
            <span>Bounding boxes rendered via YOLOv8 plot engine</span>
          </div>
        </div>

        {/* Right Column: Defect Breakdown & List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Summary Counts by Class */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem' }}>
              Defect Distribution Summary
            </h3>
            {summary.total_defects === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
                <CheckCircle size={36} color="var(--color-accent)" style={{ margin: '0 auto 0.5rem' }} />
                <p>No manufacturing flaws detected on this PCB.</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                {Object.entries(summary.defects_by_class).map(([className, count]) => (
                  <div 
                    key={className}
                    style={{ 
                      background: 'var(--bg-surface)', 
                      padding: '0.75rem', 
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{className}</span>
                    <span style={{ 
                      fontFamily: 'var(--font-mono)', 
                      fontSize: '1rem', 
                      fontWeight: 700,
                      color: 'var(--color-danger)'
                    }}>
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Detailed Defect Occurrences */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                Defect Telemetry ({detections.length})
              </h3>
              {summary.average_confidence && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Avg Conf: {(summary.average_confidence * 100).toFixed(1)}%
                </span>
              )}
            </div>

            {detections.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Board certified defect-free.</p>
            ) : (
              <div className="defect-list">
                {detections.map((defect) => {
                  const tagClass = defect.standard_class || 'open';
                  const isSelected = selectedDefect?.defect_id === defect.defect_id;

                  return (
                    <div 
                      key={defect.defect_id}
                      className="defect-item"
                      style={{ 
                        borderColor: isSelected ? 'var(--color-accent)' : undefined,
                        cursor: 'pointer'
                      }}
                      onClick={() => setSelectedDefect(defect)}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            #{defect.defect_id}
                          </span>
                          <span className={`defect-tag ${tagClass}`}>
                            {defect.class_name}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '0.35rem' }}>
                          Box: [{defect.bbox.x1}, {defect.bbox.y1}] → [{defect.bbox.x2}, {defect.bbox.y2}]
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ 
                          fontFamily: 'var(--font-mono)', 
                          fontSize: '0.95rem', 
                          fontWeight: 700,
                          color: defect.confidence >= 0.4 ? 'var(--color-accent)' : 'var(--color-warning)'
                        }}>
                          {defect.confidence_percentage}%
                        </div>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          Confidence
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
