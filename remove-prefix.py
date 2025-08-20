import argparse
from safetensors.torch import load_file, save_file

def remove_prefix_from_keys(input_path, output_path, prefixes):
    print(f"🔍 Loading: {input_path}")
    state_dict = load_file(input_path)

    new_state_dict = {}
    for k, v in state_dict.items():
        new_key = k
        for prefix in prefixes:
            if new_key.startswith(prefix):
                new_key = new_key[len(prefix):]
                break
        new_state_dict[new_key] = v

    print(f"🧼 Prefixes removed. Saving as: {output_path}")
    save_file(new_state_dict, output_path)
    print("✅ Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove prefixes from keys in a .safetensors file.")
    parser.add_argument("--input", type=str, required=True, help="Path to input .safetensors file")
    parser.add_argument("--output", type=str, required=True, help="Path to save output .safetensors file")
    parser.add_argument("--prefixes", nargs="+", default=["model.diffusion_model.", "diffusion_model."],
                        help="List of prefixes to remove from keys (default: model.diffusion_model., diffusion_model.)")

    args = parser.parse_args()
    remove_prefix_from_keys(args.input, args.output, args.prefixes)
