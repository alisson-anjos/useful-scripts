import os
import re
import math
import argparse

from moviepy import *


def get_trailing_number(filename: str):
    """
    Returns the integer if `filename` (minus extension) ends with `_<digits>`.
    Otherwise returns None.
    Example:
      "video_1.mp4" -> 1
      "movie_25.mp4" -> 25
      "test.mp4" -> None
    """
    # remove extension
    base, ext = os.path.splitext(filename)
    match = re.search(r"_([0-9]+)$", base)
    if match:
        return int(match.group(1))
    return None


def create_video_mosaic_with_titles(input_directory, output_file, bg_color=None):
    """
    1) Collect all .mp4 files in `input_directory`.
    2) Sort them so any file ending with _NUMBER goes first in ascending numeric order,
       and any file without trailing _NUMBER is sorted alphabetically afterward.
    3) Overlay each clip with a text clip showing its filename.
    4) Arrange these labeled clips in a matrix (mosaic) with clips_array().
    5) Write the final mosaic to `output_file`.
    """

    #########################
    # 1) Collect .mp4 files #
    #########################
    all_files_in_dir = sorted(
        f for f in os.listdir(input_directory) if f.lower().endswith(".mp4")
    )
    if not all_files_in_dir:
        print(f"No .mp4 files found in '{input_directory}'")
        return

    #######################################################
    # 2) Sort by trailing number, then alphabetical order #
    #######################################################
    def sort_key(fname):
        trailing_num = get_trailing_number(fname)
        if trailing_num is not None:
            # Put numeric-tail files first, sorted by the trailing number
            return (0, trailing_num)
        else:
            # Then put everything else in alphabetical order
            return (1, fname)

    video_files = sorted(all_files_in_dir, key=sort_key)

    print("Final sorted order:")
    for vf in video_files:
        print("  ", vf)

    labeled_clips = []
    for vf in video_files:
        full_path = os.path.join(input_directory, vf)

        # Load video
        clip = VideoFileClip(full_path)

        # Create text overlay (NEW TextClip)
        text_overlay = TextClip(
            font="arial.ttf",     # Provide a valid .ttf/.otf font path
            text=vf,              # The filename
            font_size=20,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="label",       # 'label' auto-sizes; 'caption' requires fixed size
            text_align="center",
            horizontal_align="center",
            vertical_align="top",
            interline=4,
            transparent=True,
            duration=clip.duration
        )

        # Position text at top-center
        text_overlay = text_overlay.with_position(("center", "top"))

        # Composite the original clip + text
        clip_with_text = CompositeVideoClip([clip, text_overlay])
        labeled_clips.append(clip_with_text)

    ###############################################
    # 3) Build a mosaic (matrix) by rows & cols.  #
    ###############################################
    n = len(labeled_clips)
    n_cols = math.ceil(math.sqrt(n))
    n_rows = math.ceil(n / n_cols)

    matrix_of_clips = []
    idx = 0
    for _ in range(n_rows):
        row_clips = []
        for _ in range(n_cols):
            if idx < n:
                row_clips.append(labeled_clips[idx])
            else:
                # Fill blank if no more clips
                blank = ColorClip(size=(128, 128), color=(0, 0, 0)).with_duration(1)
                row_clips.append(blank)
            idx += 1
        matrix_of_clips.append(row_clips)

    #####################################
    # 4) Create mosaic and write output #
    #####################################
    final_clip = clips_array(matrix_of_clips, bg_color=bg_color)
    final_clip.write_videofile(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Arrange .mp4 files in a folder into a mosaic, each labeled with its filename. "
                    "Files ending with _NUMBER come first in ascending numeric order."
    )
    parser.add_argument(
        "-i", "--input_directory",
        type=str,
        required=True,
        help="Path to the directory containing .mp4 files."
    )
    parser.add_argument(
        "-o", "--output_file",
        type=str,
        required=True,
        help="Name/path for the output .mp4 file."
    )
    parser.add_argument(
        "--bg_color",
        default=None,
        help="Background color in 'R,G,B' form or None for transparent."
    )

    args = parser.parse_args()

    bg_color_tuple = None
    if args.bg_color:
        try:
            r, g, b = map(int, args.bg_color.split(","))
            bg_color_tuple = (r, g, b)
        except:
            print("Invalid bg_color format. Using None (transparent).")
            bg_color_tuple = None

    create_video_mosaic_with_titles(
        input_directory=args.input_directory,
        output_file=args.output_file,
        bg_color=bg_color_tuple
    )


if __name__ == "__main__":
    main()
