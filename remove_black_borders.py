import os
import subprocess
import argparse
from pathlib import Path

def detect_crop_filter(video_path):
    command = [
        "ffmpeg", "-i", str(video_path),
        "-t", "5",
        "-vf", "cropdetect=24:16:100",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lines = result.stdout.splitlines()
        crop_lines = [line for line in lines if "crop=" in line]
        if crop_lines:
            last_crop = crop_lines[-1]
            crop_filter = last_crop.split("crop=")[-1].strip()
            return crop_filter
    except Exception as e:
        print(f"[ERROR] Failed to detect crop filter for {video_path.name}: {e}")
    return None

def apply_crop(input_path, output_path, crop_filter):
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=height",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_path)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        original_height = int(probe.stdout.strip())
        _, crop_h, crop_y = int(crop_filter.split(":")[1]), int(crop_filter.split(":")[1]), int(crop_filter.split(":")[3])

        top_border = crop_y
        bottom_border = original_height - crop_h - crop_y
        max_border = max(top_border, bottom_border)

        crop_y_new = max_border
        crop_h_new = original_height - max_border * 2
        crop_filter = f"{crop_filter.split(":")[0]}:{crop_h_new}:{crop_filter.split(":")[2]}:{crop_y_new}"
        print(f"[ADJUSTED] Top={top_border}, Bottom={bottom_border}, Final crop={crop_filter}")

    except Exception as e:
        print(f"[WARNING] Border balance crop failed for {input_path.name}: {e}")

    command = [
        "ffmpeg", "-i", str(input_path),
        "-vf", f"crop={crop_filter}",
        "-c:v", "libx264",
        "-crf", "0",
        "-preset", "veryslow",
        "-c:a", "copy",
        "-y", str(output_path)
    ]
    subprocess.run(command)

def process_all_videos(input_folder, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    video_exts = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm"]

    for video_file in input_path.iterdir():
        if video_file.suffix.lower() not in video_exts:
            continue

        crop_filter = detect_crop_filter(video_file)
        if not crop_filter:
            print(f"[SKIP] Could not determine crop for {video_file.name}")
            continue

        output_file = output_path / video_file.name
        print(f"[CROP] {video_file.name} -> crop={crop_filter}")
        apply_crop(video_file, output_file, crop_filter)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove black borders from videos using ffmpeg cropdetect")
    parser.add_argument("-input", required=True, help="Input folder with videos")
    parser.add_argument("-output", required=True, help="Output folder for cropped videos")
    args = parser.parse_args()
    process_all_videos(args.input, args.output)
