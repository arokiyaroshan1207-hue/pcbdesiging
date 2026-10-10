import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera, RefreshCw, Check, X, SwitchCamera } from 'lucide-react';

export default function WebcamModal({ isOpen, onClose, onCapture }) {
  const webcamRef = useRef(null);
  const [facingMode, setFacingMode] = useState('environment'); // Default to rear/desk camera
  const [capturedImage, setCapturedImage] = useState(null);

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot({ width: 1920, height: 1080 });
      setCapturedImage(imageSrc);
    }
  }, [webcamRef]);

  const retake = () => {
    setCapturedImage(null);
  };

  const confirmCapture = async () => {
    if (!capturedImage) return;

    try {
      // Convert Data URL to real File/Blob for standard multipart upload
      const res = await fetch(capturedImage);
      const blob = await res.blob();
      const file = new File([blob], `webcam_pcb_${Date.now()}.jpg`, { type: 'image/jpeg' });
      onCapture(file, capturedImage);
      setCapturedImage(null);
      onClose();
    } catch (err) {
      console.error('Failed to convert webcam snapshot:', err);
    }
  };

  const toggleCamera = () => {
    setFacingMode((prev) => (prev === 'user' ? 'environment' : 'user'));
  };

  if (!isOpen) return null;

  const videoConstraints = {
    width: { ideal: 1920 },
    height: { ideal: 1080 },
    facingMode: facingMode,
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="modal-header">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Camera size={20} color="var(--color-accent)" />
            Live Inspection Camera Feed
          </h3>
          <button className="btn btn-secondary" style={{ padding: '0.35rem 0.6rem' }} onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          <div className="preview-container" style={{ minHeight: '380px' }}>
            {capturedImage ? (
              <img src={capturedImage} alt="Captured PCB snapshot" className="preview-image" />
            ) : (
              <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                videoConstraints={videoConstraints}
                style={{ width: '100%', height: 'auto', maxHeight: '420px', objectFit: 'contain' }}
              />
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem' }}>
            <div>
              {!capturedImage && (
                <button className="btn btn-secondary" onClick={toggleCamera} title="Switch camera source">
                  <SwitchCamera size={16} />
                  <span>Switch Camera</span>
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              {capturedImage ? (
                <>
                  <button className="btn btn-secondary" onClick={retake}>
                    <RefreshCw size={16} />
                    <span>Retake</span>
                  </button>
                  <button className="btn btn-primary" onClick={confirmCapture}>
                    <Check size={16} />
                    <span>Use Snapshot</span>
                  </button>
                </>
              ) : (
                <button className="btn btn-primary" onClick={capture}>
                  <Camera size={18} />
                  <span>Capture Photo</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
