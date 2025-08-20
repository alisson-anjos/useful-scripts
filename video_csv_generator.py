import os
import csv
from pathlib import Path

def generate_video_csv(folder_path, output_csv="metadata.csv"):
    """
    Gera um arquivo CSV com informações de vídeos e suas respectivas captions.
    
    Args:
        folder_path (str): Caminho para a pasta contendo os vídeos e arquivos .txt
        output_csv (str): Nome do arquivo CSV de saída (padrão: metadata.csv)
    """
    
    # Converte para Path para facilitar manipulação
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Erro: A pasta '{folder_path}' não existe!")
        return
    
    # Lista para armazenar os dados
    video_data = []
    
    # Busca por todos os arquivos de vídeo na pasta
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    for video_file in folder.iterdir():
        if video_file.is_file() and video_file.suffix.lower() in video_extensions:
            # Nome do arquivo de caption correspondente
            caption_file = video_file.with_suffix('.txt')
            
            if caption_file.exists():
                try:
                    # Lê o conteúdo do arquivo de caption
                    with open(caption_file, 'r', encoding='utf-8') as f:
                        caption_text = f.read().strip()
                    
                    # Adiciona à lista de dados
                    video_data.append({
                        'video': video_file.name,
                        'prompt': caption_text
                    })
                    
                    print(f"Processado: {video_file.name} -> {caption_text[:50]}...")
                    
                except Exception as e:
                    print(f"Erro ao ler caption para {video_file.name}: {e}")
            else:
                print(f"Aviso: Caption não encontrada para {video_file.name}")
    
    if not video_data:
        print("Nenhum par vídeo/caption foi encontrado!")
        return
    
    # Ordena os dados por nome do vídeo para consistência
    video_data.sort(key=lambda x: x['video'])
    
    # Caminho completo para o arquivo CSV de saída
    output_path = folder / output_csv
    
    # Escreve o arquivo CSV
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['video', 'prompt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Escreve o cabeçalho
            writer.writeheader()
            
            # Escreve os dados
            for row in video_data:
                writer.writerow(row)
        
        print(f"\n✅ Arquivo CSV gerado com sucesso: {output_path}")
        print(f"Total de vídeos processados: {len(video_data)}")
        
    except Exception as e:
        print(f"Erro ao escrever arquivo CSV: {e}")

def main():
    """Função principal para execução do script"""
    
    # Solicita o caminho da pasta ao usuário
    folder_path = input("Digite o caminho da pasta com os vídeos: ").strip()
    
    # Remove aspas se o usuário colou um caminho com aspas
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    
    # Nome do arquivo CSV (você pode alterar se quiser)
    csv_filename = "metadata.csv"
    
    print(f"\nProcessando pasta: {folder_path}")
    print(f"Arquivo CSV será salvo como: {csv_filename}")
    print("-" * 50)
    
    # Gera o CSV
    generate_video_csv(folder_path, csv_filename)

if __name__ == "__main__":
    main()
