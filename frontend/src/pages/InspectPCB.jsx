import React, { useState, useRef } from 'react';
import { 
  UploadCloud, Camera, Cpu, AlertCircle, RefreshCw, 
  Sliders, Image as ImageIcon, Sparkles, CheckCircle2 
} from 'lucide-react';
import WebcamModal from '../components/WebcamModal';
import DetectionResults from '../components/DetectionResults';
import { detectPCBDefects, extractErrorMessage, API_BASE_URL } from '../services/api';

/**
 * Optimizes oversized photos (especially smartphone camera captures > 2048px or > 2.5MB)
 * to speed up upload transfer and prevent cloud container memory limits from triggering.
 */
async function optimizeImageForUpload(file, maxDimension = 2048, quality = 0.92) {
  if (!file || !file.type.startsWith('image/')) return file;
  if (file.size < 1.5 * 1024 * 1024 && !file.type.includes('bmp')) {
    return file; // Already reasonably sized
  }

  return new Promise((resolve) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      let { width, height } = img;

      if (width <= maxDimension && height <= maxDimension && file.size < 3 * 1024 * 1024) {
        resolve(file);
        return;
      }

      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = Math.round((height * maxDimension) / width);
          width = maxDimension;
        } else {
          width = Math.round((width * maxDimension) / height);
          height = maxDimension;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          if (blob && blob.size < file.size) {
            const optimizedFile = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });
            resolve(optimizedFile);
          } else {
            resolve(file);
          }
        },
        'image/jpeg',
        quality
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(file);
    };

    img.src = objectUrl;
  });
}

export default function InspectPCB({ onInspectionComplete, onViewReport, healthInfo, isCheckingHealth }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isWebcamOpen, setIsWebcamOpen] = useState(false);
  
  // Detection parameters
  const [confThreshold, setConfThreshold] = useState(0.25);
  const [iouThreshold, setIouThreshold] = useState(0.45);

  // Execution states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState('');
  const [error, setError] = useState(null);
  const [detectionResult, setDetectionResult] = useState(null);

  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|bmp|webp)$/i)) {
      setError('Unsupported file type. Please upload a JPEG, PNG, BMP, or WebP image.');
      return;
    }

    setError(null);
    setSelectedFile(file);
    setDetectionResult(null);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleWebcamCapture = (file, dataUrl) => {
    setSelectedFile(file);
    setPreviewUrl(dataUrl);
    setDetectionResult(null);
    setError(null);
  };

  // Quick load sample PCB image from backend sample assets
  const loadSamplePCB = async (sampleName = 'pcb1.jpg') => {
    try {
      setError(null);
      setAnalysisStep('Loading test sample PCB image...');
      // Fetch sample PCB directly using configured API base URL (with local proxy fallback)
      let response = await fetch(`${API_BASE_URL}/sample-images/${sampleName}`).catch(() => null);
      if (!response || !response.ok) {
        response = await fetch(`/api/sample-images/${sampleName}`).catch(() => null);
      }
      
      let blob = null;
      if (response && response.ok) {
        blob = await response.blob();
      }

      if (blob) {
        const file = new File([blob], sampleName, { type: 'image/jpeg' });
        handleFileSelect(file);
      } else {
        setError(`Could not fetch test sample ${sampleName}. Please upload manually.`);
      }
    } catch (err) {
      console.warn('Could not load sample automatically:', err);
      setError('Could not load sample PCB image.');
    } finally {
      setAnalysisStep('');
    }
  };

  const runAnalysis = async () => {
    if (!selectedFile) {
      setError('Please select or capture a PCB image before running analysis.');
      return;
    }

    try {
      setIsAnalyzing(true);
      setError(null);

      const isServerAsleep = !healthInfo || healthInfo?.status === 'offline';
      if (isServerAsleep) {
        setAnalysisStep('Connecting to AI backend pipeline (waking server if on standby)...');
      } else {
        setAnalysisStep('Optimizing image for detection pipeline...');
      }

      // Optimize oversized smartphone photos to prevent upload delay and memory exhaustion
      const fileToUpload = await optimizeImageForUpload(selectedFile, 2048, 0.92);

      setAnalysisStep('Streaming PCB image to backend pipeline...');
      await new Promise((r) => setTimeout(r, 200));
      setAnalysisStep('Running YOLOv8 inference and defect classification...');

      const result = await detectPCBDefects(fileToUpload, confThreshold, iouThreshold);

      setAnalysisStep('Formatting bounding box overlays...');
      setDetectionResult(result);

      if (onInspectionComplete) {
        onInspectionComplete(result);
      }
    } catch (err) {
      console.error('Detection failed:', err);
      setError(extractErrorMessage(err));
    } finally {
      setIsAnalyzing(false);
      setAnalysisStep('');
    }
  };

  const resetInspection = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setDetectionResult(null);
    setError(null);
  };

  // If inspection completed, render the results view
  if (detectionResult) {
    return (
      <DetectionResults 
        result={detectionResult}
        originalPreviewUrl={previewUrl}
        onReset={resetInspection}
        onViewReport={onViewReport}
      />
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Cpu size={28} color="var(--color-accent)" />
            PCB Quality Inspection Station
          </h1>
          <p className="page-subtitle">
            Upload printed circuit board micrographs or stream from live camera feed to detect manufacturing flaws.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert-banner alert-danger" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <AlertCircle size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Inspection Notice:</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.9rem' }}>{error}</p>
            </div>
          </div>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', whiteSpace: 'nowrap', marginLeft: '1rem' }}
            onClick={runAnalysis}
            disabled={isAnalyzing}
          >
            <RefreshCw size={14} className={isAnalyzing ? 'spin' : ''} /> Retry
          </button>
        </div>
      )}

      <div className="grid-2" style={{ gridTemplateColumns: '1.2fr 0.8fr', alignItems: 'start' }}>
        
        {/* Left Column: Image Ingestion Station */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <ImageIcon size={18} color="var(--color-accent)" />
              Optical Image Ingestion
            </h3>
            {previewUrl && (
              <button className="btn btn-secondary" style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem' }} onClick={resetInspection}>
                <RefreshCw size={14} /> Clear Image
              </button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/bmp,image/webp"
            style={{ display: 'none' }}
            onChange={(e) => handleFileSelect(e.target.files?.[0])}
          />

          {!previewUrl ? (
            <div
              className={`upload-dropzone ${isDragActive ? 'drag-active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="upload-icon" />
              <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                Drag and drop PCB image here
              </h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
                Supports high-resolution JPEG, PNG, BMP, and WebP (up to 15 MB)
              </p>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }} onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <UploadCloud size={16} />
                  <span>Browse File</span>
                </button>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsWebcamOpen(true)}
                >
                  <Camera size={16} />
                  <span>Webcam Capture</span>
                </button>
              </div>

              {/* One-Click Sample Test Buttons */}
              <div 
                style={{ 
                  marginTop: '1.5rem', 
                  paddingTop: '1.25rem', 
                  borderTop: '1px solid var(--border-subtle)', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  gap: '0.5rem', 
                  flexWrap: 'wrap' 
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Quick Test Samples:
                </span>
                {['pcb1.jpg', 'pcb2.jpg', 'pcb8.jpg', 'pcb10.jpg'].map((sName) => (
                  <button
                    key={sName}
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}
                    onClick={() => loadSamplePCB(sName)}
                  >
                    {sName}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="preview-container">
              <img src={previewUrl} alt="PCB Inspection Target" className="preview-image" />
              
              {isAnalyzing && (
                <div className="scanning-overlay">
                  <div className="scan-laser"></div>
                  <div style={{ 
                    background: 'var(--bg-secondary)', 
                    padding: '1.25rem 2rem', 
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-active)',
                    textAlign: 'center',
                    boxShadow: 'var(--shadow-lg)'
                  }}>
                    <RefreshCw size={24} className="spin" color="var(--color-accent)" style={{ margin: '0 auto 0.75rem' }} />
                    <strong style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>Analyzing Circuit Geometry</strong>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                      {analysisStep || 'Executing YOLOv8 neural network inference...'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {previewUrl && !isAnalyzing && (
            <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Target: {selectedFile?.name || 'captured_pcb.jpg'} ({((selectedFile?.size || 0) / 1024).toFixed(1)} KB)
              </span>
              <button 
                className="btn btn-secondary" 
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}
                onClick={() => setIsWebcamOpen(true)}
              >
                <Camera size={14} /> Retake via Webcam
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Inference Parameters & Execution Station */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1.25rem' }}>
              <Sliders size={18} color="var(--color-accent)" />
              Inference Tuning Parameters
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="slider-group">
                <div className="slider-label">
                  <span>Confidence Threshold</span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-accent)' }}>
                    {Math.round(confThreshold * 100)}%
                  </strong>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.95"
                  step="0.05"
                  value={confThreshold}
                  onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                  className="slider-input"
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Filters out candidate detections with confidence below {Math.round(confThreshold * 100)}%.
                </span>
              </div>

              <div className="slider-group">
                <div className="slider-label">
                  <span>IoU NMS Threshold</span>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-cyan)' }}>
                    {Math.round(iouThreshold * 100)}%
                  </strong>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.90"
                  step="0.05"
                  value={iouThreshold}
                  onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                  className="slider-input"
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Suppresses redundant overlapping bounding boxes.
                </span>
              </div>
            </div>
          </div>

          {/* Action Trigger Card */}
          <div className="card" style={{ background: 'var(--bg-surface)' }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={16} color="var(--color-accent)" />
              Automated Inspection Pipeline
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Scans for 6 standard manufacturing flaws: Open Circuit, Short Circuit, Mouse Bite, Spur, Spurious Copper, and Missing Hole.
            </p>

            {(!healthInfo || healthInfo?.status === 'offline') && (
              <div style={{
                background: 'rgba(234, 179, 8, 0.08)',
                border: '1px solid rgba(234, 179, 8, 0.25)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.6rem 0.85rem',
                fontSize: '0.8rem',
                color: '#eab308',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}>
                <AlertCircle size={15} style={{ flexShrink: 0 }} />
                <span>Backend is on standby. First inspection will wake container (~40-50s).</span>
              </div>
            )}

            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.875rem 1.5rem', fontSize: '1rem' }}
              disabled={!selectedFile || isAnalyzing}
              onClick={runAnalysis}
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw size={18} className="spin" />
                  <span>Processing YOLOv8 Inference...</span>
                </>
              ) : (
                <>
                  <Cpu size={18} />
                  <span>Analyze PCB</span>
                </>
              )}
            </button>
          </div>

        </div>

      </div>

      {/* Webcam Capture Modal */}
      <WebcamModal
        isOpen={isWebcamOpen}
        onClose={() => setIsWebcamOpen(false)}
        onCapture={handleWebcamCapture}
      />
    </div>
  );
}
