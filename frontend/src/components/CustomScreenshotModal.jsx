import React, { useState, useRef, useEffect } from 'react';
import { Upload, Camera, Play, Pause, ChevronLeft, ChevronRight, X, Check, Image as ImageIcon } from 'lucide-react';

export default function CustomScreenshotModal({ isOpen, onClose, videoStreamUrl, jobId, onReferenceAdded }) {
  const [activeTab, setActiveTab] = useState('capture'); // 'upload' | 'capture'
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadPreview, setUploadPreview] = useState(null);
  const [refName, setRefName] = useState('');
  
  // Video player / frame selector state
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [capturedDataUrl, setCapturedDataUrl] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setUploadFile(null);
      setUploadPreview(null);
      setCapturedDataUrl(null);
      setRefName('');
      setIsPlaying(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Handle Option A: Upload file from computer
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadFile(file);
      setUploadPreview(URL.createObjectURL(file));
      if (!refName) {
        setRefName(file.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleUploadSubmit = async () => {
    if (!uploadFile || !jobId) return;
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('image', uploadFile);
      formData.append('job_id', jobId);
      formData.append('name', refName || 'Uploaded Reference');

      const res = await fetch('/api/upload-reference', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        onReferenceAdded(data.all_references);
        onClose();
      } else {
        alert(data.detail || 'Failed to upload screenshot');
      }
    } catch (err) {
      alert('Error uploading screenshot: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Option B: Video frame capture
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else {
        videoRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const stepTime = (delta) => {
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
      videoRef.current.currentTime = Math.max(0, Math.min(duration, videoRef.current.currentTime + delta));
    }
  };

  const captureCurrentFrame = async () => {
    if (!videoRef.current) return;
    videoRef.current.pause();
    setIsPlaying(false);

    const video = videoRef.current;
    const canvas = canvasRef.current || document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/png');
    setCapturedDataUrl(dataUrl);
    
    const formatted = formatTime(video.currentTime);
    if (!refName) {
      setRefName(`Frame at ${formatted}`);
    }
  };

  const handleCaptureSubmit = async () => {
    if (!jobId) return;
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('job_id', jobId);
      formData.append('timestamp', currentTime.toString());
      formData.append('name', refName || `Captured Frame (${formatTime(currentTime)})`);

      const res = await fetch('/api/create-custom-reference', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        onReferenceAdded(data.all_references);
        onClose();
      } else {
        alert(data.detail || 'Failed to capture frame');
      }
    } catch (err) {
      alert('Error capturing frame: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const s = (secs % 60).toFixed(2);
    return `${mins.toString().padStart(2, '0')}:${s.padStart(5, '0')}`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Camera size={22} color="#3B82F6" />
            <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Add Reference Screenshot</h3>
          </div>
          <button className="btn-icon-delete" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-input)' }}>
          <button
            onClick={() => setActiveTab('capture')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'capture' ? 'var(--bg-card)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'capture' ? '2px solid var(--primary)' : 'none',
              color: activeTab === 'capture' ? '#FFFFFF' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Camera size={16} /> Option B: Capture from Video
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'upload' ? 'var(--bg-card)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'upload' ? '2px solid var(--primary)' : 'none',
              color: activeTab === 'upload' ? '#FFFFFF' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Upload size={16} /> Option A: Upload from Computer
          </button>
        </div>

        <div className="modal-body">
          {activeTab === 'upload' ? (
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 600 }}>
                Select Image File (PNG, JPG, JPEG)
              </label>
              <input
                type="file"
                accept="image/png, image/jpeg, image/jpg, image/webp"
                onChange={handleFileChange}
                style={{ marginBottom: '16px', display: 'block', width: '100%', color: 'var(--text-secondary)' }}
              />

              {uploadPreview && (
                <div style={{ marginBottom: '16px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color)', maxHeight: '200px', textAlign: 'center', background: '#000' }}>
                  <img src={uploadPreview} alt="Upload preview" style={{ maxHeight: '200px', maxWidth: '100%', objectFit: 'contain' }} />
                </div>
              )}

              <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 600 }}>
                Screenshot Reference Name
              </label>
              <input
                type="text"
                className="input-text"
                placeholder="e.g. Transition Screen / Fast 100"
                value={refName}
                onChange={(e) => setRefName(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          ) : (
            <div>
              {videoStreamUrl ? (
                <div>
                  <video
                    ref={videoRef}
                    src={videoStreamUrl}
                    className="frame-selector-video"
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={handleLoadedMetadata}
                  />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />

                  {/* Scrubber & Controls */}
                  <div style={{ marginTop: '12px' }}>
                    <input
                      type="range"
                      min={0}
                      max={duration || 100}
                      step={0.05}
                      value={currentTime}
                      onChange={(e) => {
                        const t = parseFloat(e.target.value);
                        setCurrentTime(t);
                        if (videoRef.current) videoRef.current.currentTime = t;
                      }}
                      className="input-range"
                    />
                  </div>

                  <div className="scrubber-controls" style={{ justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button className="btn btn-secondary" style={{ padding: '6px 12px' }} onClick={togglePlay}>
                        {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                        {isPlaying ? 'Pause' : 'Play'}
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '6px 10px' }} onClick={() => stepTime(-1.0)} title="-1 second">
                        <ChevronLeft size={16} /> -1s
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '6px 10px' }} onClick={() => stepTime(-0.1)} title="-0.1s (-1 frame)">
                        -1f
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '6px 10px' }} onClick={() => stepTime(0.1)} title="+0.1s (+1 frame)">
                        +1f
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '6px 10px' }} onClick={() => stepTime(1.0)} title="+1 second">
                        +1s <ChevronRight size={16} />
                      </button>
                    </div>

                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--accent-cyan)' }}>
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                  </div>

                  <div style={{ marginTop: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <button className="btn btn-primary" onClick={captureCurrentFrame} style={{ flex: 1 }}>
                      <Camera size={16} /> Grab Current Frame
                    </button>
                  </div>

                  {capturedDataUrl && (
                    <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg-input)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-emerald)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Check size={14} /> Frame Captured at {formatTime(currentTime)}
                      </div>
                      <img src={capturedDataUrl} alt="Captured frame" style={{ maxHeight: '140px', borderRadius: '4px', display: 'block', margin: '0 auto 12px auto' }} />
                      <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 600 }}>
                        Reference Label Name
                      </label>
                      <input
                        type="text"
                        className="input-text"
                        placeholder="e.g. Breaking News Transition"
                        value={refName}
                        onChange={(e) => setRefName(e.target.value)}
                        style={{ width: '100%' }}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Please upload a video first to capture frames directly from it.
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </button>
          {activeTab === 'upload' ? (
            <button className="btn btn-primary" onClick={handleUploadSubmit} disabled={!uploadFile || isSubmitting}>
              {isSubmitting ? 'Uploading...' : 'Add Screenshot'}
            </button>
          ) : (
            <button className="btn btn-primary" onClick={handleCaptureSubmit} disabled={!capturedDataUrl || isSubmitting}>
              {isSubmitting ? 'Saving Frame...' : 'Save As Reference'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
