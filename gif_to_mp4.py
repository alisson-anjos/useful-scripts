import os
import subprocess
from pathlib import Path

def converter_gifs_para_mp4(pasta):
    # Encontrar todos os arquivos GIF na pasta
    gifs = list(Path(pasta).glob('*.gif'))
    
    print(f"Encontrados {len(gifs)} arquivos GIF")
    
    for gif in gifs:
        # Nome do arquivo de saída (substitui .gif por .mp4)
        mp4_output = gif.with_suffix('.mp4')
        
        print(f"Convertendo: {gif.name} -> {mp4_output.name}")
        
        # Comando FFmpeg para conversão
        cmd = [
            'ffmpeg', '-i', str(gif),
            '-movflags', 'faststart',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            str(mp4_output)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Convertido: {mp4_output.name}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Erro ao converter {gif.name}: {e}")

# Usar o script
pasta_gifs = "caminho/para/sua/pasta"
converter_gifs_para_mp4(pasta_gifs)