import torch
import argparse
from safetensors.torch import load_file, save_file
from tqdm import tqdm
import os

LORA_TARGET_MODULES = [
    ".attn.qkv.weight", ".attn.proj.weight",
    ".img_attn.qkv.weight", ".img_attn.proj.weight",
    ".txt_attn.qkv.weight", ".txt_attn.proj.weight",
    ".img_mod.lin.weight", ".txt_mod.lin.weight", ".modulation.lin.weight",
    "ffn.1.weight", "ffn.2.weight", "mlp.fc1.weight", "mlp.fc2.weight",
]

def is_target_module(key: str) -> bool:
    return any(key.endswith(target) for target in LORA_TARGET_MODULES)

def create_arch_lora(
    base_model_path: str,
    tuned_model_path: str,
    arch_patch_output_path: str,
    lora_output_path: str,
    rank: int,
    alpha: float,
    device: str,
    precision: str,
    prune_rate: float,
):
    print("--- Fase 1: Carregando Modelos ---")
    base_sd = load_file(base_model_path, device="cpu")
    tuned_sd = load_file(tuned_model_path, device="cpu")
    final_dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}.get(precision, torch.bfloat16)

    base_keys, tuned_keys = set(base_sd.keys()), set(tuned_sd.keys())
    common_keys = base_keys & tuned_keys
    new_keys = tuned_keys - base_keys  # Camadas que só existem no modelo ajustado

    print("\n--- Fase 2: Análise de Arquitetura ---")
    print(f"  - {len(common_keys)} layers em comum (serão usadas para o LoRA).")
    print(f"  - {len(new_keys)} layers novas encontradas (irão para o patch de arquitetura).")

    # Dicionários para os dois arquivos de saída
    arch_patch_sd = {}
    lora_sd = {}

    # --- 2a. Criar o Patch de Arquitetura ---
    if new_keys:
        print("\n--- Fase 3a: Criando Patch de Arquitetura ---")
        for key in tqdm(new_keys, desc="  Extraindo layers novas"):
            arch_patch_sd[key] = tuned_sd[key].cpu().to(final_dtype).contiguous()
        
        print(f"💾 Salvando Patch de Arquitetura em: {arch_patch_output_path}")
        save_file(arch_patch_sd, arch_patch_output_path)
    else:
        print("\n--- Fase 3a: Nenhuma camada nova encontrada. Nenhum patch de arquitetura será criado. ---")


    # --- 2b. Criar o LoRA de Diferença com DARE+SVD ---
    print("\n--- Fase 3b: Criando LoRA de Diferença (DARE+SVD) ---")
    processed_count = 0
    for key in tqdm(common_keys, desc="  Processando diffs"):
        if not is_target_module(key):
            continue
        
        processed_count += 1
        base_tensor = base_sd[key].to(device=device, dtype=torch.float32)
        tuned_tensor = tuned_sd[key].to(device=device, dtype=torch.float32)

        if base_tensor.shape != tuned_tensor.shape: continue
        diff = tuned_tensor - base_tensor
        if diff.dim() not in [2, 4]: continue

        if prune_rate > 0:
            diff_flat = diff.flatten()
            num_to_prune = int(len(diff_flat) * prune_rate)
            if num_to_prune > 0:
                threshold = torch.kthvalue(diff_flat.abs(), k=num_to_prune).values
                diff[diff.abs() < threshold] = 0

        original_shape = diff.shape
        try:
            if diff.dim() == 4: diff = diff.reshape(original_shape[0], -1)
            U, S, Vh = torch.linalg.svd(diff)
            U, S, Vh = U[:, :rank], S[:rank], Vh[:rank, :]
            lora_down, lora_up = Vh, U @ torch.diag(S)

            if len(original_shape) == 4:
                lora_down = lora_down.reshape(rank, original_shape[1], *original_shape[2:])
                lora_up = lora_up.reshape(original_shape[0], rank, 1, 1)

            lora_key_base = key.rsplit('.', 1)[0]
            lora_sd[f"{lora_key_base}.lora_down.weight"] = lora_down.cpu().to(final_dtype).contiguous()
            lora_sd[f"{lora_key_base}.lora_up.weight"] = lora_up.cpu().to(final_dtype).contiguous()
            lora_sd[f"{lora_key_base}.alpha"] = torch.tensor(alpha, dtype=torch.float32).cpu()
        except Exception as e:
            print(f"🔥 Erro SVD na layer {key}: {e}. Ignorando.")
            continue

    if not lora_sd:
        print("\n❌ Nenhum LoRA foi criado.")
    else:
        print(f"\n✅ {processed_count} camadas foram processadas e extraídas para o LoRA.")
        metadata = {"ss_network_module": "networks.lora", "ss_network_rank": str(rank), "ss_network_alpha": str(alpha)}
        print(f"💾 Salvando LoRA de Diferença em: {lora_output_path}")
        save_file(lora_sd, lora_output_path, metadata=metadata)
        
    print("\n✅ Processo concluído!")

# O resto do script com argparse permanece o mesmo, ajustando os argumentos de saída.
def main():
    parser = argparse.ArgumentParser(description="Extrai um Patch de Arquitetura e um LoRA de Diferença entre dois modelos.")
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--tuned_model", type=str, required=True)
    parser.add_argument("--arch_patch_output", type=str, required=True, help="Caminho para salvar o patch de arquitetura (.safetensors).")
    parser.add_argument("--lora_output", type=str, required=True, help="Caminho para salvar o LoRA de diferença (.safetensors).")
    parser.add_argument("--rank", type=int, default=128)
    parser.add_argument("--alpha", type=float, default=128.0)
    parser.add_argument("--prune_rate", type=float, default=0.0, help="Taxa de poda DARE. Recomendo 0 por agora para garantir que todas as diferenças sejam capturadas.")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--precision", type=str, default="bf16", choices=["fp32", "fp16", "bf16"])
    args = parser.parse_args()

    create_arch_lora(
        base_model_path=args.base_model, tuned_model_path=args.tuned_model,
        arch_patch_output_path=args.arch_patch_output, lora_output_path=args.lora_output,
        rank=args.rank, alpha=args.alpha, device=args.device,
        precision=args.precision, prune_rate=args.prune_rate
    )

if __name__ == "__main__":
    main()