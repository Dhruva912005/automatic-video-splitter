import os
import cv2
import numpy as np
import uuid
from typing import List, Dict, Any, Callable, Optional
try:
    from models import DetectionSettings, CutPoint, ReferenceInfo
except ImportError:
    from backend.models import DetectionSettings, CutPoint, ReferenceInfo

def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS.ms (or HH:MM:SS.ms if >= 1 hour)"""
    if seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:05.2f}"
    return f"{mins:02d}:{secs:05.2f}"

class VideoDetector:
    def __init__(self, video_path: str, reference_images: List[Dict[str, Any]], settings: DetectionSettings):
        self.video_path = video_path
        self.reference_images = reference_images # list of {'id', 'name', 'path'}
        self.settings = settings
        self.scales = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10] if settings.multi_scale else [1.00]

    def _prepare_templates(self) -> List[Dict[str, Any]]:
        """Load and preprocess reference screenshots into grayscale blurred templates"""
        prepared = []
        for ref in self.reference_images:
            path = ref["path"]
            if not os.path.exists(path):
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            prepared.append({
                "id": ref["id"],
                "name": ref["name"],
                "gray": blurred,
                "height": blurred.shape[0],
                "width": blurred.shape[1]
            })
        return prepared

    def scan_video(self, progress_callback: Optional[Callable[[int, float, float, int, str], None]] = None) -> List[CutPoint]:
        """
        Scan the video sequentially according to check_interval, matching frames against
        all reference templates at multiple scales.
        """
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        templates = self._prepare_templates()
        if not templates:
            raise ValueError("No valid reference templates available for detection.")

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video file: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 25.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if total_frames > 0 else 0

        frame_step = max(1, int(round(fps * self.settings.check_interval)))
        
        # Raw detections: list of dicts {timestamp, score, ref_name}
        raw_detections = []
        
        frame_no = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_no % frame_step == 0:
                current_time = frame_no / fps
                
                # Report progress
                percent = min(99, int((current_time / duration * 100))) if duration > 0 else 0
                if progress_callback:
                    progress_callback(percent, current_time, duration, len(raw_detections), "Scanning video frames...")

                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_gray = cv2.GaussianBlur(frame_gray, (3, 3), 0)
                frame_h, frame_w = frame_gray.shape[:2]

                best_frame_score = 0.0
                best_ref_name = ""

                for tmpl in templates:
                    tmpl_gray = tmpl["gray"]
                    tmpl_h, tmpl_w = tmpl["height"], tmpl["width"]

                    for scale in self.scales:
                        tw = int(tmpl_w * scale)
                        th = int(tmpl_h * scale)

                        # Template must not exceed frame dimensions
                        if tw > frame_w or th > frame_h or tw <= 10 or th <= 10:
                            continue

                        resized_tmpl = cv2.resize(tmpl_gray, (tw, th))
                        res = cv2.matchTemplate(frame_gray, resized_tmpl, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                        if max_val > best_frame_score:
                            best_frame_score = float(max_val)
                            best_ref_name = tmpl["name"]

                if best_frame_score >= self.settings.threshold:
                    raw_detections.append({
                        "timestamp": round(current_time, 2),
                        "score": round(best_frame_score, 4),
                        "ref_name": best_ref_name
                    })

            frame_no += 1

        cap.release()

        # Step 7 & 8: Remove duplicate / close detections with Non-Maximum Suppression within min_gap
        filtered_points = self._cluster_and_suppress(raw_detections, self.settings.min_gap)

        # Ignore detections too close to the very start if requested
        if self.settings.ignore_initial_seconds > 0:
            filtered_points = [p for p in filtered_points if p["timestamp"] >= self.settings.ignore_initial_seconds]

        # Convert to CutPoint models
        cut_points = []
        for p in filtered_points:
            cut_points.append(CutPoint(
                id=str(uuid.uuid4())[:8],
                timestamp=p["timestamp"],
                formatted_time=format_timestamp(p["timestamp"]),
                reference_name=p["ref_name"],
                match_score=p["score"],
                is_manual=False
            ))

        return cut_points

    def _cluster_and_suppress(self, detections: List[Dict[str, Any]], min_gap: float) -> List[Dict[str, Any]]:
        """
        Group detections that occur within `min_gap` of each other and keep the detection
        with the highest matching score in each cluster.
        """
        if not detections:
            return []

        # Sort by timestamp
        sorted_dets = sorted(detections, key=lambda x: x["timestamp"])
        
        clusters = []
        current_cluster = [sorted_dets[0]]

        for det in sorted_dets[1:]:
            prev_det = current_cluster[-1]
            if det["timestamp"] - prev_det["timestamp"] <= min_gap:
                current_cluster.append(det)
            else:
                clusters.append(current_cluster)
                current_cluster = [det]
        if current_cluster:
            clusters.append(current_cluster)

        # Select the best in each cluster
        best_points = []
        for cluster in clusters:
            best_det = max(cluster, key=lambda x: x["score"])
            best_points.append(best_det)

        return best_points
