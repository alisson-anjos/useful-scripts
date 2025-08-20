#!/usr/bin/env python3
import torch
from safetensors.torch import load_file, save_file
import argparse
from pathlib import Path

# dimensões antigas (1.3B) e novas (14B)
OLD_H, OLD_F = 1536, 8960
NEW_H, NEW_F = 5120, 13824

def pad_lora_matrix(tensor: torch.Tensor) -> torch.Tensor:
    """
    Se tensor for 2D, pad cada eixo:
     - se rows==OLD_H → NEW_H; se rows==OLD_F → NEW_F
     - se cols==OLD_H → NEW_H; se cols==OLD_F → NEW_F
    Caso contrário, retorna cópia inalterada.
    """
    if tensor.ndim != 2:
        return tensor.clone()
    r, c = tensor.shape
    # calcula alvo
    new_r = {OLD_H: NEW_H, OLD_F: NEW_F}.get(r, r)
    new_c = {OLD_H: NEW_H, OLD_F: NEW_F}.get(c, c)
    if (new_r, new_c) == (r, c):
        return tensor.clone()
    out = torch.zeros((new_r, new_c), dtype=tensor.dtype, device=tensor.device)
    out[:r, :c] = tensor
    return out

def convert_lora(in_path: Path, out_path: Path):
    print(f"▶ Carregando LoRA 1.3B: {in_path}")
    state = load_file(str(in_path))  # safetensors → dict[str,Tensor]
    new_state = {}
    for k, t in state.items():
        t2 = pad_lora_matrix(t)
        if t2.shape != t.shape:
            print(f"  [PAD] {k}: {tuple(t.shape)} → {tuple(t2.shape)}")
        new_state[k] = t2
    print(f"▶ Salvando LoRA 14B em: {out_path}")
    save_file(new_state, str(out_path))
    print("✔ Conversão completa.")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Converte LoRA Wan2.1 1.3B → 14B (zero-pad nas matrizes)"
    )
    p.add_argument("input",  help="LoRA 1.3B (.safetensors)")
    p.add_argument("output", help="Saída para 14B (.safetensors)")
    args = p.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        print(f"❌ Arquivo não encontrado: {inp}")
        exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    convert_lora(inp, out)
