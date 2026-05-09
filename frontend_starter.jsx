/**
 * Universal Media Downloader - Frontend Starter Code (React)
 * Author: Senior Full-Stack Developer
 * Version: 0.1.0 (MVP)
 */

import React, { useState, useCallback, useEffect } from "react";
import axios from "axios";

// ============================================================================
// CONSTANTS
// ============================================================================

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const SUPPORTED_PLATFORMS = [
  { name: "YouTube", icon: "📺", pattern: /(youtube\.com|youtu\.be)/ },
  { name: "TikTok", icon: "🎵", pattern: /(tiktok\.com|vm\.tiktok\.com)/ },
  { name: "Instagram", icon: "📷", pattern: /instagram\.com/ },
  { name: "X (Twitter)", icon: "🐦", pattern: /(twitter\.com|x\.com)/ },
  { name: "Facebook", icon: "👍", pattern: /facebook\.com/ },
  { name: "Pinterest", icon: "📌", pattern: /pinterest\.com/ },
  { name: "LinkedIn", icon: "💼", pattern: /linkedin\.com/ },
];

const FORMATS = [
  { value: "mp4", label: "MP4 (Video)" },
  { value: "mp3", label: "MP3 (Audio)" },
  { value: "mov", label: "MOV (Video)" },
];

const QUALITIES = [
  { value: "720p", label: "720p (HD)" },
  { value: "1080p", label: "1080p (Full HD)" },
  { value: "4k", label: "4K (Ultra HD)" },
];

// ============================================================================
// CUSTOM HOOKS
// ============================================================================

/**
 * Hook for managing download state
 */
const useDownloadManager = () => {
  const [jobs, setJobs] = useState({});
  const [currentJob, setCurrentJob] = useState(null);

  const addJob = useCallback((jobData) => {
    setJobs((prev) => ({
      ...prev,
      [jobData.job_id]: jobData,
    }));
    setCurrentJob(jobData.job_id);
  }, []);

  const updateJob = useCallback((jobId, updates) => {
    setJobs((prev) => ({
      ...prev,
      [jobId]: { ...prev[jobId], ...updates },
    }));
  }, []);

  const getJob = useCallback(
    (jobId) => jobs[jobId] || null,
    [jobs]
  );

  return { jobs, currentJob, addJob, updateJob, getJob };
};

/**
 * Hook for polling job status
 */
const useJobStatus = (jobId, interval = 1000) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const pollStatus = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `${API_BASE_URL}/api/download/${jobId}/status`
        );
        setStatus(response.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to fetch status");
      } finally {
        setLoading(false);
      }
    };

    // Poll immediately
    pollStatus();

    // Set interval for polling
    const pollInterval = setInterval(pollStatus, interval);

    return () => clearInterval(pollInterval);
  }, [jobId, interval]);

  return { status, loading, error };
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Detect platform from URL
 */
const detectPlatform = (url) => {
  if (!url) return null;

  for (const platform of SUPPORTED_PLATFORMS) {
    if (platform.pattern.test(url)) {
      return platform;
    }
  }

  return null;
};

/**
 * Validate URL format
 */
const validateUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Format bytes to human-readable format
 */
const formatBytes = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
};

/**
 * Format seconds to time string
 */
const formatTime = (seconds) => {
  if (!seconds || seconds < 0) return "Unknown";
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs}s`;
};

// ============================================================================
// COMPONENTS
// ============================================================================

/**
 * Input Section Component
 */
const InputSection = ({ url, setUrl, onDetect, loading, platform }) => {
  const handleClear = () => setUrl("");

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text);
    } catch (err) {
      alert("Failed to paste from clipboard");
    }
  };

  return (
    <div className="input-section">
      <h1>🔗 UniDownload</h1>
      <p className="subtitle">Paste any social media link to download</p>

      <div className="input-container">
        <div className="url-input-group">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste YouTube, TikTok, Instagram, X, Facebook, Pinterest, or LinkedIn URL"
            className="url-input"
            disabled={loading}
            onKeyPress={(e) => e.key === "Enter" && onDetect()}
          />
          <button
            onClick={handlePaste}
            className="btn btn-secondary"
            disabled={loading}
            title="Paste from clipboard"
          >
            📋
          </button>
          <button
            onClick={handleClear}
            className="btn btn-secondary"
            disabled={loading}
            title="Clear input"
          >
            ✖
          </button>
        </div>

        <button
          onClick={onDetect}
          disabled={!url || loading}
          className="btn btn-primary"
        >
          {loading ? "⏳ Detecting..." : "🔍 Detect"}
        </button>
      </div>

      {platform && (
        <div className="platform-badge">
          {platform.icon} Platform: {platform.name}
        </div>
      )}
    </div>
  );
};

/**
 * Options Section Component
 */
const OptionsSection = ({
  format,
  setFormat,
  quality,
  setQuality,
  onDownload,
  loading,
  metadata,
}) => {
  return (
    <div className="options-section">
      {metadata && (
        <div className="metadata">
          {metadata.thumbnail && (
            <img
              src={metadata.thumbnail}
              alt="Thumbnail"
              className="thumbnail"
            />
          )}
          <div className="metadata-info">
            <h3>{metadata.title}</h3>
            {metadata.duration && (
              <p>Duration: {formatTime(metadata.duration)}</p>
            )}
          </div>
        </div>
      )}

      <div className="options-grid">
        <div className="option-group">
          <label>📁 Format</label>
          <div className="radio-group">
            {FORMATS.map((fmt) => (
              <label key={fmt.value} className="radio-label">
                <input
                  type="radio"
                  value={fmt.value}
                  checked={format === fmt.value}
                  onChange={(e) => setFormat(e.target.value)}
                  disabled={loading}
                />
                {fmt.label}
              </label>
            ))}
          </div>
        </div>

        <div className="option-group">
          <label>🎬 Quality</label>
          <div className="radio-group">
            {QUALITIES.map((qual) => (
              <label key={qual.value} className="radio-label">
                <input
                  type="radio"
                  value={qual.value}
                  checked={quality === qual.value}
                  onChange={(e) => setQuality(e.target.value)}
                  disabled={loading}
                />
                {qual.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={onDownload}
        disabled={!metadata || loading}
        className="btn btn-download"
      >
        {loading ? "⏳ Processing..." : "📥 Download"}
      </button>
    </div>
  );
};

/**
 * Progress Section Component
 */
const ProgressSection = ({ status, loading }) => {
  if (!status) return null;

  const isProcessing = ["queued", "processing"].includes(status.status);
  const isCompleted = status.status === "completed";
  const isFailed = status.status === "failed";

  return (
    <div className={`progress-section status-${status.status}`}>
      <h3>
        {isProcessing && "⏳ Processing..."}
        {isCompleted && "✅ Ready to Download!"}
        {isFailed && "❌ Download Failed"}
      </h3>

      {isProcessing && (
        <>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${status.progress}%` }}
            ></div>
          </div>
          <p className="progress-text">
            {status.progress}% Complete
            {status.estimated_time && ` • ETA: ${formatTime(status.estimated_time)}`}
          </p>
        </>
      )}

      {isCompleted && (
        <a
          href={`${API_BASE_URL}/api/download/${status.job_id}/file`}
          className="btn btn-success"
          download
        >
          ⬇️ Download File
        </a>
      )}

      {isFailed && (
        <p className="error-message">
          {status.error || "Download failed. Please try again."}
        </p>
      )}
    </div>
  );
};

/**
 * Error Message Component
 */
const ErrorBanner = ({ error, onClose }) => {
  if (!error) return null;

  const errorMessages = {
    400: "Invalid URL. Please check the link format.",
    404: "Content not found or is no longer available.",
    403: "This content is private or restricted.",
    500: "Server error. Please try again later.",
    timeout: "Request timed out. Please try again.",
    network: "Network error. Check your connection.",
  };

  const message = errorMessages[error.code] || error.message || "An error occurred";

  return (
    <div className="error-banner">
      <span>❌ {message}</span>
      <button onClick={onClose} className="btn-close">
        ✖
      </button>
    </div>
  );
};

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

function App() {
  const [url, setUrl] = useState("");
  const [format, setFormat] = useState("mp4");
  const [quality, setQuality] = useState("1080p");
  const [platform, setPlatform] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { jobs, currentJob, addJob, updateJob, getJob } = useDownloadManager();
  const { status: jobStatus } = useJobStatus(currentJob, 1000);

  // Handle platform detection
  const handleDetect = useCallback(async () => {
    setError(null);

    if (!url.trim()) {
      setError({ message: "Please enter a URL" });
      return;
    }

    if (!validateUrl(url)) {
      setError({ message: "Invalid URL format" });
      return;
    }

    const detectedPlatform = detectPlatform(url);
    if (!detectedPlatform) {
      setError({ message: "Platform not supported" });
      return;
    }

    setPlatform(detectedPlatform);
    setLoading(true);

    try {
      // Simulate metadata fetch (replace with actual API call)
      const mockMetadata = {
        title: "Sample Video Title",
        duration: 445,
        thumbnail: "https://via.placeholder.com/300x200",
      };

      await new Promise((resolve) => setTimeout(resolve, 1000));
      setMetadata(mockMetadata);
    } catch (err) {
      setError({
        code: err.response?.status || 500,
        message: err.response?.data?.detail || "Failed to detect platform",
      });
      setPlatform(null);
    } finally {
      setLoading(false);
    }
  }, [url]);

  // Handle download initiation
  const handleDownload = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/download`,
        {
          url,
          format,
          quality,
        }
      );

      addJob({
        job_id: response.data.job_id,
        platform: response.data.platform,
        status: "queued",
        progress: 0,
      });
    } catch (err) {
      setError({
        code: err.response?.status || 500,
        message: err.response?.data?.detail || "Failed to start download",
      });
    } finally {
      setLoading(false);
    }
  }, [url, format, quality, addJob]);

  // Handle job status updates
  useEffect(() => {
    if (jobStatus) {
      updateJob(currentJob, {
        status: jobStatus.status,
        progress: jobStatus.progress,
        error: jobStatus.error,
      });
    }
  }, [jobStatus, currentJob, updateJob]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔗 Universal Media Downloader</h1>
        <p>Download from YouTube, TikTok, Instagram, X, Facebook, Pinterest & LinkedIn</p>
      </header>

      <main className="app-main">
        <ErrorBanner
          error={error}
          onClose={() => setError(null)}
        />

        <section className="section">
          <InputSection
            url={url}
            setUrl={setUrl}
            onDetect={handleDetect}
            loading={loading}
            platform={platform}
          />
        </section>

        {metadata && (
          <section className="section">
            <OptionsSection
              format={format}
              setFormat={setFormat}
              quality={quality}
              setQuality={setQuality}
              onDownload={handleDownload}
              loading={loading}
              metadata={metadata}
            />
          </section>
        )}

        {currentJob && (
          <section className="section">
            <ProgressSection
              status={getJob(currentJob)}
              loading={loading}
            />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>🔒 Privacy-First • No Account Required • Secure Encryption</p>
        <p>© 2024 Universal Media Downloader. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
