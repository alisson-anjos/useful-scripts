#!/usr/bin/env python3
import os
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

def find_paired_images(input_folder: Path, image_extensions: List[str] = None, 
                      txt_extensions: List[str] = None) -> List[Tuple[Path, Path]]:
    """
    Encontra todas as imagens que têm um arquivo de texto correspondente
    
    Args:
        input_folder: Pasta de entrada
        image_extensions: Extensões de imagem aceitas
        txt_extensions: Extensões de texto aceitas
    
    Returns:
        Lista de tuplas (caminho_imagem, caminho_txt)
    """
    if image_extensions is None:
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']
    
    if txt_extensions is None:
        txt_extensions = ['.txt', '.caption']
    
    paired_files = []
    
    # Buscar todas as imagens na pasta
    for img_file in input_folder.iterdir():
        if img_file.is_file() and img_file.suffix.lower() in image_extensions:
            # Verificar se existe um arquivo de texto correspondente
            base_name = img_file.stem  # Nome sem extensão
            
            txt_found = False
            txt_file = None
            
            for txt_ext in txt_extensions:
                potential_txt = input_folder / f"{base_name}{txt_ext}"
                if potential_txt.exists():
                    txt_file = potential_txt
                    txt_found = True
                    break
            
            if txt_found:
                paired_files.append((img_file, txt_file))
    
    return paired_files

def process_paired_files(input_folder: str, output_folder: str, copy_txt: bool = True, 
                        move_files: bool = False, dry_run: bool = False, verbose: bool = False) -> None:
    """
    Copia ou move imagens e seus arquivos de texto correspondentes
    
    Args:
        input_folder: Pasta de origem
        output_folder: Pasta de destino
        copy_txt: Se deve processar também os arquivos de texto
        move_files: Se True, move os arquivos; se False, copia
        dry_run: Se True, apenas mostra o que seria processado sem fazer nada
        verbose: Se True, mostra informações detalhadas
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    # Verificar se a pasta de entrada existe
    if not input_path.exists():
        print(f"❌ Erro: Pasta de entrada '{input_folder}' não existe!")
        return
    
    if not input_path.is_dir():
        print(f"❌ Erro: '{input_folder}' não é uma pasta!")
        return
    
    # Verificar se está tentando mover para a mesma pasta
    if move_files and input_path.resolve() == output_path.resolve():
        print(f"❌ Erro: Não é possível mover arquivos para a mesma pasta de origem!")
        return
    
    # Criar pasta de destino se não existir
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"📁 Pasta de destino: {output_path}")
    
    # Definir ação
    action_verb = "movendo" if move_files else "copiando"
    action_verb_past = "movidas" if move_files else "copiadas"
    action_emoji = "📦" if move_files else "📋"
    
    # Encontrar arquivos pareados
    print(f"🔍 Procurando imagens com texto correspondente em: {input_path}")
    paired_files = find_paired_images(input_path)
    
    if not paired_files:
        print("❌ Nenhuma imagem com arquivo de texto correspondente encontrada!")
        return
    
    print(f"✅ Encontradas {len(paired_files)} imagens com texto correspondente")
    print(f"{action_emoji} {action_verb.capitalize()} arquivos para: {output_path}")
    
    if dry_run:
        print(f"\n🧪 MODO DRY RUN - Nenhum arquivo será {action_verb_past}\n")
    
    processed_images = 0
    processed_texts = 0
    errors = 0
    
    for img_file, txt_file in paired_files:
        try:
            # Definir caminhos de destino
            img_dest = output_path / img_file.name
            txt_dest = output_path / txt_file.name
            
            if verbose or dry_run:
                action_symbol = "➡️" if move_files else "📋"
                print(f"{action_symbol} 📷 {img_file.name} ↔ 📝 {txt_file.name}")
            
            if not dry_run:
                # Processar imagem
                if move_files:
                    shutil.move(str(img_file), str(img_dest))
                else:
                    shutil.copy2(img_file, img_dest)
                processed_images += 1
                
                # Processar arquivo de texto se solicitado
                if copy_txt:
                    if move_files:
                        shutil.move(str(txt_file), str(txt_dest))
                    else:
                        shutil.copy2(txt_file, txt_dest)
                    processed_texts += 1
            else:
                processed_images += 1
                if copy_txt:
                    processed_texts += 1
                    
        except Exception as e:
            errors += 1
            print(f"❌ Erro ao {action_verb} {img_file.name}: {str(e)}")
    
    # Relatório final
    print(f"\n📊 Relatório Final:")
    print(f"   🖼️  Imagens {action_verb_past}: {processed_images}")
    if copy_txt:
        print(f"   📝 Textos {action_verb_past}: {processed_texts}")
    if errors > 0:
        print(f"   ❌ Erros: {errors}")
    
    if not dry_run:
        print(f"   📁 Destino: {output_path}")
        if move_files:
            print(f"   ⚠️  Os arquivos foram removidos da pasta original")
    else:
        action_flag = "--move" if move_files else ""
        print(f"   🧪 Modo dry run - execute sem --dry-run {action_flag} para {action_verb} os arquivos")

def main():
    parser = argparse.ArgumentParser(
        description="Copia ou move imagens que possuem arquivo de texto correspondente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Copiar imagens e textos
  python copy_paired.py /path/input /path/output

  # Mover imagens e textos
  python copy_paired.py /path/input /path/output --move

  # Apenas visualizar o que seria copiado
  python copy_paired.py /path/input /path/output --dry-run

  # Visualizar o que seria movido
  python copy_paired.py /path/input /path/output --move --dry-run

  # Copiar apenas imagens (sem os arquivos de texto)
  python copy_paired.py /path/input /path/output --no-txt

  # Mover apenas imagens (sem os arquivos de texto)
  python copy_paired.py /path/input /path/output --move --no-txt

  # Modo verboso com detalhes
  python copy_paired.py /path/input /path/output --verbose

Extensões suportadas:
  - Imagens: .jpg, .jpeg, .png, .webp, .bmp, .tiff
  - Texto: .txt, .caption

⚠️  ATENÇÃO: Ao usar --move, os arquivos são REMOVIDOS da pasta original!
        """
    )
    
    parser.add_argument(
        'input_folder',
        type=str,
        help='Pasta de entrada contendo as imagens e arquivos de texto'
    )
    
    parser.add_argument(
        'output_folder', 
        type=str,
        help='Pasta de destino onde processar os arquivos'
    )
    
    parser.add_argument(
        '--move', '-m',
        action='store_true',
        help='Mover arquivos ao invés de copiar (REMOVE os arquivos da pasta original)'
    )
    
    parser.add_argument(
        '--no-txt',
        action='store_true',
        help='Processar apenas as imagens, sem os arquivos de texto'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo de teste - apenas mostrar o que seria processado sem fazer nada'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar informações detalhadas durante o processo'
    )
    
    args = parser.parse_args()
    
    # Executar o processamento
    process_paired_files(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        copy_txt=not args.no_txt,
        move_files=args.move,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()