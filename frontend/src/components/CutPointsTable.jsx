import React, { useState } from 'react';
import { Scissors, Play, Trash2, Plus, Edit2, Check, Clock, Sparkles } from 'lucide-react';

export default function CutPointsTable({
  cutPoints,
  totalDuration,
  onSeekVideo,
  onAddManualPoint,
  onDeletePoint,
  onEditPoint,
  onSplitVideo,
  isProcessing
}) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [manualTime, setManualTime] = useState('');
  const [manualLabel, setManualLabel] = useState('Manual Cut');

  const [editingId, setEditingId] = useState(null);
  const [editTimeValue, setEditTimeValue] = useState('');

  const parseTimeToSeconds = (input) => {
    if (!input) return null;
    const str = input.toString().trim();
    if (str.includes(':')) {
      const parts = str.split(':');
      if (parts.length === 2) {
        return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
      } else if (parts.length === 3) {
        return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2]);
      }
    }
    const val = parseFloat(str);
    return isNaN(val) ? null : val;
  };

  const handleAddSubmit = (e) => {
    e.preventDefault();
    const secs = parseTimeToSeconds(manualTime);
    if (secs === null || secs < 0 || (totalDuration > 0 && secs > totalDuration)) {
      alert(`Please enter a valid time between 0 and ${totalDuration.toFixed(1)}s (e.g., 45.5 or 01:15)`);
      return;
    }
    onAddManualPoint(secs, manualLabel);
    setManualTime('');
    setShowAddForm(false);
  };

  const startEdit = (cp) => {
    setEditingId(cp.id);
    setEditTimeValue(cp.timestamp.toString());
  };

  const saveEdit = (id) => {
    const secs = parseTimeToSeconds(editTimeValue);
    if (secs === null || secs < 0) {
      alert('Please enter a valid timestamp');
      return;
    }
    onEditPoint(id, secs);
    setEditingId(null);
  };

  return (
    <div className="card" style={{ marginBottom: '28px' }}>
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="card-title">
            <Scissors size={20} color="#3B82F6" />
            Detected Cut Points ({cutPoints.length})
          </h3>
          <p className="card-desc">
            Review and fine-tune cut timestamps before splitting the video into clips.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-secondary"
            style={{ padding: '8px 14px', fontSize: '13px' }}
            onClick={() => setShowAddForm(!showAddForm)}
          >
            <Plus size={16} /> + Add Manual Cut Point
          </button>
          <button
            className="btn btn-emerald"
            style={{ padding: '8px 18px', fontSize: '14px' }}
            onClick={onSplitVideo}
            disabled={isProcessing || cutPoints.length === 0}
          >
            <Scissors size={16} /> Split Video Now ({cutPoints.length + 1} clips)
          </button>
        </div>
      </div>

      {/* Manual Cut Form */}
      {showAddForm && (
        <form
          onSubmit={handleAddSubmit}
          style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-end',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ flex: '1', minWidth: '160px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Timestamp (Seconds or MM:SS)
            </label>
            <input
              type="text"
              className="input-text"
              placeholder="e.g. 01:25.50 or 85.5"
              value={manualTime}
              onChange={(e) => setManualTime(e.target.value)}
              style={{ width: '100%' }}
              required
            />
          </div>
          <div style={{ flex: '1', minWidth: '160px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              Label / Reference Description
            </label>
            <input
              type="text"
              className="input-text"
              placeholder="e.g. Custom Anchor Transition"
              value={manualLabel}
              onChange={(e) => setManualLabel(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ padding: '9px 16px' }}>
            <Plus size={16} /> Add Point
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => setShowAddForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {/* Visual Timeline Scrubber Bar */}
      {totalDuration > 0 && (
        <div style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
            <span>00:00 (Start)</span>
            <span>Video Timeline ({totalDuration.toFixed(1)}s)</span>
            <span>{Math.floor(totalDuration / 60)}:{(totalDuration % 60).toFixed(0).padStart(2, '0')} (End)</span>
          </div>
          <div className="timeline-bar-wrapper">
            {cutPoints.map((cp, idx) => {
              const leftPct = (cp.timestamp / totalDuration) * 100;
              return (
                <div
                  key={cp.id || idx}
                  className="timeline-marker"
                  style={{ left: `${Math.min(99.5, Math.max(0.5, leftPct))}%` }}
                  onClick={() => onSeekVideo(cp.timestamp)}
                  title={`Cut #${idx + 1} at ${cp.formatted_time} (${cp.reference_name})`}
                >
                  <div className="timeline-marker-tag">
                    #{idx + 1} {cp.formatted_time}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Table */}
      {cutPoints.length === 0 ? (
        <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
          No cut points detected yet. Click "Detect Cut Points" or add manual cut points above.
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>No.</th>
                <th>Cut Timestamp</th>
                <th>Reference Screen</th>
                <th>Match Score</th>
                <th>Type</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {cutPoints.map((cp, index) => (
                <tr key={cp.id || index}>
                  <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    #{index + 1}
                  </td>
                  <td>
                    {editingId === cp.id ? (
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <input
                          type="text"
                          className="input-text"
                          style={{ padding: '4px 8px', width: '90px' }}
                          value={editTimeValue}
                          onChange={(e) => setEditTimeValue(e.target.value)}
                        />
                        <button
                          className="btn btn-emerald"
                          style={{ padding: '4px 8px' }}
                          onClick={() => saveEdit(cp.id)}
                        >
                          <Check size={14} />
                        </button>
                      </div>
                    ) : (
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                        {cp.formatted_time} ({cp.timestamp.toFixed(2)}s)
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ fontWeight: 500 }}>{cp.reference_name}</span>
                  </td>
                  <td>
                    <span className="score-badge">
                      {cp.is_manual ? '1.000' : (cp.match_score ? cp.match_score.toFixed(3) : '0.000')}
                    </span>
                  </td>
                  <td>
                    {cp.is_manual ? (
                      <span style={{ fontSize: '11px', color: 'var(--accent-amber)', background: 'rgba(245, 158, 11, 0.12)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                        Manual
                      </span>
                    ) : (
                      <span style={{ fontSize: '11px', color: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                        Detected
                      </span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                        onClick={() => onSeekVideo(cp.timestamp)}
                        title="Jump video player to this timestamp"
                      >
                        <Play size={12} /> Preview
                      </button>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        onClick={() => startEdit(cp)}
                        title="Edit timestamp"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        className="btn-icon-delete"
                        onClick={() => onDeletePoint(cp.id)}
                        title="Delete cut point"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
