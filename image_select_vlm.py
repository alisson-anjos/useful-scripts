import os
import shutil
import json
from pathlib import Path
import time
from typing import List, Dict, Tuple, Optional
import logging
import torch
import glob
from PIL import Image
import re
from transformers import AutoProcessor, AutoModelForImageTextToText
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import gc

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StableXRayProcessor:
    def __init__(self, 
                 model_path: str = "SicariusSicariiStuff/X-Ray_Alpha",
                 device: str = "auto",
                 batch_size: int = 1,  # Começar com 1 para estabilidade
                 num_workers: int = 2,
                 max_image_size: int = 512):  # Menor para evitar problemas
        """
        Processador X-Ray Alpha estável e robusto
        
        Args:
            model_path: Caminho do modelo
            device: "auto", "cuda", "cpu"
            batch_size: Começar com 1, aumentar gradualmente
            num_workers: Workers para I/O
            max_image_size: Tamanho máximo das imagens
        """
        self.model_path = model_path
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.max_image_size = max_image_size
        self.device = self._setup_device(device)
        
        # Configurações de segurança
        self.use_batch_processing = False  # Desabilitar batch inicialmente
        self.enable_warm_up = False       # Desabilitar warm-up problemático
        
        logger.info(f"Configuração estável:")
        logger.info(f"  - Modo: Processamento individual (mais estável)")
        logger.info(f"  - Workers: {num_workers}")
        logger.info(f"  - Max image size: {max_image_size}px")
        
        self._load_model()
        
    def _setup_device(self, device: str) -> str:
        """Configura dispositivo com segurança"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                
                # Configurações conservadoras para estabilidade
                torch.backends.cudnn.benchmark = False  # Mais estável
                torch.backends.cuda.matmul.allow_tf32 = False  # Mais preciso
                
                logger.info(f"GPU: {torch.cuda.get_device_name()}")
                vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"VRAM: {vram_gb:.1f}GB")
                
                # Configurar variáveis de ambiente para debug
                os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # Para debug de erros CUDA
                
            else:
                device = "cpu"
                logger.info("Usando CPU")
        
        return device
    
    def _load_model(self):
        """Carrega modelo com configurações conservadoras"""
        try:
            # Usar float32 para máxima estabilidade
            torch_dtype = torch.float32
            
            logger.info("Carregando modelo com configurações estáveis...")
            
            # Configurações conservadoras
            model_kwargs = {
                "device_map": "auto",
                "torch_dtype": torch_dtype,
                "attn_implementation": "eager",
                "low_cpu_mem_usage": True,
            }
            
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_path, **model_kwargs
            )
            
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                use_fast=False  # Usar processador lento mais estável
            )
            
            # Configurar modelo para inferência
            self.model.eval()
            
            # Pular warm-up por causar problemas
            if self.enable_warm_up:
                self._warmup_model()
            
            logger.info("✅ Modelo carregado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise
    
    def _warmup_model(self):
        """Warm-up simplificado e seguro"""
        try:
            logger.info("Fazendo warm-up...")
            dummy_image = Image.new('RGB', (224, 224), color='white')
            
            # Warm-up simples sem batch
            result = self.process_single_image_safe(dummy_image, "Test")
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Warm-up concluído")
        except Exception as e:
            logger.warning(f"Warm-up falhou (ok para continuar): {e}")
    
    def process_single_image_safe(self, image: Image.Image, prompt_text: str) -> str:
        """
        Processa uma única imagem com máxima segurança
        """
        try:
            # Redimensionar imagem se necessário
            if max(image.size) > self.max_image_size:
                image.thumbnail((self.max_image_size, self.max_image_size), Image.Resampling.LANCZOS)
            
            # Formato de mensagem simples
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": image},
                        {"type": "text", "text": prompt_text}
                    ]
                }
            ]
            
            # Aplicar chat template
            prompt = self.processor.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # Processar com configurações conservadoras
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048  # Limitar comprimento
            )
            
            # Mover para device
            if self.device != "cpu":
                inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                         for k, v in inputs.items()}
            
            # Geração com parâmetros conservadores
            with torch.no_grad():
                try:
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=256,    # Reduzido para estabilidade
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.9,
                        num_beams=1,           # Beam search desabilitado
                        pad_token_id=self.processor.tokenizer.eos_token_id,
                        early_stopping=True,
                        no_repeat_ngram_size=2
                    )
                except Exception as gen_error:
                    logger.warning(f"Erro na geração, tentando modo mais simples: {gen_error}")
                    # Fallback para geração mais simples
                    outputs = self.model.generate(
                        inputs['input_ids'],
                        max_new_tokens=128,
                        do_sample=False,
                        pad_token_id=self.processor.tokenizer.eos_token_id
                    )
            
            # Decodificar resposta
            output_text = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            
            # Limpar resposta
            cleaned_text = self._clean_response(output_text, prompt)
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Erro no processamento seguro: {e}")
            return f"Error: Falha no processamento"
    
    def _clean_response(self, response: str, original_prompt: str) -> str:
        """Limpa a resposta removendo artefatos"""
        try:
            # Remover o prompt original da resposta
            if original_prompt in response:
                response = response.replace(original_prompt, "").strip()
            
            # Procurar por 'model' e extrair apenas a parte após
            if "model" in response:
                parts = response.split("model", 1)
                if len(parts) > 1:
                    response = parts[1].strip()
            
            # Remover prefixos específicos
            prefixes = [
                "**SÄ«cÄrius** trained **X-Ray_Alpha** to serve:",
                "Caption:", "Description:", "The image shows:", "This image shows:",
                "I can see:", "Looking at this image:", "In this image:",
                "user", "assistant", "model", "<start_of_turn>", "<end_of_turn>"
            ]
            
            for prefix in prefixes:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            # Limpar formatação
            response = re.sub(r'\n+', ' ', response)  # Quebras de linha
            response = re.sub(r'\s+', ' ', response)  # Espaços múltiplos
            response = re.sub(r'\*\*([^*]+)\*\*', r'\1', response)  # Bold
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
            return response
    
    def analyze_image_quality(self, image_path: str, quality_criteria: str) -> Dict:
        """Analisa qualidade de uma imagem"""
        try:
            image = Image.open(image_path).convert("RGB")
            
            quality_prompt = f"""
            Analyze this image quality: {quality_criteria}
            
            Respond in this exact format:
            SCORE: [number 1-10]
            PASSES: [YES or NO]
            REASON: [brief explanation]
            """
            
            result = self.process_single_image_safe(image, quality_prompt)
            
            # Extrair informações
            score = self._extract_score(result)
            passes = self._extract_passes(result)
            
            return {
                "score": score,
                "passes": passes,
                "raw_response": result,
                "issues": [] if passes else ["Below threshold"]
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de {image_path}: {e}")
            return {
                "score": 0,
                "passes": False,
                "raw_response": str(e),
                "issues": ["processing_error"]
            }
    
    def generate_caption(self, image_path: str, caption_template: str) -> str:
        """Gera caption para uma imagem"""
        try:
            image = Image.open(image_path).convert("RGB")
            
            caption = self.process_single_image_safe(image, caption_template)
            
            # Limitar a 250 caracteres
            if len(caption) > 250:
                caption = caption[:247] + "..."
            
            return caption
            
        except Exception as e:
            logger.error(f"Erro na caption de {image_path}: {e}")
            return "Error generating caption"
    
    def _extract_score(self, text: str) -> float:
        """Extrai score do texto"""
        try:
            # Procurar SCORE: [number]
            score_match = re.search(r'SCORE:\s*([0-9.]+)', text, re.IGNORECASE)
            if score_match:
                return min(10.0, max(1.0, float(score_match.group(1))))
            
            # Procurar números de 1-10
            numbers = re.findall(r'\b([1-9]|10)\b', text)
            if numbers:
                return float(numbers[0])
            
            # Análise de palavras-chave
            text_lower = text.lower()
            if any(word in text_lower for word in ['excellent', 'great', 'outstanding', 'beautiful']):
                return 8.0
            elif any(word in text_lower for word in ['good', 'nice', 'attractive', 'decent']):
                return 6.5
            elif any(word in text_lower for word in ['average', 'okay', 'fine']):
                return 5.0
            elif any(word in text_lower for word in ['poor', 'bad', 'low', 'ugly']):
                return 3.0
            
            return 5.0  # Default
            
        except Exception:
            return 5.0
    
    def _extract_passes(self, text: str) -> bool:
        """Extrai se passou no teste"""
        try:
            # Procurar PASSES: YES/NO
            passes_match = re.search(r'PASSES:\s*(YES|NO)', text, re.IGNORECASE)
            if passes_match:
                return passes_match.group(1).upper() == 'YES'
            
            # Baseado no score
            score = self._extract_score(text)
            return score >= 6.0
            
        except Exception:
            return False
    
    def process_folder_stable(self, 
                             input_folder: str,
                             output_folder: str,
                             quality_criteria: str,
                             caption_template: str,
                             min_score: float = 6.0) -> Dict:
        """
        Processa pasta com máxima estabilidade
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Encontrar imagens
        image_files = []
        for pattern in ["*.jpg", "*.jpeg", "*.png"]:
            image_files.extend(input_path.rglob(pattern))
        
        total_images = len(image_files)
        logger.info(f"🔄 PROCESSAMENTO ESTÁVEL: {total_images} imagens")
        logger.info(f"Modo: Individual (sem batch) para máxima estabilidade")
        
        stats = {
            'total': total_images,
            'processed': 0,
            'approved': 0,
            'rejected': 0,
            'errors': 0
        }
        
        start_time = time.time()
        
        # Processar uma imagem por vez
        for i, image_file in enumerate(image_files):
            try:
                if i % 100 == 0:  # Log a cada 100 imagens
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 and i > 0 else 0
                    eta = (total_images - i) / rate if rate > 0 else 0
                    
                    logger.info(f"Progresso: {i}/{total_images} | "
                              f"Taxa: {rate:.1f} imgs/s | ETA: {eta/60:.1f}min")
                
                # Analisar qualidade
                quality_result = self.analyze_image_quality(str(image_file), quality_criteria)
                
                if quality_result['score'] >= min_score and quality_result['passes']:
                    # Gerar caption
                    caption = self.generate_caption(str(image_file), caption_template)
                    
                    # Salvar arquivos
                    output_image_path = output_path / image_file.name
                    shutil.copy2(image_file, output_image_path)
                    
                    # Caption
                    caption_file = output_path / f"{image_file.stem}.txt"
                    with open(caption_file, 'w', encoding='utf-8') as f:
                        f.write(caption)
                    
                    # Metadata
                    metadata_file = output_path / f"{image_file.stem}_metadata.json"
                    metadata = {
                        'original_path': str(image_file),
                        'quality_score': quality_result['score'],
                        'quality_analysis': quality_result,
                        'caption': caption,
                        'processed_at': time.time()
                    }
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    
                    stats['approved'] += 1
                    logger.debug(f"✅ {image_file.name} (score: {quality_result['score']:.1f})")
                    
                else:
                    stats['rejected'] += 1
                    logger.debug(f"❌ {image_file.name} (score: {quality_result['score']:.1f})")
                
                stats['processed'] += 1
                
                # Limpeza de memória a cada 50 imagens
                if i % 50 == 0 and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
            except Exception as e:
                logger.error(f"Erro processando {image_file}: {e}")
                stats['errors'] += 1
                
                # Se muitos erros, parar
                if stats['errors'] > 10:
                    logger.error("Muitos erros, parando processamento")
                    break
        
        # Estatísticas finais
        elapsed_time = time.time() - start_time
        stats['processing_time'] = elapsed_time
        stats['images_per_second'] = stats['processed'] / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"\n🏁 PROCESSAMENTO CONCLUÍDO!")
        logger.info(f"Total: {stats['total']} | Processadas: {stats['processed']}")
        logger.info(f"Aprovadas: {stats['approved']} | Rejeitadas: {stats['rejected']}")
        logger.info(f"Erros: {stats['errors']}")
        logger.info(f"Tempo: {elapsed_time:.1f}s | Taxa: {stats['images_per_second']:.2f} imgs/s")
        
        return stats


# Configuração estável
if __name__ == "__main__":
    config = {
        "model_path": "SicariusSicariiStuff/X-Ray_Alpha",
        
        # Configurações conservadoras para estabilidade
        "batch_size": 1,         # Sem batch processing
        "num_workers": 2,        # Poucos workers
        "max_image_size": 512,   # Imagens menores
        
        "input_folder": "D:/Datasets/Instagram/images",
        "output_folder": "D:/Datasets/Instagram/selecteds", 
        
        "quality_criteria": """
        Rate 1-10: TECHNICAL QUALITY (40%) + BEAUTY/ATTRACTIVENESS (60%).
        6+ = good tech quality AND attractive subject.
        """,
        
        "caption_template": """
        Brief description (max 250 chars): person's appearance, pose, outfit, setting.
        """,
        
        "min_score": 6.0
    }
    
    try:
        logger.info("🛡️ INICIANDO PROCESSAMENTO ESTÁVEL")
        
        processor = StableXRayProcessor(
            model_path=config["model_path"],
            batch_size=config["batch_size"],
            num_workers=config["num_workers"],
            max_image_size=config["max_image_size"]
        )
        
        results = processor.process_folder_stable(
            input_folder=config["input_folder"],
            output_folder=config["output_folder"],
            quality_criteria=config["quality_criteria"],
            caption_template=config["caption_template"],
            min_score=config["min_score"]
        )
        
        print(f"\n🎉 SUCESSO!")
        approval_rate = results['approved'] / results['processed'] * 100 if results['processed'] > 0 else 0
        print(f"Taxa de aprovação: {approval_rate:.1f}%")
        print(f"Velocidade: {results['images_per_second']:.2f} imgs/s")
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        logger.info("\n🔧 SOLUÇÕES:")
        logger.info("1. Reiniciar Python completamente")
        logger.info("2. Limpar cache CUDA: torch.cuda.empty_cache()")
        logger.info("3. Tentar batch_size=1 e image_size=256")