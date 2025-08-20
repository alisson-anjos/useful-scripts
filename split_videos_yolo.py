import os
import sys
import math
import argparse
import shutil
import tempfile
import subprocess
import multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv

import cv2
from ultralytics import YOLO

def get_fps(video_path):
    command = [
        "ffprobe", "-v", "0",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        r_frame_rate = result.stdout.decode().strip()
        num, denom = map(int, r_frame_rate.split('/'))
        return num / denom if denom != 0 else 0
    except Exception as e:
        print(f"Error retrieving FPS for {video_path.name}: {e}", file=sys.stderr)
        return 0

def get_duration(video_path):
    command = [
        "ffprobe", "-v", "0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return float(result.stdout.decode().strip())
    except Exception as e:
        print(f"Error retrieving duration for {video_path.name}: {e}", file=sys.stderr)
        return 0.0

def detect_face_keyframes(video_path, detection_fps=2, min_score=0.8):
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    model = YOLO("yolov8n.pt")

    keyframes = []
    frame_interval = int(fps // detection_fps)
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            results = model(frame, verbose=False)
            for result in results:
                if result.boxes is not None:
                    scores = result.boxes.conf
                    if scores is not None and len(scores) > 0:
                        score = float(scores[0].item())
                        timestamp = frame_idx / fps
                        if score >= min_score:
                            print(f"[FACE] {video_path.name} @ {timestamp:.2f}s with confidence {score*100:.1f}%")
                            keyframes.append(timestamp)

        frame_idx += 1

    cap.release()

    filtered_keyframes = []
    last_time = -999
    for t in sorted(keyframes):
        if t >= last_time + 5:
            filtered_keyframes.append(t)
            last_time = t

    return filtered_keyframes

def cut_segments_from_keyframes(video_path, output_folder, keyframes, segment_duration=5.0):
    video_name = Path(video_path).stem
    video_duration = get_duration(video_path)

    log_path = Path(output_folder) / "segment_log.csv"
    log_exists = log_path.exists()
    with open(log_path, mode="a", newline="", encoding="utf-8") as log_file:
        log_writer = csv.writer(log_file)
        if not log_exists:
            log_writer.writerow(["filename", "start_time", "duration", "bitrate_kbps", "size_kb"])

        for i, start_time in enumerate(keyframes):
            end_time = min(start_time + segment_duration, video_duration)
            duration = end_time - start_time
            output_file = Path(output_folder) / f"{video_name}_face_{i+1:03d}.mp4"

            command = [
                "ffmpeg", "-hide_banner", "-loglevel", "info",
                "-ss", f"{start_time:.3f}", "-t", f"{duration:.3f}",
                "-i", str(video_path),
                "-c:v", "libx264",
                "-crf", "0",
                "-preset", "veryslow",
                "-c:a", "copy",
                "-g", "1",
                "-y", str(output_file)
            ]

            print(f"[CUT] {video_path.name} -> {output_file.name} | start: {start_time:.2f}s duration: {duration:.2f}s")
            subprocess.run(command)
            size_kb = output_file.stat().st_size // 1024
            log_writer.writerow([output_file.name, f"{start_time:.2f}", f"{duration:.2f}", "CRF=0", size_kb])

def process_face_mode(video_file, output_path, segment_duration, min_score):
    keyframes = detect_face_keyframes(video_file, min_score=min_score)
    if not keyframes:
        print(f"[SKIP] No faces found in {video_file.name}.")
        return
    cut_segments_from_keyframes(video_file, output_path, keyframes, segment_duration)

def main(input_folder, output_folder, face_segment_duration, max_workers, min_score):
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    if not input_path.exists():
        print(f"Input folder '{input_folder}' does not exist.", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.wmv']
    video_files = [f for f in input_path.iterdir() if f.suffix.lower() in video_extensions]

    if not video_files:
        print(f"No supported video files found in '{input_folder}'.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Found {len(video_files)} video(s) to process.")
    max_workers = min(max_workers or multiprocessing.cpu_count(), multiprocessing.cpu_count())
    print(f"[INFO] Using {max_workers} worker(s)...\n")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_face_mode,
                video_file,
                output_path,
                face_segment_duration,
                min_score
            ): video_file for video_file in video_files
        }

        for future in as_completed(futures):
            video_file = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"[ERROR] {video_file.name}: {exc}", file=sys.stderr)

    print("\u2705 All videos processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split videos into segments using face-based keyframe detection.")
    parser.add_argument("-input_folder", type=str, required=True, help="Folder with input videos.")
    parser.add_argument("-output_folder", type=str, required=True, help="Folder to save the segments.")
    parser.add_argument("--face_segment_duration", type=float, default=5.0, help="Duration of each segment when using face_mode.")
    parser.add_argument("--min_score", type=float, default=0.8, help="Minimum confidence score for face detection (0-1 range).")
    parser.add_argument("-w", "--workers", type=int, default=None, help="Number of processes (default = CPU count).")
    args = parser.parse_args()

    main(
        args.input_folder,
        args.output_folder,
        args.face_segment_duration,
        args.workers,
        args.min_score
    )
