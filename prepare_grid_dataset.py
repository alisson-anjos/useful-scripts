import os
import cv2
import numpy as np
import argparse
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

def detect_scenes(video_path):
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30.0))
    base_timecode = video_manager.get_base_timecode()

    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list(base_timecode)

    frame_ranges = [(scene[0].get_frames(), scene[1].get_frames()) for scene in scene_list]
    video_manager.release()
    return frame_ranges

def extract_frame_at(video_path, frame_number):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def extract_scene(video_path, start_frame, end_frame):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return cap, fps, width, height

def create_grid(frames, grid_shape):
    rows, cols = grid_shape
    if len(frames) < rows * cols:
        return None

    h, w, _ = frames[0].shape
    grid_img = np.zeros((h * rows, w * cols, 3), dtype=np.uint8)

    for idx, frame in enumerate(frames):
        row = idx // cols
        col = idx % cols
        grid_img[row * h:(row + 1) * h, col * w:(col + 1) * w] = frame

    return grid_img

def save_video_with_prefix(grid_frame, cap, start_frame, end_frame, output_path, fps, repeat_prefix):
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    ret, test_frame = cap.read()
    if not ret:
        return
    h, w, _ = test_frame.shape
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # Resize grid to match video
    grid_frame_resized = cv2.resize(grid_frame, (w, h))
    for _ in range(repeat_prefix):
        out.write(grid_frame_resized)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    for frame_num in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    out.release()

def main(args):
    os.makedirs(args.output, exist_ok=True)
    scenes = detect_scenes(args.video)
    print(f"✅ Detected {len(scenes)} scenes.")

    group_size = args.scenes_per_grid
    grid_rows = args.rows
    grid_cols = args.cols

    for i in range(0, len(scenes), group_size):
        scene_group = scenes[i:i + group_size]
        if len(scene_group) < group_size:
            continue

        # Coleta primeiros frames do grupo
        grid_frames = []
        for start_frame, _ in scene_group:
            frame = extract_frame_at(args.video, start_frame)
            if frame is not None:
                grid_frames.append(frame)

        grid_img = create_grid(grid_frames, (grid_rows, grid_cols))
        if grid_img is None:
            print(f"⚠️ Could not create grid for group {i}")
            continue

        # Cria um vídeo por cena, prefixando o grid
        for j, (start_frame, end_frame) in enumerate(scene_group):
            cap, fps, _, _ = extract_scene(args.video, start_frame, end_frame)
            output_path = os.path.join(args.output, f"scene_{i + j:03}.mp4")
            save_video_with_prefix(grid_img, cap, start_frame, end_frame, output_path, fps, args.prefix_frames)
            cap.release()
            print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai cenas com prefixo de grid 2x2 a partir de um vídeo.")
    parser.add_argument('--video', type=str, required=True, help='Caminho do vídeo de entrada.')
    parser.add_argument('--output', type=str, default='output', help='Pasta de saída dos vídeos.')
    parser.add_argument('--scenes-per-grid', type=int, default=4, help='Quantidade de cenas por grid.')
    parser.add_argument('--prefix-frames', type=int, default=8, help='Quantidade de vezes que o grid será repetido no início.')
    parser.add_argument('--rows', type=int, default=2, help='Linhas no grid.')
    parser.add_argument('--cols', type=int, default=2, help='Colunas no grid.')
    args = parser.parse_args()
    main(args)
