import os
import re
import math
import argparse

from moviepy import *


def get_trailing_number(filename: str):
    """
    Retorna o inteiro se `filename` (sem extensão) terminar com `_<digits>`.
    Caso contrário, retorna None.
    Exemplo:
      "video_1.mp4" -> 1
      "movie_25.mp4" -> 25
      "test.mp4" -> None
    """
    base, ext = os.path.splitext(filename)
    match = re.search(r"_([0-9]+)$", base)
    if match:
        return int(match.group(1))
    return None


def create_video_mosaic_with_titles(
    input_directory, 
    output_file, 
    bg_color=None,
    rows=None,
    cols=None
):
    """
    1) Coleta todos arquivos .mp4 em `input_directory`.
    2) Ordena: se o arquivo termina em _NUMERO, eles vêm primeiro em ordem numérica.
       Arquivos sem número no final são ordenados alfabeticamente depois.
    3) Cria um `TextClip` mostrando o nome do arquivo e o sobrepõe ao vídeo.
    4) Define a quantidade de linhas/colunas (rows/cols):
       - Se rows e cols forem ambos None, usa sqrt para tentar um grid quadrado.
       - Se apenas um for fornecido, calcula o outro a partir de `len(videos)`.
       - Se ambos forem fornecidos, usa esses valores diretamente.
    5) Usa `clips_array` para criar o mosaic e grava no arquivo de saída.
    """

    # 1) Coleta arquivos
    all_files_in_dir = sorted(
        f for f in os.listdir(input_directory) if f.lower().endswith(".mp4")
    )
    if not all_files_in_dir:
        print(f"Nenhum arquivo .mp4 encontrado em '{input_directory}'")
        return

    # 2) Ordena considerando se o nome termina com _NUMBER
    def sort_key(fname):
        trailing_num = get_trailing_number(fname)
        if trailing_num is not None:
            # (0, n) => primeiro pelo zero, e dentro disso pelo número
            return (0, trailing_num)
        else:
            # (1, fname) => depois, em ordem alfabética
            return (1, fname)

    video_files = sorted(all_files_in_dir, key=sort_key)

    print("Ordem final dos vídeos:")
    for vf in video_files:
        print("  ", vf)

    labeled_clips = []
    for vf in video_files:
        full_path = os.path.join(input_directory, vf)

        # Carrega o vídeo
        clip = VideoFileClip(full_path)

        # Cria o overlay de texto com o nome do arquivo
        text_overlay = TextClip(
            font="arial.ttf",     
            text=vf,              
            font_size=40,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="label",       
            text_align="center",
            horizontal_align="center",
            vertical_align="top",
            interline=4,
            transparent=True,
            duration=clip.duration
        )

        # Posição top-center
        text_overlay = text_overlay.with_position(("center", "top"))

        # Composição do vídeo + texto
        clip_with_text = CompositeVideoClip([clip, text_overlay])
        labeled_clips.append(clip_with_text)

    # Número total de vídeos
    n = len(labeled_clips)

    ###########################################################
    # 4) Lógica para definir rows/cols conforme argumentos    #
    ###########################################################
    if rows is None and cols is None:
        # Se nenhum definido, tenta deixar quadrado
        n_cols = math.ceil(math.sqrt(n))
        n_rows = math.ceil(n / n_cols)
    elif rows is not None and cols is not None:
        # Ambos definidos
        n_rows = rows
        n_cols = cols
    elif rows is not None:
        # Só rows
        n_rows = rows
        n_cols = math.ceil(n / n_rows)
    else:
        # Só cols
        n_cols = cols
        n_rows = math.ceil(n / n_cols)

    print(f"Usando grid de {n_rows} linhas × {n_cols} colunas.")

    # Monta a matriz (rows x cols)
    matrix_of_clips = []
    idx = 0
    for _ in range(n_rows):
        row_clips = []
        for _ in range(n_cols):
            if idx < n:
                row_clips.append(labeled_clips[idx])
            else:
                # Se acabaram os clipes, preenche com "blank"
                blank = ColorClip(size=(128, 128), color=(0, 0, 0)).with_duration(1)
                row_clips.append(blank)
            idx += 1
        matrix_of_clips.append(row_clips)

    # 5) Cria o mosaic e grava
    final_clip = clips_array(matrix_of_clips, bg_color=bg_color)
    final_clip.write_videofile(output_file)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Cria um mosaic (grid) de todos os .mp4 de um diretório, ordenando "
            "primeiro os que terminam em _NUMBER (ordem crescente), depois o resto "
            "por ordem alfabética. Cada vídeo recebe overlay do seu nome."
        )
    )
    parser.add_argument(
        "-i", "--input_directory",
        type=str,
        required=True,
        help="Caminho para o diretório contendo arquivos .mp4."
    )
    parser.add_argument(
        "-o", "--output_file",
        type=str,
        required=True,
        help="Nome/caminho do arquivo .mp4 de saída."
    )
    parser.add_argument(
        "--bg_color",
        default=None,
        help="Cor de fundo em 'R,G,B'. Use None para transparente."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Quantidade de linhas no grid. Se não especificado, calculado automaticamente."
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=None,
        help="Quantidade de colunas no grid. Se não especificado, calculado automaticamente."
    )

    args = parser.parse_args()

    bg_color_tuple = None
    if args.bg_color:
        try:
            r, g, b = map(int, args.bg_color.split(","))
            bg_color_tuple = (r, g, b)
        except:
            print("Formato inválido de bg_color. Usando None (transparente).")
            bg_color_tuple = None

    create_video_mosaic_with_titles(
        input_directory=args.input_directory,
        output_file=args.output_file,
        bg_color=bg_color_tuple,
        rows=args.rows,
        cols=args.cols
    )


if __name__ == "__main__":
    main()
