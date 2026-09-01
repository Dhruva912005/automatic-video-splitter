import os
import subprocess
import shutil
import uuid
import cv2
from typing import List, Optional, Callable
try:
    from models import GeneratedClip, CutPoint, DetectionSettings
    from detector import format_timestamp
except ImportError:
    from backend.models import GeneratedClip, CutPoint, DetectionSettings
    from backend.detector import format_timestamp

class VideoSplitter:
    def __init__(self, video_path: str, output_dir: str, duration: float, settings: DetectionSettings):
        self.video_path = video_path
        self.output_dir = output_dir
        self.duration = duration
        self.settings = settings
        os.makedirs(self.output_dir, exist_ok=True)

    def split_by_cut_points(self, cut_points: List[CutPoint], progress_callback: Optional[Callable[[int, str], None]] = None) -> List[GeneratedClip]:
        """
        Split original video into segments bounded by cut points.
        Builds [0, cut1, cut2, ..., duration], skips clips < min_clip_duration.
        """
        # Collect and sort unique timestamps
        raw_times = [0.0]
        for cp in cut_points:
            t = float(cp.timestamp)
            if 0 < t < self.duration:
                raw_times.append(t)
        raw_times.append(self.duration)
        
        # Deduplicate and sort
        sorted_times = sorted(list(set(round(t, 2) for t in raw_times)))

        clips: List[GeneratedClip] = []
        clip_number = 1
        total_segments = len(sorted_times) - 1

        for i in range(total_segments):
            start = sorted_times[i]
            end = sorted_times[i + 1]
            length = round(end - start, 2)

            if length < self.settings.min_clip_duration:
                continue

            clip_filename = f"clip_{clip_number:03d}.mp4"
            clip_path = os.path.join(self.output_dir, clip_filename)
            thumb_filename = f"thumb_{clip_number:03d}.jpg"
            thumb_path = os.path.join(self.output_dir, thumb_filename)

            if progress_callback:
                percent = int((i / max(1, total_segments)) * 100)
                progress_callback(percent, f"Cutting Clip {clip_number:03d} ({format_timestamp(start)} -> {format_timestamp(end)})...")

            # Cut using ffmpeg
            if self.settings.cut_mode == "accurate":
                # Re-encode for frame-accurate cut
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-i", self.video_path,
                    "-t", str(length),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-c:a", "aac",
                    "-avoid_negative_ts", "make_zero",
                    clip_path
                ]
            else:
                # Fast stream copy mode
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-i", self.video_path,
                    "-t", str(length),
                    "-map", "0",
                    "-c", "copy",
                    "-avoid_negative_ts", "make_zero",
                    clip_path
                ]

            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            # If fast mode failed (some containers fail with stream copy), fall back to re-encode
            if not os.path.exists(clip_path) or os.path.getsize(clip_path) == 0:
                fallback_cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-i", self.video_path,
                    "-t", str(length),
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-c:a", "aac",
                    "-avoid_negative_ts", "make_zero",
                    clip_path
                ]
                subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Generate thumbnail for clip
            self._generate_thumbnail(clip_path, thumb_path)

            file_size_mb = round(os.path.getsize(clip_path) / (1024 * 1024), 2) if os.path.exists(clip_path) else 0.0

            clips.append(GeneratedClip(
                clip_id=str(uuid.uuid4())[:8],
                clip_number=clip_number,
                filename=clip_filename,
                start_time=start,
                end_time=end,
                formatted_start=format_timestamp(start),
                formatted_end=format_timestamp(end),
                duration=length,
                file_size_mb=file_size_mb,
                video_url=f"/api/media/download-clip?filename={clip_filename}",
                thumbnail_url=f"/api/media/download-clip?filename={thumb_filename}" if os.path.exists(thumb_path) else None
            ))

            clip_number += 1

        return clips

    def _generate_thumbnail(self, video_path: str, thumb_path: str):
        """Extract a middle frame from the clip as thumbnail"""
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                mid_frame = max(0, total_frames // 4)
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Resize thumbnail to max height 240
                    h, w = frame.shape[:2]
                    target_h = 240
                    target_w = int(w * (target_h / h))
                    resized = cv2.resize(frame, (target_w, target_h))
                    cv2.imwrite(thumb_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
                cap.release()
        except Exception:
            pass

    def create_zip(self, zip_base_path: str) -> str:
        """Create a zip archive containing all generated clips in output_dir"""
        zip_path = shutil.make_archive(zip_base_path, "zip", self.output_dir)
        return zip_path
