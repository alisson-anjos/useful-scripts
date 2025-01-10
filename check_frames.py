import subprocess
from pathlib import Path
import argparse

def get_video_info(video_path):
    """
    Retrieves the frame count and resolution of a video using ffprobe.

    :param video_path: Path to the video file.
    :return: Tuple containing frame count (int) and resolution (str in format 'widthxheight').
    """
    # Command to get frame count
    frame_command = [
        "ffprobe",
        "-v", "error",
        "-count_frames",
        "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames",
        "-of", "csv=p=0",
        str(video_path)
    ]

    # Command to get resolution
    resolution_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        str(video_path)
    ]

    try:
        # Get frame count
        frame_result = subprocess.run(frame_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        frame_count_str = frame_result.stdout.decode().strip()
        if frame_count_str.isdigit():
            frame_count = int(frame_count_str)
        else:
            # Fallback: Calculate frame count based on duration and FPS
            frame_count = calculate_frame_count(video_path)

        # Get resolution
        resolution_result = subprocess.run(resolution_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        resolution = resolution_result.stdout.decode().strip()
        if 'x' in resolution:
            width, height = resolution.split('x')
            resolution = f"{width}x{height}"
        else:
            resolution = "Unknown"

        return frame_count, resolution

    except subprocess.CalledProcessError as e:
        print(f"Error processing {video_path.name}: {e.stderr.decode().strip()}")
        return 0, "Unknown"

def calculate_frame_count(video_path):
    """
    Calculates frame count based on duration and FPS if exact frame count isn't available.

    :param video_path: Path to the video file.
    :return: Estimated frame count (int).
    """
    fps = get_fps(video_path)
    duration = get_duration(video_path)
    if fps > 0 and duration > 0:
        return int(fps * duration)
    else:
        return 0

def get_fps(video_path):
    """
    Retrieves the Frames Per Second (FPS) of a video using ffprobe.

    :param video_path: Path to the video file.
    :return: FPS as a float.
    """
    fps_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(fps_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        r_frame_rate = result.stdout.decode().strip()
        num, denom = map(int, r_frame_rate.split('/'))
        fps = num / denom if denom != 0 else 0
        return fps
    except Exception as e:
        print(f"Error obtaining FPS for {video_path.name}: {e}")
        return 0

def get_duration(video_path):
    """
    Retrieves the duration of a video in seconds using ffprobe.

    :param video_path: Path to the video file.
    :return: Duration in seconds as a float.
    """
    duration_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        result = subprocess.run(duration_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration_str = result.stdout.decode().strip()
        return float(duration_str)
    except Exception as e:
        print(f"Error obtaining duration for {video_path.name}: {e}")
        return 0.0

def main(folder_path):
    supported_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    input_path = Path(folder_path)
    if not input_path.exists():
        print(f"Folder '{folder_path}' does not exist.")
        return

    video_files = [f for f in input_path.iterdir() if f.suffix.lower() in supported_extensions]

    if not video_files:
        print(f"No supported video files found in '{folder_path}'.")
        return

    print(f"{'Video Name':<50} {'Frame Count':<15} {'Resolution':<10}")
    print("-" * 80)

    for video in video_files:
        frame_count, resolution = get_video_info(video)
        print(f"{video.name:<50} {frame_count:<15} {resolution:<10}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get frame count and resolution for all videos in a folder using ffprobe.")
    parser.add_argument("folder", type=str, help="Path to the folder containing videos.")
    args = parser.parse_args()
    main(args.folder)
