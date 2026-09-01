from pydantic import BaseModel, Field
from typing import List, Optional

class DetectionSettings(BaseModel):
    threshold: float = Field(default=0.70, ge=0.40, le=0.99, description="Matching threshold (0.50 - 0.95)")
    check_interval: float = Field(default=0.25, ge=0.05, le=5.0, description="Check frame every N seconds")
    min_gap: float = Field(default=3.0, ge=0.5, le=30.0, description="Minimum gap between detections in seconds")
    multi_scale: bool = Field(default=True, description="Enable multi-scale template matching")
    ignore_initial_seconds: float = Field(default=3.0, description="Ignore detection if within first N seconds of video")
    cut_mode: str = Field(default="fast", description="'fast' (stream copy) or 'accurate' (re-encode)")
    min_clip_duration: float = Field(default=2.0, description="Minimum clip duration in seconds")

class CutPoint(BaseModel):
    id: str
    timestamp: float
    formatted_time: str
    reference_name: str
    match_score: float
    is_manual: bool = False

class ReferenceInfo(BaseModel):
    id: str
    name: str
    filename: str
    preview_url: str
    status: str = "Ready"

class VideoMetadata(BaseModel):
    filename: str
    filesize_mb: float
    duration: float
    formatted_duration: str
    width: int
    height: int
    fps: float
    total_frames: int

class GeneratedClip(BaseModel):
    clip_id: str
    clip_number: int
    filename: str
    start_time: float
    end_time: float
    formatted_start: str
    formatted_end: str
    duration: float
    file_size_mb: float
    video_url: str
    thumbnail_url: Optional[str] = None

class JobProgress(BaseModel):
    job_id: str
    stage: str # uploading, ready, scanning, cutting, complete, error
    stage_text: str
    percent: int
    current_time: float
    total_duration: float
    formatted_current_time: str
    formatted_total_duration: str
    detected_count: int
    error_message: Optional[str] = None

class JobResults(BaseModel):
    job_id: str
    video_metadata: Optional[VideoMetadata] = None
    references: List[ReferenceInfo] = []
    cut_points: List[CutPoint] = []
    clips: List[GeneratedClip] = []
    zip_url: Optional[str] = None
    settings: DetectionSettings = DetectionSettings()
    status: str = "ready"
