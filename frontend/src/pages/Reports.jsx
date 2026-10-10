import React, { useState } from 'react';
import { 
  FileText, Download, Printer, ArrowLeft, CheckCircle2, 
  AlertTriangle, Shield, Calendar, User, Clock, Hash,
  FileDown, RefreshCw
} from 'lucide-react';
import { resolveResultImageUrl, downloadInspectionPDF } from '../services/api';

export default function Reports({ 
  inspectionHistory = [], 
  selectedReport, 
  onBackToDashboard 
}) {
  const [currentReport, setCurrentReport] = useState(
    selectedReport || (inspectionHistory.length > 0 ? inspectionHistory[0] : null)
  );
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = async () => {
    if (!currentReport) return;
    try {
      setIsDownloadingPDF(true);
      await downloadInspectionPDF(currentReport);
    } catch (err) {
      console.error('Failed to download PDF:', err);
      alert('Failed to download PDF report from server. Please check backend logs.');
    } finally {
      setIsDownloadingPDF(false);
    }
  };

  if (!currentReport) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <FileText size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
        <h3 style={{ marginBottom: '0.5rem' }}>No Inspection Reports Available</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Execute a PCB inspection to generate verifiable quality assurance documentation.
        </p>
        <button className="btn btn-primary" onClick={onBackToDashboard}>
          Return to Dashboard
        </button>
      </div>
    );
  }

  const {
    inspection_id,
    timestamp,
    original_filename,
    image_width,
    image_height,
    annotated_image_url,
    inference_time_ms,
    detections,
    summary,
  } = currentReport;

  const isPass = summary.pass_inspection;
  const fullAnnotatedUrl = resolveResultImageUrl(annotated_image_url);

  return (
    <div>
      {/* Action Bar */}
      <div className="page-header">
        <button className="btn btn-secondary" onClick={onBackToDashboard}>
          <ArrowLeft size={16} />
          <span>Back to Dashboard</span>
        </button>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {inspectionHistory.length > 1 && (
            <select
              className="btn btn-secondary"
              value={currentReport.inspection_id}
              onChange={(e) => {
                const found = inspectionHistory.find((item) => item.inspection_id === e.target.value);
                if (found) setCurrentReport(found);
              }}
              style={{ padding: '0.5rem 1rem' }}
            >
              {inspectionHistory.map((h) => (
                <option key={h.inspection_id} value={h.inspection_id}>
                  {h.inspection_id} - {h.original_filename} ({h.summary.total_defects} flaws)
                </option>
              ))}
            </select>
          )}

          <button className="btn btn-primary" onClick={handleDownloadPDF} disabled={isDownloadingPDF}>
            {isDownloadingPDF ? <RefreshCw size={16} className="spin" /> : <FileDown size={16} />}
            <span>Download PDF Report</span>
          </button>

          <button className="btn btn-secondary" onClick={handlePrint}>
            <Printer size={16} />
            <span>Print Certificate</span>
          </button>
        </div>
      </div>

      {/* Printable Quality Certificate Sheet */}
      <div className="card" style={{ 
        maxWidth: '900px', 
        margin: '0 auto', 
        background: '#0d1527', 
        border: '1px solid var(--border-active)',
        padding: '2.5rem'
      }}>
        
        {/* Certificate Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'flex-start',
          borderBottom: '2px solid var(--border-subtle)',
          paddingBottom: '1.5rem',
          marginBottom: '2rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Shield size={28} color="var(--color-accent)" />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.025em' }}>
                PCB SENTINEL QUALITY CERTIFICATE
              </h2>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
              Automated Optical Inspection (AOI) System | YOLOv8 Defect Classifier
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ 
              display: 'inline-block',
              padding: '0.35rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              fontWeight: 700,
              fontFamily: 'var(--font-mono)',
              background: isPass ? 'rgba(0, 229, 153, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: isPass ? 'var(--color-accent)' : 'var(--color-danger)',
              border: `1px solid ${isPass ? 'rgba(0, 229, 153, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`
            }}>
              {isPass ? 'STATUS: ACCEPTED' : 'STATUS: REJECTED'}
            </span>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Report ID: {inspection_id}
            </div>
          </div>
        </div>

        {/* Telemetry Summary Metadata Table */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: '1rem',
          background: 'var(--bg-surface)',
          padding: '1.25rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '2rem',
          border: '1px solid var(--border-subtle)'
        }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Target Sample</span>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{original_filename}</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{image_width} × {image_height} px</span>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Inspection Timestamp</span>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{new Date(timestamp).toLocaleDateString()}</div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{new Date(timestamp).toLocaleTimeString()}</span>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Inference Duration</span>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--color-cyan)', fontFamily: 'var(--font-mono)' }}>
              {inference_time_ms} ms
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Neural processing latency</span>
          </div>
        </div>

        {/* Annotated Visual Inspection Image */}
        <div style={{ marginBottom: '2rem' }}>
          <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Annotated Defect Spatial Overlay
          </h4>
          <div className="preview-container" style={{ maxHeight: '380px' }}>
            <img src={fullAnnotatedUrl} alt="Annotated Result" className="preview-image" style={{ maxHeight: '380px' }} />
          </div>
        </div>

        {/* Defect Itemization Table */}
        <div style={{ marginBottom: '2rem' }}>
          <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Detected Anomaly Itemization ({summary.total_defects})
          </h4>
          
          {detections.length === 0 ? (
            <div style={{ padding: '1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', textAlign: 'center', color: 'var(--color-accent)' }}>
              Zero manufacturing defects detected on board surface. Complies with Class-3 IPC criteria.
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Defect Class</th>
                  <th>Bounding Box [X1, Y1, X2, Y2]</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {detections.map((d) => (
                  <tr key={d.defect_id}>
                    <td>{d.defect_id}</td>
                    <td>
                      <span className={`defect-tag ${d.standard_class || 'open'}`}>
                        {d.class_name}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      [{d.bbox.x1}, {d.bbox.y1}] → [{d.bbox.x2}, {d.bbox.y2}]
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {d.confidence_percentage}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Sign-off Section */}
        <div style={{ 
          borderTop: '1px solid var(--border-subtle)', 
          paddingTop: '1.5rem', 
          display: 'grid', 
          gridTemplateColumns: 'repeat(2, 1fr)', 
          gap: '2rem' 
        }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Quality Assurance Engineer
            </span>
            <div style={{ marginTop: '1.5rem', borderBottom: '1px solid var(--border-active)', paddingBottom: '0.25rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                System Automated Sign-off: YOLOv8 Engine
              </span>
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Approval Date
            </span>
            <div style={{ marginTop: '1.5rem', borderBottom: '1px solid var(--border-active)', paddingBottom: '0.25rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                {new Date().toISOString().split('T')[0]}
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
