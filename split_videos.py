import os
import subprocess
from pathlib import Path
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import math
import tempfile
import shutil


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


def get_frame_count(video_path):
    command = [
        "ffprobe", "-v", "0", "-count_frames",
        "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        frame_count_str = result.stdout.decode().strip()
        if frame_count_str.isdigit():
            return int(frame_count_str)
        else:
            fps = get_fps(video_path)
            if fps == 0:
                return 0
            duration = get_duration(video_path)
            return math.floor(fps * duration)
    except Exception as e:
        print(f"Error retrieving frame count for {video_path.name}: {e}", file=sys.stderr)
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


def cut_and_adjust_fps(video_path, target_fps, frames_needed):
    duration_needed = frames_needed / target_fps
    temp_dir = tempfile.mkdtemp()
    output_temp_path = Path(temp_dir) / f"{video_path.stem}_cutfps{target_fps}.mp4"

    command = [
        "ffmpeg", "-ss", "0", "-t", f"{duration_needed:.3f}",
        "-i", str(video_path),
        "-r", str(target_fps),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy", "-y",
        str(output_temp_path)
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_temp_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to cut and adjust FPS for {video_path.name}: {e.stderr.decode()}", file=sys.stderr)
        return video_path


def split_video_exact_frames(video_path, output_dir, frames_per_segment, max_segments=None,
                             preserve_name_if_single_segment=False, original_name=None):
    fps = get_fps(video_path)
    if fps == 0:
        print(f"Could not determine FPS for {video_path.name}. Skipping.", file=sys.stderr)
        return

    total_frames = get_frame_count(video_path)
    if total_frames == 0:
        print(f"Could not determine frame count for {video_path.name}. Skipping.", file=sys.stderr)
        return

    total_segments = total_frames // frames_per_segment
    if max_segments is not None:
        total_segments = min(total_segments, max_segments)

    video_name = video_path.stem

    if total_segments == 0:
        print(f"{video_path.name} has fewer frames ({total_frames}) than {frames_per_segment}. Skipping.", file=sys.stderr)
        return

    print(f"Splitting {video_path.name} into {total_segments} segment(s) of {frames_per_segment} frames each...")

    for segment in range(total_segments):
        start_frame = segment * frames_per_segment
        start_time = start_frame / fps
        duration = frames_per_segment / fps

        if preserve_name_if_single_segment and total_segments == 1 and original_name:
            output_filename = output_dir / original_name
        else:
            output_filename = output_dir / f"{video_name}_segment_{segment + 1:03d}.mp4"

        command = [
            "ffmpeg", "-i", str(video_path),
            "-ss", f"{start_time:.3f}", "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-crf", "22", "-c:a", "copy",
            "-avoid_negative_ts", "1", "-preset", "fast", "-y",
            str(output_filename)
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"  Saved: {output_filename.name}")
        except subprocess.CalledProcessError as e:
            print(f"  Error segment {segment + 1}: {e.stderr.decode()}", file=sys.stderr)

    print(f"Done: {video_path.name}\n")


def process_video(video_file, output_path, frames_per_segment, target_fps, max_segments, preserve_name):
    temp_path = None
    try:
        if target_fps:
            temp_path = cut_and_adjust_fps(video_file, target_fps, frames_per_segment)
            split_video_exact_frames(
                temp_path,
                output_path,
                frames_per_segment,
                max_segments,
                preserve_name_if_single_segment=preserve_name,
                original_name=video_file.name
            )
        else:
            split_video_exact_frames(
                video_file,
                output_path,
                frames_per_segment,
                max_segments,
                preserve_name_if_single_segment=preserve_name,
                original_name=video_file.name
            )
    finally:
        if temp_path and temp_path != video_file:
            shutil.rmtree(temp_path.parent, ignore_errors=True)


def main(input_folder, output_folder, frames_per_segment, max_workers, target_fps, max_segments, preserve_name):
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

    print(f"Found {len(video_files)} video(s) to process.")
    max_workers = min(max_workers or multiprocessing.cpu_count(), multiprocessing.cpu_count())
    print(f"Using {max_workers} worker(s)...\n")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_video,
                video_file,
                output_path,
                frames_per_segment,
                target_fps,
                max_segments,
                preserve_name
            ): video_file
            for video_file in video_files
        }
        for future in as_completed(futures):
            video_file = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Error processing {video_file.name}: {exc}", file=sys.stderr)

    print("✅ All videos processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split videos into fixed-frame segments, with optional FPS adjustment.")
    parser.add_argument("-input_folder", type=str, required=True, help="Folder with input videos.")
    parser.add_argument("-output_folder", type=str, required=True, help="Folder to save the segments.")
    parser.add_argument("-frames_per_segment", type=int, required=True, help="Exact number of frames per segment.")
    parser.add_argument("-target_fps", type=int, default=None, help="(Optional) Convert videos to this FPS before splitting.")
    parser.add_argument("-max_segments", type=int, default=None, help="Maximum number of segments per video.")
    parser.add_argument("-w", "--workers", type=int, default=None, help="Number of processes (default = CPU count).")
    parser.add_argument("--preserve_name", action="store_true", help="If set, saves with original filename when only one segment is created.")

    args = parser.parse_args()

    if args.frames_per_segment <= 0:
        print("frames_per_segment must be > 0", file=sys.stderr)
        sys.exit(1)

    main(
        args.input_folder,
        args.output_folder,
        args.frames_per_segment,
        args.workers,
        args.target_fps,
        args.max_segments,
        args.preserve_name
    )
