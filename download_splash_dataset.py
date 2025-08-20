import os
import pandas as pd
from datasets import load_dataset
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

def download_and_extract_dataset(dataset_name="mrzjy/splash-art-gacha-collection-10k", 
                                output_dir="splash_art_dataset", 
                                max_workers=4):
    """
    Baixa o dataset e extrai imagens e captions para pastas organizadas usando múltiplas threads
    
    Args:
        dataset_name (str): Nome do dataset no Hugging Face
        output_dir (str): Diretório de saída para salvar os arquivos
        max_workers (int): Número máximo de threads (padrão: 4)
    """
    
    # Criar diretórios de saída
    base_path = Path(output_dir)
    images_path = base_path / "images"
    captions_path = base_path / "captions"
    
    # Criar as pastas se não existirem
    base_path.mkdir(exist_ok=True)
    images_path.mkdir(exist_ok=True)
    captions_path.mkdir(exist_ok=True)
    
    print(f"Carregando dataset: {dataset_name}")
    
    try:
        # Carregar o dataset
        dataset = load_dataset(dataset_name)
        
        # Assumindo que o dataset tem uma divisão 'train' - ajuste conforme necessário
        if 'train' in dataset:
            data = dataset['train']
        else:
            # Se não tiver 'train', pega a primeira divisão disponível
            split_name = list(dataset.keys())[0]
            data = dataset[split_name]
            print(f"Usando divisão: {split_name}")
        
        print(f"Dataset carregado com {len(data)} amostras")
        print("Colunas esperadas: image, prompt, character")
        
        # Verificar se as colunas necessárias existem
        required_columns = ['image', 'prompt', 'character']
        missing_columns = [col for col in required_columns if col not in data.column_names]
        
        if missing_columns:
            print(f"Aviso: Colunas não encontradas: {missing_columns}")
            print(f"Colunas disponíveis: {data.column_names}")
        else:
            print("✓ Todas as colunas necessárias encontradas")
        
        # Forçar carregamento de uma amostra para testar
        print("Testando acesso aos dados...")
        try:
            first_item = data[0]
            print(f"✓ Primeiro item acessado com sucesso")
            print(f"  - Tem imagem: {'image' in first_item and first_item['image'] is not None}")
            print(f"  - Prompt: {str(first_item.get('prompt', 'N/A'))[:50]}...")
            print(f"  - Character: {first_item.get('character', 'N/A')}")
        except Exception as e:
            print(f"❌ Erro ao acessar dados: {e}")
            return
        
        # Contadores thread-safe
        successful_downloads = 0
        failed_downloads = 0
        progress_lock = Lock()
        
        def process_item(args):
            """Função para processar um item individual em thread separada"""
            idx, item = args
            nonlocal successful_downloads, failed_downloads
            
            try:
                # Extrair dados conforme as colunas específicas do dataset
                image = item.get('image')
                prompt = item.get('prompt', '')
                character = item.get('character', '')
                
                # Criar caption combinando prompt com tag do personagem
                if character and character.strip():
                    caption = f"{prompt} [{character}]".strip()
                else:
                    caption = prompt.strip()
                
                if image is None:
                    with progress_lock:
                        failed_downloads += 1
                    return f"Aviso: Imagem não encontrada no item {idx}"
                
                if not caption:
                    return f"Aviso: Caption vazio no item {idx} - continuando mesmo assim"
                
                # Nome base comum para imagem e caption
                base_filename = f"{idx:06d}"
                
                # Salvar imagem
                if isinstance(image, Image.Image):
                    # Se já é uma imagem PIL
                    img_filename = f"{base_filename}.jpg"
                    img_path = images_path / img_filename
                    
                    # Converter RGBA para RGB se necessário
                    if image.mode in ('RGBA', 'LA'):
                        # Criar fundo branco
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'RGBA':
                            background.paste(image, mask=image.split()[-1])  # Usar canal alpha como máscara
                        else:  # LA mode
                            background.paste(image, mask=image.split()[-1])
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    image.save(img_path, "JPEG", quality=95)
                    
                elif isinstance(image, str) and image.startswith(('http://', 'https://')):
                    # Se é uma URL, baixar a imagem
                    img_filename = f"{base_filename}.jpg"
                    img_path = images_path / img_filename
                    
                    response = requests.get(image, timeout=30)
                    response.raise_for_status()
                    
                    pil_image = Image.open(BytesIO(response.content))
                    
                    # Converter RGBA para RGB se necessário
                    if pil_image.mode in ('RGBA', 'LA'):
                        # Criar fundo branco
                        background = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'RGBA':
                            background.paste(pil_image, mask=pil_image.split()[-1])  # Usar canal alpha como máscara
                        else:  # LA mode
                            background.paste(pil_image, mask=pil_image.split()[-1])
                        pil_image = background
                    elif pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    pil_image.save(img_path, "JPEG", quality=95)
                    
                else:
                    with progress_lock:
                        failed_downloads += 1
                    return f"Aviso: Formato de imagem não reconhecido no item {idx}"
                
                # Salvar caption
                caption_filename = f"{base_filename}.txt"
                caption_path = captions_path / caption_filename
                
                with open(caption_path, 'w', encoding='utf-8') as f:
                    f.write(str(caption))
                
                with progress_lock:
                    successful_downloads += 1
                
                return f"Sucesso: Item {idx} processado"
                
            except Exception as e:
                with progress_lock:
                    failed_downloads += 1
                return f"Erro ao processar item {idx}: {str(e)}"
        
        # Processar itens usando ThreadPoolExecutor
        print(f"\nIniciando processamento com {max_workers} threads...")
        print("Preparando lista de itens...")
        
        # Preparar lista de argumentos (índice, item) - fazer isso de forma mais eficiente
        total_items = len(data)
        print(f"Total de {total_items} itens para processar")
        
        # Usar ThreadPoolExecutor para processar em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            print("ThreadPoolExecutor criado, iniciando processamento...")
            
            # Processar itens conforme são submetidos (sem acumular futures)
            active_futures = {}
            submitted_count = 0
            
            for idx in range(total_items):
                try:
                    # Se temos muitas tarefas ativas, esperar algumas completarem
                    while len(active_futures) >= max_workers * 2:  # Buffer de 2x o número de workers
                        completed_futures = []
                        for future, future_idx in list(active_futures.items()):
                            if future.done():
                                try:
                                    result = future.result()
                                    if "Erro" in result or "Aviso" in result:
                                        print(result)
                                except Exception as exc:
                                    with progress_lock:
                                        failed_downloads += 1
                                    print(f'Item {future_idx} gerou uma exceção: {exc}')
                                
                                completed_futures.append(future)
                        
                        # Remover futures completados
                        for future in completed_futures:
                            del active_futures[future]
                        
                        # Log do progresso
                        with progress_lock:
                            total_processed = successful_downloads + failed_downloads
                            if total_processed % 50 == 0 and total_processed > 0:
                                print(f"Progresso: {total_processed}/{total_items} | "
                                      f"Sucessos: {successful_downloads} | "
                                      f"Falhas: {failed_downloads}")
                        
                        if len(active_futures) >= max_workers * 2:
                            time.sleep(0.1)  # Pequeno delay se ainda temos muitas tarefas
                    
                    # Submeter nova tarefa
                    item = data[idx]
                    future = executor.submit(process_item, (idx, item))
                    active_futures[future] = idx
                    submitted_count += 1
                    
                    if submitted_count % 100 == 0:
                        print(f"Submetidos: {submitted_count}/{total_items}")
                    
                except Exception as e:
                    print(f"Erro ao acessar item {idx}: {e}")
                    with progress_lock:
                        failed_downloads += 1
            
            # Aguardar conclusão de todas as tarefas restantes
            print("Aguardando conclusão das tarefas restantes...")
            while active_futures:
                completed_futures = []
                for future, future_idx in list(active_futures.items()):
                    if future.done():
                        try:
                            result = future.result()
                            if "Erro" in result or "Aviso" in result:
                                print(result)
                        except Exception as exc:
                            with progress_lock:
                                failed_downloads += 1
                            print(f'Item {future_idx} gerou uma exceção: {exc}')
                        
                        completed_futures.append(future)
                
                # Remover futures completados
                for future in completed_futures:
                    del active_futures[future]
                
                # Log do progresso final
                with progress_lock:
                    total_processed = successful_downloads + failed_downloads
                    if len(active_futures) % 50 == 0 or len(active_futures) < 10:
                        print(f"Restam: {len(active_futures)} tarefas | "
                              f"Progresso: {total_processed}/{total_items}")
                
                if active_futures:
                    time.sleep(0.5)
        
        print(f"\n=== Extração Completa ===")
        print(f"Total de itens processados: {len(data)}")
        print(f"Downloads bem-sucedidos: {successful_downloads}")
        print(f"Downloads falhados: {failed_downloads}")
        print(f"Imagens salvas em: {images_path}")
        print(f"Captions salvas em: {captions_path}")
        
        # Criar arquivo de índice
        create_index_file(base_path, successful_downloads)
        
    except Exception as e:
        print(f"Erro ao carregar o dataset: {str(e)}")
        print("Verifique se o nome do dataset está correto e se você tem acesso a ele.")

def create_index_file(base_path, num_files):
    """Cria um arquivo de índice com informações sobre o dataset extraído"""
    index_path = base_path / "dataset_info.txt"
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("=== Splash Art Gacha Collection Dataset ===\n")
        f.write(f"Número total de arquivos: {num_files}\n")
        f.write(f"Fonte: mrzjy/splash-art-gacha-collection-10k\n")
        f.write(f"Colunas processadas: image, prompt, character\n")
        f.write(f"Formato do caption: [prompt] [character] (quando character disponível)\n")
        f.write(f"Estrutura:\n")
        f.write(f"  - images/: Contém as imagens (000000.jpg, 000001.jpg, etc.)\n")
        f.write(f"  - captions/: Contém as descrições (000000.txt, 000001.txt, etc.)\n")
        f.write(f"  - Os arquivos têm o mesmo nome base (000000, 000001, etc.)\n")
        f.write(f"  - Cada imagem corresponde ao caption com o mesmo nome\n")
    
    print(f"Arquivo de índice criado: {index_path}")

if __name__ == "__main__":
    # Instalar dependências necessárias se não estiverem instaladas
    try:
        import datasets
        from PIL import Image
        import requests
    except ImportError as e:
        print(f"Dependência não encontrada: {e}")
        print("Instale as dependências com:")
        print("pip install datasets pillow requests pandas")
        exit(1)
    
    # Executar a extração com 4 threads (ajuste conforme necessário)
    download_and_extract_dataset(max_workers=4)
    
    print("\n=== Script finalizado! ===")
    print("Para usar o dataset extraído:")
    print("1. As imagens estão na pasta 'splash_art_dataset/images/'")
    print("2. As captions estão na pasta 'splash_art_dataset/captions/'")
    print("3. Os arquivos têm o mesmo nome base (000000.jpg <-> 000000.txt)")
