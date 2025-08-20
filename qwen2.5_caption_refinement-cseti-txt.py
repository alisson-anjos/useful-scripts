import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Diretórios de arquivos de texto
    INPUT_DIR: str = "/workspace/dataset"    # Diretório de entrada com arquivos .txt
    OUTPUT_DIR: str = "/workspace/final"    # Diretório de saída para os arquivos refinados
    
    # Configuração do modelo
    MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    MAX_TOKENS: int = 200
    BATCH_SIZE: int = 1  # Mantido para compatibilidade, mas o processamento é arquivo a arquivo
    
    # Configurações de quantização
    USE_QUANTIZATION: bool = True  # Ativa ou desativa a quantização
    QUANTIZATION_BITS: int = 8      # Pode ser 4 ou 8
    
    # Configurações de geração
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9

# Template do prompt do sistema
SYSTEM_PROMPT = """You are an AI prompt engineer tasked with helping me modifying a list of automatically generated prompts.

Keep the original text but only do the following modifications:
- you responses should just be the prompt
- Always start each prompt with "4n1m4t3dl0g0"
- Write continuously, don't use multiple paragraphs, make the text form one coherent whole
- do not mention your task or the text itself
- The descriptions are about animated logotypes, Keep the writing and if the logo changes, describe the change, for example: the initial logo became "text...." or vice versa, always in this caption style.
- Don't refer to characters as 'characters' and 'persons', instead always use their gender or refer to them with their gender
- remove references to video such as "the video begins" or "the video features" etc., but keep those sentences meaningful
- mention the clothing details of the characters
- use only declarative sentences"""

class Qwen25Refiner:
    def __init__(self, config: Config):
        self.config = config
        
        # Preparar parâmetros para carregamento do modelo
        model_kwargs = {
            "torch_dtype": "auto",
            "device_map": "auto",
        }
        
        # Adiciona as configurações de quantização, se habilitado
        if config.USE_QUANTIZATION:
            if config.QUANTIZATION_BITS not in [4, 8]:
                raise ValueError("QUANTIZATION_BITS must be either 4 or 8")
            quantization_key = f"load_in_{config.QUANTIZATION_BITS}bit"
            model_kwargs[quantization_key] = True
        
        print(f"Loading model with settings: {model_kwargs}")
        
        # Carrega o modelo e o tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            config.MODEL_NAME,
            **model_kwargs
        )
        self.tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)

    def refine_text(self, text: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Could you enhance and refine the following text while maintaining its core meaning:\n\n{text}\n\nPlease limit the response to {self.config.MAX_TOKENS} tokens."}
        ]

        try:
            # Aplica o template do chat
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Prepara os inputs para o modelo
            model_inputs = self.tokenizer([prompt], return_tensors="pt").to(self.model.device)

            # Gera a resposta
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=self.config.MAX_TOKENS,
                do_sample=True,
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P
            )

            # Extrai a resposta gerada
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

            return response.strip()

        except Exception as e:
            print(f"Error refining text: {str(e)}")
            return ""

def main():
    # Inicializa a configuração
    config = Config(
        USE_QUANTIZATION=True,  # Ativa ou desativa a quantização
        QUANTIZATION_BITS=8     # Escolha entre 4 ou 8 bits
    )
    
    # Inicializa o modelo
    refiner = Qwen25Refiner(config)
    
    # Garante que o diretório de saída existe
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Lista os arquivos .txt no diretório de entrada
    txt_files = [f for f in os.listdir(config.INPUT_DIR) if f.endswith('.txt')]
    total_files = len(txt_files)
    print(f"Found {total_files} .txt files to process.")
    
    for idx, filename in enumerate(txt_files):
        input_path = os.path.join(config.INPUT_DIR, filename)
        output_path = os.path.join(config.OUTPUT_DIR, filename)
        try:
            with open(input_path, "r", encoding="utf-8") as file:
                input_text = file.read().strip()
            
            if not input_text:
                print(f"Skipping file {filename}: empty content")
                continue
            
            print(f"\nProcessing file {idx+1}/{total_files}: {filename}...")
            refined_text = refiner.refine_text(input_text)
            
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(refined_text)
                
            print(f"Refined text saved to {output_path}")
            
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
