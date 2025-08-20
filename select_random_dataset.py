import os
import random
import shutil
import sys

def copy_random_videos(src_folder, dst_folder, num_videos, video_extensions=None):
    # Define as extensões de vídeo permitidas, se não especificado.
    if video_extensions is None:
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
    
    # Cria a pasta de destino, se não existir.
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
    
    # Lista todos os arquivos da pasta de origem.
    all_files = os.listdir(src_folder)
    
    # Filtra os vídeos que possuem as extensões definidas E que também possuem um arquivo .txt com o mesmo nome base.
    video_files = [
        f for f in all_files
        if os.path.splitext(f)[1].lower() in video_extensions
        and f"{os.path.splitext(f)[0]}.txt" in all_files
    ]
    
    # Verifica se o número de vídeos solicitado é maior que os disponíveis.
    if num_videos > len(video_files):
        raise ValueError(f"Você solicitou {num_videos} vídeos, mas somente {len(video_files)} foram encontrados na pasta com o arquivo .txt correspondente.")
    
    # Seleciona aleatoriamente "num_videos" da lista filtrada.
    selected_videos = random.sample(video_files, num_videos)
    
    # Copia os vídeos e os respectivos arquivos .txt.
    for video in selected_videos:
        video_src_path = os.path.join(src_folder, video)
        video_dst_path = os.path.join(dst_folder, video)
        shutil.copy2(video_src_path, video_dst_path)
        print(f"Vídeo copiado: {video}")
        
        # Copia o arquivo .txt correspondente.
        base_name, _ = os.path.splitext(video)
        text_filename = base_name + '.txt'
        text_src_path = os.path.join(src_folder, text_filename)
        text_dst_path = os.path.join(dst_folder, text_filename)
        shutil.copy2(text_src_path, text_dst_path)
        print(f"Arquivo de texto copiado: {text_filename}")

if __name__ == '__main__':
    # Valida os argumentos passados via linha de comando.
    if len(sys.argv) != 4:
        print("Uso: python copia_videos.py <pasta_origem> <pasta_destino> <numero_de_videos>")
        sys.exit(1)
        
    src_folder = sys.argv[1]
    dst_folder = sys.argv[2]
    try:
        num_videos = int(sys.argv[3])
    except ValueError:
        print("O terceiro argumento deve ser um número inteiro representando a quantidade de vídeos a copiar.")
        sys.exit(1)
        
    copy_random_videos(src_folder, dst_folder, num_videos)
