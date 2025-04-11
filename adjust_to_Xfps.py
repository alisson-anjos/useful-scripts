#!/usr/bin/env python3

import os
import argparse
import subprocess

def convert_videos_to_x_fps(input_dir, fps):
    """
    Converts the frame rate of each video file in 'input_dir' to X fps.
    Requires FFmpeg to be installed.
    """
    # Define valid video file extensions
    video_extensions = (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".mpeg")

    # Check if the directory exists
    if not os.path.isdir(input_dir):
        print(f"The directory '{input_dir}' does not exist.")
        return

    # Iterate over files in the directory
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)

        # Check if it's a valid video
        if os.path.isfile(file_path) and filename.lower().endswith(video_extensions):
            # Remove the extension from the filename
            name_without_ext, ext = os.path.splitext(filename)

            # Construct output file name (e.g. "video_24fps.mp4")
            # If you prefer to overwrite the original, you can keep the same name (but watch out for data loss).
            output_filename = f"{name_without_ext}_{fps}fps{ext}"
            output_path = os.path.join(input_dir, output_filename)

            # Run ffmpeg command to convert FPS to X
            command = [
                "ffmpeg",
                "-y",             # Overwrite output without asking
                "-i", file_path,  # Input file
                "-r", f"{fps}",       # Output frame rate
                output_path
            ]

            print(f"Converting '{filename}' to {fps} fps...")
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Finished: {output_path}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Convert the frame rate of all videos in a directory to X fps."
    )
	
    parser.add_argument(
        "-i", "--input-dir",
        required=True,
        help="Path to the directory containing the videos to convert."
    )

    parser.add_argument(
        "-fps", "--fps",
        required=True,
        help="FPS Target"
    )

    args = parser.parse_args()

    convert_videos_to_x_fps(args.input_dir, args.fps)

if __name__ == "__main__":
    main()
