import React, { useState, useEffect, useRef } from 'react';
import {
  Upload, Film, Image as ImageIcon, Plus, Play, Pause, Trash2, CheckCircle2,
  AlertCircle, RefreshCw, Scissors, Archive, Sliders, Sparkles, Video, Eye,
  ArrowRight, Download, Cpu
} from 'lucide-react';

import CustomScreenshotModal from './components/CustomScreenshotModal';
import SettingsPanel from './components/SettingsPanel';
import CutPointsTable from './components/CutPointsTable';
import ClipsGallery from './components/ClipsGallery';

export default function App() {
  // Job & Upload State
  const [jobId, setJobId] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [videoStreamUrl, setVideoStreamUrl] = useState(null);
  const [references, setReferences] = useState([]);
  
  // Custom Reference Modal
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Settings State
  const [settings, setSettings] = useState({
    threshold: 0.70,
    check_interval: 0.25,
    min_gap: 3.0,
    multi_scale: true,
    cut_mode: 'fast'
  });

  // Processing & Progress State
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMode, setProcessingMode] = useState(''); // 'detect' | 'split' | 'full'
  const [progress, setProgress] = useState({
    stage: 'ready',
    stage_text: '',
    percent: 0,
    current_time: 0,
    total_duration: 0,
    formatted_current_time: '00:00.00',
    formatted_total_duration: '00:00.00',
    detected_count: 0,
    error_message: null
  });

  // Results State
  const [cutPoints, setCutPoints] = useState([]);
  const [clips, setClips] = useState([]);
  const [zipUrl, setZipUrl] = useState(null);

  // Main video player ref
  const mainVideoRef = useRef(null);
  const pollTimerRef = useRef(null);

  // Drag and drop state
  const [isDraggingVideo, setIsDraggingVideo] = useState(false);

  // Poll progress while processing
  useEffect(() => {
    if (isProcessing && jobId) {
      pollTimerRef.current = setInterval(async () => {
        try {
          const res = await fetch(`/api/progress/${jobId}`);
          if (res.ok) {
            const data = await res.json();
            setProgress(data);

            if (data.stage === 'detected') {
              // Fetch results for detected cut points
              await fetchResults();
              if (processingMode === 'detect') {
                setIsProcessing(false);
              }
            } else if (data.stage === 'complete') {
              await fetchResults();
              setIsProcessing(false);
            } else if (data.stage === 'error') {
              setIsProcessing(false);
            }
          }
        } catch (err) {
          console.error("Progress polling error:", err);
        }
      }, 750);
    } else {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    }
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [isProcessing, jobId, processingMode]);

  const fetchResults = async () => {
    if (!jobId) return;
    try {
      const res = await fetch(`/api/results/${jobId}`);
      if (res.ok) {
        const data = await res.json();
        setCutPoints(data.cut_points || []);
        setClips(data.clips || []);
        setZipUrl(data.zip_url);
        if (data.references) setReferences(data.references);
      }
    } catch (err) {
      console.error("Error fetching results:", err);
    }
  };

  // 1. Upload Video
  const handleVideoUpload = async (file) => {
    if (!file) return;
    setVideoFile(file);
    setCutPoints([]);
    setClips([]);
    setZipUrl(null);

    const formData = new FormData();
    formData.append('video', file);
    if (jobId) formData.append('job_id', jobId);

    try {
      setProgress(p => ({ ...p, stage_text: 'Uploading video...', percent: 50 }));
      const res = await fetch('/api/upload-video', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setJobId(data.job_id);
        setVideoMetadata(data.metadata);
        setVideoStreamUrl(data.video_stream_url);
        setProgress(p => ({ ...p, stage: 'ready', stage_text: 'Video ready', percent: 0 }));
      } else {
        alert(data.detail || 'Failed to upload video');
      }
    } catch (err) {
      alert('Error uploading video: ' + err.message);
    }
  };

  // 2. Upload Reference Screenshots from File Input
  const handleReferenceFilesUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    for (const file of files) {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('name', file.name.replace(/\.[^/.]+$/, ""));
      formData.append('job_id', jobId || 'new_job');

      try {
        const res = await fetch('/api/upload-reference', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (res.ok) {
          setJobId(data.job_id);
          setReferences(data.all_references);
        }
      } catch (err) {
        console.error("Error uploading reference:", err);
      }
    }
  };

  // Delete Reference
  const handleDeleteReference = async (refId) => {
    if (!jobId) return;
    try {
      const res = await fetch(`/api/reference/${jobId}/${refId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setReferences(refs => refs.filter(r => r.id !== refId));
      }
    } catch (err) {
      console.error("Error deleting reference:", err);
    }
  };

  // Load Sample Demo Video
  const handleLoadDemo = async () => {
    try {
      setProgress(p => ({ ...p, stage_text: 'Generating Demo Sample Video...', percent: 50 }));
      const res = await fetch('/api/create-sample-demo', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        setJobId(data.job_id);
        setVideoMetadata(data.metadata);
        setReferences(data.references);
        setVideoStreamUrl(data.video_stream_url);
        setCutPoints([]);
        setClips([]);
        setZipUrl(null);
        setProgress(p => ({ ...p, stage: 'ready', stage_text: 'Sample Demo Ready', percent: 0 }));
      }
    } catch (err) {
      alert('Error loading sample demo: ' + err.message);
    }
  };

  // 3. Start Automatic Detection Only
  const handleStartDetection = async () => {
    if (!jobId || !videoMetadata) {
      alert('Please upload a video first.');
      return;
    }
    if (references.length === 0) {
      alert('Please add at least one reference screenshot.');
      return;
    }

    setIsProcessing(true);
    setProcessingMode('detect');
    setCutPoints([]);
    setClips([]);

    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('threshold', settings.threshold.toString());
    formData.append('check_interval', settings.check_interval.toString());
    formData.append('min_gap', settings.min_gap.toString());
    formData.append('multi_scale', settings.multi_scale.toString());
    formData.append('cut_mode', settings.cut_mode);

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || 'Failed to start detection');
        setIsProcessing(false);
      }
    } catch (err) {
      alert('Error starting detection: ' + err.message);
      setIsProcessing(false);
    }
  };

  // 4. One-Click Full Automatic Pipeline: Process & Auto-Split
  const handleProcessAndSplitAll = async () => {
    if (!jobId || !videoMetadata) {
      alert('Please upload a video first.');
      return;
    }
    if (references.length === 0) {
      alert('Please add at least one reference screenshot.');
      return;
    }

    setIsProcessing(true);
    setProcessingMode('full');
    setCutPoints([]);
    setClips([]);

    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('threshold', settings.threshold.toString());
    formData.append('check_interval', settings.check_interval.toString());
    formData.append('min_gap', settings.min_gap.toString());
    formData.append('multi_scale', settings.multi_scale.toString());
    formData.append('cut_mode', settings.cut_mode);

    try {
      const res = await fetch('/api/process-and-split', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || 'Failed to start automatic pipeline');
        setIsProcessing(false);
      }
    } catch (err) {
      alert('Error starting pipeline: ' + err.message);
      setIsProcessing(false);
    }
  };

  // 5. Trigger Splitting from Confirmed Cut Points
  const handleSplitVideo = async () => {
    if (!jobId || cutPoints.length === 0) return;

    setIsProcessing(true);
    setProcessingMode('split');

    const formData = new FormData();
    formData.append('job_id', jobId);

    try {
      const res = await fetch('/api/split-video', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const data = await res.json();
        alert(data.detail || 'Failed to start video splitting');
        setIsProcessing(false);
      }
    } catch (err) {
      alert('Error splitting video: ' + err.message);
      setIsProcessing(false);
    }
  };

  // Manual Cut Point Adjustments
  const handleAddManualPoint = async (seconds, label) => {
    if (!jobId) return;
    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('action', 'add');
    formData.append('timestamp', seconds.toString());
    formData.append('ref_name', label || 'Manual Cut');

    try {
      const res = await fetch('/api/update-cut-points', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setCutPoints(data.cut_points);
      }
    } catch (err) {
      console.error("Error adding manual point:", err);
    }
  };

  const handleDeletePoint = async (cutId) => {
    if (!jobId) return;
    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('action', 'delete');
    formData.append('cut_id', cutId);

    try {
      const res = await fetch('/api/update-cut-points', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setCutPoints(data.cut_points);
      }
    } catch (err) {
      console.error("Error deleting point:", err);
    }
  };

  const handleEditPoint = async (cutId, newSeconds) => {
    if (!jobId) return;
    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('action', 'edit');
    formData.append('cut_id', cutId);
    formData.append('timestamp', newSeconds.toString());

    try {
      const res = await fetch('/api/update-cut-points', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setCutPoints(data.cut_points);
      }
    } catch (err) {
      console.error("Error editing point:", err);
    }
  };

  // Seek video preview player to timestamp
  const handleSeekVideo = (timestamp) => {
    if (mainVideoRef.current) {
      mainVideoRef.current.currentTime = Math.max(0, timestamp - 0.5);
      mainVideoRef.current.play();
      mainVideoRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div>
          <div className="header-badge">
            <Sparkles size={14} /> AI & Computer Vision Video Tool
          </div>
          <h1 className="header-title">Automatic Video Splitter</h1>
          <p className="header-subtitle">
            Upload a long multi-segment video and reference transition screenshots. The system will automatically scan the video frames, detect match points, deduplicate timestamps, and split the video into individual clips.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button className="btn btn-secondary" onClick={handleLoadDemo}>
            <Sparkles size={16} color="#F59E0B" /> Load Sample Demo Video
          </button>
        </div>
      </header>

      {/* Main 2-Column Grid: Video Upload & Reference Screenshots */}
      <div className="grid-2col">
        {/* Left Column: Video Upload */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Film size={20} color="#3B82F6" /> 1. Upload Video
              </h3>
              <p className="card-desc">Supported: MP4, MOV, MKV, AVI</p>
            </div>
          </div>

          <div
            className={`dropzone ${isDraggingVideo ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDraggingVideo(true); }}
            onDragLeave={() => setIsDraggingVideo(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingVideo(false);
              if (e.dataTransfer.files?.[0]) handleVideoUpload(e.dataTransfer.files[0]);
            }}
            onClick={() => document.getElementById('video-file-input').click()}
          >
            <input
              id="video-file-input"
              type="file"
              accept="video/mp4,video/quicktime,video/x-matroska,video/x-msvideo"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files?.[0]) handleVideoUpload(e.target.files[0]);
              }}
            />
            <div className="dropzone-icon">
              <Upload size={24} />
            </div>
            <div className="dropzone-title">
              {videoMetadata ? videoMetadata.filename : 'Drop video here or click to browse'}
            </div>
            <div className="dropzone-sub">
              {videoMetadata ? `${videoMetadata.filesize_mb} MB • Ready for processing` : 'MP4, MOV, MKV, AVI files supported'}
            </div>
            <div className="format-tags">
              <span className="format-tag">.MP4</span>
              <span className="format-tag">.MOV</span>
              <span className="format-tag">.MKV</span>
              <span className="format-tag">.AVI</span>
            </div>
          </div>

          {/* Video Metadata & Player */}
          {videoMetadata && (
            <>
              <div className="metadata-grid">
                <div className="meta-item">
                  <div className="meta-label">Duration</div>
                  <div className="meta-value">{videoMetadata.formatted_duration}</div>
                </div>
                <div className="meta-item">
                  <div className="meta-label">Resolution</div>
                  <div className="meta-value">{videoMetadata.width}x{videoMetadata.height}</div>
                </div>
                <div className="meta-item">
                  <div className="meta-label">FPS</div>
                  <div className="meta-value">{videoMetadata.fps}</div>
                </div>
                <div className="meta-item">
                  <div className="meta-label">File Size</div>
                  <div className="meta-value">{videoMetadata.filesize_mb} MB</div>
                </div>
              </div>

              {videoStreamUrl && (
                <div className="video-preview-wrapper">
                  <video
                    ref={mainVideoRef}
                    src={videoStreamUrl}
                    controls
                    className="video-preview-player"
                  />
                </div>
              )}
            </>
          )}
        </div>

        {/* Right Column: Reference Cut Screens */}
        <div className="card">
          <div className="card-header" style={{ flexWrap: 'wrap', gap: '8px' }}>
            <div>
              <h3 className="card-title">
                <ImageIcon size={20} color="#3B82F6" /> 2. Reference Cut Screens
              </h3>
              <p className="card-desc">Screenshots representing transitions where cuts occur</p>
            </div>
            <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
              <Plus size={16} /> + Add Custom Screenshot
            </button>
          </div>

          {/* References Grid */}
          {references.length === 0 ? (
            <div style={{ padding: '36px 20px', textAlign: 'center', border: '1px dashed var(--border-color)', borderRadius: '12px' }}>
              <ImageIcon size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px auto', display: 'block' }} />
              <div style={{ fontWeight: 600, color: '#FFFFFF', marginBottom: '6px' }}>
                No Reference Screenshots Added
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                Upload transition screenshots or capture frames directly from your video.
              </p>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
                <button className="btn btn-secondary" onClick={() => document.getElementById('ref-file-input').click()}>
                  <Upload size={14} /> Upload Images
                </button>
                <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
                  <Plus size={14} /> Add Custom Screenshot
                </button>
              </div>
              <input
                id="ref-file-input"
                type="file"
                multiple
                accept="image/png,image/jpeg,image/jpg,image/webp"
                style={{ display: 'none' }}
                onChange={handleReferenceFilesUpload}
              />
            </div>
          ) : (
            <>
              <div className="references-grid">
                {references.map((ref, idx) => (
                  <div key={ref.id || idx} className="ref-card">
                    <div className="ref-card-img-wrap">
                      <img src={ref.preview_url} alt={ref.name} className="ref-card-img" />
                    </div>
                    <div className="ref-card-body">
                      <div className="ref-card-name" title={ref.name}>
                        {ref.name}
                      </div>
                      <div className="ref-card-footer">
                        <span className="status-pill">
                          <CheckCircle2 size={10} /> {ref.status || 'Ready'}
                        </span>
                        <button
                          className="btn-icon-delete"
                          onClick={() => handleDeleteReference(ref.id)}
                          title="Delete reference"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={() => document.getElementById('ref-file-input').click()}
                >
                  <Upload size={12} /> + Upload More Images
                </button>
                <input
                  id="ref-file-input"
                  type="file"
                  multiple
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  style={{ display: 'none' }}
                  onChange={handleReferenceFilesUpload}
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Advanced Detection Settings Accordion */}
      <SettingsPanel settings={settings} onChange={setSettings} />

      {/* Action Banner */}
      <div className="action-banner">
        <div className="action-info">
          <h3>Ready to Process Video?</h3>
          <p>
            {references.length > 0 && videoMetadata
              ? `Video (${videoMetadata.formatted_duration}) and ${references.length} reference screen(s) loaded.`
              : 'Upload video and add reference screenshots to begin automatic detection.'}
          </p>
        </div>

        <div className="action-buttons">
          <button
            className="btn btn-secondary btn-lg"
            onClick={handleStartDetection}
            disabled={isProcessing || !videoMetadata || references.length === 0}
          >
            <Eye size={18} /> 🔍 Detect Cut Points Only
          </button>

          <button
            className="btn btn-primary btn-lg"
            onClick={handleProcessAndSplitAll}
            disabled={isProcessing || !videoMetadata || references.length === 0}
            style={{ fontWeight: 700 }}
          >
            <Sparkles size={18} /> 🚀 Process & Auto Split Video
          </button>
        </div>
      </div>

      {/* Real-time Progress Monitor */}
      {isProcessing && (
        <div className="progress-card processing-active">
          <div className="progress-header">
            <div className="progress-stage">
              <RefreshCw size={18} className="spin" style={{ animation: 'spin 1.5s linear infinite' }} color="#3B82F6" />
              <span>{progress.stage_text || 'Processing video...'}</span>
            </div>
            <div className="progress-pct">{progress.percent}%</div>
          </div>

          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${progress.percent}%` }} />
          </div>

          <div className="progress-stats-row">
            <div>
              Scanning Time: <span style={{ color: 'var(--accent-cyan)' }}>{progress.formatted_current_time}</span> / {progress.formatted_total_duration}
            </div>
            <div>
              Detected Cut Points: <span style={{ color: 'var(--accent-amber)', fontWeight: 700 }}>{progress.detected_count}</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {progress.stage === 'error' && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid var(--accent-rose)', borderRadius: '12px', padding: '16px 20px', marginBottom: '28px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={22} color="var(--accent-rose)" />
          <div>
            <div style={{ fontWeight: 700, color: 'var(--accent-rose)' }}>Processing Encountered an Issue</div>
            <div style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{progress.error_message || progress.stage_text}</div>
          </div>
        </div>
      )}

      {/* Detected Cut Points Section & Interactive Timeline */}
      {cutPoints.length > 0 && (
        <CutPointsTable
          cutPoints={cutPoints}
          totalDuration={videoMetadata ? videoMetadata.duration : 0}
          onSeekVideo={handleSeekVideo}
          onAddManualPoint={handleAddManualPoint}
          onDeletePoint={handleDeletePoint}
          onEditPoint={handleEditPoint}
          onSplitVideo={handleSplitVideo}
          isProcessing={isProcessing}
        />
      )}

      {/* Generated Clips Gallery & ZIP Download */}
      <ClipsGallery
        clips={clips}
        jobId={jobId}
        zipUrl={zipUrl}
        videoMetadata={videoMetadata}
        referencesCount={references.length}
        cutPointsCount={cutPoints.length}
      />

      {/* Custom Screenshot Capture Modal */}
      <CustomScreenshotModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        videoStreamUrl={videoStreamUrl}
        jobId={jobId}
        onReferenceAdded={(updatedRefs) => setReferences(updatedRefs)}
      />

      {/* Global CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
