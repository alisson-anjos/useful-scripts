import torch
import argparse
import os
from safetensors.torch import load_file as load_safetensors

def load_model_weights(path):
    if path.endswith(".safetensors"):
        return load_safetensors(path)
    else:
        return torch.load(path, map_location="cpu")

def compare_model_keys(model1_path, model2_path, show_shape_diff=False):
    model1 = load_model_weights(model1_path)
    model2 = load_model_weights(model2_path)

    keys1 = set(model1.keys())
    keys2 = set(model2.keys())

    only_in_model1 = keys1 - keys2
    only_in_model2 = keys2 - keys1
    common_keys = keys1 & keys2

    print(f"\n🔹 Layers only in {os.path.basename(model1_path)}:")
    for key in sorted(only_in_model1):
        print(f"  - {key}")

    print(f"\n🔹 Layers only in {os.path.basename(model2_path)}:")
    for key in sorted(only_in_model2):
        print(f"  - {key}")

    if show_shape_diff:
        print(f"\n🔸 Layers with shape differences:")
        for key in sorted(common_keys):
            if model1[key].shape != model2[key].shape:
                print(f"  - {key}: {tuple(model1[key].shape)} vs {tuple(model2[key].shape)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare layer names and shapes between two model files.")
    parser.add_argument("--model1", type=str, required=True, help="Path to the first model (.safetensors or .pt)")
    parser.add_argument("--model2", type=str, required=True, help="Path to the second model (.safetensors or .pt)")
    parser.add_argument("--show-shape-diff", action="store_true", help="Show shape differences for common layers")

    args = parser.parse_args()
    compare_model_keys(args.model1, args.model2, args.show_shape_diff)
