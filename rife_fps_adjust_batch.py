import cv2

def get_video_fps(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return fps

def convert_video_rife(input_path: Path, output_path: Path, target_fps: int, rife_exec_path: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_input_dir = Path("tmp_frames/in")
    tmp_output_dir = Path("tmp_frames/out")
    tmp_input_dir.mkdir(parents=True, exist_ok=True)
    tmp_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔍 Extracting frames from: {input_path.name}")
    subprocess.run([
        "ffmpeg", "-i", str(input_path),
        f"{tmp_input_dir}/%05d.png",
        "-hide_banner", "-loglevel", "error"
    ])

    # Detect original FPS
    input_fps = get_video_fps(input_path)
    interpolation_factor = input_fps / target_fps
    if interpolation_factor < 1 or interpolation_factor != int(interpolation_factor):
        print(f"❌ Invalid FPS conversion: {input_fps} -> {target_fps}. Must be divisible.")
        return

    interpolation_factor = int(interpolation_factor)

    print(f"⚙️ Interpolating with RIFE: {input_fps} -> {target_fps} (factor {interpolation_factor})")
    subprocess.run([
        rife_exec_path,
        "-i", str(tmp_input_dir),
        "-o", str(tmp_output_dir),
        "-f", str(interpolation_factor)
    ])

    if not any(tmp_output_dir.glob("*.png")):
        print(f"❌ RIFE did not generate output frames.")
        return

    print(f"🎥 Re-encoding video to: {output_path.name}")
    subprocess.run([
        "ffmpeg",
        "-r", str(target_fps),
        "-i", f"{tmp_output_dir}/%05d.png",
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
        "-y", "-hide_banner", "-loglevel", "error"
    ])

    print("🧹 Cleaning temporary files...")
    for p in tmp_input_dir.glob("*"): p.unlink()
    for p in tmp_output_dir.glob("*"): p.unlink()
    tmp_input_dir.rmdir()
    tmp_output_dir.rmdir()
