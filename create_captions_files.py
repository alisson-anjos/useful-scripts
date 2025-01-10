#!/usr/bin/env python3

import os
import argparse

def create_txt_files(directory, content):
    """
    Creates a .txt file (with the same name) for each video file in the specified directory
    and writes the given content inside.
    """

    # Define valid video file extensions
    video_extensions = (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".mpeg")

    # Check if the directory exists
    if not os.path.isdir(directory):
        print(f"The directory '{directory}' does not exist.")
        return

    # Iterate over each file in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Check if it's a file and has a valid video extension
        if os.path.isfile(file_path) and filename.lower().endswith(video_extensions):
            # Remove the extension from the filename
            name_without_ext, _ = os.path.splitext(filename)

            # Create a .txt file with the same base name
            txt_filename = f"{name_without_ext}.txt"
            txt_path = os.path.join(directory, txt_filename)

            # Write the desired content into the .txt file
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(content)
            
            print(f"Created: {txt_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Create a .txt file for each video file in a given directory."
    )
    parser.add_argument(
        "-i", "--input-dir",
        required=True,
        help="Path to the directory containing video files."
    )
    parser.add_argument(
        "-c", "--content",
        required=True,
        help="Text content to write inside each created .txt file."
    )

    args = parser.parse_args()

    create_txt_files(args.input_dir, args.content)

if __name__ == "__main__":
    main()
