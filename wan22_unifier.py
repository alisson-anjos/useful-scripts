#!/usr/bin/env python3
"""
Script para unificar os modelos WAN 2.2 High/Low Noise em um único arquivo
Cria um checkpoint que contém ambos os modelos sem fazer merge dos pesos
"""

import torch
import argparse
import os
from pathlib import Path
import json
from datetime import datetime

def load_model_safely(model_path):
    """
    Carrega um modelo de forma segura
    """
    print(f"📁 Loading model: {model_path}")
    
    try:
        if model_path.endswith('.safetensors'):
            from safetensors.torch import load_file
            model_data = load_file(model_path)
        else:
            model_data = torch.load(model_path, map_location='cpu')
        
        print(f"✅ Model loaded successfully ({len(model_data)} keys)")
        return model_data
    
    except Exception as e:
        print(f"❌ Error loading {model_path}: {e}")
        return None

def create_unified_model(high_noise_path, low_noise_path, output_path, threshold=0.5):
    """
    Cria um modelo unificado contendo ambos os modelos
    """
    print("🎭 WAN 2.2 Model Unifier")
    print("=" * 50)
    
    # Carrega os modelos
    high_noise_model = load_model_safely(high_noise_path)
    low_noise_model = load_model_safely(low_noise_path)
    
    if high_noise_model is None or low_noise_model is None:
        print("❌ Failed to load one or both models!")
        return False
    
    # Cria o modelo unificado
    unified_model = {
        # Metadata do modelo unificado
        '__wan22_unified_metadata__': {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'high_noise_model': os.path.basename(high_noise_path),
            'low_noise_model': os.path.basename(low_noise_path),
            'default_threshold': threshold,
            'description': 'WAN 2.2 Unified Model - Contains both High and Low Noise models'
        },
        
        # Modelo High Noise com prefixo
        **{f'high_noise.{key}': value for key, value in high_noise_model.items()},
        
        # Modelo Low Noise com prefixo  
        **{f'low_noise.{key}': value for key, value in low_noise_model.items()},
        
        # Configurações de threshold
        '__wan22_threshold_config__': {
            'default': threshold,
            'recommended': {
                'general': 0.5,
                'high_detail': 0.3,
                'fast_generation': 0.7,
                'artistic': 0.4,
                'photorealistic': 0.6
            }
        }
    }
    
    print(f"🔗 Unified model created:")
    print(f"   - High Noise keys: {len([k for k in unified_model.keys() if k.startswith('high_noise.')])}")
    print(f"   - Low Noise keys: {len([k for k in unified_model.keys() if k.startswith('low_noise.')])}")
    print(f"   - Total size: {sum(v.numel() if hasattr(v, 'numel') else 0 for v in unified_model.values() if isinstance(v, torch.Tensor)):,} parameters")
    
    # Salva o modelo unificado
    print(f"💾 Saving unified model to: {output_path}")
    
    try:
        if output_path.endswith('.safetensors'):
            from safetensors.torch import save_file
            
            # Separa tensors de metadata para safetensors
            tensors = {k: v for k, v in unified_model.items() if isinstance(v, torch.Tensor)}
            metadata = {k: json.dumps(v) if isinstance(v, dict) else str(v) 
                       for k, v in unified_model.items() if not isinstance(v, torch.Tensor)}
            
            save_file(tensors, output_path, metadata=metadata)
        else:
            torch.save(unified_model, output_path)
        
        print("✅ Unified model saved successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error saving unified model: {e}")
        return False

def extract_model_from_unified(unified_path, model_type, output_path):
    """
    Extrai um modelo específico do arquivo unificado
    """
    print(f"📤 Extracting {model_type} model from unified file")
    
    try:
        if unified_path.endswith('.safetensors'):
            from safetensors.torch import load_file
            unified_model = load_file(unified_path)
        else:
            unified_model = torch.load(unified_path, map_location='cpu')
        
        # Extrai o modelo específico
        prefix = f'{model_type}_noise.'
        extracted_model = {}
        
        for key, value in unified_model.items():
            if key.startswith(prefix):
                # Remove o prefixo
                new_key = key[len(prefix):]
                extracted_model[new_key] = value
        
        if not extracted_model:
            print(f"❌ No {model_type} model found in unified file!")
            return False
        
        # Salva o modelo extraído
        if output_path.endswith('.safetensors'):
            from safetensors.torch import save_file
            save_file(extracted_model, output_path)
        else:
            torch.save(extracted_model, output_path)
        
        print(f"✅ {model_type.title()} model extracted to: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error extracting model: {e}")
        return False

def inspect_unified_model(unified_path):
    """
    Inspeciona um modelo unificado
    """
    print("🔍 Inspecting unified model")
    print("=" * 50)
    
    try:
        if unified_path.endswith('.safetensors'):
            from safetensors.torch import load_file
            unified_model = load_file(unified_path)
        else:
            unified_model = torch.load(unified_path, map_location='cpu')
        
        # Conta os tipos de keys
        high_noise_keys = [k for k in unified_model.keys() if k.startswith('high_noise.')]
        low_noise_keys = [k for k in unified_model.keys() if k.startswith('low_noise.')]
        metadata_keys = [k for k in unified_model.keys() if k.startswith('__wan22_')]
        
        print(f"📊 Model Statistics:")
        print(f"   - High Noise keys: {len(high_noise_keys)}")
        print(f"   - Low Noise keys: {len(low_noise_keys)}")
        print(f"   - Metadata keys: {len(metadata_keys)}")
        print(f"   - Total keys: {len(unified_model)}")
        
        # Mostra metadata se disponível
        if '__wan22_unified_metadata__' in unified_model:
            metadata = unified_model['__wan22_unified_metadata__']
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            print(f"\n📋 Metadata:")
            for key, value in metadata.items():
                print(f"   - {key}: {value}")
        
        # Mostra configuração de threshold
        if '__wan22_threshold_config__' in unified_model:
            threshold_config = unified_model['__wan22_threshold_config__']
            if isinstance(threshold_config, str):
                threshold_config = json.loads(threshold_config)
            
            print(f"\n⚖️ Threshold Configuration:")
            print(f"   - Default: {threshold_config.get('default', 'N/A')}")
            
            if 'recommended' in threshold_config:
                print(f"   - Recommended:")
                for use_case, threshold in threshold_config['recommended'].items():
                    print(f"     • {use_case}: {threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="WAN 2.2 Model Unifier - Combine High/Low Noise models into a single file"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Comando para unificar
    unify_parser = subparsers.add_parser('unify', help='Unify two models into one file')
    unify_parser.add_argument('--high-noise', required=True, help='Path to High Noise model')
    unify_parser.add_argument('--low-noise', required=True, help='Path to Low Noise model')
    unify_parser.add_argument('--output', required=True, help='Output path for unified model')
    unify_parser.add_argument('--threshold', type=float, default=0.5, help='Default threshold (default: 0.5)')
    
    # Comando para extrair
    extract_parser = subparsers.add_parser('extract', help='Extract a specific model from unified file')
    extract_parser.add_argument('--unified', required=True, help='Path to unified model')
    extract_parser.add_argument('--type', choices=['high', 'low'], required=True, help='Model type to extract')
    extract_parser.add_argument('--output', required=True, help='Output path for extracted model')
    
    # Comando para inspecionar
    inspect_parser = subparsers.add_parser('inspect', help='Inspect a unified model')
    inspect_parser.add_argument('--unified', required=True, help='Path to unified model')
    
    args = parser.parse_args()
    
    if args.command == 'unify':
        success = create_unified_model(
            args.high_noise, 
            args.low_noise, 
            args.output, 
            args.threshold
        )
        exit(0 if success else 1)
        
    elif args.command == 'extract':
        success = extract_model_from_unified(
            args.unified,
            args.type,
            args.output
        )
        exit(0 if success else 1)
        
    elif args.command == 'inspect':
        success = inspect_unified_model(args.unified)
        exit(0 if success else 1)
        
    else:
        parser.print_help()
        print("\n🎭 Examples:")
        print("  # Unify models:")
        print("  python wan22_unifier.py unify --high-noise high.safetensors --low-noise low.safetensors --output unified.safetensors")
        print("\n  # Extract high noise model:")
        print("  python wan22_unifier.py extract --unified unified.safetensors --type high --output extracted_high.safetensors")
        print("\n  # Inspect unified model:")
        print("  python wan22_unifier.py inspect --unified unified.safetensors")

if __name__ == "__main__":
    main()