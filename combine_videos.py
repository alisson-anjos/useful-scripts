import os
import argparse
import subprocess
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

def detect_scenes(video_path):
    """
    Detecta cenas em um vídeo usando PySceneDetect.

    Args:
        video_path (str): Caminho para o arquivo de vídeo.

    Returns:
        List[Tuple[float, float]]: Lista de cenas com tempos de início e fim (em segundos).
    """
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())

    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    return [(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scene_list]

def extract_scenes_ffmpeg(video_path, output_dir, scenes, target_fps=24, duration_sec=None, num_frames=None, reverse=False):
    """
    Extrai as cenas detectadas usando FFmpeg.

    Args:
        video_path (str): Caminho do vídeo original.
        output_dir (str): Diretório para salvar as cenas extraídas.
        scenes (list): Lista de tuplas (start, end) das cenas detectadas.
        target_fps (int): FPS desejado para os vídeos extraídos.
        duration_sec (float): Limita a duração máxima de cada cena.
        num_frames (int): Define um número fixo de frames a serem extraídos.
        reverse (bool): Inverte o vídeo extraído.
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, (start, end) in enumerate(scenes):
        scene_duration = end - start

        if duration_sec and scene_duration > duration_sec:
            end = start + duration_sec
        elif num_frames:
            frame_duration = num_frames / target_fps
            if scene_duration > frame_duration:
                end = start + frame_duration

        base_name = os.path.basename(video_path)
        name, ext = os.path.splitext(base_name)
        output_name = f"{name}_scene_{i+1:03d}{ext}"
        output_path = os.path.join(output_dir, output_name)

        ffmpeg_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", video_path, 
            "-ss", str(start),
            "-to", str(end),
            "-r", str(target_fps),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]

        if reverse:
            ffmpeg_cmd.insert(-1, "-vf")
            ffmpeg_cmd.insert(-1, "reverse")

        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Salvou: {output_path}")

def process_directory(input_dir, output_dir, **kwargs):
    """
    Processa todos os vídeos dentro de um diretório.

    Args:
        input_dir (str): Diretório contendo os vídeos.
        output_dir (str): Diretório onde os vídeos processados serão salvos.
        kwargs: Parâmetros a serem passados para `extract_scenes_ffmpeg`.
    """
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv')

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(video_extensions):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, input_dir)
                dest_dir = os.path.join(output_dir, rel_path)

                try:
                    print(f"Detectando cenas em: {input_path}")
                    scenes = detect_scenes(input_path)

                    if not scenes:
                        print(f"Nenhuma cena detectada para {input_path}, pulando...")
                        continue

                    extract_scenes_ffmpeg(input_path, dest_dir, scenes, **kwargs)
                except Exception as e:
                    print(f"Erro ao processar {input_path}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ferramenta de processamento de vídeo com detecção de cenas e extração via FFmpeg",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("input_dir", help="Diretório contendo os vídeos")
    parser.add_argument("output_dir", help="Diretório de saída para as cenas extraídas")
    parser.add_argument("--fps", type=int, default=24, help="FPS desejado")
    parser.add_argument("--duration", type=float, help="Limite de duração por cena")
    parser.add_argument("--frames", type=int, help="Número de frames a extrair (alternativa à duração)")
    parser.add_argument("--reverse", action="store_true", help="Reverter os vídeos extraídos")

    args = parser.parse_args()

    if args.duration and args.frames:
        parser.error("Não é possível especificar ambos --duration e --frames")

    process_directory(
        args.input_dir,
        args.output_dir,
        target_fps=args.fps,
        duration_sec=args.duration,
        num_frames=args.frames,
        reverse=args.reverse
    )
