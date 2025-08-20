import os
import shutil
from pathlib import Path
from PIL import Image
import logging
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import argparse
import sys
import cv2
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextPersonDetector:
    def __init__(self, 
                 source_folder: str,
                 output_folder: str = None,
                 copy_files: bool = True,
                 max_workers: int = 4,
                 confidence_threshold: float = 0.5):
        """
        Detector de texto e pessoas em imagens
        
        Args:
            source_folder: Pasta com as imagens
            output_folder: Pasta de saída
            copy_files: True para copiar, False para mover
            max_workers: Workers para processamento paralelo
            confidence_threshold: Threshold de confiança para detecções
        """
        self.source_folder = Path(source_folder)
        self.output_folder = Path(output_folder) if output_folder else self.source_folder / "organized_by_content"
        self.copy_files = copy_files
        self.max_workers = max_workers
        self.confidence_threshold = confidence_threshold
        
        # Extensões suportadas
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
        
        # Categorias de organização
        self.categories = {
            "has_text": "with_text",
            "has_person": "with_person", 
            "has_both": "text_and_person",
            "no_text_no_person": "no_text_no_person",
            "error": "processing_errors"
        }
        
        logger.info(f"📁 Pasta origem: {self.source_folder}")
        logger.info(f"📁 Pasta destino: {self.output_folder}")
        logger.info(f"🔄 Modo: {'Copiar' if copy_files else 'Mover'}")
        
        self._load_models()
        
    def _load_models(self):
        """Carrega modelos para detecção"""
        logger.info("🤖 Carregando modelos de detecção...")
        
        try:
            # Carregar EasyOCR para detecção de texto
            import easyocr
            self.text_reader = easyocr.Reader(['pt', 'en'], gpu=True if cv2.cuda.getCudaEnabledDeviceCount() > 0 else False)
            logger.info("✅ EasyOCR carregado")
        except ImportError:
            logger.error("❌ EasyOCR não instalado. Execute: pip install easyocr")
            raise
        except Exception as e:
            logger.warning(f"⚠️ Erro carregando EasyOCR com GPU, usando CPU: {e}")
            import easyocr
            self.text_reader = easyocr.Reader(['pt', 'en'], gpu=False)
        
        try:
            # Carregar YOLOv4 ou usar Haar Cascades como fallback
            self._load_person_detector()
            logger.info("✅ Detector de pessoas carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando detector de pessoas: {e}")
            raise
    
    def _load_person_detector(self):
        """Carrega detector de pessoas"""
        try:
            # Tentar YOLOv4 primeiro (mais preciso)
            self.detection_method = "yolo"
            # Você pode baixar os pesos YOLO de: https://github.com/AlexeyAB/darknet
            # Por simplicidade, vamos usar Haar Cascades que vem com OpenCV
            raise FileNotFoundError("Usando Haar Cascades como padrão")
            
        except FileNotFoundError:
            # Fallback para Haar Cascades (menos preciso mas funciona)
            self.detection_method = "haar"
            self.person_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            if self.person_cascade.empty() or self.face_cascade.empty():
                logger.error("❌ Não foi possível carregar Haar Cascades")
                raise
            
            logger.info("ℹ️ Usando Haar Cascades para detecção de pessoas")
    
    def detect_text(self, image_path: str) -> Tuple[bool, List[str], float]:
        """
        Detecta texto na imagem
        
        Returns:
            Tuple com (has_text, detected_texts, confidence)
        """
        try:
            # Ler imagem
            image = cv2.imread(image_path)
            if image is None:
                return False, [], 0.0
            
            # Converter para RGB para EasyOCR
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detectar texto
            results = self.text_reader.readtext(rgb_image)
            
            # Filtrar por confiança
            detected_texts = []
            max_confidence = 0.0
            
            for (bbox, text, confidence) in results:
                if confidence >= self.confidence_threshold:
                    detected_texts.append(text.strip())
                    max_confidence = max(max_confidence, confidence)
            
            has_text = len(detected_texts) > 0
            
            return has_text, detected_texts, max_confidence
            
        except Exception as e:
            logger.error(f"Erro na detecção de texto em {image_path}: {e}")
            return False, [], 0.0
    
    def detect_person(self, image_path: str) -> Tuple[bool, int, float]:
        """
        Detecta pessoas na imagem
        
        Returns:
            Tuple com (has_person, person_count, confidence)
        """
        try:
            # Ler imagem
            image = cv2.imread(image_path)
            if image is None:
                return False, 0, 0.0
            
            if self.detection_method == "haar":
                return self._detect_person_haar(image)
            else:
                return self._detect_person_yolo(image)
                
        except Exception as e:
            logger.error(f"Erro na detecção de pessoa em {image_path}: {e}")
            return False, 0, 0.0
    
    def _detect_person_haar(self, image: np.ndarray) -> Tuple[bool, int, float]:
        """Detecta pessoas usando Haar Cascades"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar corpos inteiros
        bodies = self.person_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=3,
            minSize=(30, 30)
        )
        
        # Detectar rostos
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )
        
        # Considerar tanto corpos quanto rostos
        total_detections = len(bodies) + len(faces)
        has_person = total_detections > 0
        
        # Simular confiança baseada no número de detecções
        confidence = min(0.9, total_detections * 0.3) if has_person else 0.0
        
        return has_person, total_detections, confidence
    
    def _detect_person_yolo(self, image: np.ndarray) -> Tuple[bool, int, float]:
        """Detecta pessoas usando YOLO (implementação placeholder)"""
        # Implementação YOLO aqui se você tiver os pesos
        # Por enquanto retorna False
        return False, 0, 0.0
    
    def analyze_image(self, image_path: Path) -> Dict:
        """
        Analisa uma imagem para texto e pessoas
        
        Returns:
            Dict com resultados da análise
        """
        try:
            # Verificar se é imagem suportada
            if image_path.suffix.lower() not in self.supported_extensions:
                return {"error": "Extensão não suportada"}
            
            # Detectar texto
            has_text, detected_texts, text_confidence = self.detect_text(str(image_path))
            
            # Detectar pessoas
            has_person, person_count, person_confidence = self.detect_person(str(image_path))
            
            # Determinar categoria
            if has_text and has_person:
                category = "has_both"
            elif has_text:
                category = "has_text"
            elif has_person:
                category = "has_person"
            else:
                category = "no_text_no_person"
            
            # Informações da análise
            analysis = {
                "has_text": has_text,
                "detected_texts": detected_texts,
                "text_confidence": text_confidence,
                "has_person": has_person,
                "person_count": person_count,
                "person_confidence": person_confidence,
                "category": category,
                "folder_name": self.categories[category],
                "file_size": image_path.stat().st_size,
                "original_path": str(image_path)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro analisando {image_path}: {e}")
            return {"error": str(e), "category": "error", "folder_name": self.categories["error"]}
    
    def create_output_folders(self):
        """Cria as pastas de saída"""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Criar pastas para cada categoria
        for category, folder_name in self.categories.items():
            folder_path = self.output_folder / folder_name
            folder_path.mkdir(exist_ok=True)
            logger.debug(f"📁 Pasta criada: {folder_name}")
    
    def find_all_images(self) -> List[Path]:
        """Encontra todas as imagens na pasta"""
        logger.info("🔍 Escaneando imagens...")
        
        image_files = []
        for ext in self.supported_extensions:
            image_files.extend(self.source_folder.rglob(f"*{ext}"))
            image_files.extend(self.source_folder.rglob(f"*{ext.upper()}"))
        
        # Remover duplicatas
        unique_files = list(set(image_files))
        
        logger.info(f"📸 Encontradas {len(unique_files)} imagens")
        return unique_files
    
    def organize_images(self) -> Dict:
        """
        Organiza todas as imagens por conteúdo
        
        Returns:
            Estatísticas do processamento
        """
        # Criar pastas de saída
        self.create_output_folders()
        
        # Encontrar imagens
        image_files = self.find_all_images()
        
        if not image_files:
            logger.warning("❌ Nenhuma imagem encontrada!")
            return {"total": 0, "processed": 0, "errors": 0}
        
        # Estatísticas
        stats = {
            "total": len(image_files),
            "processed": 0,
            "errors": 0,
            "categories": {folder: 0 for folder in self.categories.values()},
            "text_detections": [],
            "person_detections": []
        }
        
        # Processar imagens em paralelo
        logger.info(f"🤖 Analisando {len(image_files)} imagens com {self.max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter todas as tarefas
            future_to_path = {
                executor.submit(self.analyze_image, img_path): img_path 
                for img_path in image_files
            }
            
            # Processar resultados
            for i, future in enumerate(as_completed(future_to_path)):
                img_path = future_to_path[future]
                
                try:
                    analysis = future.result()
                    
                    if "error" not in analysis:
                        # Determinar destino
                        dest_folder = self.output_folder / analysis["folder_name"]
                        dest_path = dest_folder / img_path.name
                        
                        # Evitar sobrescrever
                        counter = 1
                        original_dest = dest_path
                        while dest_path.exists():
                            stem = original_dest.stem
                            suffix = original_dest.suffix
                            dest_path = dest_folder / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        # Copiar ou mover arquivo
                        if self.copy_files:
                            shutil.copy2(img_path, dest_path)
                        else:
                            shutil.move(str(img_path), str(dest_path))
                        
                        # Atualizar estatísticas
                        stats["categories"][analysis["folder_name"]] += 1
                        stats["processed"] += 1
                        
                        # Salvar análise detalhada
                        if analysis.get("has_text"):
                            stats["text_detections"].append({
                                "file": img_path.name,
                                "texts": analysis["detected_texts"],
                                "confidence": analysis["text_confidence"]
                            })
                        
                        if analysis.get("has_person"):
                            stats["person_detections"].append({
                                "file": img_path.name,
                                "count": analysis["person_count"],
                                "confidence": analysis["person_confidence"]
                            })
                        
                        # Salvar metadados
                        metadata_file = dest_path.with_suffix('.json')
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(analysis, f, indent=2, ensure_ascii=False)
                        
                        logger.debug(f"✅ {img_path.name} → {analysis['folder_name']}")
                        
                    else:
                        stats["errors"] += 1
                        logger.error(f"❌ Erro processando {img_path.name}: {analysis.get('error', 'Desconhecido')}")
                
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"❌ Erro geral com {img_path}: {e}")
                
                # Log de progresso
                if i % 50 == 0:
                    progress = (i + 1) / len(image_files) * 100
                    logger.info(f"📊 Progresso: {i+1}/{len(image_files)} ({progress:.1f}%)")
        
        return stats
    
    def generate_report(self, stats: Dict):
        """Gera relatório detalhado"""
        logger.info(f"\n📊 RELATÓRIO DE ANÁLISE DE CONTEÚDO")
        logger.info(f"=" * 50)
        logger.info(f"Total de imagens: {stats['total']}")
        logger.info(f"Processadas com sucesso: {stats['processed']}")
        logger.info(f"Erros: {stats['errors']}")
        
        if stats['categories']:
            logger.info(f"\n📁 DISTRIBUIÇÃO POR CATEGORIA:")
            for folder, count in stats['categories'].items():
                percentage = (count / stats['processed']) * 100 if stats['processed'] > 0 else 0
                logger.info(f"  {folder}: {count} imagens ({percentage:.1f}%)")
        
        logger.info(f"\n📝 DETECÇÕES DE TEXTO: {len(stats['text_detections'])}")
        logger.info(f"👤 DETECÇÕES DE PESSOAS: {len(stats['person_detections'])}")
        
        # Salvar relatório detalhado
        report_path = self.output_folder / "analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Relatório detalhado salvo em: {report_path}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Organiza imagens detectando texto e pessoas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python text_person_detector.py /path/to/images
  python text_person_detector.py /path/to/images -o /path/to/output
  python text_person_detector.py /path/to/images --move -w 8
  python text_person_detector.py /path/to/images --confidence 0.7

Pastas criadas:
  with_text/           - Imagens com texto detectado
  with_person/         - Imagens com pessoas detectadas  
  text_and_person/     - Imagens com texto E pessoas
  no_text_no_person/   - Imagens sem texto nem pessoas
  processing_errors/   - Imagens com erro no processamento

Requisitos:
  pip install opencv-python easyocr
        """
    )
    
    parser.add_argument(
        "source_folder",
        help="Pasta contendo as imagens para analisar"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Pasta de saída (padrão: source_folder/organized_by_content)",
        default=None
    )
    
    parser.add_argument(
        "--move",
        action="store_true",
        help="Mover arquivos ao invés de copiar"
    )
    
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=4,
        help="Número de workers paralelos (padrão: 4)"
    )
    
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Threshold de confiança para detecções (0.0-1.0, padrão: 0.5)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verboso"
    )
    
    return parser.parse_args()


def main():
    """Função principal"""
    args = parse_arguments()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar pasta de origem
    source_path = Path(args.source_folder)
    if not source_path.exists():
        logger.error(f"❌ Pasta de origem não existe: {source_path}")
        sys.exit(1)
    
    # Determinar pasta de saída
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = source_path / "organized_by_content"
    
    # Validar threshold
    if not 0.0 <= args.confidence <= 1.0:
        logger.error("❌ Confidence deve estar entre 0.0 e 1.0")
        sys.exit(1)
    
    logger.info("🤖 DETECTOR DE TEXTO E PESSOAS")
    logger.info(f"📁 Pasta origem: {source_path}")
    logger.info(f"📁 Pasta destino: {output_path}")
    logger.info(f"🔄 Operação: {'Mover' if args.move else 'Copiar'}")
    logger.info(f"🎯 Confiança: {args.confidence}")
    logger.info(f"⚡ Workers: {args.workers}")
    
    try:
        # Criar detector
        detector = TextPersonDetector(
            source_folder=str(source_path),
            output_folder=str(output_path),
            copy_files=not args.move,
            max_workers=args.workers,
            confidence_threshold=args.confidence
        )
        
        # Organizar imagens
        stats = detector.organize_images()
        
        # Gerar relatório
        detector.generate_report(stats)
        
        print(f"\n🎉 ANÁLISE CONCLUÍDA!")
        print(f"📁 Imagens organizadas em: {output_path}")
        print(f"📊 {stats['processed']}/{stats['total']} imagens processadas")
        
        if stats['categories']:
            print(f"\n📈 RESUMO DAS CATEGORIAS:")
            for folder, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"  {folder}: {count} imagens")
        
        print(f"\n🔍 DETECÇÕES:")
        print(f"  📝 Texto: {len(stats['text_detections'])} imagens")
        print(f"  👤 Pessoas: {len(stats['person_detections'])} imagens")
        
        if stats['errors'] > 0:
            print(f"  ⚠️ Erros: {stats['errors']} imagens")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        logger.info("\n💡 VERIFICAÇÕES:")
        logger.info("1. Instale as dependências: pip install opencv-python easyocr")
        logger.info("2. Verifique se há imagens na pasta")
        logger.info("3. Verifique permissões de escrita")
        sys.exit(1)


if __name__ == "__main__":
    main()