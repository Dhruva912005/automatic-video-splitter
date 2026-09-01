import streamlit as st
import cv2
import numpy as np
import os
import shutil
import subprocess
import uuid
import zipfile
from pathlib import Path
from PIL import Image
import tempfile
import io

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Automatic Video Cut Point Detector & Splitter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════
# PIXEL-PERFECT DESIGN SYSTEM CSS (Replicating Previous React UI)
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Global App Theme ── */
:root {
  --bg-main: #0B0F17;
  --bg-card: #131A26;
  --bg-card-hover: #192233;
  --bg-input: #1A2436;
  --border-color: #26334D;
  --border-focus: #3B82F6;
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --primary: #3B82F6;
  --accent-cyan: #06B6D4;
  --accent-emerald: #10B981;
  --accent-amber: #F59E0B;
  --accent-rose: #F43F5E;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp, [class*="css"] {
  font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased !important;
  color: #F8FAFC !important;
}

.stApp {
  background-color: #0B0F17 !important;
  background-image:
    radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 85% 75%, rgba(139, 92, 246, 0.08) 0%, transparent 40%) !important;
  background-attachment: fixed !important;
}

/* Hide unnecessary default Streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], .stDeployButton,
[data-testid="collapsedControl"] {
  display: none !important;
  visibility: hidden !important;
}

section[data-testid="stSidebar"] { display: none !important; }

.main .block-container {
  max-width: 1320px !important;
  padding: 36px 28px 80px 28px !important;
}

/* ── Typography & Header ── */
.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 9999px;
  color: #06B6D4 !important;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.header-title {
  font-size: 38px !important;
  font-weight: 800 !important;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #FFFFFF 30%, #93C5FD 100%);
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  margin-bottom: 8px !important;
  line-height: 1.2 !important;
}

.header-subtitle {
  font-size: 15px !important;
  color: #94A3B8 !important;
  max-width: 780px;
  line-height: 1.6 !important;
}

/* ── Container Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #131A26 !important;
  border: 1px solid #26334D !important;
  border-radius: 18px !important;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5) !important;
  padding: 4px !important;
  transition: border-color 0.2s ease, transform 0.2s ease !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(59, 130, 246, 0.4) !important;
}

.card-title-wrap {
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #FFFFFF !important;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: #94A3B8 !important;
  margin: 0;
}

/* ── Dropzone & Upload Styling ── */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(26, 36, 54, 0.4) !important;
  border: 2px dashed #26334D !important;
  border-radius: 12px !important;
  min-height: 130px !important;
  transition: all 0.2s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
  border-color: #3B82F6 !important;
  background: rgba(59, 130, 246, 0.08) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div { color: #94A3B8 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span { color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; }
[data-testid="stFileUploaderDropzoneInstructions"] small { color: #64748B !important; }

.format-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
}

.format-tag {
  padding: 2px 8px;
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: #94A3B8 !important;
}

/* ── Metadata Grid ── */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 16px;
  margin-bottom: 14px;
}

.meta-item {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 10px;
  color: #64748B !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.meta-value {
  font-size: 15px;
  font-weight: 700;
  color: #FFFFFF !important;
  font-family: 'JetBrains Mono', monospace;
}

/* ── Video Player ── */
[data-testid="stVideo"] {
  border: 1px solid #26334D !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  background: #000 !important;
  margin-top: 12px !important;
}

/* ── Reference Screenshots Grid ── */
.refs-empty {
  border: 1px dashed #26334D;
  border-radius: 12px;
  padding: 34px 20px;
  text-align: center;
  margin: 10px 0;
}

.refs-empty-icon { font-size: 36px; margin-bottom: 10px; }
.refs-empty-title { font-weight: 600; color: #FFFFFF !important; margin-bottom: 6px; font-size: 15px; }
.refs-empty-sub { font-size: 13px; color: #94A3B8 !important; margin-bottom: 14px; }

.ref-card-body {
  padding: 8px 10px;
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 0 0 8px 8px;
}

.ref-card-name {
  font-size: 12px;
  font-weight: 600;
  color: #FFFFFF !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.15);
  color: #10B981 !important;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* ── Advanced Detection Settings Accordion ── */
[data-testid="stExpander"] {
  background: #131A26 !important;
  border: 1px solid #26334D !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  margin: 20px 0 !important;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5) !important;
}

[data-testid="stExpander"] > details > summary {
  background: rgba(26, 36, 54, 0.4) !important;
  padding: 16px 22px !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  color: #FFFFFF !important;
}

[data-testid="stExpander"] > details > summary:hover {
  background: rgba(26, 36, 54, 0.8) !important;
}

.setting-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.setting-label {
  font-size: 13px;
  font-weight: 600;
  color: #F8FAFC !important;
}

.setting-val-badge {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #06B6D4 !important;
  padding: 2px 6px;
}

.setting-desc {
  font-size: 11px;
  color: #64748B !important;
  margin-top: 4px;
  line-height: 1.4;
}

/* ── Action Banner ── */
.action-banner {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(19, 26, 38, 0.95) 100%);
  border: 1px solid rgba(59, 130, 246, 0.35);
  border-radius: 18px;
  padding: 22px 28px;
  margin: 24px 0 12px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.action-info h3 {
  font-size: 20px !important;
  font-weight: 700 !important;
  color: #FFFFFF !important;
  margin-bottom: 4px !important;
}

.action-info p {
  color: #94A3B8 !important;
  font-size: 14px !important;
  margin: 0 !important;
}

/* ── Standard Button Overrides ── */
.stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 12px !important;
  transition: all 0.2s ease !important;
  background: #1A2436 !important;
  border: 1px solid #26334D !important;
  color: #F8FAFC !important;
  padding: 10px 20px !important;
  font-size: 14px !important;
}

.stButton > button:hover {
  background: #192233 !important;
  border-color: rgba(59, 130, 246, 0.5) !important;
}

/* Main primary glowing button */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #8B5CF6 100%) !important;
  border: none !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 18px rgba(59, 130, 246, 0.45) !important;
  font-weight: 700 !important;
}

.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(59, 130, 246, 0.6) !important;
}

/* Emerald Download button */
[data-testid="stDownloadButton"] > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
  border: none !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4) !important;
  padding: 12px 24px !important;
  font-size: 15px !important;
}

[data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 22px rgba(16, 185, 129, 0.55) !important;
}

/* ── Progress Monitor Card ── */
.progress-card {
  background: #131A26;
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 16px;
  padding: 22px 26px;
  margin: 20px 0;
  box-shadow: 0 0 25px rgba(59, 130, 246, 0.25);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-stage {
  font-size: 16px;
  font-weight: 600;
  color: #3B82F6 !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-pct {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: #06B6D4 !important;
}

.progress-stats-row {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  color: #94A3B8 !important;
}

/* ── Interactive Timeline ── */
.timeline-wrap {
  margin: 16px 0 22px 0;
}

.timeline-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #64748B !important;
  margin-bottom: 6px;
  font-family: 'JetBrains Mono', monospace;
}

.timeline-bg {
  position: relative;
  width: 100%;
  height: 38px;
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 8px;
  overflow: visible;
}

.timeline-mark {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #F43F5E;
  transform: translateX(-50%);
  border-radius: 2px;
}

.timeline-mark-tip {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  background: #000;
  border: 1px solid #F43F5E;
  color: #FFF !important;
  font-size: 9px;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 4px;
  border-radius: 3px;
  white-space: nowrap;
}

/* ── Cut Points Table ── */
.ts-wrapper {
  overflow-x: auto;
  border: 1px solid #26334D;
  border-radius: 12px;
  margin-top: 12px;
  margin-bottom: 12px;
}

.ts-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.ts-table th {
  background: #1A2436;
  padding: 12px 16px;
  color: #94A3B8 !important;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #26334D;
  text-align: left;
}

.ts-table td {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(38, 51, 77, 0.4);
  color: #F8FAFC !important;
}

.ts-table tr:hover td {
  background: #192233;
}

.score-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.15);
  color: #06B6D4 !important;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.manual-badge {
  background: rgba(245, 158, 11, 0.15) !important;
  color: #F59E0B !important;
  border-color: rgba(245, 158, 11, 0.3) !important;
}

.detected-badge {
  background: rgba(16, 185, 129, 0.12) !important;
  color: #10B981 !important;
  border-color: rgba(16, 185, 129, 0.3) !important;
}

/* ── Clips Grid ── */
.clip-card-inner {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
}

.clip-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.clip-num {
  font-size: 15px;
  font-weight: 700;
  color: #FFFFFF !important;
}

.clip-dur {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.15);
  color: #10B981 !important;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.clip-ts {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #94A3B8 !important;
}

.clip-size {
  font-size: 12px;
  color: #64748B !important;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 4px;
}

/* ── Custom Divider ── */
.app-divider {
  border: 0;
  border-top: 1px solid #26334D;
  margin: 28px 0;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════
def format_timestamp(seconds: float) -> str:
    if seconds < 0: seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:05.2f}"
    return f"{mins:02d}:{secs:05.2f}"

def get_video_metadata(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)
    return dict(
        fps=int(round(fps)),
        total_frames=total_frames,
        duration=round(duration, 2),
        width=width,
        height=height,
        size_mb=size_mb,
        formatted_duration=format_timestamp(duration)
    )

def prepare_template(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (3, 3), 0)

def extract_frame_at_timestamp(video_path: str, timestamp_sec: float) -> bytes:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_idx = int(round(timestamp_sec * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return None
    _, buf = cv2.imencode(".png", frame)
    return buf.tobytes()

def scan_video(video_path: str, templates: list, threshold: float, check_interval: float,
               min_gap: float, multi_scale: bool, progress_bar, stage_elem, pct_elem, stats_elem) -> list:
    scales = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10] if multi_scale else [1.00]
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frame_step = max(1, int(round(fps * check_interval)))
    raw_detections = []
    frame_no = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_no % frame_step == 0:
            cur_time = frame_no / fps
            pct = min(1.0, cur_time / duration) if duration > 0 else 0
            progress_bar.progress(pct)
            pct_elem.markdown(f'<div class="progress-pct">{int(pct * 100)}%</div>', unsafe_allow_html=True)
            stage_elem.markdown(
                '<div class="progress-stage">🔍 Scanning video frames with multi-scale matching...</div>',
                unsafe_allow_html=True
            )
            stats_elem.markdown(
                f'<div class="progress-stats-row">'
                f'<div>Scanning Time: <span style="color:var(--accent-cyan);">{format_timestamp(cur_time)}</span> / {format_timestamp(duration)}</div>'
                f'<div>Detected Cut Points: <span style="color:var(--accent-amber);font-weight:700;">{len(raw_detections)}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (3, 3), 0)
            fh, fw = frame_gray.shape[:2]
            best_score, best_ref = 0.0, ""

            for tmpl in templates:
                th_px, tw_px = tmpl["gray"].shape[:2]
                for scale in scales:
                    tw, th = int(tw_px * scale), int(th_px * scale)
                    if tw > fw or th > fh or tw <= 10 or th <= 10:
                        continue
                    resized = cv2.resize(tmpl["gray"], (tw, th))
                    res = cv2.matchTemplate(frame_gray, resized, cv2.TM_CCOEFF_NORMED)
                    s = float(res.max())
                    if s > best_score:
                        best_score = s
                        best_ref = tmpl["name"]

            if best_score >= threshold:
                raw_detections.append({
                    "timestamp": round(cur_time, 2),
                    "score": round(best_score, 4),
                    "ref_name": best_ref
                })

        frame_no += 1

    cap.release()

    if not raw_detections:
        return []

    # Non-Maximum Suppression (group detections within min_gap seconds)
    sorted_dets = sorted(raw_detections, key=lambda x: x["timestamp"])
    clusters, cluster = [], [sorted_dets[0]]
    for det in sorted_dets[1:]:
        if det["timestamp"] - cluster[-1]["timestamp"] <= min_gap:
            cluster.append(det)
        else:
            clusters.append(cluster)
            cluster = [det]
    if cluster:
        clusters.append(cluster)

    return [max(c, key=lambda x: x["score"]) for c in clusters]

def split_video_ffmpeg(video_path: str, cut_points: list, output_dir: str, duration: float,
                       min_clip_sec: float, cut_mode: str, progress_bar, stage_elem, pct_elem) -> list:
    os.makedirs(output_dir, exist_ok=True)
    times = sorted(set([0.0] + [cp["timestamp"] for cp in cut_points] + [duration]))
    clips = []
    total = len(times) - 1

    for i in range(total):
        start, end = times[i], times[i + 1]
        length = round(end - start, 2)
        if length < min_clip_sec:
            continue

        clip_num = len(clips) + 1
        out_file = os.path.join(output_dir, f"clip_{clip_num:03d}.mp4")
        pct = i / max(1, total)
        progress_bar.progress(pct)
        pct_elem.markdown(f'<div class="progress-pct">{int(pct * 100)}%</div>', unsafe_allow_html=True)
        stage_elem.markdown(
            f'<div class="progress-stage">✂️ Cutting Clip {clip_num:03d}: {format_timestamp(start)} → {format_timestamp(end)} ({length:.1f}s)</div>',
            unsafe_allow_html=True
        )

        if cut_mode == "accurate":
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(length),
                   "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-avoid_negative_ts", "make_zero", out_file]
        else:
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(length),
                   "-map", "0", "-c", "copy", "-avoid_negative_ts", "make_zero", out_file]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
            cmd_fb = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(length),
                      "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", out_file]
            subprocess.run(cmd_fb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        size_mb = round(os.path.getsize(out_file) / (1024 * 1024), 2) if os.path.exists(out_file) else 0
        clips.append({
            "number": clip_num,
            "filename": f"clip_{clip_num:03d}.mp4",
            "path": out_file,
            "start": start,
            "end": end,
            "duration": length,
            "size_mb": size_mb,
            "formatted_start": format_timestamp(start),
            "formatted_end": format_timestamp(end)
        })

    progress_bar.progress(1.0)
    return clips

def create_zip_archive(clips: list, zip_path: str) -> str:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in clips:
            if os.path.exists(c["path"]):
                zf.write(c["path"], c["filename"])
    return zip_path

def generate_sample_demo(job_dir: str):
    """Generate 25-second synthetic demo video and reference screenshots"""
    t1 = np.ones((240, 420, 3), dtype=np.uint8) * 230
    cv2.rectangle(t1, (20, 20), (400, 220), (30, 30, 200), -1)
    cv2.putText(t1, "FAST 100", (60, 130), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 4)
    cv2.putText(t1, "BREAKING NEWS", (90, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 100), 2)

    t2 = np.ones((240, 420, 3), dtype=np.uint8) * 40
    cv2.rectangle(t2, (20, 20), (400, 220), (0, 140, 255), -1)
    cv2.putText(t2, "SPEED NEWS", (45, 130), cv2.FONT_HERSHEY_DUPLEX, 1.8, (255, 255, 255), 4)
    cv2.putText(t2, "SPECIAL BULLETIN", (80, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)

    _, t1_png = cv2.imencode(".png", t1)
    _, t2_png = cv2.imencode(".png", t2)

    video_path = os.path.join(job_dir, "sample_demo_video.mp4")
    width, height, fps = 640, 360, 25
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    total_frames = 25 * fps

    for f in range(total_frames):
        sec = f / fps
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        if 8.0 <= sec < 9.0:
            frame = cv2.resize(t1, (width, height))
        elif 16.0 <= sec < 17.0:
            frame = cv2.resize(t2, (width, height))
        else:
            bg_color = (int(sec * 10) % 255, 80, 120)
            frame[:] = bg_color
            cv2.putText(frame, f"NEWS SEGMENT at {sec:.1f}s", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            cv2.putText(frame, "Automatic Video Cut Point Detector Demo", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)
        out.write(frame)
    out.release()

    return video_path, [
        {"name": "Transition Fast 100", "bytes": t1_png.tobytes(), "gray": prepare_template(t1_png.tobytes())},
        {"name": "Transition Speed News", "bytes": t2_png.tobytes(), "gray": prepare_template(t2_png.tobytes())}
    ]


# ═══════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "job_dir": None,
        "video_path": None,
        "video_bytes": None,
        "video_meta": None,
        "video_filename": None,
        "templates": [],
        "ref_previews": [],
        "cut_points": [],
        "clips": [],
        "zip_path": None,
        "stage": "upload",
        "show_custom_modal": False,
        "show_add_manual": False,
        "settings": {
            "threshold": 0.70,
            "check_interval": 0.25,
            "min_gap": 3.0,
            "multi_scale": True,
            "cut_mode": "fast"
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def get_job_dir():
    if not st.session_state.job_dir:
        jid = str(uuid.uuid4())[:8]
        jdir = os.path.join(tempfile.gettempdir(), f"vidsplit_{jid}")
        os.makedirs(jdir, exist_ok=True)
        st.session_state.job_dir = jdir
    return st.session_state.job_dir


# ═══════════════════════════════════════════════════════════
# 1. HEADER / BRANDING (Exact Layout & Load Sample Demo)
# ═══════════════════════════════════════════════════════════
hdr_col1, hdr_col2 = st.columns([4, 1.2])

with hdr_col1:
    st.markdown('<div class="header-badge">✦ AI &amp; COMPUTER VISION VIDEO TOOL</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="header-title">Automatic Video Splitter</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="header-subtitle">'
        'Upload a long multi-segment video and reference transition screenshots. The system will '
        'automatically scan the video frames, detect match points, deduplicate timestamps, and split the video '
        'into individual clips.'
        '</p>',
        unsafe_allow_html=True
    )

with hdr_col2:
    st.markdown('<div style="padding-top: 38px;"></div>', unsafe_allow_html=True)
    if st.button("✦ Load Sample Demo Video", use_container_width=True):
        jdir = get_job_dir()
        vpath, demo_refs = generate_sample_demo(jdir)
        with open(vpath, "rb") as f:
            vbytes = f.read()
        meta = get_video_metadata(vpath)
        st.session_state.video_path = vpath
        st.session_state.video_bytes = vbytes
        st.session_state.video_meta = meta
        st.session_state.video_filename = "sample_demo_video.mp4"
        st.session_state.templates = [{"name": r["name"], "gray": r["gray"]} for r in demo_refs]
        st.session_state.ref_previews = [{"name": r["name"], "bytes": r["bytes"]} for r in demo_refs]
        st.session_state.cut_points = []
        st.session_state.clips = []
        st.session_state.zip_path = None
        st.session_state.stage = "upload"
        st.rerun()

st.markdown('<hr class="app-divider">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 2. MAIN 2-COLUMN GRID: VIDEO UPLOAD & REFERENCE SCREENS
# ═══════════════════════════════════════════════════════════
col_video, col_refs = st.columns(2, gap="large")

# ────────────────────────────────────────────────────────────
# LEFT COLUMN: 1. Upload Video Card
# ────────────────────────────────────────────────────────────
with col_video:
    with st.container(border=True):
        st.markdown("""
        <div class="card-title-wrap">
          <div class="card-title">📹 1. Upload Video</div>
          <p class="card-desc">Supported: MP4, MOV, MKV, AVI</p>
        </div>
        """, unsafe_allow_html=True)

        video_file = st.file_uploader(
            "Drop video here or click to browse",
            type=["mp4", "mov", "mkv", "avi"],
            key="video_uploader",
            label_visibility="collapsed"
        )

        st.markdown("""
        <div class="format-tags">
          <span class="format-tag">.MP4</span>
          <span class="format-tag">.MOV</span>
          <span class="format-tag">.MKV</span>
          <span class="format-tag">.AVI</span>
        </div>
        """, unsafe_allow_html=True)

        # Process uploaded file
        if video_file is not None and st.session_state.video_filename != video_file.name:
            jdir = get_job_dir()
            ext = Path(video_file.name).suffix or ".mp4"
            vpath = os.path.join(jdir, f"uploaded_video{ext}")
            vbytes = video_file.read()
            with open(vpath, "wb") as f:
                f.write(vbytes)
            meta = get_video_metadata(vpath)
            st.session_state.video_path = vpath
            st.session_state.video_bytes = vbytes
            st.session_state.video_meta = meta
            st.session_state.video_filename = video_file.name
            st.session_state.cut_points = []
            st.session_state.clips = []
            st.session_state.zip_path = None
            st.session_state.stage = "upload"

        # Show Metadata Grid & Video Preview
        if st.session_state.video_meta:
            meta = st.session_state.video_meta
            st.markdown(f"""
            <div class="metadata-grid">
              <div class="meta-item">
                <div class="meta-label">Duration</div>
                <div class="meta-value">{meta['formatted_duration']}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Resolution</div>
                <div class="meta-value">{meta['width']}x{meta['height']}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">FPS</div>
                <div class="meta-value">{meta['fps']}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">File Size</div>
                <div class="meta-value">{meta['size_mb']} MB</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.video_bytes:
                st.video(st.session_state.video_bytes)


# ────────────────────────────────────────────────────────────
# RIGHT COLUMN: 2. Reference Cut Screens Card
# ────────────────────────────────────────────────────────────
with col_refs:
    with st.container(border=True):
        r_hdr_left, r_hdr_right = st.columns([2.2, 1.8])
        with r_hdr_left:
            st.markdown("""
            <div class="card-title-wrap">
              <div class="card-title">🖼️ 2. Reference Cut Screens</div>
              <p class="card-desc">Screenshots representing transitions where cuts occur</p>
            </div>
            """, unsafe_allow_html=True)
        with r_hdr_right:
            st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
            if st.button("➕ Add Custom Screenshot", key="btn_toggle_custom", type="primary", use_container_width=True):
                st.session_state.show_custom_modal = not st.session_state.show_custom_modal
            st.markdown('</div>', unsafe_allow_html=True)

        # Empty State vs Grid
        if not st.session_state.ref_previews:
            st.markdown("""
            <div class="refs-empty">
              <div class="refs-empty-icon">🖼️</div>
              <div class="refs-empty-title">No Reference Screenshots Added</div>
              <div class="refs-empty-sub">Upload transition screenshots or capture frames directly from your video.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            cols_per_row = 3
            refs = st.session_state.ref_previews
            for row_start in range(0, len(refs), cols_per_row):
                row_refs = refs[row_start : row_start + cols_per_row]
                ref_cols = st.columns(len(row_refs))
                for ci, rp in enumerate(row_refs):
                    idx = row_start + ci
                    with ref_cols[ci]:
                        pil_img = Image.open(io.BytesIO(rp["bytes"]))
                        st.image(pil_img, use_column_width=True)
                        st.markdown(f"""
                        <div class="ref-card-body">
                          <div class="ref-card-name" title="{rp['name']}">{rp['name']}</div>
                          <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="status-pill">✓ Ready</span>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("🗑️ Delete", key=f"del_ref_{idx}", help=f"Remove {rp['name']}"):
                            st.session_state.ref_previews.pop(idx)
                            st.session_state.templates.pop(idx)
                            st.rerun()

        # Upload more images input at bottom
        st.markdown('<hr class="app-divider" style="margin: 16px 0 10px 0;">', unsafe_allow_html=True)
        ref_files = st.file_uploader(
            "⬆ + Upload More Reference Images",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="ref_file_input",
            label_visibility="visible"
        )
        if ref_files:
            added = 0
            existing = {r["name"] for r in st.session_state.ref_previews}
            for rf in ref_files:
                name = Path(rf.name).stem
                if name not in existing:
                    raw = rf.read()
                    tmpl = prepare_template(raw)
                    if tmpl is not None:
                        st.session_state.templates.append({"name": name, "gray": tmpl})
                        st.session_state.ref_previews.append({"name": name, "bytes": raw})
                        existing.add(name)
                        added += 1
            if added:
                st.rerun()


# ═══════════════════════════════════════════════════════════
# 3. CUSTOM SCREENSHOT MODAL / DRAWER (Inline Replicating Modal)
# ═══════════════════════════════════════════════════════════
if st.session_state.show_custom_modal:
    st.markdown('<hr class="app-divider">', unsafe_allow_html=True)
    with st.container(border=True):
        m_head_l, m_head_r = st.columns([5, 1])
        with m_head_l:
            st.markdown('<div class="card-title">📷 Add Custom Reference Screenshot</div>', unsafe_allow_html=True)
        with m_head_r:
            if st.button("✕ Close", key="close_custom_modal", use_container_width=True):
                st.session_state.show_custom_modal = False
                st.rerun()

        tab_opt_b, tab_opt_a = st.tabs(["📷 Option B — Capture Frame from Video", "⬆ Option A — Upload Image from Computer"])

        with tab_opt_b:
            if not st.session_state.video_path:
                st.info("📹 Please upload a video first to extract frames directly.")
            else:
                meta = st.session_state.video_meta or {}
                max_duration = float(meta.get("duration", 3600.0))
                st.markdown('<p class="card-desc">Seek through your video and capture the exact frame where the transition appears.</p>', unsafe_allow_html=True)

                seek_sec = st.slider(
                    "Seek to timestamp (seconds)",
                    0.0, max_duration, 0.0, 0.5,
                    format="%.2fs",
                    key="frame_seek_slider"
                )
                st.markdown(f'<div style="font-family:JetBrains Mono,monospace;color:#06B6D4;font-size:14px;margin-bottom:12px;">Current Position: <b>{format_timestamp(seek_sec)}</b></div>', unsafe_allow_html=True)

                frame_name = st.text_input("Reference Name", value=f"Frame at {format_timestamp(seek_sec)}", key="frame_name_input")

                fcol1, fcol2 = st.columns([1, 1])
                with fcol1:
                    if st.button("🎞️ Preview Frame at Timestamp", key="btn_seek_preview"):
                        fbytes = extract_frame_at_timestamp(st.session_state.video_path, seek_sec)
                        if fbytes:
                            st.session_state.temp_frame_preview = fbytes
                        else:
                            st.error("Could not extract frame at this position.")

                if "temp_frame_preview" in st.session_state and st.session_state.temp_frame_preview:
                    pil_preview = Image.open(io.BytesIO(st.session_state.temp_frame_preview))
                    st.image(pil_preview, caption=f"Extracted Frame at {format_timestamp(seek_sec)}", use_column_width=True)

                with fcol2:
                    if st.button("✅ Capture & Add Reference", type="primary", key="btn_save_frame"):
                        fbytes = extract_frame_at_timestamp(st.session_state.video_path, seek_sec)
                        if fbytes:
                            tmpl = prepare_template(fbytes)
                            if tmpl is not None:
                                lbl = frame_name or f"Frame at {format_timestamp(seek_sec)}"
                                st.session_state.templates.append({"name": lbl, "gray": tmpl})
                                st.session_state.ref_previews.append({"name": lbl, "bytes": fbytes})
                                st.session_state.show_custom_modal = False
                                if "temp_frame_preview" in st.session_state:
                                    del st.session_state.temp_frame_preview
                                st.rerun()
                        else:
                            st.error("Failed to capture frame.")

        with tab_opt_a:
            st.markdown('<p class="card-desc">Select any screenshot image from your device to use as a visual cut transition.</p>', unsafe_allow_html=True)
            custom_img = st.file_uploader("Select Image File (PNG, JPG, WEBP)", type=["png", "jpg", "jpeg", "webp"], key="custom_img_uploader")
            custom_lbl = st.text_input("Reference Label", value="Custom Reference", key="custom_lbl_input")
            if st.button("Add as Reference Screenshot", type="primary", key="btn_add_img_ref"):
                if custom_img:
                    raw = custom_img.read()
                    tmpl = prepare_template(raw)
                    if tmpl is not None:
                        lbl = custom_lbl or Path(custom_img.name).stem
                        st.session_state.templates.append({"name": lbl, "gray": tmpl})
                        st.session_state.ref_previews.append({"name": lbl, "bytes": raw})
                        st.session_state.show_custom_modal = False
                        st.rerun()
                    else:
                        st.error("Could not parse image.")
                else:
                    st.warning("Please upload an image file first.")


# ═══════════════════════════════════════════════════════════
# 4. ADVANCED DETECTION SETTINGS ACCORDION
# ═══════════════════════════════════════════════════════════
curr_s = st.session_state.settings

with st.expander(
    f"⚙ Advanced Detection Settings  "
    f"(Threshold: {curr_s['threshold']}, Interval: {curr_s['check_interval']}s, Min Gap: {curr_s['min_gap']}s, Mode: {curr_s['cut_mode']})"
):
    st_c1, st_c2, st_c3 = st.columns(3)
    st_c4, st_c5, _ = st.columns(3)

    with st_c1:
        st.markdown(f'<div class="setting-label-row"><span class="setting-label">1. Detection Threshold</span><span class="setting-val-badge">{curr_s["threshold"]:.2f}</span></div>', unsafe_allow_html=True)
        new_thresh = st.slider("Detection Threshold", 0.50, 0.95, curr_s["threshold"], 0.01, key="adv_thresh", label_visibility="collapsed")
        st.markdown('<p class="setting-desc">Higher value = stricter matching (fewer false positives). Lower value = more sensitive detections.</p>', unsafe_allow_html=True)

    with st_c2:
        st.markdown(f'<div class="setting-label-row"><span class="setting-label">2. Frame Check Interval</span><span class="setting-val-badge">{curr_s["check_interval"]}s</span></div>', unsafe_allow_html=True)
        intervals = [0.10, 0.25, 0.50, 1.00]
        new_interval = st.selectbox(
            "Frame Check Interval",
            intervals,
            index=intervals.index(curr_s["check_interval"]) if curr_s["check_interval"] in intervals else 1,
            format_func=lambda x: f"{x:.2f} seconds ({'Ultra-fine' if x==0.1 else 'Recommended' if x==0.25 else 'Fast' if x==0.5 else 'Quick'})",
            key="adv_interval",
            label_visibility="collapsed"
        )
        st.markdown('<p class="setting-desc">Lower interval gives higher accuracy near boundaries but inspects more frames.</p>', unsafe_allow_html=True)

    with st_c3:
        st.markdown(f'<div class="setting-label-row"><span class="setting-label">3. Min Gap Between Detections</span><span class="setting-val-badge">{curr_s["min_gap"]:.1f}s</span></div>', unsafe_allow_html=True)
        new_gap = st.slider("Min Gap Between Detections", 1.0, 10.0, curr_s["min_gap"], 0.5, key="adv_gap", label_visibility="collapsed")
        st.markdown('<p class="setting-desc">Prevents the same transition graphic from creating multiple cuts (keeps the strongest peak).</p>', unsafe_allow_html=True)

    with st_c4:
        st.markdown(f'<div class="setting-label-row"><span class="setting-label">4. Multi-Scale Matching</span><span class="setting-val-badge">{"Enabled" if curr_s["multi_scale"] else "Disabled"}</span></div>', unsafe_allow_html=True)
        new_ms = st.toggle("Match across multiple scale ratios (0.60x – 1.10x)", value=curr_s["multi_scale"], key="adv_ms")
        st.markdown('<p class="setting-desc">Handles resolution differences between reference screenshots and video frames.</p>', unsafe_allow_html=True)

    with st_c5:
        st.markdown(f'<div class="setting-label-row"><span class="setting-label">5. Video Cut Mode</span><span class="setting-val-badge">{"Fast" if curr_s["cut_mode"]=="fast" else "Accurate"}</span></div>', unsafe_allow_html=True)
        new_cut_mode = st.radio(
            "Video Cut Mode",
            ["fast", "accurate"],
            format_func=lambda x: "⚡ Fast (Stream Copy)" if x == "fast" else "🎯 Accurate (Re-encode)",
            index=0 if curr_s["cut_mode"] == "fast" else 1,
            key="adv_cut_mode",
            label_visibility="collapsed"
        )
        st.markdown('<p class="setting-desc">Fast mode cuts in seconds without re-encoding. Accurate mode re-encodes for frame precision.</p>', unsafe_allow_html=True)

    st.session_state.settings = {
        "threshold": new_thresh,
        "check_interval": new_interval,
        "min_gap": new_gap,
        "multi_scale": new_ms,
        "cut_mode": new_cut_mode
    }


# ═══════════════════════════════════════════════════════════
# 5. ACTION BANNER & MAIN PROCESSING BUTTONS
# ═══════════════════════════════════════════════════════════
can_process = (
    st.session_state.video_path is not None
    and os.path.exists(st.session_state.video_path or "")
    and len(st.session_state.templates) > 0
)

st.markdown(f"""
<div class="action-banner">
  <div class="action-info">
    <h3>Ready to Process Video?</h3>
    <p>{f"Video ({st.session_state.video_meta['formatted_duration']}) and {len(st.session_state.templates)} reference screen(s) loaded." if can_process else "Upload video and add reference screenshots to begin automatic detection."}</p>
  </div>
</div>
""", unsafe_allow_html=True)

act_col1, act_col2, act_col3 = st.columns([2, 2.5, 1])

with act_col1:
    detect_clicked = st.button(
        "🔍  Detect Cut Points Only",
        disabled=not can_process,
        key="btn_detect_action",
        use_container_width=True
    )

with act_col2:
    process_all_clicked = st.button(
        "✦ 🚀  AUTO DETECT & SPLIT VIDEO",
        disabled=not can_process,
        type="primary",
        key="btn_full_action",
        use_container_width=True
    )

with act_col3:
    if st.button("🗑️ Reset", key="btn_reset_all", use_container_width=True):
        if st.session_state.job_dir and os.path.exists(st.session_state.job_dir):
            shutil.rmtree(st.session_state.job_dir, ignore_errors=True)
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_state()
        st.rerun()


# ═══════════════════════════════════════════════════════════
# 6. PROCESSING PIPELINE (Detection & Split Execution)
# ═══════════════════════════════════════════════════════════
def execute_detection():
    meta = st.session_state.video_meta
    st.markdown('<div class="progress-card">', unsafe_allow_html=True)
    p_hdr_l, p_hdr_r = st.columns([4, 1])
    with p_hdr_l:
        stg_elem = st.empty()
    with p_hdr_r:
        pct_elem = st.empty()
    pbar = st.progress(0)
    stat_elem = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

    cfg = st.session_state.settings
    detections = scan_video(
        st.session_state.video_path,
        st.session_state.templates,
        cfg["threshold"],
        cfg["check_interval"],
        cfg["min_gap"],
        cfg["multi_scale"],
        pbar,
        stg_elem,
        pct_elem,
        stat_elem
    )
    pbar.progress(1.0)
    pct_elem.markdown('<div class="progress-pct">100%</div>', unsafe_allow_html=True)
    stg_elem.markdown('<div class="progress-stage">✅ Detection complete!</div>', unsafe_allow_html=True)

    st.session_state.cut_points = [
        {
            "id": str(uuid.uuid4())[:8],
            "timestamp": d["timestamp"],
            "formatted_time": format_timestamp(d["timestamp"]),
            "reference_name": d["ref_name"],
            "match_score": d["score"],
            "is_manual": False
        }
        for d in detections
    ]
    st.session_state.stage = "detected"
    return detections

def execute_split():
    meta = st.session_state.video_meta
    cfg = st.session_state.settings

    st.markdown('<div class="progress-card">', unsafe_allow_html=True)
    s_hdr_l, s_hdr_r = st.columns([4, 1])
    with s_hdr_l:
        stg_elem2 = st.empty()
    with s_hdr_r:
        pct_elem2 = st.empty()
    pbar2 = st.progress(0)
    st.markdown('</div>', unsafe_allow_html=True)

    out_dir = os.path.join(st.session_state.job_dir, "output")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    clips = split_video_ffmpeg(
        st.session_state.video_path,
        st.session_state.cut_points,
        out_dir,
        meta["duration"],
        2.0,
        cfg["cut_mode"],
        pbar2,
        stg_elem2,
        pct_elem2
    )

    zip_path = os.path.join(st.session_state.job_dir, "all_clips.zip")
    create_zip_archive(clips, zip_path)

    st.session_state.clips = clips
    st.session_state.zip_path = zip_path
    st.session_state.stage = "complete"
    stg_elem2.markdown(f'<div class="progress-stage">✅ Complete! Created {len(clips)} clips.</div>', unsafe_allow_html=True)
    pct_elem2.markdown('<div class="progress-pct">100%</div>', unsafe_allow_html=True)

if detect_clicked and can_process:
    st.markdown('<hr class="app-divider">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#FFFFFF;font-weight:700;margin-bottom:12px;">🔍 Scanning Video...</h3>', unsafe_allow_html=True)
    dets = execute_detection()
    if dets:
        st.success(f"✅ Detection complete! Found **{len(dets)}** cut point(s). Review and click **Split Video Now** below.")
    else:
        st.warning(f"⚠️ No matches found with threshold {st.session_state.settings['threshold']}. Try lowering the threshold in Advanced Settings.")

if process_all_clicked and can_process:
    st.markdown('<hr class="app-divider">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#FFFFFF;font-weight:700;margin-bottom:12px;">🔍 Phase 1 — Scanning Video Frames...</h3>', unsafe_allow_html=True)
    dets = execute_detection()
    if not dets:
        st.warning(f"⚠️ No matches found above threshold {st.session_state.settings['threshold']}. Try lowering threshold in settings.")
    else:
        st.markdown('<h3 style="color:#FFFFFF;font-weight:700;margin:18px 0 12px 0;">✂️ Phase 2 — Cutting Video into Clips...</h3>', unsafe_allow_html=True)
        execute_split()


# ═══════════════════════════════════════════════════════════
# 7. DETECTED CUT POINTS TABLE & INTERACTIVE TIMELINE
# ═══════════════════════════════════════════════════════════
if st.session_state.cut_points:
    st.markdown('<hr class="app-divider">', unsafe_allow_html=True)

    with st.container(border=True):
        cp_hdr_l, cp_hdr_r = st.columns([3, 2.5])
        with cp_hdr_l:
            st.markdown(f"""
            <div class="card-title-wrap">
              <div class="card-title">✂️ Detected Cut Points ({len(st.session_state.cut_points)})</div>
              <p class="card-desc">Review and fine-tune cut timestamps before splitting the video into clips.</p>
            </div>
            """, unsafe_allow_html=True)

        with cp_hdr_r:
            st_b1, st_b2 = st.columns(2)
            with st_b1:
                if st.button("➕ Add Manual Cut Point", key="btn_open_man_form", use_container_width=True):
                    st.session_state.show_add_manual = not st.session_state.show_add_manual
            with st_b2:
                if st.session_state.stage != "complete":
                    if st.button(
                        f"✂️ Split Video Now ({len(st.session_state.cut_points) + 1} clips)",
                        key="btn_split_direct",
                        type="primary",
                        use_container_width=True
                    ):
                        execute_split()

        # Add Manual Cut Point Form
        if st.session_state.show_add_manual:
            with st.container(border=False):
                st.markdown('<div style="background:#1A2436;border:1px solid #26334D;border-radius:10px;padding:16px;margin:12px 0;">', unsafe_allow_html=True)
                m_c1, m_c2, m_c3 = st.columns([2, 2, 1])
                with m_c1:
                    max_t = float(st.session_state.video_meta["duration"]) if st.session_state.video_meta else 9999.0
                    m_sec = st.number_input("Timestamp (seconds)", 0.0, max_t, step=0.5, key="man_input_sec")
                with m_c2:
                    m_name = st.text_input("Label / Description", value="Manual Cut", key="man_input_label")
                with m_c3:
                    st.markdown('<div style="margin-top:26px;"></div>', unsafe_allow_html=True)
                    if st.button("Add Cut Point", type="primary", key="btn_commit_man"):
                        st.session_state.cut_points.append({
                            "id": str(uuid.uuid4())[:8],
                            "timestamp": round(m_sec, 2),
                            "formatted_time": format_timestamp(m_sec),
                            "reference_name": m_name or "Manual Cut",
                            "match_score": 1.0,
                            "is_manual": True
                        })
                        st.session_state.cut_points.sort(key=lambda x: x["timestamp"])
                        st.session_state.show_add_manual = False
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Visual Timeline
        total_d = st.session_state.video_meta["duration"] if st.session_state.video_meta else 0
        if total_d > 0:
            pins_html = ""
            for idx, cp in enumerate(st.session_state.cut_points):
                pct_pos = min(99.5, max(0.5, (cp["timestamp"] / total_d) * 100))
                pins_html += f"""
                <div class="timeline-mark" style="left:{pct_pos}%;">
                  <div class="timeline-mark-tip">#{idx+1} {cp.get('formatted_time', format_timestamp(cp['timestamp']))}</div>
                </div>
                """

            st.markdown(f"""
            <div class="timeline-wrap">
              <div class="timeline-labels">
                <span>00:00 (Start)</span>
                <span>Interactive Timeline ({format_timestamp(total_d)})</span>
                <span>{format_timestamp(total_d)} (End)</span>
              </div>
              <div class="timeline-bg">{pins_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # Table of Cut Points
        rows = ""
        for i, cp in enumerate(st.session_state.cut_points):
            badge = (
                '<span class="score-badge manual-badge">Manual</span>'
                if cp.get("is_manual") else
                '<span class="score-badge detected-badge">Detected</span>'
            )
            score_val = cp.get("match_score", cp.get("score", 1.0))
            ts_str = cp.get("formatted_time", format_timestamp(cp["timestamp"]))
            rows += f"""
            <tr>
              <td style="font-weight:700;font-family:'JetBrains Mono',monospace;">#{i+1}</td>
              <td style="font-family:'JetBrains Mono',monospace;color:#06B6D4;font-weight:600;">{ts_str} ({cp['timestamp']:.2f}s)</td>
              <td style="font-weight:500;">{cp.get('reference_name', cp.get('ref_name', 'Manual'))}</td>
              <td><span class="score-badge">{score_val:.3f}</span></td>
              <td>{badge}</td>
            </tr>
            """

        st.markdown(f"""
        <div class="ts-wrapper">
          <table class="ts-table">
            <thead>
              <tr>
                <th>No.</th>
                <th>Timestamp</th>
                <th>Reference Screen</th>
                <th>Match Score</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

        # Delete Cut Point Selector
        del_opts = ["— Select cut point to delete —"] + [
            f"#{i+1} — {cp.get('formatted_time', format_timestamp(cp['timestamp']))} ({cp.get('reference_name', cp.get('ref_name', 'Cut'))})"
            for i, cp in enumerate(st.session_state.cut_points)
        ]
        d_col1, d_col2 = st.columns([3, 1])
        with d_col1:
            sel_to_del = st.selectbox("🗑️ Remove a cut point", del_opts, key="sel_cut_to_del", label_visibility="collapsed")
        with d_col2:
            if st.button("Delete Point", key="btn_do_delete"):
                if sel_to_del != del_opts[0]:
                    del_idx = del_opts.index(sel_to_del) - 1
                    if 0 <= del_idx < len(st.session_state.cut_points):
                        st.session_state.cut_points.pop(del_idx)
                        st.rerun()


# ═══════════════════════════════════════════════════════════
# 8. RESULTS & DOWNLOAD ZIP SECTION
# ═══════════════════════════════════════════════════════════
if st.session_state.stage == "complete" and st.session_state.clips:
    st.markdown('<hr class="app-divider">', unsafe_allow_html=True)

    with st.container(border=True):
        r_head_l, r_head_r = st.columns([3, 2])
        with r_head_l:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
              <span style="padding:4px 10px; background:rgba(16,185,129,0.2); color:#10B981; border:1px solid rgba(16,185,129,0.4); border-radius:9999px; font-size:12px; font-weight:700;">
                ✓ Processing Complete
              </span>
            </div>
            <h3 class="card-title" style="font-size:22px;">Generated Video Clips ({len(st.session_state.clips)})</h3>
            <p class="card-desc">All segments have been automatically cut and prepared for instant download.</p>
            """, unsafe_allow_html=True)

        with r_head_r:
            if st.session_state.zip_path and os.path.exists(st.session_state.zip_path):
                with open(st.session_state.zip_path, "rb") as zf:
                    st.download_button(
                        label="📦 Download All Clips as ZIP",
                        data=zf.read(),
                        file_name="video_split_clips.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )

        # Summary Statistics Grid
        meta = st.session_state.video_meta or {}
        st.markdown(f"""
        <div class="metadata-grid" style="margin-top:18px; margin-bottom:24px;">
          <div class="meta-item">
            <div class="meta-label">Total Duration</div>
            <div class="meta-value">{meta.get('formatted_duration', 'N/A')}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Reference Screens</div>
            <div class="meta-value" style="color:#06B6D4;">{len(st.session_state.ref_previews)}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Cut Points</div>
            <div class="meta-value" style="color:#F59E0B;">{len(st.session_state.cut_points)}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Clips Created</div>
            <div class="meta-value" style="color:#10B981;">{len(st.session_state.clips)}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Clips Grid
        clips_per_row = 3
        clips = st.session_state.clips
        for row_start in range(0, len(clips), clips_per_row):
            row_clips = clips[row_start : row_start + clips_per_row]
            c_cols = st.columns(len(row_clips))
            for ci, clip in enumerate(row_clips):
                with c_cols[ci]:
                    st.markdown(f"""
                    <div class="clip-card-inner">
                      <div class="clip-title-row">
                        <span class="clip-num">Clip {clip['number']:03d}</span>
                        <span class="clip-dur">{clip['duration']:.1f}s</span>
                      </div>
                      <div class="clip-ts">{clip['formatted_start']} → {clip['formatted_end']}</div>
                      <div class="clip-size">{clip['size_mb']} MB</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if os.path.exists(clip["path"]):
                        with open(clip["path"], "rb") as vf:
                            st.download_button(
                                label=f"⬇ Download Clip {clip['number']:03d}",
                                data=vf.read(),
                                file_name=clip["filename"],
                                mime="video/mp4",
                                key=f"btn_dl_{clip['number']}",
                                use_container_width=True
                            )


# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center; color:#64748B; font-size:12px; padding:30px 0 10px 0; border-top:1px solid #26334D; margin-top:40px;">
  Automatic Video Cut Point Detector &amp; Splitter &nbsp;|&nbsp; Built with Streamlit + OpenCV + FFmpeg
</div>
""", unsafe_allow_html=True)
