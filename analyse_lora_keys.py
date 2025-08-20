#!/usr/bin/env python3
"""
LoRA Inspector - Analyze and visualize LoRA file structure
Usage: python lora_inspector.py input_path [--detailed] [--export]
"""

import argparse
import sys
import os
import json
from collections import defaultdict, Counter
import safetensors.torch
import torch


def analyze_lora_structure(input_path, detailed=False, export_json=False):
    """
    Analyzes the structure of a LoRA file
    
    Args:
        input_path (str): Path to the LoRA file
        detailed (bool): Show detailed information about each key
        export_json (bool): Export analysis to JSON file
    """
    
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    print(f"🔍 Analyzing LoRA: {input_path}")
    print(f"📁 File size: {os.path.getsize(input_path) / (1024*1024):.2f} MB")
    
    # Load safetensors file
    try:
        sd = safetensors.torch.load_file(input_path)
        print(f"✅ Successfully loaded {len(sd.keys())} keys")
    except Exception as e:
        raise RuntimeError(f"Error loading file: {e}")
    
    # Analysis data
    analysis = {
        "file_path": input_path,
        "total_keys": len(sd.keys()),
        "keys": [],
        "patterns": {},
        "statistics": {}
    }
    
    # Collect key information
    key_patterns = defaultdict(int)
    component_types = Counter()
    layer_types = Counter()
    block_numbers = Counter()
    
    print(f"\n📊 DETAILED KEY ANALYSIS")
    print("=" * 80)
    
    for i, key in enumerate(sorted(sd.keys())):
        tensor = sd[key]
        shape = list(tensor.shape)
        dtype = str(tensor.dtype)
        
        # Store key info
        key_info = {
            "key": key,
            "shape": shape,
            "dtype": dtype,
            "total_params": torch.numel(tensor)
        }
        analysis["keys"].append(key_info)
        
        # Analyze key patterns
        parts = key.split('.')
        
        # Count different components
        if len(parts) >= 3:
            if parts[0] == "diffusion_model" and len(parts) >= 4:
                if parts[1] == "blocks":
                    block_numbers[parts[2]] += 1
                    if len(parts) >= 5:
                        component_types[parts[3]] += 1
        
        # Detect LoRA patterns
        if "lora_A" in key:
            layer_types["lora_A"] += 1
        elif "lora_B" in key:
            layer_types["lora_B"] += 1
        elif "alpha" in key:
            layer_types["alpha"] += 1
        elif "lora_down" in key:
            layer_types["lora_down"] += 1
        elif "lora_up" in key:
            layer_types["lora_up"] += 1
        
        # Pattern analysis
        if "diffusion_model" in key:
            pattern = "diffusion_model.*"
        elif "blocks." in key:
            pattern = "blocks.*"
        else:
            pattern = "other"
        key_patterns[pattern] += 1
        
        # Print detailed info if requested
        if detailed or i < 20:  # Always show first 20
            print(f"{i+1:3d}. {key}")
            print(f"     Shape: {shape}, Dtype: {dtype}, Params: {torch.numel(tensor):,}")
            
            if not detailed and i == 19 and len(sd.keys()) > 20:
                print(f"     ... and {len(sd.keys()) - 20} more keys (use --detailed to see all)")
                break
    
    # Statistics
    total_params = sum(torch.numel(tensor) for tensor in sd.values())
    analysis["statistics"] = {
        "total_parameters": total_params,
        "key_patterns": dict(key_patterns),
        "component_types": dict(component_types),
        "layer_types": dict(layer_types),
        "block_numbers": dict(block_numbers)
    }
    
    # Display summary
    print(f"\n📈 SUMMARY STATISTICS")
    print("=" * 50)
    print(f"Total keys: {len(sd.keys())}")
    print(f"Total parameters: {total_params:,}")
    print(f"Average parameters per key: {total_params // len(sd.keys()):,}")
    
    print(f"\n🔗 KEY PATTERNS:")
    for pattern, count in key_patterns.items():
        print(f"  {pattern}: {count} keys")
    
    print(f"\n🏗️ COMPONENT TYPES:")
    for comp, count in component_types.most_common():
        print(f"  {comp}: {count} keys")
    
    print(f"\n⚡ LAYER TYPES:")
    for layer, count in layer_types.most_common():
        print(f"  {layer}: {count} keys")
    
    if block_numbers:
        print(f"\n🧱 BLOCK DISTRIBUTION:")
        for block in sorted(block_numbers.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
            print(f"  Block {block}: {block_numbers[block]} keys")
    
    # Sample key analysis
    print(f"\n🔍 SAMPLE KEY BREAKDOWN:")
    sample_keys = list(sd.keys())[:5]
    for key in sample_keys:
        print(f"\nKey: {key}")
        parts = key.split('.')
        print(f"  Parts: {' → '.join(parts)}")
        print(f"  Structure analysis:")
        for i, part in enumerate(parts):
            indent = "    " * (i + 1)
            print(f"{indent}[{i}] {part}")
    
    # Format detection
    print(f"\n🎯 FORMAT DETECTION:")
    if any("diffusion_model.blocks." in k for k in sd.keys()):
        print("  ✅ ComfyUI/WAN format detected (diffusion_model.blocks.*)")
    elif any(k.startswith("blocks.") and not k.startswith("diffusion_model") for k in sd.keys()):
        print("  ✅ DiffSynth format detected (blocks.* without diffusion_model prefix)")
    elif any("lora_unet" in k for k in sd.keys()):
        print("  ✅ Standard Diffusers format detected (lora_unet.*)")
    else:
        print("  ❓ Unknown format - manual analysis needed")
    
    # Export to JSON if requested
    if export_json:
        json_path = input_path.replace('.safetensors', '_analysis.json')
        with open(json_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Analysis exported to: {json_path}")
    
    return analysis


def compare_loras(file1, file2):
    """Compare two LoRA files"""
    print(f"\n🔄 COMPARING LORA FILES")
    print("=" * 50)
    
    try:
        sd1 = safetensors.torch.load_file(file1)
        sd2 = safetensors.torch.load_file(file2)
        
        keys1 = set(sd1.keys())
        keys2 = set(sd2.keys())
        
        print(f"File 1: {len(keys1)} keys")
        print(f"File 2: {len(keys2)} keys")
        
        common_keys = keys1 & keys2
        only_in_1 = keys1 - keys2
        only_in_2 = keys2 - keys1
        
        print(f"\nCommon keys: {len(common_keys)}")
        print(f"Only in file 1: {len(only_in_1)}")
        print(f"Only in file 2: {len(only_in_2)}")
        
        if only_in_1:
            print(f"\n🔸 Keys only in {file1}:")
            for key in sorted(list(only_in_1)[:10]):
                print(f"  {key}")
            if len(only_in_1) > 10:
                print(f"  ... and {len(only_in_1) - 10} more")
        
        if only_in_2:
            print(f"\n🔹 Keys only in {file2}:")
            for key in sorted(list(only_in_2)[:10]):
                print(f"  {key}")
            if len(only_in_2) > 10:
                print(f"  ... and {len(only_in_2) - 10} more")
                
    except Exception as e:
        print(f"❌ Error comparing files: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and visualize LoRA file structure",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "input_path",
        help="Path to LoRA file to analyze"
    )
    
    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed information for all keys"
    )
    
    parser.add_argument(
        "--export", "-e",
        action="store_true",
        help="Export analysis to JSON file"
    )
    
    parser.add_argument(
        "--compare", "-c",
        help="Compare with another LoRA file"
    )
    
    args = parser.parse_args()
    
    try:
        # Expand relative paths
        input_path = os.path.abspath(args.input_path)
        
        print(f"🔍 LoRA Inspector")
        print("-" * 50)
        
        # Analyze main file
        analysis = analyze_lora_structure(
            input_path=input_path,
            detailed=args.detailed,
            export_json=args.export
        )
        
        # Compare with another file if requested
        if args.compare:
            compare_path = os.path.abspath(args.compare)
            compare_loras(input_path, compare_path)
        
        print(f"\n✅ Analysis completed!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Analysis error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()