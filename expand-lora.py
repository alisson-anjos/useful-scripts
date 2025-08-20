import argparse
from safetensors.torch import load_file, save_file

def expand_model(base_path, patch_path, output_path, allow_conflicts=False):
    print(f"📂 Base (keep existing): {patch_path}")
    print(f"➕ Adding missing from: {base_path}")

    base = load_file(base_path)
    patch = load_file(patch_path)

    new_state = dict(patch)  # start with Chroma
    added = 0
    skipped = 0
    conflict = 0

    for k, v in base.items():
        if k not in new_state:
            new_state[k] = v
            added += 1
        elif new_state[k].shape != v.shape:
            conflict += 1
            if allow_conflicts:
                print(f"⚠️ Conflict on shape, replacing anyway: {k}")
                new_state[k] = v
            else:
                print(f"⛔ Shape mismatch, keeping original: {k}")
        else:
            skipped += 1

    print("\n✅ Summary:")
    print(f"  ➕ Added new layers: {added}")
    print(f"  ↔️ Skipped existing (same shape): {skipped}")
    print(f"  ⚠️ Conflicts (shape mismatch): {conflict}")

    print(f"\n💾 Saving to: {output_path}")
    save_file(new_state, output_path)
    print("✅ Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand a model by adding missing layers from another.")
    parser.add_argument("--base", required=True, help="Path to the model that has extra layers (e.g. flux)")
    parser.add_argument("--patch", required=True, help="Path to the model to expand (e.g. chroma)")
    parser.add_argument("--output", required=True, help="Path to save the expanded model")
    parser.add_argument("--allow-conflicts", action="store_true", help="Force overwrite on shape conflict")

    args = parser.parse_args()
    expand_model(args.base, args.patch, args.output, args.allow_conflicts)
