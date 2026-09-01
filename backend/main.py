import os
import shutil
import uuid
import asyncio
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

try:
    from models import (
        DetectionSettings, CutPoint, ReferenceInfo, VideoMetadata,
        GeneratedClip, JobProgress, JobResults
    )
    from detector import VideoDetector, format_timestamp
    from splitter import VideoSplitter
except ImportError:
    from backend.models import (
        DetectionSettings, CutPoint, ReferenceInfo, VideoMetadata,
        GeneratedClip, JobProgress, JobResults
    )
    from backend.detector import VideoDetector, format_timestamp
    from backend.splitter import VideoSplitter

app = FastAPI(title="Automatic Video Cut Point Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

# In-memory job state store
jobs_db: Dict[str, Dict[str, Any]] = {}

def get_job_dir(job_id: str) -> str:
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(os.path.join(job_dir, "references"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "output"), exist_ok=True)
    return job_dir

def init_job(job_id: Optional[str] = None) -> str:
    if not job_id or job_id not in jobs_db:
        jid = job_id or str(uuid.uuid4())[:8]
        get_job_dir(jid)
        jobs_db[jid] = {
            "job_id": jid,
            "stage": "ready",
            "stage_text": "Ready",
            "percent": 0,
            "current_time": 0.0,
            "total_duration": 0.0,
            "detected_count": 0,
            "error_message": None,
            "video_path": None,
            "video_metadata": None,
            "references": [], # list of {'id', 'name', 'filename', 'path', 'preview_url', 'status'}
            "cut_points": [], # list of CutPoint dicts
            "clips": [],
            "zip_path": None,
            "settings": DetectionSettings().model_dump()
        }
        return jid
    return job_id


@app.post("/api/upload-video")
async def upload_video(
    video: UploadFile = File(...),
    job_id: Optional[str] = Form(None)
):
    job_id = init_job(job_id)
    job_dir = get_job_dir(job_id)
    
    # Save video file
    ext = os.path.splitext(video.filename)[1].lower() or ".mp4"
    saved_filename = f"original_video{ext}"
    video_path = os.path.join(job_dir, saved_filename)
    
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)
        
    # Inspect video metadata with OpenCV
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Unable to open video file. Ensure it is a valid video format.")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or np.isnan(fps):
        fps = 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if total_frames > 0 else 0.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    file_size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)
    
    metadata = VideoMetadata(
        filename=video.filename,
        filesize_mb=file_size_mb,
        duration=round(duration, 2),
        formatted_duration=format_timestamp(duration),
        width=width,
        height=height,
        fps=round(fps, 2),
        total_frames=total_frames
    )
    
    jobs_db[job_id]["video_path"] = video_path
    jobs_db[job_id]["video_metadata"] = metadata.model_dump()
    jobs_db[job_id]["total_duration"] = duration
    jobs_db[job_id]["stage"] = "ready"
    jobs_db[job_id]["stage_text"] = "Video uploaded"
    
    return {
        "job_id": job_id,
        "metadata": metadata,
        "video_stream_url": f"/api/media/video/{job_id}/{saved_filename}"
    }


@app.post("/api/upload-reference")
async def upload_reference(
    image: UploadFile = File(...),
    name: Optional[str] = Form(None),
    job_id: str = Form(...)
):
    if job_id not in jobs_db:
        init_job(job_id)
        
    job_dir = get_job_dir(job_id)
    ref_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(image.filename)[1].lower() or ".png"
    ref_filename = f"ref_{ref_id}{ext}"
    ref_path = os.path.join(job_dir, "references", ref_filename)
    
    with open(ref_path, "wb") as f:
        shutil.copyfileobj(image.file, f)
        
    # Validate image
    test_img = cv2.imread(ref_path)
    if test_img is None:
        if os.path.exists(ref_path):
            os.remove(ref_path)
        raise HTTPException(status_code=400, detail="Invalid image file format.")
        
    ref_name = name if name and name.strip() else f"Reference {len(jobs_db[job_id]['references']) + 1}"
    
    ref_info = {
        "id": ref_id,
        "name": ref_name,
        "filename": ref_filename,
        "path": ref_path,
        "preview_url": f"/api/media/ref/{job_id}/{ref_filename}",
        "status": "Ready"
    }
    
    jobs_db[job_id]["references"].append(ref_info)
    
    return {
        "job_id": job_id,
        "reference": ReferenceInfo(
            id=ref_info["id"],
            name=ref_info["name"],
            filename=ref_info["filename"],
            preview_url=ref_info["preview_url"],
            status=ref_info["status"]
        ),
        "all_references": [
            ReferenceInfo(
                id=r["id"],
                name=r["name"],
                filename=r["filename"],
                preview_url=r["preview_url"],
                status=r["status"]
            ) for r in jobs_db[job_id]["references"]
        ]
    }


@app.post("/api/create-custom-reference")
async def create_custom_reference(
    job_id: str = Form(...),
    timestamp: float = Form(...),
    name: Optional[str] = Form(None)
):
    """Capture a frame from the uploaded video at the specified timestamp as a reference screenshot"""
    if job_id not in jobs_db or not jobs_db[job_id].get("video_path"):
        raise HTTPException(status_code=400, detail="Video not uploaded for this job.")
        
    video_path = jobs_db[job_id]["video_path"]
    job_dir = get_job_dir(job_id)
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_idx = int(round(timestamp * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        raise HTTPException(status_code=400, detail=f"Could not extract frame at {timestamp}s.")
        
    ref_id = str(uuid.uuid4())[:8]
    ref_filename = f"ref_custom_{ref_id}.png"
    ref_path = os.path.join(job_dir, "references", ref_filename)
    cv2.imwrite(ref_path, frame)
    
    ref_name = name if name and name.strip() else f"Custom Frame ({format_timestamp(timestamp)})"
    
    ref_info = {
        "id": ref_id,
        "name": ref_name,
        "filename": ref_filename,
        "path": ref_path,
        "preview_url": f"/api/media/ref/{job_id}/{ref_filename}",
        "status": "Ready"
    }
    
    jobs_db[job_id]["references"].append(ref_info)
    
    return {
        "job_id": job_id,
        "reference": ReferenceInfo(
            id=ref_info["id"],
            name=ref_info["name"],
            filename=ref_info["filename"],
            preview_url=ref_info["preview_url"],
            status=ref_info["status"]
        ),
        "all_references": [
            ReferenceInfo(
                id=r["id"],
                name=r["name"],
                filename=r["filename"],
                preview_url=r["preview_url"],
                status=r["status"]
            ) for r in jobs_db[job_id]["references"]
        ]
    }


@app.delete("/api/reference/{job_id}/{ref_id}")
async def delete_reference(job_id: str, ref_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    refs = jobs_db[job_id]["references"]
    target = next((r for r in refs if r["id"] == ref_id), None)
    if target:
        if os.path.exists(target["path"]):
            try:
                os.remove(target["path"])
            except Exception:
                pass
        jobs_db[job_id]["references"] = [r for r in refs if r["id"] != ref_id]
        
    return {"status": "success", "remaining_count": len(jobs_db[job_id]["references"])}


def run_detection_task(job_id: str, settings: DetectionSettings):
    try:
        jobs_db[job_id]["stage"] = "scanning"
        jobs_db[job_id]["stage_text"] = "Scanning video frames..."
        jobs_db[job_id]["percent"] = 0
        jobs_db[job_id]["error_message"] = None
        jobs_db[job_id]["settings"] = settings.model_dump()
        
        video_path = jobs_db[job_id]["video_path"]
        references = jobs_db[job_id]["references"]
        
        def progress_cb(percent, current_time, total_duration, det_count, stage_text):
            jobs_db[job_id]["percent"] = percent
            jobs_db[job_id]["current_time"] = round(current_time, 2)
            jobs_db[job_id]["total_duration"] = round(total_duration, 2)
            jobs_db[job_id]["detected_count"] = det_count
            jobs_db[job_id]["stage_text"] = stage_text

        detector = VideoDetector(video_path, references, settings)
        cut_points = detector.scan_video(progress_callback=progress_cb)
        
        jobs_db[job_id]["cut_points"] = [cp.model_dump() for cp in cut_points]
        jobs_db[job_id]["detected_count"] = len(cut_points)
        jobs_db[job_id]["percent"] = 100
        jobs_db[job_id]["stage"] = "detected"
        jobs_db[job_id]["stage_text"] = f"Detection complete. Found {len(cut_points)} cut points."
    except Exception as e:
        jobs_db[job_id]["stage"] = "error"
        jobs_db[job_id]["error_message"] = str(e)
        jobs_db[job_id]["stage_text"] = f"Error: {str(e)}"


@app.post("/api/process")
async def start_detection(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    threshold: float = Form(0.70),
    check_interval: float = Form(0.25),
    min_gap: float = Form(3.0),
    multi_scale: bool = Form(True),
    cut_mode: str = Form("fast")
):
    if job_id not in jobs_db or not jobs_db[job_id].get("video_path"):
        raise HTTPException(status_code=400, detail="Video not uploaded.")
    if not jobs_db[job_id].get("references"):
        raise HTTPException(status_code=400, detail="Please upload at least one reference screenshot.")
        
    settings = DetectionSettings(
        threshold=threshold,
        check_interval=check_interval,
        min_gap=min_gap,
        multi_scale=multi_scale,
        cut_mode=cut_mode
    )
    
    background_tasks.add_task(run_detection_task, job_id, settings)
    return {"status": "started", "job_id": job_id}


def run_split_task(job_id: str):
    try:
        jobs_db[job_id]["stage"] = "cutting"
        jobs_db[job_id]["stage_text"] = "Splitting video into clips..."
        jobs_db[job_id]["percent"] = 0
        jobs_db[job_id]["error_message"] = None
        
        job_dir = get_job_dir(job_id)
        output_dir = os.path.join(job_dir, "output")
        # Clean previous output
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        video_path = jobs_db[job_id]["video_path"]
        duration = jobs_db[job_id]["total_duration"]
        settings = DetectionSettings(**jobs_db[job_id]["settings"])
        cut_points = [CutPoint(**cp) for cp in jobs_db[job_id]["cut_points"]]
        
        def progress_cb(percent, text):
            jobs_db[job_id]["percent"] = percent
            jobs_db[job_id]["stage_text"] = text

        splitter = VideoSplitter(video_path, output_dir, duration, settings)
        clips = splitter.split_by_cut_points(cut_points, progress_callback=progress_cb)
        
        # Create ZIP
        jobs_db[job_id]["stage_text"] = "Creating ZIP archive of all clips..."
        zip_base = os.path.join(job_dir, "all_clips")
        zip_path = splitter.create_zip(zip_base)
        
        jobs_db[job_id]["clips"] = [c.model_dump() for c in clips]
        jobs_db[job_id]["zip_path"] = zip_path
        jobs_db[job_id]["percent"] = 100
        jobs_db[job_id]["stage"] = "complete"
        jobs_db[job_id]["stage_text"] = f"Complete! Created {len(clips)} clips."
    except Exception as e:
        jobs_db[job_id]["stage"] = "error"
        jobs_db[job_id]["error_message"] = str(e)
        jobs_db[job_id]["stage_text"] = f"Error during splitting: {str(e)}"


@app.post("/api/split-video")
async def split_video(background_tasks: BackgroundTasks, job_id: str = Form(...)):
    if job_id not in jobs_db or not jobs_db[job_id].get("video_path"):
        raise HTTPException(status_code=400, detail="Video not uploaded.")
        
    background_tasks.add_task(run_split_task, job_id)
    return {"status": "started", "job_id": job_id}


def run_full_pipeline_task(job_id: str, settings: DetectionSettings):
    """Run detection and immediately split video in one go"""
    run_detection_task(job_id, settings)
    if jobs_db[job_id]["stage"] != "error":
        run_split_task(job_id)

@app.post("/api/process-and-split")
async def process_and_split_all(
    background_tasks: BackgroundTasks,
    job_id: str = Form(...),
    threshold: float = Form(0.70),
    check_interval: float = Form(0.25),
    min_gap: float = Form(3.0),
    multi_scale: bool = Form(True),
    cut_mode: str = Form("fast")
):
    """1-Click full automated detection + splitting pipeline"""
    if job_id not in jobs_db or not jobs_db[job_id].get("video_path"):
        raise HTTPException(status_code=400, detail="Video not uploaded.")
    if not jobs_db[job_id].get("references"):
        raise HTTPException(status_code=400, detail="Please upload at least one reference screenshot.")
        
    settings = DetectionSettings(
        threshold=threshold,
        check_interval=check_interval,
        min_gap=min_gap,
        multi_scale=multi_scale,
        cut_mode=cut_mode
    )
    background_tasks.add_task(run_full_pipeline_task, job_id, settings)
    return {"status": "started", "job_id": job_id}


@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    j = jobs_db[job_id]
    return JobProgress(
        job_id=job_id,
        stage=j["stage"],
        stage_text=j["stage_text"],
        percent=j["percent"],
        current_time=j.get("current_time", 0.0),
        total_duration=j.get("total_duration", 0.0),
        formatted_current_time=format_timestamp(j.get("current_time", 0.0)),
        formatted_total_duration=format_timestamp(j.get("total_duration", 0.0)),
        detected_count=j.get("detected_count", 0),
        error_message=j.get("error_message")
    )


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    j = jobs_db[job_id]
    refs = [
        ReferenceInfo(
            id=r["id"],
            name=r["name"],
            filename=r["filename"],
            preview_url=r["preview_url"],
            status=r["status"]
        ) for r in j.get("references", [])
    ]
    cut_points = [CutPoint(**cp) for cp in j.get("cut_points", [])]
    clips = [GeneratedClip(**c) for c in j.get("clips", [])]
    meta = VideoMetadata(**j["video_metadata"]) if j.get("video_metadata") else None
    
    return JobResults(
        job_id=job_id,
        video_metadata=meta,
        references=refs,
        cut_points=cut_points,
        clips=clips,
        zip_url=f"/api/download-zip/{job_id}" if j.get("zip_path") else None,
        settings=DetectionSettings(**j.get("settings", {})),
        status=j["stage"]
    )


@app.post("/api/update-cut-points")
async def update_cut_points(
    job_id: str = Form(...),
    action: str = Form(...), # "add", "delete", "edit"
    cut_id: Optional[str] = Form(None),
    timestamp: Optional[float] = Form(None),
    ref_name: Optional[str] = Form("Manual Cut")
):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    cps = jobs_db[job_id].get("cut_points", [])
    
    if action == "add" and timestamp is not None:
        new_cp = CutPoint(
            id=str(uuid.uuid4())[:8],
            timestamp=round(timestamp, 2),
            formatted_time=format_timestamp(timestamp),
            reference_name=ref_name or "Manual Cut",
            match_score=1.0,
            is_manual=True
        )
        cps.append(new_cp.model_dump())
    elif action == "delete" and cut_id:
        cps = [cp for cp in cps if cp["id"] != cut_id]
    elif action == "edit" and cut_id and timestamp is not None:
        for cp in cps:
            if cp["id"] == cut_id:
                cp["timestamp"] = round(timestamp, 2)
                cp["formatted_time"] = format_timestamp(timestamp)
                cp["is_manual"] = True
                break
                
    # Re-sort cut points by timestamp
    cps.sort(key=lambda x: x["timestamp"])
    jobs_db[job_id]["cut_points"] = cps
    jobs_db[job_id]["detected_count"] = len(cps)
    
    return {"status": "success", "cut_points": [CutPoint(**cp) for cp in cps]}


@app.get("/api/download-zip/{job_id}")
async def download_zip(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found.")
    zip_path = jobs_db[job_id].get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not ready or not found.")
        
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"video_split_clips_{job_id}.zip"
    )


# Media static / streaming endpoints
@app.get("/api/media/video/{job_id}/{filename}")
async def stream_video(job_id: str, filename: str):
    job_dir = get_job_dir(job_id)
    video_path = os.path.join(job_dir, filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found.")
    return FileResponse(video_path, media_type="video/mp4")


@app.get("/api/media/ref/{job_id}/{filename}")
async def get_reference_image(job_id: str, filename: str):
    job_dir = get_job_dir(job_id)
    ref_path = os.path.join(job_dir, "references", filename)
    if not os.path.exists(ref_path):
        raise HTTPException(status_code=404, detail="Reference image not found.")
    return FileResponse(ref_path)


@app.get("/api/media/download-clip")
async def get_clip_media(filename: str = Query(...), job_id: Optional[str] = Query(None)):
    # Look across jobs or target job
    if job_id and job_id in jobs_db:
        path = os.path.join(get_job_dir(job_id), "output", filename)
        if os.path.exists(path):
            media_type = "image/jpeg" if filename.endswith(".jpg") else "video/mp4"
            return FileResponse(path, media_type=media_type)
            
    # Search all jobs
    for jid in jobs_db.keys():
        path = os.path.join(get_job_dir(jid), "output", filename)
        if os.path.exists(path):
            media_type = "image/jpeg" if filename.endswith(".jpg") else "video/mp4"
            return FileResponse(path, media_type=media_type)
            
    raise HTTPException(status_code=404, detail="Clip not found.")


@app.post("/api/create-sample-demo")
async def create_sample_demo():
    """
    Utility endpoint: Generates a 25-second synthetic demo video with two distinct
    transition splash screens ("FAST 100" at 00:08 and "SPEED NEWS" at 00:16)
    along with the corresponding reference screenshot images, automatically initializing a ready-to-test job.
    """
    job_id = init_job()
    job_dir = get_job_dir(job_id)
    
    # Create sample reference templates
    # Template 1: FAST 100 style
    t1 = np.ones((240, 420, 3), dtype=np.uint8) * 230
    cv2.rectangle(t1, (20, 20), (400, 220), (30, 30, 200), -1)
    cv2.putText(t1, "FAST 100", (60, 130), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 4)
    cv2.putText(t1, "BREAKING NEWS", (90, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 100), 2)
    
    # Template 2: SPEED NEWS style
    t2 = np.ones((240, 420, 3), dtype=np.uint8) * 40
    cv2.rectangle(t2, (20, 20), (400, 220), (0, 140, 255), -1)
    cv2.putText(t2, "SPEED NEWS", (45, 130), cv2.FONT_HERSHEY_DUPLEX, 1.8, (255, 255, 255), 4)
    cv2.putText(t2, "SPECIAL BULLETIN", (80, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    
    ref1_path = os.path.join(job_dir, "references", "ref_fast100.png")
    ref2_path = os.path.join(job_dir, "references", "ref_speednews.png")
    cv2.imwrite(ref1_path, t1)
    cv2.imwrite(ref2_path, t2)
    
    # Generate 25-second synthetic MP4 video
    video_path = os.path.join(job_dir, "original_video.mp4")
    width, height, fps = 640, 360, 25
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    total_frames = 25 * fps # 25 seconds
    # Transition 1 at second 8 (frame 200 - 225)
    # Transition 2 at second 16 (frame 400 - 425)
    
    for f in range(total_frames):
        sec = f / fps
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        if 8.0 <= sec < 9.0:
            # Render Fast 100 transition
            resized_t1 = cv2.resize(t1, (width, height))
            frame = resized_t1
        elif 16.0 <= sec < 17.0:
            # Render Speed News transition
            resized_t2 = cv2.resize(t2, (width, height))
            frame = resized_t2
        else:
            # Normal news story background with moving countdown / text
            bg_color = (int(sec * 10) % 255, 80, 120)
            frame[:] = bg_color
            cv2.putText(frame, f"NEWS SEGMENT at {sec:.1f}s", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            cv2.putText(frame, "Automatic Video Cut Point Detector Demo", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)
            
        out.write(frame)
    out.release()
    
    meta = VideoMetadata(
        filename="demo_sample_news.mp4",
        filesize_mb=round(os.path.getsize(video_path) / (1024 * 1024), 2),
        duration=25.0,
        formatted_duration=format_timestamp(25.0),
        width=width,
        height=height,
        fps=float(fps),
        total_frames=total_frames
    )
    
    refs = [
        {
            "id": "demo_ref_1",
            "name": "FAST 100 Transition",
            "filename": "ref_fast100.png",
            "path": ref1_path,
            "preview_url": f"/api/media/ref/{job_id}/ref_fast100.png",
            "status": "Ready"
        },
        {
            "id": "demo_ref_2",
            "name": "SPEED NEWS Transition",
            "filename": "ref_speednews.png",
            "path": ref2_path,
            "preview_url": f"/api/media/ref/{job_id}/ref_speednews.png",
            "status": "Ready"
        }
    ]
    
    jobs_db[job_id]["video_path"] = video_path
    jobs_db[job_id]["video_metadata"] = meta.model_dump()
    jobs_db[job_id]["total_duration"] = 25.0
    jobs_db[job_id]["references"] = refs
    jobs_db[job_id]["stage"] = "ready"
    jobs_db[job_id]["stage_text"] = "Sample Demo Loaded"
    
    return {
        "job_id": job_id,
        "metadata": meta,
        "references": [ReferenceInfo(**r) for r in refs],
        "video_stream_url": f"/api/media/video/{job_id}/original_video.mp4"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
