import os
import sys
import argparse
from pathlib import Path
import imageio.v3 as iio
from tqdm import tqdm  # Optional: For progress bar

# Define common video file extensions
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg',
    '.webm', '.vob', '.ogv', '.3gp', '.3g2', '.m4v', '.ts', '.mts', '.m2ts'
}

def is_video_file(filename: str) -> bool:
    """
    Check if the filename has a video extension.
    """
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS

def count_frames(video_path: str, framerate: float = None) -> int:
    """
    Count the total number of frames in the video by iterating through each frame.

    Args:
        video_path (str): Path to the video file.
        framerate (float, optional): Frames per second. If None, imageio will use the video's framerate.

    Returns:
        int: Total number of frames. Returns -1 if an error occurs.
    """
    try:
        # Initialize frame counter
        frame_count = 0

        # Initialize the iterator with optional framerate
        if framerate:
            frame_iterator = iio.imiter(video_path, fps=framerate)
        else:
            frame_iterator = iio.imiter(video_path)

        # Iterate through each frame
        for _ in tqdm(frame_iterator, desc=f"Counting frames in '{Path(video_path).name}'", unit="frame"):
            frame_count += 1

        return frame_count

    except Exception as e:
        print(f"Error processing '{Path(video_path).name}': {e}")
        return -1

def process_videos_in_directory(directory: str, framerate: float = None):
    """
    Traverse the specified directory, count frames for each video file, and print the results.

    Args:
        directory (str): Path to the directory containing video files.
        framerate (float, optional): Frames per second to use with imageio.v3.imiter.
    """
    if not os.path.isdir(directory):
        print(f"Error: The provided path '{directory}' is not a directory or does not exist.")
        sys.exit(1)

    # List all files in the directory
    try:
        all_files = os.listdir(directory)
    except Exception as e:
        print(f"Error accessing directory '{directory}': {e}")
        sys.exit(1)

    # Filter video files based on extensions
    video_files = [f for f in all_files if is_video_file(f)]

    if not video_files:
        print(f"No video files found in directory '{directory}'.")
        sys.exit(0)

    print(f"Found {len(video_files)} video file(s) in '{directory}':\n")

    # Iterate through each video file and count frames
    for video in video_files:
        video_path = os.path.join(directory, video)
        print(f"Processing '{video}'...")
        total_frames = count_frames(video_path, framerate)
        if total_frames != -1:
            print(f"Total frames: {total_frames}\n")
        else:
            print("Could not determine the number of frames.\n")

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Iteratively count total frames in video files within a directory using imageio.v3.imiter."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Path to the directory containing video files."
    )
    parser.add_argument(
        "--framerate",
        type=float,
        default=None,
        help="Optional. Specify frames per second for imageio.v3.imiter."
    )

    args = parser.parse_args()

    # Process videos in the specified directory
    process_videos_in_directory(args.directory, args.framerate)

if __name__ == "__main__":
    main()
