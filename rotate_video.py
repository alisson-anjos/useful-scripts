import os
import argparse
import subprocess

def get_transpose_filter(degrees):
    if degrees == 90:
        return "transpose=1"
    elif degrees == 180:
        return "transpose=1,transpose=1"
    elif degrees == 270:
        return "transpose=2"
    else:
        raise ValueError("Only 90, 180, and 270 degrees are supported.")

def rotate_video(input_path, output_path, degrees):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    vf_filter = get_transpose_filter(degrees)
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf_filter,
        "-c:a", "copy",  # Copy audio stream without re-encoding
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def main(input_dir, output_dir, degrees):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                print(f"Rotating: {rel_path}")
                rotate_video(input_path, output_path, degrees)
    print("✅ Finished rotation.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotate all videos in a folder.")
    parser.add_argument("--input_dir", required=True, help="Folder with input videos")
    parser.add_argument("--output_dir", required=True, help="Folder to save rotated videos")
    parser.add_argument("--degrees", type=int, required=True, choices=[90, 180, 270], help="Rotation angle in degrees")
    args = parser.parse_args()

    main(args.input_dir, args.output_dir, args.degrees)
