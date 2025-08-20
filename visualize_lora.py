import torch
from safetensors.torch import load_file
import argparse

def format_shape(shape):
    return "[" + " ".join(f"{s:,}".replace(",", " ") for s in shape) + "]"

def get_dtype(tensor):
    return "BF16" if tensor.dtype == torch.bfloat16 else "F32" if tensor.dtype == torch.float32 else str(tensor.dtype).upper()

def visualize_lora(file_path):
    state_dict = load_file(file_path)
    hierarchy = {}

    for key, tensor in state_dict.items():
        parts = key.split(".")
        current = hierarchy
        for p in parts[:-1]:
            current = current.setdefault(p, {})
        current[parts[-1]] = {
            "shape": format_shape(tensor.shape),
            "dtype": get_dtype(tensor)
        }

    def print_recursive(tree, prefix=""):
        for k, v in tree.items():
            if isinstance(v, dict) and "shape" in v:
                print(f"{prefix}{k}\t{v['shape']}\n{v['dtype']}\n")
            elif isinstance(v, dict):
                num_children = len(v)
                print(f"{prefix}{k}({num_children}) \t\n")
                print_recursive(v, prefix + k + ".")

    print_recursive(hierarchy)

def main():
    parser = argparse.ArgumentParser(description="Visualize LoRA structure")
    parser.add_argument("--input", required=True, help="Path to LoRA .safetensors file")
    args = parser.parse_args()

    visualize_lora(args.input)

if __name__ == "__main__":
    main()
