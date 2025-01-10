import os
import subprocess
from pathlib import Path
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import math

def get_fps(video_path):
    """
    Retrieves the Frames Per Second (FPS) of a video using ffprobe.

    :param video_path: Path to the video file.
    :return: FPS as a float.
    """
    command = [
        "ffprobe",
        "-v", "0",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        r_frame_rate = result.stdout.decode().strip()
        num, denom = map(int, r_frame_rate.split('/'))
        fps = num / denom if denom != 0 else 0
        return fps
    except Exception as e:
        print(f"Error retrieving FPS for {video_path.name}: {e}", file=sys.stderr)
        return 0

def get_frame_count(video_path):
    """
    Retrieves the total number of frames in a video using ffprobe.

    :param video_path: Path to the video file.
    :return: Total number of frames as an integer.
    """
    command = [
        "ffprobe",
        "-v", "0",
        "-count_frames",
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
            # Fallback: Calculate frame count based on duration and FPS
            fps = get_fps(video_path)
            if fps == 0:
                return 0
            duration = get_duration(video_path)
            return math.floor(fps * duration)
    except Exception as e:
        print(f"Error retrieving frame count for {video_path.name}: {e}", file=sys.stderr)
        return 0

def get_duration(video_path):
    """
    Retrieves the duration of a video in seconds using ffprobe.

    :param video_path: Path to the video file.
    :return: Duration in seconds as a float.
    """
    command = [
        "ffprobe",
        "-v", "0",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration_str = result.stdout.decode().strip()
        return float(duration_str)
    except Exception as e:
        print(f"Error retrieving duration for {video_path.name}: {e}", file=sys.stderr)
        return 0.0

def split_video_exact_frames(video_path, output_dir, frames_per_segment=30):
    """
    Splits a video into segments with an exact number of frames.

    :param video_path: Path to the input video file.
    :param output_dir: Directory where the segments will be saved.
    :param frames_per_segment: Number of frames per segment.
    """
    fps = get_fps(video_path)
    if fps == 0:
        print(f"Could not determine FPS for {video_path.name}. Skipping segmentation.", file=sys.stderr)
        return

    total_frames = get_frame_count(video_path)
    if total_frames == 0:
        print(f"Could not determine frame count for {video_path.name}. Skipping segmentation.", file=sys.stderr)
        return

    total_segments = total_frames // frames_per_segment  # Apenas segmentos completos
    video_name = video_path.stem

    if total_segments == 0:
        print(f"Video {video_path.name} has fewer frames ({total_frames}) than the specified frames per segment ({frames_per_segment}). Skipping.", file=sys.stderr)
        return

    print(f"Splitting {video_path.name} into {total_segments} segment(s) of {frames_per_segment} frames each...")

    for segment in range(total_segments):
        start_frame = segment * frames_per_segment
        start_time = start_frame / fps
        duration = frames_per_segment / fps

        # Nome do arquivo de saída inclui o nome do vídeo e o número do segmento
        output_filename = output_dir / f"{video_name}_segment_{segment + 1:03d}.mp4"

        command = [
            "ffmpeg",
            "-i", str(video_path),
            "-ss", f"{start_time:.3f}",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-crf", "22",
            "-c:a", "copy",
            "-avoid_negative_ts", "1",
            "-preset", "fast",  # Opcional: melhora a velocidade de codificação
            str(output_filename)
        ]

        print(f"  Segment {segment + 1}/{total_segments}: Start Time = {start_time:.3f}s, Duration = {duration:.3f}s")

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"    Saved: {output_filename}")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode().strip()
            print(f"    Error processing segment {segment + 1} of {video_path.name}: {error_message}", file=sys.stderr)

    # Informar se houveram frames ignorados
    remaining_frames = total_frames % frames_per_segment
    if remaining_frames > 0:
        print(f"  Note: {remaining_frames} frame(s) at the end of {video_path.name} were ignored as they do not complete a full segment.\n")
    else:
        print(f"Segments saved in: {output_dir}\n")

def process_video(video_file, output_path, frames_per_segment):
    """
    Initiates the splitting process for a single video.

    :param video_file: Path object of the video file to process.
    :param output_path: Path object of the main output directory.
    :param frames_per_segment: Number of frames per segment.
    """
    split_video_exact_frames(video_file, output_path, frames_per_segment)

def main(input_folder, output_folder, frames_per_segment, max_workers):
    """
    Iterates through all videos in the input folder, splits them using multiprocessing, and saves the segments.

    :param input_folder: Folder containing the input videos.
    :param output_folder: Folder where the segments will be saved.
    :param frames_per_segment: Number of frames per segment.
    :param max_workers: Maximum number of worker processes to use.
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    if not input_path.exists():
        print(f"Input folder '{input_folder}' does not exist.", file=sys.stderr)
        sys.exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    # Supported video file extensions
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

    # Gather all video files
    video_files = [video_file for video_file in input_path.iterdir() if video_file.suffix.lower() in video_extensions]

    if not video_files:
        print(f"No supported video files found in '{input_folder}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(video_files)} video(s) to process.")

    # Determine the number of workers
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    else:
        max_workers = min(max_workers, multiprocessing.cpu_count())

    print(f"Using {max_workers} worker(s) for processing.\n")

    # Use ProcessPoolExecutor for multiprocessing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all video processing tasks
        futures = {executor.submit(process_video, video_file, output_path, frames_per_segment): video_file for video_file in video_files}

        for future in as_completed(futures):
            video_file = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Generated an exception while processing {video_file.name}: {exc}", file=sys.stderr)

    print("All videos have been processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split videos into segments with an exact number of frames using FFmpeg with multiprocessing."
    )
    parser.add_argument(
        "input_folder",
        type=str,
        help="Path to the input folder containing videos."
    )
    parser.add_argument(
        "output_folder",
        type=str,
        help="Path to the output folder where segments will be saved."
    )
    parser.add_argument(
        "frames_per_segment",
        type=int,
        help="Number of frames per segment."
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=None,
        help="Maximum number of worker processes to use (default: number of CPU cores)."
    )

    args = parser.parse_args()

    if args.frames_per_segment <= 0:
        print("The number of frames per segment must be greater than zero.", file=sys.stderr)
        sys.exit(1)

    main(args.input_folder, args.output_folder, args.frames_per_segment, args.workers)
