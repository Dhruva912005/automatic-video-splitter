import os
import cv2
import numpy as np
import shutil
from backend.models import DetectionSettings, CutPoint
from backend.detector import VideoDetector
from backend.splitter import VideoSplitter

def test_full_pipeline():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_temp")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

    # 1. Create reference image 1
    ref1_path = os.path.join(test_dir, "ref1.png")
    t1 = np.ones((240, 320, 3), dtype=np.uint8) * 50
    cv2.rectangle(t1, (20, 20), (300, 220), (0, 0, 255), -1)
    cv2.putText(t1, "CUT 1", (70, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    cv2.imwrite(ref1_path, t1)

    # 2. Create reference image 2
    ref2_path = os.path.join(test_dir, "ref2.png")
    t2 = np.ones((240, 320, 3), dtype=np.uint8) * 50
    cv2.rectangle(t2, (20, 20), (300, 220), (255, 100, 0), -1)
    cv2.putText(t2, "CUT 2", (70, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    cv2.imwrite(ref2_path, t2)

    # 3. Create test video (15 seconds, 25 fps = 375 frames)
    # Transition 1 appears around second 5 (frame 125)
    # Transition 2 appears around second 10 (frame 250)
    video_path = os.path.join(test_dir, "test_video.mp4")
    fps = 25
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    for f in range(15 * fps):
        sec = f / fps
        if 5.0 <= sec < 6.0:
            frame = t1.copy()
        elif 10.0 <= sec < 11.0:
            frame = t2.copy()
        else:
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (int(sec * 15) % 255, 100, 100)
            cv2.putText(frame, f"Time: {sec:.1f}s", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        out.write(frame)
    out.release()
    print("[OK] Test video generated at:", video_path)

    # 4. Run VideoDetector
    settings = DetectionSettings(
        threshold=0.70,
        check_interval=0.25,
        min_gap=3.0,
        multi_scale=True,
        cut_mode="fast"
    )
    references = [
        {"id": "1", "name": "Transition 1", "path": ref1_path},
        {"id": "2", "name": "Transition 2", "path": ref2_path}
    ]

    detector = VideoDetector(video_path, references, settings)
    cut_points = detector.scan_video()
    print(f"[OK] Detection finished. Found {len(cut_points)} cut points:")
    for cp in cut_points:
        print(f"   -> Timestamp: {cp.formatted_time} ({cp.timestamp}s) | Score: {cp.match_score:.3f} | Ref: {cp.reference_name}")

    assert len(cut_points) == 2, f"Expected 2 cut points, got {len(cut_points)}"
    assert 4.5 <= cut_points[0].timestamp <= 5.5, f"Cut point 1 out of range: {cut_points[0].timestamp}"
    assert 9.5 <= cut_points[1].timestamp <= 10.5, f"Cut point 2 out of range: {cut_points[1].timestamp}"

    # 5. Run VideoSplitter
    output_dir = os.path.join(test_dir, "output")
    splitter = VideoSplitter(video_path, output_dir, 15.0, settings)
    clips = splitter.split_by_cut_points(cut_points)
    print(f"[OK] Video splitting finished. Created {len(clips)} clips:")
    for c in clips:
        print(f"   -> {c.filename}: {c.formatted_start} to {c.formatted_end} ({c.duration}s, {c.file_size_mb} MB)")

    assert len(clips) == 3, f"Expected 3 clips, got {len(clips)}"

    # 6. Test ZIP creation
    zip_base = os.path.join(test_dir, "test_clips")
    zip_path = splitter.create_zip(zip_base)
    print("[OK] ZIP archive created:", zip_path)
    assert os.path.exists(zip_path), "ZIP file does not exist"

    # Cleanup test_temp
    shutil.rmtree(test_dir)
    print("\nALL PIPELINE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_pipeline()
