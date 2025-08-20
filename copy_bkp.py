import os
import shutil
import argparse

# Extensões de imagem suportadas
EXTENSOES_IMAGENS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif'}

def copiar_arquivos(base_folder, search_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Coleta os nomes base (sem extensão) das imagens da pasta base
    nomes_base = {
        os.path.splitext(f)[0]
        for f in os.listdir(base_folder)
        if os.path.splitext(f)[1].lower() in EXTENSOES_IMAGENS
    }

    # Percorre os arquivos na pasta de busca
    for file in os.listdir(search_folder):
        name, ext = os.path.splitext(file)
        if name in nomes_base:
            src_path = os.path.join(search_folder, file)
            dst_path = os.path.join(output_folder, file)
            shutil.copy2(src_path, dst_path)
            print(f'Copiado: {file}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copiar arquivos com nomes base de imagens.')
    parser.add_argument('--base-folder', required=True, help='Pasta com as imagens base (quaisquer extensões)')
    parser.add_argument('--search-folder', required=True, help='Pasta onde procurar arquivos com mesmo nome base')
    parser.add_argument('--output-folder', required=True, help='Pasta onde salvar os arquivos copiados')

    args = parser.parse_args()
    copiar_arquivos(args.base_folder, args.search_folder, args.output_folder)
