import os
import subprocess
import argparse
from glob import glob

def get_resolution(path):
    """Retorna (largura, altura) usando ffprobe"""
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
        path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        width, height = result.stdout.decode().strip().split(',')
        return int(width), int(height)
    except:
        return None, None

def resize_video(input_path, output_path, base_width):
    before_w, before_h = get_resolution(input_path)

    command = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', f"scale=min({base_width},iw):-2",
        '-c:a', 'copy',
        output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    after_w, after_h = get_resolution(output_path)
    
    if after_w is None:
        print(f"❌ Failed to read output: {os.path.basename(output_path)}")
    elif before_w > base_width and after_w == base_width:
        print(f"✅ Resized: {os.path.basename(output_path)} ({before_w}→{after_w})")
    elif before_w <= base_width and after_w == before_w:
        print(f"⏭️ Skipped (already <= {base_width}): {os.path.basename(output_path)}")
    else:
        print(f"❌ Resize failed: {os.path.basename(output_path)} (Still {after_w})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--base', type=int, default=1280)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    videos = glob(os.path.join(args.input, '**/*.mp4'), recursive=True)

    for path in videos:
        filename = os.path.basename(path)
        output_path = os.path.join(args.output, filename)
        resize_video(path, output_path, args.base)

if __name__ == '__main__':
    main()
