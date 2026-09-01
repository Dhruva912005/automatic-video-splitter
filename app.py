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
    page_title="Automatic Video Splitter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════
# CLEAN MODERN DARK CSS (Matching Reference Design Exactly)
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Global Theme ── */
:root {
  --bg-main: #0B0F17;
  --bg-card: #131A26;
  --bg-input: #1A2436;
  --border-color: #26334D;
  --primary: #3B82F6;
  --accent-cyan: #06B6D4;
  --accent-emerald: #10B981;
  --accent-amber: #F59E0B;
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

/* Hide Streamlit default branding */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], .stDeployButton,
[data-testid="collapsedControl"], section[data-testid="stSidebar"] {
  display: none !important;
  visibility: hidden !important;
}

.main .block-container {
  max-width: 1280px !important;
  padding: 32px 24px 60px 24px !important;
}

/* ── Header ── */
.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 9999px;
  color: #06B6D4 !important;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.header-title {
  font-size: 36px !important;
  font-weight: 800 !important;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #FFFFFF 40%, #93C5FD 100%);
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  margin-bottom: 8px !important;
  line-height: 1.2 !important;
}

.header-subtitle {
  font-size: 14.5px !important;
  color: #94A3B8 !important;
  max-width: 740px;
  line-height: 1.6 !important;
  margin-bottom: 0 !important;
}

/* ── Main Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #131A26 !important;
  border: 1px solid #26334D !important;
  border-radius: 18px !important;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5) !important;
  padding: 6px !important;
}

.card-title {
  font-size: 17px;
  font-weight: 700;
  color: #FFFFFF !important;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.card-desc {
  font-size: 13px;
  color: #94A3B8 !important;
  margin-bottom: 14px;
}

/* ── Upload Area & Tags ── */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(26, 36, 54, 0.4) !important;
  border: 2px dashed #26334D !important;
  border-radius: 12px !important;
  min-height: 120px !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
  border-color: #3B82F6 !important;
  background: rgba(59, 130, 246, 0.08) !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div { color: #94A3B8 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span { color: #FFFFFF !important; font-weight: 600 !important; }

.format-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
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
  gap: 10px;
  margin-top: 14px;
  margin-bottom: 12px;
}

.meta-item {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 8px;
  padding: 8px 12px;
}

.meta-label {
  font-size: 10px;
  color: #64748B !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.meta-value {
  font-size: 14px;
  font-weight: 700;
  color: #FFFFFF !important;
  font-family: 'JetBrains Mono', monospace;
}

/* ── Reference Screens Grid & Empty State ── */
.refs-empty {
  border: 1px dashed #26334D;
  border-radius: 12px;
  padding: 32px 20px;
  text-align: center;
  margin: 8px 0;
}

.refs-empty-icon { font-size: 32px; margin-bottom: 8px; }
.refs-empty-title { font-weight: 600; color: #FFFFFF !important; margin-bottom: 4px; font-size: 14px; }
.refs-empty-sub { font-size: 12.5px; color: #94A3B8 !important; }

.ref-card-box {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 8px;
  overflow: hidden;
  padding: 4px;
  margin-bottom: 6px;
}

.ref-card-name {
  font-size: 12px;
  font-weight: 600;
  color: #FFFFFF !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 4px 6px 2px 6px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 7px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.15);
  color: #10B981 !important;
  border: 1px solid rgba(16, 185, 129, 0.3);
  margin-left: 6px;
  margin-bottom: 4px;
}

/* ── Collapsible Advanced Settings ── */
[data-testid="stExpander"] {
  background: #131A26 !important;
  border: 1px solid #26334D !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  margin: 18px 0 !important;
}

[data-testid="stExpander"] > details > summary {
  background: rgba(26, 36, 54, 0.3) !important;
  padding: 14px 20px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  color: #FFFFFF !important;
}

/* ── Action Card ── */
.action-banner {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(19, 26, 38, 0.9) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 16px;
  padding: 20px 24px;
  margin: 20px 0 10px 0;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
}

.action-banner h3 {
  font-size: 18px !important;
  font-weight: 700 !important;
  color: #FFFFFF !important;
  margin-bottom: 2px !important;
}

.action-banner p {
  color: #94A3B8 !important;
  font-size: 13.5px !important;
  margin: 0 !important;
}

/* ── Buttons ── */
.stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: all 0.2s ease !important;
  background: #1A2436 !important;
  border: 1px solid #26334D !important;
  color: #F8FAFC !important;
  padding: 8px 18px !important;
}

.stButton > button:hover {
  background: #192233 !important;
  border-color: rgba(59, 130, 246, 0.5) !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #8B5CF6 100%) !important;
  border: none !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4) !important;
  font-weight: 700 !important;
}

.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 22px rgba(59, 130, 246, 0.55) !important;
}

[data-testid="stDownloadButton"] > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
  border: none !important;
  color: #FFFFFF !important;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
  padding: 10px 22px !important;
}

/* ── Progress Card ── */
.progress-card {
  background: #131A26;
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 14px;
  padding: 18px 22px;
  margin: 16px 0;
}

.progress-stage {
  font-size: 15px;
  font-weight: 600;
  color: #3B82F6 !important;
}

/* ── Simple Timestamp List & Clips ── */
.ts-list-box {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 10px;
  padding: 14px 18px;
  margin: 14px 0;
}

.ts-list-item {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13.5px;
  color: #F8FAFC !important;
  padding: 4px 0;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(38, 51, 77, 0.3);
}

.ts-list-item:last-child {
  border-bottom: none;
}

.clip-simple-card {
  background: #1A2436;
  border: 1px solid #26334D;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 10px;
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
               min_gap: float, multi_scale: bool, progress_bar, stage_elem) -> list:
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
            stage_elem.markdown(
                f'<div class="progress-stage">🔍 Scanning {format_timestamp(cur_time)} / {format_timestamp(duration)} &nbsp;|&nbsp; Matches: <b>{len(raw_detections)}</b></div>',
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

    # Non-Maximum Suppression (min gap deduplication)
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
                       min_clip_sec: float, cut_mode: str, progress_bar, stage_elem) -> list:
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
        try:
            progress_bar.progress(pct)
            stage_elem.markdown(
                f'<div class="progress-stage">✂️ Cutting Clip {clip_num:03d}: {format_timestamp(start)} → {format_timestamp(end)} ({length:.1f}s)</div>',
                unsafe_allow_html=True
            )
        except Exception:
            pass

        success = False

        if cut_mode == "fast":
            # Stream copy — fast. -map 0:v maps video, -map 0:a? maps audio if it exists (? = optional, no error if missing)
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(length),
                "-map", "0:v",
                "-map", "0:a?",
                "-c:v", "copy",
                "-c:a", "copy",
                "-avoid_negative_ts", "make_zero",
                "-movflags", "+faststart",
                out_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if os.path.exists(out_file) and os.path.getsize(out_file) > 1024:
                success = True

        if not success:
            # Accurate re-encode — always preserves audio by re-encoding to aac
            # -map 0:a? means: include audio if source has it, skip silently if not
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(length),
                "-map", "0:v",
                "-map", "0:a?",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-avoid_negative_ts", "make_zero",
                "-movflags", "+faststart",
                out_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if not (os.path.exists(out_file) and os.path.getsize(out_file) > 1024):
                # Last resort: no audio mapping (video-only source)
                cmd_vo = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-i", video_path,
                    "-t", str(length),
                    "-map", "0:v",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                    "-avoid_negative_ts", "make_zero",
                    "-movflags", "+faststart",
                    out_file
                ]
                subprocess.run(cmd_vo, capture_output=True, text=True)

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

    try:
        progress_bar.progress(1.0)
    except Exception:
        pass
    return clips


def create_zip_archive(clips: list, zip_path: str) -> str:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in clips:
            if os.path.exists(c["path"]):
                zf.write(c["path"], c["filename"])
    return zip_path


def normalize_for_web(input_path: str, job_dir: str) -> str:
    """
    Remux/re-encode the uploaded video to a browser-compatible MP4:
      - Video stream: copy as-is (no quality loss, very fast)
      - Audio stream: re-encode to AAC 192 kbps (browser safe)
      - Container:    MP4 with faststart (streamable)
    Returns path to the normalized file. Falls back to original if FFmpeg fails.
    """
    out_path = os.path.join(job_dir, "uploaded_normalized.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-map", "0:v",
        "-map", "0:a?",          # include audio only if it exists
        "-c:v", "copy",          # copy video — no re-encode, instant
        "-c:a", "aac",           # re-encode audio to AAC (browser compatible)
        "-b:a", "192k",
        "-ar", "44100",          # standard sample rate
        "-ac", "2",              # stereo
        "-movflags", "+faststart",  # MP4 optimised for web streaming
        "-avoid_negative_ts", "make_zero",
        out_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        return out_path
    # Fallback: return original if FFmpeg failed
    return input_path

def generate_sample_demo(job_dir: str):
    width, height, fps = 640, 360, 25
    
    t1 = np.ones((height, width, 3), dtype=np.uint8) * 30
    cv2.rectangle(t1, (40, 40), (600, 320), (30, 30, 200), -1)
    cv2.putText(t1, "FAST 100", (120, 190), cv2.FONT_HERSHEY_DUPLEX, 2.8, (255, 255, 255), 5)
    cv2.putText(t1, "BREAKING NEWS", (160, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 100), 3)

    t2 = np.ones((height, width, 3), dtype=np.uint8) * 40
    cv2.rectangle(t2, (40, 40), (600, 320), (0, 140, 255), -1)
    cv2.putText(t2, "SPEED NEWS", (100, 190), cv2.FONT_HERSHEY_DUPLEX, 2.5, (255, 255, 255), 5)
    cv2.putText(t2, "SPECIAL BULLETIN", (140, 270), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 3)

    _, t1_png = cv2.imencode(".png", t1)
    _, t2_png = cv2.imencode(".png", t2)

    video_path = os.path.join(job_dir, "sample_demo_video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    total_frames = 25 * fps

    for f in range(total_frames):
        sec = f / fps
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        if 8.0 <= sec < 9.0:
            frame = t1.copy()
        elif 16.0 <= sec < 17.0:
            frame = t2.copy()
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
# 1. HEADER / BRANDING
# ═══════════════════════════════════════════════════════════
hdr_left, hdr_right = st.columns([4, 1.2])

with hdr_left:
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

with hdr_right:
    st.markdown('<div style="padding-top: 36px;"></div>', unsafe_allow_html=True)
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

st.markdown('<div style="margin-bottom: 24px;"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 2. MAIN 2-COLUMN GRID
# ═══════════════════════════════════════════════════════════
col_video, col_refs = st.columns(2, gap="large")

# ────────────────────────────────────────────────────────────
# LEFT CARD: 1. Upload Video
# ────────────────────────────────────────────────────────────
with col_video:
    with st.container(border=True):
        st.markdown('<div class="card-title">📹 1. Upload Video</div>', unsafe_allow_html=True)
        st.markdown('<p class="card-desc">Supported: MP4, MOV, MKV, AVI</p>', unsafe_allow_html=True)

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

        if video_file is not None and st.session_state.video_filename != video_file.name:
            jdir = get_job_dir()
            ext = Path(video_file.name).suffix or ".mp4"
            raw_path = os.path.join(jdir, f"uploaded_video{ext}")
            vbytes = video_file.read()
            with open(raw_path, "wb") as f:
                f.write(vbytes)
            # Normalize to web-compatible MP4 (H.264 + AAC) so browser plays audio
            with st.spinner("⚙️ Preparing video for playback..."):
                vpath = normalize_for_web(raw_path, jdir)
            meta = get_video_metadata(vpath)
            st.session_state.video_path = vpath
            # Store path instead of bytes to avoid large memory usage; read fresh on display
            st.session_state.video_bytes = None
            st.session_state.video_meta = meta
            st.session_state.video_filename = video_file.name
            st.session_state.cut_points = []
            st.session_state.clips = []
            st.session_state.zip_path = None
            st.session_state.stage = "upload"

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

            # Always read from the normalized file path — ensures audio works in browser
            if st.session_state.video_path and os.path.exists(st.session_state.video_path):
                with open(st.session_state.video_path, "rb") as vf:
                    st.video(vf.read())


# ────────────────────────────────────────────────────────────
# RIGHT CARD: 2. Reference Cut Screens
# ────────────────────────────────────────────────────────────
with col_refs:
    with st.container(border=True):
        r_top_l, r_top_r = st.columns([2.2, 1.8])
        with r_top_l:
            st.markdown('<div class="card-title">🖼️ 2. Reference Cut Screens</div>', unsafe_allow_html=True)
            st.markdown('<p class="card-desc">Screenshots representing transitions where cuts occur</p>', unsafe_allow_html=True)
        with r_top_r:
            if st.button("➕ Add Custom Screenshot", key="btn_open_custom", type="primary", use_container_width=True):
                st.session_state.show_custom_modal = not st.session_state.show_custom_modal
                st.rerun()

        # ── CUSTOM SCREENSHOT DRAWER (Inside Card 2) ──
        if st.session_state.show_custom_modal:
            st.markdown("""
            <div style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
            """, unsafe_allow_html=True)
            
            m_head_l, m_head_r = st.columns([4, 1.2])
            with m_head_l:
                st.markdown('<div style="font-weight:700; color:#60A5FA; font-size:15px; display:flex; align-items:center; gap:6px;">📷 Add Custom Reference Screenshot</div>', unsafe_allow_html=True)
            with m_head_r:
                if st.button("✕ Close", key="close_custom_modal", use_container_width=True):
                    st.session_state.show_custom_modal = False
                    st.rerun()

            tab_capture, tab_upload = st.tabs(["📷 Capture Frame from Video", "⬆ Upload Image File"])

            with tab_capture:
                if not st.session_state.video_path or not os.path.exists(st.session_state.video_path or ""):
                    st.info("📹 Please upload a video first to extract frames.")
                else:
                    meta = st.session_state.video_meta or {}
                    max_duration = float(meta.get("duration", 3600.0))
                    seek_sec = st.slider(
                        "Seek to timestamp (seconds)",
                        0.0, max(max_duration, 1.0), 0.0, 0.25,
                        format="%.2fs",
                        key="frame_seek_slider"
                    )
                    st.caption(f"Selected position: **{format_timestamp(seek_sec)}**")

                    # Live frame preview
                    frame_bytes = extract_frame_at_timestamp(st.session_state.video_path, seek_sec)
                    if frame_bytes:
                        preview_img = Image.open(io.BytesIO(frame_bytes))
                        st.image(preview_img, caption=f"Frame at {format_timestamp(seek_sec)}", use_column_width=True)

                    frame_name = st.text_input(
                        "Reference Label",
                        value=f"Frame at {format_timestamp(seek_sec)}",
                        key="frame_name_input"
                    )

                    if st.button("✅ Capture & Add Reference", type="primary", key="btn_save_frame", use_container_width=True):
                        if frame_bytes:
                            tmpl = prepare_template(frame_bytes)
                            if tmpl is not None:
                                lbl = (frame_name or f"Frame at {format_timestamp(seek_sec)}").strip()
                                existing_labels = {r["name"] for r in st.session_state.ref_previews}
                                if lbl in existing_labels:
                                    lbl = f"{lbl} ({len(st.session_state.ref_previews)+1})"
                                st.session_state.templates.append({"name": lbl, "gray": tmpl})
                                st.session_state.ref_previews.append({"name": lbl, "bytes": frame_bytes})
                                st.session_state.cut_points = []
                                st.session_state.clips = []
                                st.session_state.stage = "upload"
                                st.session_state.show_custom_modal = False
                                st.rerun()
                            else:
                                st.error("Could not process frame.")
                        else:
                            st.error("Failed to capture frame at this timestamp.")

            with tab_upload:
                custom_img = st.file_uploader(
                    "Select Image File",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="custom_img_uploader"
                )
                if custom_img is not None:
                    raw_preview = custom_img.getvalue()
                    if raw_preview:
                        st.image(Image.open(io.BytesIO(raw_preview)), use_column_width=True)
                
                custom_lbl = st.text_input(
                    "Reference Label",
                    value=Path(custom_img.name).stem if custom_img else "Custom Reference",
                    key="custom_lbl_input"
                )
                if st.button("✅ Add Reference Image", type="primary", key="btn_add_img_ref", use_container_width=True):
                    if custom_img is not None:
                        raw = custom_img.getvalue()
                        tmpl = prepare_template(raw)
                        if tmpl is not None:
                            lbl = (custom_lbl or Path(custom_img.name).stem).strip()
                            existing_labels = {r["name"] for r in st.session_state.ref_previews}
                            if lbl in existing_labels:
                                lbl = f"{lbl} ({len(st.session_state.ref_previews)+1})"
                            st.session_state.templates.append({"name": lbl, "gray": tmpl})
                            st.session_state.ref_previews.append({"name": lbl, "bytes": raw})
                            st.session_state.cut_points = []
                            st.session_state.clips = []
                            st.session_state.stage = "upload"
                            st.session_state.show_custom_modal = False
                            st.rerun()
                        else:
                            st.error("Could not process image.")
                    else:
                        st.warning("Please select an image file first.")

            st.markdown("</div>", unsafe_allow_html=True)

        # ── Existing Reference Cards / Empty State ──
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
            to_delete = None
            for row_start in range(0, len(refs), cols_per_row):
                row_refs = refs[row_start : row_start + cols_per_row]
                ref_cols = st.columns(len(row_refs))
                for ci, rp in enumerate(row_refs):
                    idx = row_start + ci
                    with ref_cols[ci]:
                        st.markdown('<div class="ref-card-box">', unsafe_allow_html=True)
                        try:
                            pil_img = Image.open(io.BytesIO(rp["bytes"]))
                            st.image(pil_img, use_column_width=True)
                        except Exception:
                            pass
                        st.markdown(f'<div class="ref-card-name" title="{rp["name"]}">{rp["name"]}</div>', unsafe_allow_html=True)
                        st.markdown('<span class="status-pill">✓ Ready</span>', unsafe_allow_html=True)
                        if st.button("🗑️ Remove", key=f"del_ref_{idx}", help=f"Remove {rp['name']}", use_container_width=True):
                            to_delete = idx
                        st.markdown('</div>', unsafe_allow_html=True)
            
            if to_delete is not None:
                st.session_state.ref_previews.pop(to_delete)
                st.session_state.templates.pop(to_delete)
                st.session_state.cut_points = []
                st.session_state.clips = []
                st.rerun()

        # ── Bulk Image Upload ──
        st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
        ref_files = st.file_uploader(
            "⬆ Upload Images",
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
                    if raw:
                        tmpl = prepare_template(raw)
                        if tmpl is not None:
                            st.session_state.templates.append({"name": name, "gray": tmpl})
                            st.session_state.ref_previews.append({"name": name, "bytes": raw})
                            existing.add(name)
                            added += 1
            if added:
                st.session_state.cut_points = []
                st.session_state.clips = []
                st.session_state.stage = "upload"
                st.rerun()




# ═══════════════════════════════════════════════════════════
# 4. COMPACT ADVANCED SETTINGS (COLLAPSED BY DEFAULT)
# ═══════════════════════════════════════════════════════════
curr_s = st.session_state.settings

with st.expander(
    f"⚙ Advanced Detection Settings  "
    f"(Threshold: {curr_s['threshold']}, Interval: {curr_s['check_interval']}s, Min Gap: {curr_s['min_gap']}s, Mode: {curr_s['cut_mode']})",
    expanded=False
):
    st_c1, st_c2, st_c3 = st.columns(3)
    st_c4, st_c5, _ = st.columns(3)

    with st_c1:
        new_thresh = st.slider("Detection Threshold", 0.50, 0.95, curr_s["threshold"], 0.01, key="adv_thresh")
    with st_c2:
        intervals = [0.10, 0.25, 0.50, 1.00]
        new_interval = st.selectbox("Frame Check Interval", intervals, index=1, format_func=lambda x: f"{x:.2f}s", key="adv_interval")
    with st_c3:
        new_gap = st.slider("Min Gap Between Detections (sec)", 1.0, 10.0, curr_s["min_gap"], 0.5, key="adv_gap")
    with st_c4:
        new_ms = st.toggle("Multi-Scale Matching", value=curr_s["multi_scale"], key="adv_ms")
    with st_c5:
        new_cut_mode = st.radio("Video Cut Mode", ["fast", "accurate"], index=0, format_func=lambda x: "⚡ Fast (Stream Copy)" if x=="fast" else "🎯 Accurate (Re-encode)", key="adv_cut_mode")

    st.session_state.settings = {
        "threshold": new_thresh,
        "check_interval": new_interval,
        "min_gap": new_gap,
        "multi_scale": new_ms,
        "cut_mode": new_cut_mode
    }


# ═══════════════════════════════════════════════════════════
# 5. PROCESS SECTION (One Clean Action Card)
# ═══════════════════════════════════════════════════════════
can_process = (
    st.session_state.video_path is not None
    and os.path.exists(st.session_state.video_path or "")
    and len(st.session_state.templates) > 0
)

st.markdown(f"""
<div class="action-banner">
  <h3>Ready to Process Video?</h3>
  <p>{f"Video ({st.session_state.video_meta['formatted_duration']}) and {len(st.session_state.templates)} reference screenshot(s) loaded." if can_process else "Upload a video and add reference screenshots to begin automatic detection."}</p>
</div>
""", unsafe_allow_html=True)

act_col1, act_col2 = st.columns([1, 2])

with act_col1:
    detect_clicked = st.button(
        "🔍 Detect Cut Points Only",
        disabled=not can_process,
        key="btn_detect_action",
        use_container_width=True
    )

with act_col2:
    process_all_clicked = st.button(
        "✨ 🚀 Process & Auto Split Video",
        disabled=not can_process,
        type="primary",
        key="btn_full_action",
        use_container_width=True
    )


# ═══════════════════════════════════════════════════════════
# 6. AUTOMATIC PROCESSING EXECUTION
# ═══════════════════════════════════════════════════════════
def run_full_pipeline(split_video: bool):
    meta = st.session_state.video_meta
    cfg = st.session_state.settings

    st.markdown('<div class="progress-card">', unsafe_allow_html=True)
    stg_elem = st.empty()
    pbar = st.progress(0)
    st.markdown('</div>', unsafe_allow_html=True)

    # Step 1: Automatic Detection
    detections = scan_video(
        st.session_state.video_path,
        st.session_state.templates,
        cfg["threshold"],
        cfg["check_interval"],
        cfg["min_gap"],
        cfg["multi_scale"],
        pbar,
        stg_elem
    )

    st.session_state.cut_points = [
        {
            "id": str(uuid.uuid4())[:8],
            "timestamp": d["timestamp"],
            "formatted_time": format_timestamp(d["timestamp"]),
            "reference_name": d["ref_name"],
            "match_score": d["score"]
        }
        for d in detections
    ]

    if not detections:
        stg_elem.markdown('<div class="progress-stage">⚠️ No matching transition frames found above threshold.</div>', unsafe_allow_html=True)
        return

    if split_video:
        # Step 2: Automatic FFmpeg Video Splitting
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
            pbar,
            stg_elem
        )

        zip_path = os.path.join(st.session_state.job_dir, "all_clips.zip")
        create_zip_archive(clips, zip_path)

        st.session_state.clips = clips
        st.session_state.zip_path = zip_path
        st.session_state.stage = "complete"
        stg_elem.markdown(f'<div class="progress-stage">✅ Complete! Created {len(clips)} clips.</div>', unsafe_allow_html=True)
    else:
        st.session_state.stage = "detected"
        stg_elem.markdown(f'<div class="progress-stage">✅ Detection complete! Found {len(detections)} cut points.</div>', unsafe_allow_html=True)

if detect_clicked and can_process:
    run_full_pipeline(split_video=False)

if process_all_clicked and can_process:
    run_full_pipeline(split_video=True)


# ═══════════════════════════════════════════════════════════
# 7. CLEAN RESULTS SECTION
# ═══════════════════════════════════════════════════════════
if st.session_state.cut_points and st.session_state.stage in ["detected", "complete"]:
    with st.container(border=True):
        st.markdown(f'<div class="card-title">✂️ Detected Cut Points ({len(st.session_state.cut_points)})</div>', unsafe_allow_html=True)
        
        # Simple Clean Timestamps List
        st.markdown('<div class="ts-list-box">', unsafe_allow_html=True)
        for i, cp in enumerate(st.session_state.cut_points):
            st.markdown(
                f'<div class="ts-list-item">'
                f'<span><b>{i+1:02d}.</b> {cp["formatted_time"]} ({cp["timestamp"]:.2f}s)</span>'
                f'<span style="color:#06B6D4;">{cp["reference_name"]} &nbsp;•&nbsp; Score: {cp.get("match_score", 1.0):.2f}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.stage == "detected" and not st.session_state.clips:
            if st.button(f"✂️ Split Video into {len(st.session_state.cut_points)+1} Clips Now", type="primary", use_container_width=True):
                meta = st.session_state.video_meta
                cfg = st.session_state.settings
                out_dir = os.path.join(st.session_state.job_dir, "output")
                os.makedirs(out_dir, exist_ok=True)
                pb = st.progress(0)
                stg = st.empty()
                clips = split_video_ffmpeg(st.session_state.video_path, st.session_state.cut_points, out_dir, meta["duration"], 2.0, cfg["cut_mode"], pb, stg)
                zip_path = os.path.join(st.session_state.job_dir, "all_clips.zip")
                create_zip_archive(clips, zip_path)
                st.session_state.clips = clips
                st.session_state.zip_path = zip_path
                st.session_state.stage = "complete"
                st.rerun()


# ═══════════════════════════════════════════════════════════
# 8. FINAL RESULT & DOWNLOAD ZIP
# ═══════════════════════════════════════════════════════════
if st.session_state.stage == "complete" and st.session_state.clips:
    with st.container(border=True):
        st.markdown('<div class="card-title" style="color:#10B981 !important;">🎉 Processing Complete</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="card-desc">Generated <b>{len(st.session_state.clips)}</b> clips from <b>{len(st.session_state.cut_points)}</b> detected transition points.</p>', unsafe_allow_html=True)

        # 4 Summary Stats
        meta = st.session_state.video_meta or {}
        st.markdown(f"""
        <div class="metadata-grid">
          <div class="meta-item"><div class="meta-label">Total Duration</div><div class="meta-value">{meta.get('formatted_duration', 'N/A')}</div></div>
          <div class="meta-item"><div class="meta-label">Reference Screens</div><div class="meta-value" style="color:#06B6D4;">{len(st.session_state.ref_previews)}</div></div>
          <div class="meta-item"><div class="meta-label">Cut Points</div><div class="meta-value" style="color:#F59E0B;">{len(st.session_state.cut_points)}</div></div>
          <div class="meta-item"><div class="meta-label">Clips Created</div><div class="meta-value" style="color:#10B981;">{len(st.session_state.clips)}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Primary Download ZIP Button
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

        # ── View Individual Clips with Embedded Player ──
        with st.expander(f"🎬 View Individual Clips ({len(st.session_state.clips)})", expanded=False):
            st.markdown("""
            <style>
            /* Clip player card */
            .clip-player-card {
                background: #1A2436;
                border: 1px solid #26334D;
                border-radius: 14px;
                padding: 14px;
                margin-bottom: 18px;
            }
            .clip-player-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }
            .clip-player-num {
                font-size: 15px;
                font-weight: 700;
                color: #FFFFFF;
            }
            .clip-player-badge {
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
                color: #10B981;
                background: rgba(16,185,129,0.12);
                border: 1px solid rgba(16,185,129,0.3);
                border-radius: 6px;
                padding: 2px 8px;
            }
            .clip-player-times {
                font-size: 12.5px;
                font-family: 'JetBrains Mono', monospace;
                color: #94A3B8;
                margin-bottom: 10px;
            }
            .clip-player-size {
                font-size: 11px;
                color: #64748B;
                margin-top: 4px;
            }
            /* Make Streamlit video player fill width */
            .clip-player-card [data-testid="stVideo"] video {
                border-radius: 8px;
                width: 100% !important;
                background: #000;
            }
            </style>
            """, unsafe_allow_html=True)

            clips = st.session_state.clips
            clips_per_row = 2

            for row_start in range(0, len(clips), clips_per_row):
                row_clips = clips[row_start: row_start + clips_per_row]
                c_cols = st.columns(len(row_clips))

                for ci, clip in enumerate(row_clips):
                    with c_cols[ci]:
                        st.markdown(f"""
                        <div class="clip-player-card">
                          <div class="clip-player-header">
                            <span class="clip-player-num">🎬 Clip {clip['number']:03d}</span>
                            <span class="clip-player-badge">{clip['duration']:.1f}s</span>
                          </div>
                          <div class="clip-player-times">
                            ⏱ {clip['formatted_start']} &nbsp;→&nbsp; {clip['formatted_end']}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if os.path.exists(clip["path"]):
                            # Embedded video player — no autoplay, user clicks play
                            with open(clip["path"], "rb") as vf:
                                video_bytes = vf.read()
                            st.video(video_bytes)

                            st.markdown(f'<div class="clip-player-size">💾 {clip["size_mb"]} MB &nbsp;|&nbsp; {clip["filename"]}</div>', unsafe_allow_html=True)

                            # Download button below player
                            st.download_button(
                                label=f"⬇ Download Clip {clip['number']:03d}",
                                data=video_bytes,
                                file_name=clip["filename"],
                                mime="video/mp4",
                                key=f"dl_clip_{clip['number']}_{clip['filename']}",
                                use_container_width=True
                            )
                        else:
                            st.warning(f"⚠️ File not found: {clip['filename']}")

                        st.markdown('<div style="margin-bottom:8px;"></div>', unsafe_allow_html=True)



# ── Footer ──
st.markdown("""
<div style="text-align:center; color:#64748B; font-size:12px; padding:30px 0 10px 0; border-top:1px solid #26334D; margin-top:40px;">
  Automatic Video Cut Point Detector &amp; Splitter &nbsp;|&nbsp; Built with Streamlit + OpenCV + FFmpeg
</div>
""", unsafe_allow_html=True)
