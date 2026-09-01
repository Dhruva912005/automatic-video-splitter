import React, { useState } from 'react';
import { Sliders, ChevronDown, ChevronUp, Zap, Clock, ShieldCheck, Layers } from 'lucide-react';

export default function SettingsPanel({ settings, onChange }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="settings-accordion">
      <div className="settings-summary" onClick={() => setIsExpanded(!isExpanded)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sliders size={18} color="#3B82F6" />
          <span>Advanced Detection Settings</span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 400 }}>
            (Threshold: {settings.threshold}, Interval: {settings.check_interval}s, Min Gap: {settings.min_gap}s, Mode: {settings.cut_mode})
          </span>
        </div>
        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </div>

      {isExpanded && (
        <div className="settings-body">
          {/* 1. Detection Threshold */}
          <div className="setting-field">
            <div className="setting-label-row">
              <span className="setting-label">1. Detection Threshold</span>
              <span className="setting-val-badge">{settings.threshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.50"
              max="0.95"
              step="0.01"
              value={settings.threshold}
              onChange={(e) => onChange({ ...settings, threshold: parseFloat(e.target.value) })}
              className="input-range"
            />
            <p className="setting-desc">
              Higher value = stricter matching (fewer false positives). Lower value = more sensitive detections.
            </p>
          </div>

          {/* 2. Frame Check Interval */}
          <div className="setting-field">
            <div className="setting-label-row">
              <span className="setting-label">2. Frame Check Interval</span>
              <span className="setting-val-badge">{settings.check_interval}s</span>
            </div>
            <select
              className="input-select"
              value={settings.check_interval}
              onChange={(e) => onChange({ ...settings, check_interval: parseFloat(e.target.value) })}
            >
              <option value={0.10}>0.10 seconds (Ultra-fine scan)</option>
              <option value={0.25}>0.25 seconds (Recommended / Balanced)</option>
              <option value={0.50}>0.50 seconds (Fast scan)</option>
              <option value={1.00}>1.00 second (Quick scan)</option>
            </select>
            <p className="setting-desc">
              Lower interval gives higher accuracy near boundaries but inspects more frames.
            </p>
          </div>

          {/* 3. Minimum Gap Between Detections */}
          <div className="setting-field">
            <div className="setting-label-row">
              <span className="setting-label">3. Min Gap Between Detections</span>
              <span className="setting-val-badge">{settings.min_gap.toFixed(1)}s</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="10.0"
              step="0.5"
              value={settings.min_gap}
              onChange={(e) => onChange({ ...settings, min_gap: parseFloat(e.target.value) })}
              className="input-range"
            />
            <p className="setting-desc">
              Prevents the same transition graphic from creating multiple cuts (keeps the strongest peak).
            </p>
          </div>

          {/* 4. Multi Scale Matching Toggle */}
          <div className="setting-field">
            <div className="setting-label-row">
              <span className="setting-label">4. Multi-Scale Matching</span>
              <span className="setting-val-badge">{settings.multi_scale ? 'Enabled' : 'Disabled'}</span>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginTop: '6px' }}>
              <input
                type="checkbox"
                checked={settings.multi_scale}
                onChange={(e) => onChange({ ...settings, multi_scale: e.target.checked })}
                style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
              />
              <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                Match across multiple scale ratios (0.60x – 1.10x)
              </span>
            </label>
            <p className="setting-desc">
              Handles resolution differences between uploaded screenshot and video stream.
            </p>
          </div>

          {/* 5. Video Cut Mode */}
          <div className="setting-field">
            <div className="setting-label-row">
              <span className="setting-label">5. Video Cut Mode</span>
              <span className="setting-val-badge">{settings.cut_mode === 'fast' ? 'Fast Stream Copy' : 'Accurate Re-encode'}</span>
            </div>
            <select
              className="input-select"
              value={settings.cut_mode}
              onChange={(e) => onChange({ ...settings, cut_mode: e.target.value })}
            >
              <option value="fast">Fast Mode (FFmpeg Stream Copy - instant)</option>
              <option value="accurate">Accurate Mode (Re-encode - frame accurate)</option>
            </select>
            <p className="setting-desc">
              Fast mode performs near-instant cutting without re-encoding. Accurate mode re-encodes keyframes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
