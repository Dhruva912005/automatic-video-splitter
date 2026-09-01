import streamlit as st
import cv2
import numpy as np
import os
import shutil
import subprocess
import uuid
import time
import zipfile
from pathlib import Path
from PIL import Image
import tempfile
import io

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Automatic Video Splitter",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS – Dark Modern UI
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0B0F17;
    color: #F8FAFC;
}

/* Main header */
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFFFFF 30%, #93C5FD 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.hero-badge {
    display: inline-block;
    background: rgba(59,130,246,0.15);
    border: 1px solid rgba(59,130,246,0.4);
    color: #06B6D4;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.hero-subtitle {
    color: #94A3B8;
    font-size: 15px;
    line-height: 1.6;
}

/* Section cards */
.step-card {
    background: #131A26;
    border: 1px solid #26334D;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 18px;
}
.step-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Metric tiles */
.metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
.metric-tile {
    background: #1A2436;
    border: 1px solid #26334D;
    border-radius: 10px;
    padding: 10px 16px;
    flex: 1;
    min-width: 120px;
}
.metric-label { font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing:.5px; }
.metric-value { font-size: 15px; font-weight: 700; color: #FFFFFF; font-family: monospace; }

/* Reference card */
.ref-card {
    background: #1A2436;
    border: 1px solid #26334D;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
}
.ref-name { font-size: 12px; font-weight: 600; color: #FFFFFF; margin-top: 6px; word-break: break-word; }
.ref-badge {
    display: inline-block;
    background: rgba(16,185,129,0.15);
    color: #10B981;
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 999px;
    font-size: 10px;
    padding: 1px 8px;
    margin-top: 4px;
}

/* Timestamp table */
.ts-table { width:100%; border-collapse:collapse; font-size:13px; }
.ts-table th { background:#1A2436; padding:10px 14px; color:#94A3B8; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.5px; border-bottom:1px solid #26334D; }
.ts-table td { padding:10px 14px; border-bottom:1px solid rgba(38,51,77,.4); }
.ts-table tr:hover td { background:#192233; }
.score-badge {
    display: inline-block;
    background: rgba(59,130,246,0.15);
    color: #06B6D4;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 999px;
    font-family: monospace;
    font-size: 12px;
    padding: 2px 8px;
}
.manual-badge { background: rgba(245,158,11,0.15); color:#F59E0B; border-color:rgba(245,158,11,.3); }
.detected-badge { background: rgba(16,185,129,0.12); color:#10B981; border-color:rgba(16,185,129,.3); }

/* Progress */
.progress-stage { font-size:15px; font-weight:600; color:#3B82F6; margin-bottom:6px; }

/* Clip card */
.clip-card {
    background: #1A2436;
    border: 1px solid #26334D;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
}
.clip-title { font-size:15px; font-weight:700; color:#FFFFFF; }
.clip-ts { font-family:monospace; font-size:13px; color:#94A3B8; margin-top:2px; }
.clip-size { font-size:12px; color:#64748B; margin-top:4px; }

/* Primary action button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3B82F6, #8B5CF6) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-size: 15px !important;
}

/* Divider */
.section-divider { border:0; border-top: 1px solid #26334D; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
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
    duration = total_frames / fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)
    return dict(fps=round(fps, 2), total_frames=total_frames, duration=round(duration, 2),
                width=width, height=height, size_mb=size_mb,
                formatted_duration=format_timestamp(duration))

def prepare_template(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (3, 3), 0)

def scan_video(video_path: str, templates: list, threshold: float, check_interval: float,
               min_gap: float, multi_scale: bool, progress_bar, status_text) -> list:
    """
    Returns list of dicts: {timestamp, score, ref_name}
    """
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
            current_time = frame_no / fps
            pct = min(1.0, current_time / duration) if duration > 0 else 0
            progress_bar.progress(pct)
            status_text.markdown(
                f'<div class="progress-stage">🔍 Scanning {format_timestamp(current_time)} / {format_timestamp(duration)} &nbsp;|&nbsp; Detected: <b>{len(raw_detections)}</b></div>',
                unsafe_allow_html=True
            )

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (3, 3), 0)
            fh, fw = frame_gray.shape[:2]

            best_score = 0.0
            best_ref = ""

            for tmpl in templates:
                th_px, tw_px = tmpl["gray"].shape[:2]
                for scale in scales:
                    tw = int(tw_px * scale)
                    th = int(th_px * scale)
                    if tw > fw or th > fh or tw <= 10 or th <= 10:
                        continue
                    resized = cv2.resize(tmpl["gray"], (tw, th))
                    res = cv2.matchTemplate(frame_gray, resized, cv2.TM_CCOEFF_NORMED)
                    score = float(res.max())
                    if score > best_score:
                        best_score = score
                        best_ref = tmpl["name"]

            if best_score >= threshold:
                raw_detections.append({"timestamp": round(current_time, 2), "score": round(best_score, 4), "ref_name": best_ref})

        frame_no += 1

    cap.release()

    # Non-Maximum Suppression (cluster by min_gap, keep highest score)
    if not raw_detections:
        return []
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

def split_video_ffmpeg(video_path: str, cut_points: list, output_dir: str,
                       duration: float, min_clip_sec: float, cut_mode: str,
                       progress_bar, status_text) -> list:
    os.makedirs(output_dir, exist_ok=True)
    times = sorted(list(set([0.0] + [cp["timestamp"] for cp in cut_points] + [duration])))
    clips = []
    total = len(times) - 1

    for i in range(total):
        start, end = times[i], times[i + 1]
        length = round(end - start, 2)
        if length < min_clip_sec:
            continue

        pct = i / max(1, total)
        progress_bar.progress(pct)
        clip_num = len(clips) + 1
        out_file = os.path.join(output_dir, f"clip_{clip_num:03d}.mp4")
        status_text.markdown(
            f'<div class="progress-stage">✂️ Cutting Clip {clip_num:03d}: {format_timestamp(start)} → {format_timestamp(end)}</div>',
            unsafe_allow_html=True
        )

        if cut_mode == "accurate":
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(length),
                   "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-avoid_negative_ts", "make_zero", out_file]
        else:
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(length),
                   "-map", "0", "-c", "copy", "-avoid_negative_ts", "make_zero", out_file]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Fallback if stream copy failed
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
            "formatted_end": format_timestamp(end),
        })

    progress_bar.progress(1.0)
    return clips

def create_zip(clips: list, zip_path: str) -> str:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in clips:
            if os.path.exists(c["path"]):
                zf.write(c["path"], c["filename"])
    return zip_path

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "job_dir": None,
        "video_path": None,
        "video_meta": None,
        "templates": [],        # list of {name, gray}
        "ref_previews": [],     # list of {name, bytes}
        "cut_points": [],       # list of {timestamp, score, ref_name, is_manual}
        "clips": [],
        "zip_path": None,
        "stage": "upload",      # upload | detected | complete
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def make_job_dir():
    if not st.session_state.job_dir:
        job_id = str(uuid.uuid4())[:8]
        jdir = os.path.join(tempfile.gettempdir(), f"vidsplit_{job_id}")
        os.makedirs(jdir, exist_ok=True)
        st.session_state.job_dir = jdir
    return st.session_state.job_dir

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-badge">🎬 AI Computer Vision Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Automatic Video Splitter</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Upload a long video and reference transition screenshots. '
    'The system automatically scans every frame, detects where the screenshots appear, '
    'removes duplicate detections, and splits the video into individual clips ready to download.</div>',
    unsafe_allow_html=True
)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR – SETTINGS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Detection Settings")

    threshold = st.slider("Detection Threshold", 0.50, 0.95, 0.70, 0.01,
                          help="Higher = stricter matching, fewer false positives.")
    check_interval = st.selectbox("Frame Check Interval",
                                  [0.10, 0.25, 0.50, 1.00], index=1,
                                  format_func=lambda x: f"{x:.2f} seconds")
    min_gap = st.slider("Min Gap Between Detections (sec)", 1.0, 10.0, 3.0, 0.5,
                        help="Prevents the same transition from being counted multiple times.")
    multi_scale = st.toggle("Multi-Scale Matching", value=True,
                            help="Matches at scales 0.60× – 1.10× to handle resolution differences.")
    cut_mode = st.radio("Video Cut Mode",
                        ["fast", "accurate"],
                        format_func=lambda x: "⚡ Fast (Stream Copy)" if x == "fast" else "🎯 Accurate (Re-encode)")
    min_clip_sec = st.slider("Minimum Clip Duration (sec)", 1.0, 10.0, 2.0, 0.5)

    st.markdown("---")
    if st.button("🗑️ Reset Everything", use_container_width=True):
        if st.session_state.job_dir and os.path.exists(st.session_state.job_dir):
            shutil.rmtree(st.session_state.job_dir, ignore_errors=True)
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        init_state()
        st.rerun()

# ─────────────────────────────────────────────
# STEP 1 – VIDEO UPLOAD
# ─────────────────────────────────────────────
st.markdown("### 📹 Step 1 — Upload Your Video")
video_file = st.file_uploader(
    "Drop your video here (MP4, MOV, MKV, AVI)",
    type=["mp4", "mov", "mkv", "avi"],
    key="video_uploader"
)

if video_file is not None:
    job_dir = make_job_dir()
    ext = Path(video_file.name).suffix or ".mp4"
    vpath = os.path.join(job_dir, f"original_video{ext}")

    if st.session_state.video_path != vpath:
        with open(vpath, "wb") as f:
            f.write(video_file.read())
        meta = get_video_metadata(vpath)
        st.session_state.video_path = vpath
        st.session_state.video_meta = meta
        # Reset downstream when new video uploaded
        st.session_state.cut_points = []
        st.session_state.clips = []
        st.session_state.zip_path = None
        st.session_state.stage = "upload"

    meta = st.session_state.video_meta
    if meta:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("⏱️ Duration", meta["formatted_duration"])
        col2.metric("📐 Resolution", f"{meta['width']}×{meta['height']}")
        col3.metric("🎞️ FPS", meta["fps"])
        col4.metric("💾 Size", f"{meta['size_mb']} MB")

        st.video(video_file)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 2 – REFERENCE SCREENSHOTS
# ─────────────────────────────────────────────
st.markdown("### 🖼️ Step 2 — Upload Reference Cut Screens")
st.caption("Upload screenshots of the transition screens where the video should be cut. Any number of images accepted.")

ref_files = st.file_uploader(
    "Upload reference screenshots (PNG, JPG, JPEG)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
    key="ref_uploader"
)

if ref_files:
    templates = []
    ref_previews = []
    for rf in ref_files:
        img_bytes = rf.read()
        tmpl_gray = prepare_template(img_bytes)
        if tmpl_gray is not None:
            name = Path(rf.name).stem
            templates.append({"name": name, "gray": tmpl_gray})
            ref_previews.append({"name": name, "bytes": img_bytes})

    st.session_state.templates = templates
    st.session_state.ref_previews = ref_previews

    if ref_previews:
        cols = st.columns(min(len(ref_previews), 5))
        for i, rp in enumerate(ref_previews):
            with cols[i % len(cols)]:
                pil_img = Image.open(io.BytesIO(rp["bytes"]))
                st.image(pil_img, use_container_width=True)
                st.markdown(f'<div style="text-align:center;font-size:12px;font-weight:600;color:#FFFFFF;margin-top:4px;">{rp["name"]}</div>', unsafe_allow_html=True)
                st.markdown('<div style="text-align:center;"><span style="background:rgba(16,185,129,0.15);color:#10B981;border:1px solid rgba(16,185,129,0.3);border-radius:999px;font-size:10px;padding:1px 8px;">✓ Ready</span></div>', unsafe_allow_html=True)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 3 – PROCESS
# ─────────────────────────────────────────────
st.markdown("### 🚀 Step 3 — Detect & Split")

can_process = (
    st.session_state.video_path is not None and
    os.path.exists(st.session_state.video_path or "") and
    len(st.session_state.templates) > 0
)

if not can_process:
    if st.session_state.video_path is None:
        st.info("📹 Upload a video to get started.")
    elif not st.session_state.templates:
        st.info("🖼️ Upload at least one reference screenshot.")

if can_process:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        detect_only = st.button("🔍 Detect Cut Points Only", use_container_width=True)
    with col_b:
        process_all = st.button("🚀 Process & Auto Split Video", type="primary", use_container_width=True)

    # ── DETECTION ───────────────────────────────
    if detect_only or process_all:
        meta = st.session_state.video_meta
        st.markdown("---")
        st.markdown("#### 🔍 Scanning Video...")

        pb = st.progress(0)
        status = st.empty()

        detections = scan_video(
            st.session_state.video_path,
            st.session_state.templates,
            threshold, check_interval, min_gap, multi_scale,
            pb, status
        )

        pb.progress(1.0)

        if not detections:
            status.warning(f"⚠️ No matches found above threshold {threshold}. Try lowering the threshold in the sidebar.")
        else:
            status.success(f"✅ Detection complete! Found **{len(detections)}** cut point(s).")

        st.session_state.cut_points = [
            {**d, "id": str(uuid.uuid4())[:6], "is_manual": False}
            for d in detections
        ]
        st.session_state.stage = "detected"

        # If full pipeline, continue to split immediately
        if process_all and detections:
            st.markdown("---")
            st.markdown("#### ✂️ Splitting Video into Clips...")
            pb2 = st.progress(0)
            status2 = st.empty()

            out_dir = os.path.join(st.session_state.job_dir, "output")
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            os.makedirs(out_dir, exist_ok=True)

            clips = split_video_ffmpeg(
                st.session_state.video_path,
                st.session_state.cut_points,
                out_dir,
                meta["duration"],
                min_clip_sec,
                cut_mode,
                pb2, status2
            )

            st.session_state.clips = clips
            st.session_state.stage = "complete"

            zip_path = os.path.join(st.session_state.job_dir, "all_clips.zip")
            create_zip(clips, zip_path)
            st.session_state.zip_path = zip_path
            status2.success(f"✅ Done! Created **{len(clips)}** clips.")

        st.rerun()

# ─────────────────────────────────────────────
# STEP 4 – CUT POINTS TABLE (EDITABLE)
# ─────────────────────────────────────────────
if st.session_state.cut_points:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("### 🗂️ Step 4 — Review & Edit Cut Points")
    st.caption("You can delete false positives, adjust timestamps, or add manual cut points before splitting.")

    # Build editable table
    rows_html = ""
    for i, cp in enumerate(st.session_state.cut_points):
        type_badge = (
            '<span class="score-badge manual-badge">Manual</span>'
            if cp.get("is_manual") else
            '<span class="score-badge detected-badge">Detected</span>'
        )
        rows_html += f"""
        <tr>
            <td style="font-weight:700;font-family:monospace;">#{i+1}</td>
            <td style="font-family:monospace;color:#06B6D4;font-weight:600;">{format_timestamp(cp['timestamp'])} ({cp['timestamp']:.2f}s)</td>
            <td>{cp.get('ref_name','Manual')}</td>
            <td><span class="score-badge">{cp.get('score', 1.0):.3f}</span></td>
            <td>{type_badge}</td>
        </tr>"""

    st.markdown(f"""
    <table class="ts-table">
        <thead><tr>
            <th>No.</th><th>Timestamp</th><th>Reference Screen</th><th>Match Score</th><th>Type</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

    st.markdown("")

    # Delete & Add manual cut point controls
    col_del, col_add = st.columns([1, 1])
    with col_del:
        st.markdown("**❌ Delete a Cut Point**")
        timestamps = [f"#{i+1} — {format_timestamp(cp['timestamp'])} ({cp.get('ref_name','')})"
                      for i, cp in enumerate(st.session_state.cut_points)]
        del_sel = st.selectbox("Select cut point to delete", ["— None —"] + timestamps, key="del_sel")
        if st.button("Delete Selected", key="btn_del"):
            if del_sel != "— None —":
                idx = timestamps.index(del_sel)
                st.session_state.cut_points.pop(idx)
                st.rerun()

    with col_add:
        st.markdown("**➕ Add Manual Cut Point**")
        manual_ts = st.number_input("Timestamp (seconds)", min_value=0.0,
                                    max_value=float(st.session_state.video_meta["duration"]) if st.session_state.video_meta else 9999.0,
                                    step=0.5, key="manual_ts")
        manual_label = st.text_input("Label", value="Manual Cut", key="manual_label")
        if st.button("Add Manual Point", key="btn_add"):
            st.session_state.cut_points.append({
                "id": str(uuid.uuid4())[:6],
                "timestamp": round(manual_ts, 2),
                "score": 1.0,
                "ref_name": manual_label,
                "is_manual": True
            })
            st.session_state.cut_points.sort(key=lambda x: x["timestamp"])
            st.rerun()

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Split now button (only if not already split)
    if st.session_state.stage != "complete":
        if st.button("✂️ Split Video Now", type="primary", use_container_width=True):
            meta = st.session_state.video_meta
            pb = st.progress(0)
            status = st.empty()
            out_dir = os.path.join(st.session_state.job_dir, "output")
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            os.makedirs(out_dir, exist_ok=True)

            clips = split_video_ffmpeg(
                st.session_state.video_path,
                st.session_state.cut_points,
                out_dir, meta["duration"], min_clip_sec, cut_mode, pb, status
            )

            st.session_state.clips = clips
            st.session_state.stage = "complete"
            zip_path = os.path.join(st.session_state.job_dir, "all_clips.zip")
            create_zip(clips, zip_path)
            st.session_state.zip_path = zip_path
            status.success(f"✅ Done! Created **{len(clips)}** clips.")
            st.rerun()

# ─────────────────────────────────────────────
# STEP 5 – RESULTS & DOWNLOAD
# ─────────────────────────────────────────────
if st.session_state.stage == "complete" and st.session_state.clips:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.success(f"🎉 **Processing Complete!** {len(st.session_state.clips)} clips created successfully.")

    meta = st.session_state.video_meta or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📼 Total Duration", meta.get("formatted_duration", "N/A"))
    c2.metric("🖼️ Reference Screens", len(st.session_state.ref_previews))
    c3.metric("✂️ Cut Points", len(st.session_state.cut_points))
    c4.metric("🎬 Clips Created", len(st.session_state.clips))

    # ZIP download button
    if st.session_state.zip_path and os.path.exists(st.session_state.zip_path):
        with open(st.session_state.zip_path, "rb") as zf:
            st.download_button(
                label="📦 Download All Clips as ZIP",
                data=zf,
                file_name="video_split_clips.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary"
            )

    st.markdown("#### 🎬 Individual Clips")
    for clip in st.session_state.clips:
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.markdown(f"""
            <div class="clip-card">
                <div class="clip-title">Clip {clip['number']:03d}</div>
                <div class="clip-ts">{clip['formatted_start']} → {clip['formatted_end']} &nbsp;|&nbsp; {clip['duration']:.1f}s</div>
                <div class="clip-size">{clip['size_mb']} MB</div>
            </div>""", unsafe_allow_html=True)
        with col_btn:
            if os.path.exists(clip["path"]):
                with open(clip["path"], "rb") as vf:
                    st.download_button(
                        label=f"⬇️ Download",
                        data=vf,
                        file_name=clip["filename"],
                        mime="video/mp4",
                        key=f"dl_{clip['number']}"
                    )

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;color:#64748B;font-size:12px;">Automatic Video Splitter &nbsp;|&nbsp; Built with Streamlit + OpenCV + FFmpeg</div>',
    unsafe_allow_html=True
)
