#!/usr/bin/env python3
# ===================================================
# CONVERSOR SIMPLES .PKL PARA .PT
# ===================================================

"""
Script simples para converter modelos StyleGAN .pkl para .pt
sem dependências complexas.

Uso rápido:
python simple_convert.py stylegan2-ffhq.pkl
"""

import torch
import pickle
import sys
import os
from pathlib import Path

def convert_pkl_to_pt(pkl_path, output_path=None):
    """Converte .pkl para .pt de forma simples"""
    
    pkl_path = Path(pkl_path)
    
    if output_path is None:
        output_path = pkl_path.with_suffix('.pt')
    else:
        output_path = Path(output_path)
    
    print(f"🔄 Convertendo: {pkl_path} → {output_path}")
    
    # Método 1: Tentar torch.load (mais seguro)
    try:
        print("📥 Tentando carregar com torch.load...")
        with open(pkl_path, 'rb') as f:
            model = torch.load(f, map_location='cpu')
        print("✅ Carregado com torch.load")
        
    except Exception as e1:
        print(f"❌ torch.load falhou: {e1}")
        
        # Método 2: Tentar pickle.load
        try:
            print("📥 Tentando carregar com pickle.load...")
            with open(pkl_path, 'rb') as f:
                model = pickle.load(f)
            print("✅ Carregado com pickle.load")
            
        except Exception as e2:
            print(f"❌ pickle.load falhou: {e2}")
            print("💡 Tentando método alternativo...")
            
            # Método 3: Ignorar warnings e forçar
            try:
                import warnings
                warnings.filterwarnings('ignore')
                
                with open(pkl_path, 'rb') as f:
                    # Tentar carregamento "sujo"
                    f.seek(0)
                    model = torch.load(f, map_location='cpu', weights_only=False)
                print("✅ Carregado com método alternativo")
                
            except Exception as e3:
                print(f"❌ Todos os métodos falharam: {e1}, {e2}, {e3}")
                return False
    
    # Extrair gerador
    print("🔍 Procurando gerador no modelo...")
    
    generator = None
    
    # Tentar diferentes estruturas
    if hasattr(model, 'G_ema'):
        generator = model.G_ema
        print("✅ Encontrado: model.G_ema")
    elif hasattr(model, 'g_ema'):
        generator = model.g_ema
        print("✅ Encontrado: model.g_ema")
    elif hasattr(model, 'generator'):
        generator = model.generator
        print("✅ Encontrado: model.generator")
    elif hasattr(model, 'synthesis'):
        generator = model
        print("✅ Modelo parece ser o próprio gerador")
    elif isinstance(model, dict):
        print("📋 Modelo é dicionário, procurando chaves...")
        for key in ['G_ema', 'g_ema', 'generator', 'G']:
            if key in model:
                generator = model[key]
                print(f"✅ Encontrado: model['{key}']")
                break
        
        if generator is None:
            print("🔍 Chaves disponíveis:", list(model.keys())[:10])
            # Tentar a primeira chave que parece um gerador
            for key in model.keys():
                if any(term in key.lower() for term in ['gen', 'g_', 'synthesis']):
                    generator = model[key]
                    print(f"✅ Usando: model['{key}']")
                    break
    
    if generator is None:
        print("⚠️  Usando modelo original (pode não funcionar)")
        generator = model
    
    # Extrair state_dict se necessário
    if hasattr(generator, 'state_dict'):
        state_dict = generator.state_dict()
        print("📦 Extraído state_dict do gerador")
    elif isinstance(generator, dict):
        state_dict = generator
        print("📦 Gerador já é um dicionário")
    else:
        print("⚠️  Não foi possível extrair state_dict")
        state_dict = generator
    
    # Criar checkpoint final
    final_checkpoint = {
        'g_ema': state_dict,
        'info': {
            'converted_from': str(pkl_path),
            'original_type': str(type(model)),
            'generator_type': str(type(generator))
        }
    }
    
    # Salvar
    try:
        print(f"💾 Salvando em {output_path}...")
        torch.save(final_checkpoint, output_path)
        
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"✅ Conversão concluída! Arquivo: {file_size:.1f} MB")
        
        # Teste rápido
        print("🧪 Testando arquivo convertido...")
        test_model = torch.load(output_path, map_location='cpu')
        if 'g_ema' in test_model:
            print(f"✅ Teste OK! {len(test_model['g_ema'])} parâmetros encontrados")
        else:
            print("⚠️  Teste parcial - estrutura diferente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro salvando: {e}")
        return False

def batch_convert(directory):
    """Converte todos os .pkl em um diretório"""
    directory = Path(directory)
    pkl_files = list(directory.glob("*.pkl"))
    
    if not pkl_files:
        print(f"❌ Nenhum arquivo .pkl encontrado em {directory}")
        return
    
    print(f"🔍 Encontrados {len(pkl_files)} arquivos .pkl")
    
    for pkl_file in pkl_files:
        print(f"\n{'='*50}")
        convert_pkl_to_pt(pkl_file)

def main():
    if len(sys.argv) < 2:
        print("""
🔧 CONVERSOR SIMPLES .PKL PARA .PT

Uso:
python simple_convert.py model.pkl              # Converte um arquivo
python simple_convert.py model.pkl output.pt    # Especifica saída
python simple_convert.py /pasta/com/models/     # Converte todos .pkl na pasta

Exemplos:
python simple_convert.py stylegan2-ffhq.pkl
python simple_convert.py stylegan3-t-ffhq.pkl stylegan3-faces.pt
""")
        return
    
    input_path = sys.argv[1]
    
    if os.path.isdir(input_path):
        batch_convert(input_path)
    else:
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        success = convert_pkl_to_pt(input_path, output_path)
        
        if success:
            print(f"\n🎉 Sucesso! Copie o arquivo .pt para:")
            print(f"   ComfyUI/models/stylegan/")
        else:
            print(f"\n❌ Conversão falhou")
            sys.exit(1)

if __name__ == "__main__":
    main()