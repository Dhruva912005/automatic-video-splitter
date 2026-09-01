# Automatic Video Cut Point Detector & Splitter

A full-stack web application powered by **FastAPI**, **OpenCV**, and **React (Vite)** that automatically detects visual transition screens in multi-segment videos and splits them into individual clips using **FFmpeg**.

## ✨ Features
- **Drag-and-Drop Video Upload**: MP4, MOV, MKV, AVI supported with duration, FPS, and resolution detection.
- **Reference Cut Screens**: Dynamic multi-template image matching.
- **Custom Frame Capture Scrubber**: Grab exact transition reference frames directly from video.
- **Multi-Scale OpenCV Matching**: Uses `cv2.matchTemplate(..., cv2.TM_CCOEFF_NORMED)` with Gaussian blur and scale variations.
- **Non-Maximum Suppression (NMS)**: Deduplicates close detection timestamps within a configurable minimum gap.
- **Visual Cut Point Timeline & Editable Table**: Interactive preview jump, inline timestamp editing, and manual additions.
- **FFmpeg Cutting**: Fast Stream Copy mode (`-c copy`) & Frame-Accurate re-encode mode.
- **ZIP Packaging**: 1-click download of all split clips.

## 🚀 Quickstart

### Prerequisites
- Python 3.9+
- Node.js 18+
- FFmpeg installed in system PATH

### Installation & Run
1. Install backend requirements:
```bash
pip install fastapi uvicorn opencv-python numpy python-multipart pydantic
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

3. Launch application:
```bash
python run_app.py
```
Open **`http://localhost:5173`** in your browser.
