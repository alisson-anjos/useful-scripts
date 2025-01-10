#!/usr/bin/env python3

import os
import argparse
import subprocess

def convert_videos_to_24fps(input_dir):
    """
    Converts the frame rate of each video file in 'input_dir' to 24 fps.
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
            output_filename = f"{name_without_ext}_24fps{ext}"
            output_path = os.path.join(input_dir, output_filename)

            # Run ffmpeg command to convert FPS to 24
            command = [
                "ffmpeg",
                "-y",             # Overwrite output without asking
                "-i", file_path,  # Input file
                "-r", "24",       # Output frame rate
                output_path
            ]

            print(f"Converting '{filename}' to 24 fps...")
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Finished: {output_path}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Convert the frame rate of all videos in a directory to 24 fps."
    )
    parser.add_argument(
        "-i", "--input-dir",
        required=True,
        help="Path to the directory containing the videos to convert."
    )

    args = parser.parse_args()

    convert_videos_to_24fps(args.input_dir)

if __name__ == "__main__":
    main()
