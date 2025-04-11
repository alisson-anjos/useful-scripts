import os
import subprocess
import argparse

def get_video_info(video_path):
    """
    Retrieves the video's FPS and total number of frames using FFprobe.
    """
    try:
        # Get FPS (e.g., "30/1")
        cmd_fps = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        fps_output = subprocess.check_output(cmd_fps).decode().strip()
        num, den = fps_output.split('/')
        fps = float(num) / float(den) if float(den) != 0 else None

        # Get total number of frames
        cmd_frames = [
            "ffprobe", "-v", "error",
            "-count_frames",
            "-select_streams", "v:0",
            "-show_entries", "stream=nb_read_frames",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        total_frames_output = subprocess.check_output(cmd_frames).decode().strip()
        total_frames = int(total_frames_output)
        return fps, total_frames
    except Exception as e:
        print(f"Error obtaining video info for {video_path}: {e}")
        return None, None

def process_video(input_path, output_path, skip_frames, start_mode, custom_start):
    fps, total_frames = get_video_info(input_path)
    if fps is None or total_frames is None:
        print(f"Failed to obtain video info for {input_path}. Skipping.")
        return

    # Determine starting frame based on chosen mode
    if start_mode == "start":
        start_frame = skip_frames
    elif start_mode == "middle":
        start_frame = total_frames // 2
    elif start_mode == "custom":
        start_frame = custom_start
    else:
        start_frame = 0

    # Convert frame number to time in seconds based on FPS
    start_seconds = start_frame / fps

    print(f"Processing {os.path.basename(input_path)}:")
    print(f"  - FPS: {fps:.2f}, Total frames: {total_frames}")
    print(f"  - Starting at frame: {start_frame} ({start_seconds:.3f} sec)")

    # FFmpeg command to cut the video starting from the computed time
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start_seconds:.3f}",
        "-i", input_path,
        "-c", "copy",  # Copy codecs to retain the original format (fast operation)
        output_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Saved: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}: {e}")

def process_videos(input_folder, output_folder, skip_frames, start_mode, custom_start):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv')
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(video_extensions):
            continue

        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        process_video(input_path, output_path, skip_frames, start_mode, custom_start)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Skip the initial frames of each video and save the remainder using FFmpeg, retaining original parameters."
    )
    parser.add_argument("input_folder", help="Folder containing input videos")
    parser.add_argument("output_folder", help="Folder to save processed videos")
    parser.add_argument("--skip-frames", type=int, default=16,
                        help="Number of initial frames to skip (used in 'start' mode).")
    parser.add_argument("--start-mode", choices=["start", "middle", "custom"], default="start",
                        help="Start mode: 'start' (skip the first N frames), 'middle' (start from the middle), or 'custom' (use a specified frame).")
    parser.add_argument("--start-frame", type=int, default=0,
                        help="Frame index to start from (used only if --start-mode is 'custom').")

    args = parser.parse_args()
    process_videos(args.input_folder, args.output_folder, args.skip_frames, args.start_mode, args.start_frame)
