import subprocess
from pathlib import Path

def convert_all_webm_to_mp4(input_folder, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    webm_files = list(input_path.glob("*.webm"))

    for file in webm_files:
        output_file = output_path / f"{file.stem}.mp4"
        if output_file.exists():
            print(f"✔️ Skipping (already converted): {file.name}")
            continue

        print(f"🔄 Converting: {file.name} -> {output_file.name}")
        cmd = [
            "ffmpeg", "-y", "-i", str(file),
            "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
            str(output_file)
        ]
        subprocess.run(cmd)

    print("\n✅ Conversion complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert .webm to .mp4 in batch")
    parser.add_argument("--input", required=True, help="Input folder with .webm files")
    parser.add_argument("--output", required=True, help="Output folder for .mp4 files")
    args = parser.parse_args()

    convert_all_webm_to_mp4(args.input, args.output)
