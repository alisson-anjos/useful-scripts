import os
import argparse
import shutil
import random
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def detect_faces_yolo(model_path, video_path, frame_sample_rate=5):
    model = YOLO(model_path)
    cap = cv2.VideoCapture(str(video_path))
    frame_scores = []
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_sample_rate == 0:
            results = model.predict(source=frame, conf=0.3, verbose=False)
            boxes = results[0].boxes
            if boxes is not None and boxes.xyxy.shape[0] > 0:
                confidences = boxes.conf.cpu().numpy()
                areas = (boxes.xyxy[:, 2] - boxes.xyxy[:, 0]) * (boxes.xyxy[:, 3] - boxes.xyxy[:, 1])
                relative_areas = (areas / (width * height)).cpu().numpy()
                frame_scores.append(np.mean(confidences * relative_areas))
        frame_idx += 1

    cap.release()
    if frame_scores:
        return np.mean(frame_scores)
    return 0.0

def get_video_metadata(path):
    cap = cv2.VideoCapture(str(path))
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    resolution = width * height
    return int(resolution), int(frames), int(fps)

def get_bitrate(video_path):
    try:
        import subprocess
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ], capture_output=True, text=True)
        return int(result.stdout.strip()) // 1000 if result.returncode == 0 else 0  # Convert to kbps
    except:
        return 0

def process_videos(input_folder, output_folder, model_path, top_n, max_videos, num_threads, min_bitrate, min_resolution, min_frames):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    video_files = [f for f in input_path.iterdir() if f.suffix.lower() in ['.mp4', '.mov', '.avi']]
    random.shuffle(video_files)
    if max_videos:
        video_files = video_files[:max_videos]

    filtered_files = []
    for video in video_files:
        bitrate = get_bitrate(video)
        resolution, frames, fps = get_video_metadata(video)
        if bitrate >= min_bitrate and resolution >= min_resolution and frames >= min_frames:
            filtered_files.append(video)

    video_scores = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(detect_faces_yolo, model_path, video): video for video in filtered_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Analyzing videos"):
            video = futures[future]
            try:
                score = future.result()
                video_scores.append((video, score))
            except Exception as e:
                print(f"[ERROR] Failed to process {video.name}: {e}")

    video_scores.sort(key=lambda x: x[1], reverse=True)
    top_videos = video_scores[:top_n]

    for video, score in top_videos:
        shutil.copy(video, output_path / video.name)
        print(f"[SELECTED] {video.name} -> score={score:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select top-N videos with best face quality using YOLO")
    parser.add_argument("--input", required=True, help="Input folder with videos")
    parser.add_argument("--output", required=True, help="Output folder for selected videos")
    parser.add_argument("--model", required=True, help="Path to YOLO face detection model")
    parser.add_argument("--top", type=int, default=100, help="Number of top videos to keep")
    parser.add_argument("--max_videos", type=int, default=None, help="Maximum number of videos to analyze")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads to use")
    parser.add_argument("--min_bitrate", type=int, default=500, help="Minimum bitrate (in kbps)")
    parser.add_argument("--min_resolution", type=int, default=640*360, help="Minimum resolution (width * height)")
    parser.add_argument("--min_frames", type=int, default=50, help="Minimum frame count")
    args = parser.parse_args()

    process_videos(
        args.input, args.output, args.model,
        args.top, args.max_videos, args.threads,
        args.min_bitrate, args.min_resolution, args.min_frames
    )
