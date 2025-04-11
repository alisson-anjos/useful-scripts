import os
import argparse
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
from scenedetect import detect, ContentDetector

def get_video_resolution(video_path):
    """Gets the original resolution of the video."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        video_path
    ]
    output = subprocess.check_output(cmd).decode("utf-8").strip()
    width, height = map(int, output.split(","))
    return width, height

def calculate_scaled_resolution(original_width, original_height, target_size):
    """Calculates proportional resolution while maintaining aspect ratio."""
    if original_width >= original_height:
        new_width = target_size
        new_height = int((original_height / original_width) * new_width)
    else:
        new_height = target_size
        new_width = int((original_width / original_height) * new_height)

    if new_height % 2 != 0:
        new_height += 1  # Ensures height is even

    return new_width, new_height

def convert_fps(video_path, output_dir, target_fps, resize=None):
    """Adjusts the video's FPS and performs proportional downscale if needed."""
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(video_path)
    name, ext = os.path.splitext(base_name)
    output_path = os.path.join(output_dir, f"{name}_adjusted{ext}")

    if os.path.exists(output_path):
        print(f"🔄 Video already converted, skipping: {output_path}")
        return output_path

    scale_filter = ""
    if resize:
        original_width, original_height = get_video_resolution(video_path)
        new_width, new_height = calculate_scaled_resolution(original_width, original_height, int(resize))
        scale_filter = f",scale={new_width}:{new_height}"

    ffmpeg_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", video_path,
        "-filter:v", f"fps={target_fps}{scale_filter}",
        "-vsync", "vfr",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        output_path
    ]

    subprocess.run(ffmpeg_cmd, check=True)
    print(f"✅ FPS adjusted and saved: {output_path} (Resolution: {resize if resize else 'Original'})")
    return output_path

def detect_scenes(video_path, min_duration):
    """Detects scenes and filters out those shorter than `min_duration`."""
    scenes = detect(video_path, ContentDetector(), show_progress=True)

    print(f"🔍 Scenes detected in {video_path}: {len(scenes)}")

    if len(scenes) == 0:
        print(f"⚠️ No scenes detected, copying the entire video as a single scene.")
        return [(0, None)]  # Represents the entire video

    # Filter scenes with at least `min_duration` seconds
    filtered_scenes = [(start, end) for start, end in scenes if (end.get_seconds() - start.get_seconds()) >= min_duration]

    if len(filtered_scenes) == 0:
        print(f"⚠️ No scene longer than {min_duration}s, copying the entire video.")
        return [(0, None)]

    return filtered_scenes

def extract_scenes_ffmpeg(video_path, output_dir, scenes, target_fps=24, max_scenes=None):
    """Extracts detected scenes using FFmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    scene_count = 1

    for start, end in scenes:
        if max_scenes and scene_count > max_scenes:
            break

        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        output_name = f"{name}_scene_{scene_count:03d}{ext}"
        output_path = os.path.join(output_dir, output_name)

        if end is None:
            shutil.copy(video_path, output_path)
            print(f"📂 No scene detected or valid, copying full video to: {output_path}")
        else:
            ffmpeg_cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", video_path,
                "-ss", str(start.get_seconds()),
                "-to", str(end.get_seconds()),
                "-r", str(target_fps),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            print(f"🎬 Scene extracted: {output_path}")

        scene_count += 1

def process_videos_in_two_phases(input_dir, output_dir, target_fps, resize=None, threads=1, min_duration=0, max_scenes=None):
    """First converts all videos, then detects and extracts scenes."""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv')

    converted_videos_dir = os.path.join(output_dir, "converted")
    extracted_videos_dir = os.path.join(output_dir, "extracted")

    # 📌 **Phase 1: Adjust FPS and resolution**
    video_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(video_extensions):
                input_path = os.path.join(root, file)
                video_files.append(input_path)

    converted_videos = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(convert_fps, v, converted_videos_dir, target_fps, resize): v for v in video_files}

        for future in futures:
            try:
                converted_path = future.result()
                if converted_path:
                    converted_videos.append(converted_path)
            except Exception as e:
                print(f"❌ Error converting FPS for video {futures[future]}: {str(e)}")

    # 📌 **Phase 2: Detect and extract scenes**
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {}
        for v in converted_videos:
            extracted_scenes_dir = os.path.join(extracted_videos_dir, os.path.basename(v))
            if not os.path.exists(extracted_scenes_dir):
                futures[executor.submit(lambda v: extract_scenes_ffmpeg(v, extracted_videos_dir, detect_scenes(v, min_duration), target_fps, max_scenes), v)] = v

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"❌ Error processing {futures[future]}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Processing: FPS adjustment, resolution resize, scene detection and extraction using FFmpeg")

    parser.add_argument("input_dir", help="Directory containing the original videos")
    parser.add_argument("output_dir", help="Directory to save adjusted videos and extracted scenes")
    parser.add_argument("--fps", type=int, default=24, help="Desired FPS")
    parser.add_argument("--resize", type=int, help="Target resolution's longest side (e.g., 1024, 1920)")
    parser.add_argument("--duration", type=float, default=0, help="Minimum scene duration (seconds)")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads for parallel processing")
    parser.add_argument("--max-scenes", type=int, help="Maximum number of scenes to extract per video")

    args = parser.parse_args()

    process_videos_in_two_phases(
        args.input_dir,
        args.output_dir,
        args.fps,
        resize=args.resize,
        threads=args.threads,
        min_duration=args.duration,
        max_scenes=args.max_scenes
    )
