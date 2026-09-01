import React, { useState } from 'react';
import { Download, Film, Play, X, Archive, CheckCircle2, Clock, Layers, Sparkles } from 'lucide-react';

export default function ClipsGallery({
  clips,
  jobId,
  zipUrl,
  videoMetadata,
  referencesCount,
  cutPointsCount
}) {
  const [playingClip, setPlayingClip] = useState(null);

  if (!clips || clips.length === 0) return null;

  return (
    <div className="card" style={{ marginBottom: '36px' }}>
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ padding: '4px 10px', background: 'rgba(16, 185, 129, 0.2)', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '999px', fontSize: '12px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={14} /> Processing Complete
            </span>
          </div>
          <h3 className="card-title" style={{ fontSize: '22px' }}>
            Generated Video Clips ({clips.length})
          </h3>
          <p className="card-desc">
            All segments have been automatically cut and prepared for instant download.
          </p>
        </div>

        {/* Primary Download ZIP button */}
        {zipUrl && (
          <a
            href={zipUrl}
            download={`video_clips_${jobId}.zip`}
            className="btn btn-emerald btn-lg"
            style={{ textDecoration: 'none' }}
          >
            <Archive size={20} /> Download All Clips as ZIP
          </a>
        )}
      </div>

      {/* Summary Statistics Grid */}
      <div className="metadata-grid" style={{ marginBottom: '24px' }}>
        <div className="meta-item">
          <div className="meta-label">Total Duration</div>
          <div className="meta-value">{videoMetadata ? videoMetadata.formatted_duration : 'N/A'}</div>
        </div>
        <div className="meta-item">
          <div className="meta-label">Reference Screens</div>
          <div className="meta-value" style={{ color: 'var(--accent-cyan)' }}>{referencesCount}</div>
        </div>
        <div className="meta-item">
          <div className="meta-label">Cut Points</div>
          <div className="meta-value" style={{ color: 'var(--accent-amber)' }}>{cutPointsCount}</div>
        </div>
        <div className="meta-item">
          <div className="meta-label">Clips Created</div>
          <div className="meta-value" style={{ color: 'var(--accent-emerald)' }}>{clips.length}</div>
        </div>
      </div>

      {/* Clip Cards Grid */}
      <div className="clips-grid">
        {clips.map((clip) => (
          <div key={clip.clip_id || clip.clip_number} className="clip-card">
            <div className="clip-thumbnail-wrap">
              {clip.thumbnail_url ? (
                <img src={clip.thumbnail_url} alt={clip.filename} className="clip-thumbnail" />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                  <Film size={36} />
                </div>
              )}
              <button
                onClick={() => setPlayingClip(clip)}
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'rgba(0,0,0,0.3)',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  transition: 'background 0.2s'
                }}
                title="Play Clip Preview"
              >
                <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Play size={20} fill="#FFFFFF" />
                </div>
              </button>
            </div>

            <div className="clip-card-content">
              <div className="clip-title-row">
                <span className="clip-title">Clip {clip.clip_number.toString().padStart(3, '0')}</span>
                <span className="clip-duration-tag">{clip.duration.toFixed(1)}s</span>
              </div>

              <div className="clip-timestamps">
                {clip.formatted_start} &rarr; {clip.formatted_end}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '8px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {clip.file_size_mb > 0 ? `${clip.file_size_mb} MB` : ''}
                </span>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                    onClick={() => setPlayingClip(clip)}
                  >
                    <Play size={12} /> Preview
                  </button>
                  <a
                    href={clip.video_url}
                    download={clip.filename}
                    className="btn btn-primary"
                    style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}
                  >
                    <Download size={12} /> Download
                  </a>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Clip Preview Modal */}
      {playingClip && (
        <div className="modal-overlay" onClick={() => setPlayingClip(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
                {playingClip.filename} ({playingClip.formatted_start} &rarr; {playingClip.formatted_end})
              </h3>
              <button className="btn-icon-delete" onClick={() => setPlayingClip(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body" style={{ padding: '16px' }}>
              <video
                src={playingClip.video_url}
                controls
                autoPlay
                style={{ width: '100%', maxHeight: '420px', borderRadius: '8px', background: '#000', display: 'block' }}
              />
            </div>
            <div className="modal-footer">
              <a
                href={playingClip.video_url}
                download={playingClip.filename}
                className="btn btn-primary"
                style={{ textDecoration: 'none' }}
              >
                <Download size={16} /> Download This Clip
              </a>
              <button className="btn btn-secondary" onClick={() => setPlayingClip(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
