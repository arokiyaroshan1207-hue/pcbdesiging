import axios from 'axios';

// Resolve API base URL with production fallback to live Render backend
const getProductionFallbackUrl = () => {
  if (typeof window !== 'undefined') {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isLocal) {
      return 'https://pcbdesiging.onrender.com/api';
    }
  }
  return 'http://localhost:8000/api';
};

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || getProductionFallbackUrl();
// Normalize: ensure it ends with /api without double slashes
export const API_BASE_URL = RAW_BASE_URL.replace(/\/+$/, '');
export const BACKEND_ROOT_URL = API_BASE_URL.replace(/\/api$/, '');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds for heavy image inference
});

/**
 * Format and extract clean error messages from API or network responses.
 */
export function extractErrorMessage(error) {
  if (!error) return 'An unknown error occurred.';
  if (error.response) {
    const data = error.response.data;
    if (data?.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (data.detail.message) return data.detail.message;
      if (Array.isArray(data.detail)) {
        return data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
      }
      return JSON.stringify(data.detail);
    }
    return `Server Error (${error.response.status}): ${error.response.statusText || 'Request failed'}`;
  }
  if (error.request) {
    return 'Cannot reach backend server. Please verify the backend is running or give Render 30-50s to wake up from inactivity.';
  }
  return error.message || 'Network request failed.';
}

/**
 * Resolve full URL for static result images.
 */
export function resolveResultImageUrl(relativeUrlOrFilename) {
  if (!relativeUrlOrFilename) return '';
  if (relativeUrlOrFilename.startsWith('http://') || relativeUrlOrFilename.startsWith('https://')) {
    return relativeUrlOrFilename;
  }
  if (relativeUrlOrFilename.startsWith('/api/')) {
    return `${BACKEND_ROOT_URL}${relativeUrlOrFilename}`;
  }
  return `${BACKEND_ROOT_URL}/api/results/${relativeUrlOrFilename}`;
}

/**
 * Check backend operational health and model readiness.
 */
export async function getHealthStatus() {
  const response = await apiClient.get('/health');
  return response.data;
}

/**
 * Upload a PCB image and perform YOLOv8 defect detection.
 *
 * @param {File|Blob} file Image file or webcam blob
 * @param {number} confThreshold Confidence threshold (0.01 - 1.0)
 * @param {number} iouThreshold IoU threshold (0.01 - 1.0)
 */
export async function detectPCBDefects(file, confThreshold = 0.25, iouThreshold = 0.45) {
  const formData = new FormData();
  formData.append('file', file, file.name || 'pcb_capture.jpg');

  const response = await apiClient.post('/detect', formData, {
    params: {
      conf_threshold: confThreshold,
      iou_threshold: iouThreshold,
    },
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Validate image file format and integrity without running inference.
 */
export async function validateImageFile(file) {
  const formData = new FormData();
  formData.append('file', file, file.name || 'pcb_upload.jpg');

  const response = await apiClient.post('/validate-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

/**
 * Request server-side compiled PDF inspection report and trigger browser download.
 *
 * @param {Object} inspectionData Complete InspectionResult payload
 */
export async function downloadInspectionPDF(inspectionData) {
  const response = await apiClient.post('/reports/generate-pdf', inspectionData, {
    responseType: 'blob',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const blob = new Blob([response.data], { type: 'application/pdf' });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  const inspectionId = inspectionData?.inspection_id || 'result';
  link.download = `PCB_Inspection_Report_${inspectionId}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

export default apiClient;

