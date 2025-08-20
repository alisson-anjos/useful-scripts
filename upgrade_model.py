import torch
import argparse
from safetensors.torch import load_file, save_file, safe_open
from tqdm import tqdm
import os

def upgrade_model_final(
    base_model_path: str,
    tuned_model_path: str,
    output_path: str,
    device: str,
):
    print(f"--- Fase 1: Carregando Modelo Base na Memória ---")
    print(f"  Base: {base_model_path}")
    final_sd = load_file(base_model_path, device="cpu")
    base_keys = set(final_sd.keys())
    print(f"  Modelo base carregado. {len(base_keys)} camadas.")

    print(f"\n--- Fase 2: Aplicando Diferença via Streaming (Preservando dtype) ---")
    print(f"  Modelo a ser aplicado (streaming): {tuned_model_path}")
    
    with safe_open(tuned_model_path, framework="pt", device="cpu") as f_tuned:
        tuned_keys = set(f_tuned.keys())
        
        common_keys = base_keys & tuned_keys
        for key in tqdm(common_keys, desc="  Atualizando camadas comuns"):
            
            # --- CORREÇÃO DE PRECISÃO AQUI ---
            # 1. Lembre-se do dtype original
            original_dtype = final_sd[key].dtype
            
            # 2. Faça o cálculo em float32 para precisão
            base_tensor = final_sd[key].to(device=device, dtype=torch.float32)
            tuned_tensor = f_tuned.get_tensor(key).to(device=device, dtype=torch.float32)

            if base_tensor.shape != tuned_tensor.shape:
                final_sd[key] = f_tuned.get_tensor(key).clone().to('cpu') # Mantém o dtype do tuned
                continue

            diff = tuned_tensor - base_tensor
            
            # 3. Converta o resultado de volta para o dtype original antes de salvar
            final_sd[key] = (base_tensor + diff).to(dtype=original_dtype, device='cpu')
            # ------------------------------------

        new_keys = tuned_keys - base_keys
        if new_keys:
            print(f"\n--- Adicionando {len(new_keys)} Camadas Novas ---")
            for key in tqdm(new_keys, desc="  Adicionando camadas novas"):
                final_sd[key] = f_tuned.get_tensor(key).clone().to('cpu')

    print("\n--- Fase 3: Salvando o Modelo Final ---")
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    print(f"💾 Salvando modelo completo e atualizado em: {output_path}")
    
    metadata = {}
    try:
        with open(tuned_model_path, 'rb') as f:
            header_size = int.from_bytes(f.read(8), 'little')
            if header_size > 0:
                import json
                header_data = json.loads(f.read(header_size).decode('utf-8'))
                if "__metadata__" in header_data:
                    metadata = header_data["__metadata__"]
    except Exception as e:
        print(f"Não foi possível ler metadados: {e}")

    save_file(final_sd, output_path, metadata=metadata)
    print("\n✅ Processo concluído com sucesso! O tamanho do arquivo deve ser o correto.")

def main():
    parser = argparse.ArgumentParser(description="Cria um modelo completo atualizado preservando o dtype original.")
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--tuned_model", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    upgrade_model_final(
        base_model_path=args.base_model,
        tuned_model_path=args.tuned_model,
        output_path=args.output_path,
        device=args.device,
    )

if __name__ == "__main__":
    main()