#!/usr/bin/env python3
import torch
import re
from safetensors.torch import load_file, save_file
import argparse
from pathlib import Path

# dimensões do embed e MLP do Wan2.1 1.3B vs 14B
OLD_H, OLD_F = 1536, 8960
NEW_H, NEW_F = 5120, 13824
NUM_LAYERS_1B = 30  # 0..29

def crop_tensor(t: torch.Tensor) -> torch.Tensor:
    """
    Corta qualquer tensor 2D ou 1D de tamanho NEW_* para seu equivalente OLD_*.
    Outros dims são clonados.
    """
    # 2D
    if t.ndim == 2:
        r, c = t.shape
        tgt_r = OLD_H if r == NEW_H else OLD_F if r == NEW_F else r
        tgt_c = OLD_H if c == NEW_H else OLD_F if c == NEW_F else c
        if (tgt_r, tgt_c) != (r, c):
            return t[:tgt_r, :tgt_c].clone()
        return t.clone()

    # 1D
    if t.ndim == 1:
        L = t.shape[0]
        if L % NEW_H == 0:
            m = L // NEW_H
            return t[:OLD_H * m].clone()
        if L % NEW_F == 0:
            m = L // NEW_F
            return t[:OLD_F * m].clone()
        return t.clone()

    return t.clone()

def convert_14b_to_13b(in_path: Path, out_path: Path):
    print(f"▶ Carregando LoRA 14B: {in_path}")
    state = load_file(str(in_path))
    new_state = {}
    for key, t in state.items():
        # remove keys de bloco além do suporte do 1.3B
        m = re.search(r"blocks\.(\d+)\.", key)
        if m and int(m.group(1)) >= NUM_LAYERS_1B:
            print(f"  [SKIP] {key} (layer >= {NUM_LAYERS_1B})")
            continue

        t2 = crop_tensor(t)
        if t2.shape != t.shape:
            print(f"  [CROP] {key}: {tuple(t.shape)} → {tuple(t2.shape)}")
        new_state[key] = t2

    print(f"▶ Salvando LoRA 1.3B em: {out_path}")
    save_file(new_state, str(out_path))
    print("✔ Conversão 14B→1.3B completa (layers extras descartadas).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crop LoRA Wan2.1 14B → 1.3B (descarta blocks 30+ e corta tensores)"
    )
    parser.add_argument("input",  help="LoRA 14B (.safetensors)")
    parser.add_argument("output", help="Saída para 1.3B (.safetensors)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        print(f"❌ Arquivo não encontrado: {inp}")
        exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    convert_14b_to_13b(inp, out)
