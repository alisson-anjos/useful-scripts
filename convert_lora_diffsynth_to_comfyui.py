#!/usr/bin/env python3
"""
LoRA Converter from DiffSynth format to ComfyUI (WAN) format
Usage: python lora_converter.py input_path output_path [--alpha ALPHA_VALUE]
"""

import argparse
import sys
import os
from pathlib import Path
import safetensors.torch
import torch


def convert_diffsynth_to_comfyui(input_path, output_path, default_alpha=1.0):
    """
    Converts a LoRA from DiffSynth format to ComfyUI (WAN) format
    
    Args:
        input_path (str): Path to input LoRA file
        output_path (str): Path to output LoRA file
        default_alpha (float): Default alpha value for LoRA layers
    """
    
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Loading LoRA from: {input_path}")
    
    # Load safetensors file
    try:
        sd = safetensors.torch.load_file(input_path)
    except Exception as e:
        raise RuntimeError(f"Error loading file: {e}")
    
    new_sd = {}
    
    print(f"\nOriginal keys found: {len(sd.keys())}")
    print("First 10 original keys:")
    for i, k in enumerate(sorted(sd.keys())):
        if i < 10:
            print(f"  {k}")
        elif i == 10:
            print("  ...")
            break
    
    # Process each key
    converted_count = 0
    alpha_added_count = 0
    skipped_count = 0
    
    # Key mapping for DiffSynth -> ComfyUI (WAN) conversion
    def convert_key(original_key):
        """
        Converts a key from DiffSynth format to ComfyUI (WAN) format
        
        Input:  blocks.4.cross_attn.k.lora_A.default.weight
        Output: diffusion_model.blocks.4.cross_attn.k.lora_A.weight
        """
        
        key = original_key
        
        # Check if it's a valid LoRA key
        if not (".lora_A.default.weight" in key or ".lora_B.default.weight" in key):
            return None  # Skip non-LoRA keys
        
        # Remove ".default" from the middle of the key
        # From: blocks.4.cross_attn.k.lora_A.default.weight
        # To:   blocks.4.cross_attn.k.lora_A.weight
        if ".lora_A.default.weight" in key:
            base_key = key.replace(".lora_A.default.weight", ".lora_A.weight")
        elif ".lora_B.default.weight" in key:
            base_key = key.replace(".lora_B.default.weight", ".lora_B.weight")
        else:
            return None
        
        # Add diffusion_model prefix
        new_key = f"diffusion_model.{base_key}"
        
        return new_key
    
    # Process all keys
    for original_key in sorted(sd.keys()):
        new_key = convert_key(original_key)
        
        if new_key is not None:
            # Add tensor to new dictionary
            new_sd[new_key] = sd[original_key]
            converted_count += 1
            
            # Add alpha if it's lora_A (equivalent to lora_down)
            if new_key.endswith(".lora_A.weight"):
                alpha_key = new_key.replace(".lora_A.weight", ".alpha")
                if alpha_key not in new_sd:
                    new_sd[alpha_key] = torch.tensor(default_alpha, dtype=torch.float32)
                    alpha_added_count += 1
        else:
            skipped_count += 1
            if skipped_count <= 5:  # Show only first 5 errors
                print(f"⚠️  Key not converted: {original_key}")
            elif skipped_count == 6:
                print(f"⚠️  ... and {len(sd.keys()) - converted_count - 5} more keys not converted")
    
    print(f"\n📊 Conversion statistics:")
    print(f"  ✅ Keys converted: {converted_count}")
    print(f"  ➕ Alphas added: {alpha_added_count}")
    print(f"  ⚠️  Keys skipped: {skipped_count}")
    print(f"  📦 Total keys in final file: {len(new_sd.keys())}")
    
    if len(new_sd.keys()) == 0:
        raise RuntimeError("❌ No keys were converted! Check if the file format is correct.")
    
    print("\nFirst 10 transformed keys:")
    for i, k in enumerate(sorted(new_sd.keys())):
        if i < 10:
            print(f"  {k}")
        elif i == 10:
            print("  ...")
            break
    
    # Verify converted keys follow expected pattern
    sample_keys = [k for k in new_sd.keys() if not k.endswith('.alpha')][:3]
    print(f"\n🔍 Format verification (first 3 keys):")
    for key in sample_keys:
        print(f"  ✅ {key}")
    
    # Save converted file
    print(f"\n💾 Saving converted file to: {output_path}")
    try:
        safetensors.torch.save_file(new_sd, output_path)
        print("✅ Conversion completed successfully!")
    except Exception as e:
        raise RuntimeError(f"Error saving file: {e}")
    
    return len(new_sd.keys())


def main():
    parser = argparse.ArgumentParser(
        description="Convert LoRA from DiffSynth format to ComfyUI (WAN) format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "input_path",
        help="Path to input LoRA file (DiffSynth format)"
    )
    
    parser.add_argument(
        "output_path", 
        help="Path to output LoRA file (ComfyUI format)"
    )
    
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Default alpha value for LoRA layers (common values: 1.0, 16.0, 32.0)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose mode (show more details)"
    )
    
    args = parser.parse_args()
    
    try:
        # Expand relative paths
        input_path = os.path.abspath(args.input_path)
        output_path = os.path.abspath(args.output_path)
        
        print(f"🔄 LoRA Converter: DiffSynth → ComfyUI (WAN)")
        print(f"📥 Input:  {input_path}")
        print(f"📤 Output: {output_path}")
        print(f"⚡ Alpha:  {args.alpha}")
        print("-" * 70)
        
        # Execute conversion
        total_keys = convert_diffsynth_to_comfyui(
            input_path=input_path,
            output_path=output_path,
            default_alpha=args.alpha
        )
        
        print(f"\n🎉 Conversion completed!")
        print(f"📁 File saved: {output_path}")
        print(f"🔑 Total keys: {total_keys}")
        print(f"\n💡 You can now use the LoRA in ComfyUI with WAN!")
        print(f"📝 Tip: Try alpha={args.alpha} first, adjust if needed")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Conversion error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()